const express = require("express");
const cors = require("cors");

const generateExcel = require("./routes/generateExcel");
const summaryReport = require("./routes/summaryReport");
const sourcesReport = require("./routes/sourcesReport");

const app = express();
app.use(cors());
app.use(express.json());

app.use("/api/excel", generateExcel);
app.use("/api/summary", summaryReport);
app.use("/api/sources", sourcesReport);

app.listen(5000, () => console.log("Server running on port 5000"));