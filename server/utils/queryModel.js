const axios = require("axios");

const API_URL = "https://chat.binghamton.edu/api/chat/completions";
const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  throw new Error("API_KEY is not defined in the environment variables.");
}

async function queryModel(model, prompt) {
  try {
    const response = await axios.post(
      API_URL,
      {
        model,
        messages: [{ role: "user", content: prompt }],
      },
      {
        headers: {
          Authorization: `Bearer ${API_KEY}`,
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.data || !response.data.choices || response.data.choices.length === 0) {
      throw new Error("Invalid response structure from the API.");
    }

    return response.data.choices[0].message.content;
  } catch (err) {
    console.error("Error querying model:", err.response?.data || err.message);
    return `ERROR: ${err.response?.data?.error?.message || err.message}`;
  }
}

module.exports = queryModel;