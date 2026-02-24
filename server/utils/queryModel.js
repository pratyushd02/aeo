const axios = require("axios");

const API_URL = "https://chat.binghamton.edu/api/chat/completions";
const API_KEY = process.env.API_KEY;

async function queryModel(model, prompt) {
  try {
    const response = await axios.post(
      API_URL,
      {
        model,
        messages: [{ role: "user", content: prompt }]
      },
      {
        headers: {
          Authorization: `Bearer ${API_KEY}`,
          "Content-Type": "application/json"
        }
      }
    );

    return response.data.choices[0].message.content;
  } catch (err) {
    return `ERROR: ${err.message}`;
  }
}

module.exports = queryModel;