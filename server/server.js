const express = require("express");
const cors = require("cors");
require("dotenv").config();

const generateExcel = require("./routes/generateExcel");
const summaryReport = require("./routes/summaryReport");
const sourcesReport = require("./routes/sourcesReport");

const app = express();
app.use(cors());
app.use(express.json());

const corsOptions = {
  origin: "*", // Adjust this to your frontend's URL for better security
  methods: ["GET", "HEAD", "PUT", "PATCH", "POST", "DELETE"],
  allowedHeaders: ["Authorization", "Content-Type"],
};

app.use(cors(corsOptions));

const authenticate = (req, res, next) => {
  const authHeader = req.headers.authorization;
  console.log("Authorization Header:", authHeader); // Log the header for debugging

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    console.error("Authorization header missing or invalid");
    return res.status(401).json({ message: "Unauthorized" });
  }

  const token = authHeader.split(" ")[1];
  console.log("Token from Header:", token);
  console.log("Token from .env:", process.env.AUTH_TOKEN);

  if (token !== process.env.AUTH_TOKEN) {
    console.error("Invalid token provided");
    return res.status(401).json({ message: "Invalid token" });
  }

  next();
};

app.use("/api/excel", authenticate, generateExcel);
app.use("/api/summary", authenticate, summaryReport);
app.use("/api/sources", authenticate, sourcesReport);

app.listen(5000, () => console.log("Server running on port 5000"));