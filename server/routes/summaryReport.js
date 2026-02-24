const express = require("express");
const multer = require("multer");
const XLSX = require("xlsx");
const PDFDocument = require("pdfkit");
const fs = require("fs");
const queryModel = require("../utils/queryModel");

const upload = multer({ dest: "uploads/" });
const router = express.Router();

router.post("/", upload.single("file"), async (req, res) => {
  const workbook = XLSX.readFile(req.file.path);
  let allText = "";

  workbook.SheetNames.forEach(sheetName => {
    const sheet = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName]);
    sheet.forEach(row => {
      allText += `Prompt: ${row.Prompt}\nResponse: ${row.Response}\n\n`;
    });
  });

  const summary = await queryModel(req.body.model, `
  Summarize this dataset into bullet points:
  ${allText}
  `);

  const doc = new PDFDocument();
  const filePath = `uploads/summary_${Date.now()}.pdf`;
  doc.pipe(fs.createWriteStream(filePath));

  doc.fontSize(14).text("Summary Report", { underline: true });
  doc.moveDown();
  doc.fontSize(10).text(summary);

  doc.end();

  doc.on("finish", () => {
    res.download(filePath);
  });
});

module.exports = router;