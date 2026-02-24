const express = require("express");
const ExcelJS = require("exceljs");
const queryModel = require("../utils/queryModel");

const router = express.Router();

router.post("/", async (req, res) => {

  console.log("Request Body:", req.body);
  console.log("Request Headers:", req.headers);
  const { models, prompts } = req.body;

  const workbook = new ExcelJS.Workbook();

  for (const model of models) {
    const sheet = workbook.addWorksheet(model.slice(0, 6));
    sheet.addRow(["Prompt", "Response", "Sources"]);

    for (const prompt of prompts) {
      const fullPrompt = `${prompt}
      Please include a section titled 'Sources'.`;

      const responseText = await queryModel(model, fullPrompt);

      const urls = responseText.match(/https?:\/\/[^\s)]+/g) || [];
      const sources = urls.join("\n");

      sheet.addRow([prompt, responseText, sources]);

      await new Promise(r => setTimeout(r, 15000)); // 15 sec delay
    }
  }

  res.setHeader(
    "Content-Type",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  );

  await workbook.xlsx.write(res);
  res.end();
});

module.exports = router;