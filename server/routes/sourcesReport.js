// routes/sourcesReport.js

const express = require("express");
const multer = require("multer");
const XLSX = require("xlsx");
const PDFDocument = require("pdfkit");
const fs = require("fs");
const path = require("path");
const { ChartJSNodeCanvas } = require("chartjs-node-canvas");

const queryModel = require("../utils/queryModel");
const { extractAllDomains, classifySource } = require("../utils/sourceUtils");

const router = express.Router();
const upload = multer({ dest: "uploads/" });

/**
 * Generate pie chart image
 */
async function generatePieChart(categoryCounts, filePath) {
  const width = 700;
  const height = 700;
  const chartJSNodeCanvas = new ChartJSNodeCanvas({ width, height });

  const config = {
    type: "pie",
    data: {
      labels: Object.keys(categoryCounts),
      datasets: [
        {
          data: Object.values(categoryCounts),
        },
      ],
    },
  };

  const buffer = await chartJSNodeCanvas.renderToBuffer(config);
  fs.writeFileSync(filePath, buffer);
}

/**
 * POST /api/sources
 */
router.post("/", upload.single("file"), async (req, res) => {
  try {
    const workbook = XLSX.readFile(req.file.path);

    let allSources = [];

    workbook.SheetNames.forEach((sheetName) => {
      const sheet = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName]);

      sheet.forEach((row) => {
        const sourceText = row.Sources || row.sources;
        const domains = extractAllDomains(sourceText);

        domains.forEach((domain) => {
          allSources.push({
            Model: sheetName,
            Website: domain,
            Category: classifySource(domain),
          });
        });
      });
    });

    if (allSources.length === 0) {
      return res.status(400).json({ error: "No valid sources found." });
    }

    // -------------------------
    // Aggregations
    // -------------------------

    const categoryCounts = {};
    const websiteCounts = {};

    allSources.forEach((s) => {
      categoryCounts[s.Category] =
        (categoryCounts[s.Category] || 0) + 1;

      websiteCounts[s.Website] =
        (websiteCounts[s.Website] || 0) + 1;
    });

    const topWebsites = Object.entries(websiteCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .reduce((obj, [k, v]) => ({ ...obj, [k]: v }), {});

    // -------------------------
    // LLM Summary
    // -------------------------

    const summaryPrompt = `
You are analyzing sources used by multiple AI models for graduate program prompts.

Models: ${workbook.SheetNames.join(", ")}
Total sources: ${allSources.length}
Category breakdown: ${JSON.stringify(categoryCounts)}
Top 10 websites: ${JSON.stringify(topWebsites)}

Write a short bullet-point summary describing:
- General source patterns
- Biases
- Missing source types
`;

    const llmSummary = await queryModel(req.body.model, summaryPrompt);

    // -------------------------
    // Generate Chart
    // -------------------------

    const chartPath = path.join(
      "uploads",
      `pie_${Date.now()}.png`
    );

    await generatePieChart(categoryCounts, chartPath);

    // -------------------------
    // Generate PDF
    // -------------------------

    const pdfPath = path.join(
      "uploads",
      `sources_${Date.now()}.pdf`
    );

    const doc = new PDFDocument();
    doc.pipe(fs.createWriteStream(pdfPath));

    doc.fontSize(18).text("Sources Report", { underline: true });
    doc.moveDown();

    doc.fontSize(14).text("1. LLM Summary", { underline: true });
    doc.moveDown();
    doc.fontSize(10).text(llmSummary);
    doc.moveDown(2);

    doc.fontSize(14).text("2. Source Type Distribution", { underline: true });
    doc.moveDown();

    doc.image(chartPath, {
      fit: [400, 400],
      align: "center",
    });

    doc.addPage();

    doc.fontSize(14).text("3. Website Breakdown", { underline: true });
    doc.moveDown();

    Object.entries(websiteCounts)
      .sort((a, b) => b[1] - a[1])
      .forEach(([site, count]) => {
        doc.fontSize(10).text(`${site} — ${count}`);
      });

    doc.end();

    doc.on("finish", () => {
      res.download(pdfPath);
    });

  } catch (err) {
    console.error(err);
    res.status(500).json({
      error: "Failed to generate sources report.",
    });
  }
});

module.exports = router;