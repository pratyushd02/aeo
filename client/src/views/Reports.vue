<template>
  <div class="container">
    <h2>Summary & Sources Report</h2>

    <div class="section">
      <label>Upload Excel File:</label>
      <input type="file" @change="handleFileUpload" accept=".xlsx" />
    </div>

    <div class="section">
      <label>Select LLM Model:</label>
      <select v-model="selectedModel">
        <option v-for="model in models" :key="model">
          {{ model }}
        </option>
      </select>
    </div>

    <div class="section buttons">
      <button @click="generateSummary" :disabled="loading">
        Generate Summary Report
      </button>

      <button @click="generateSources" :disabled="loading">
        Generate Sources Report
      </button>
    </div>

    <div v-if="loading" class="loading">
      Processing... please wait.
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import API from "../services/api";

const selectedFile = ref(null);
const selectedModel = ref("mixtral:8x22b");
const loading = ref(false);

const models = [
  "mixtral:8x22b",
  "gpt-oss:120b",
  "codellama:70B",
  "gemma3:latest",
  "hermes3:latest",
  "llama3.1:70B",
  "phi4:latest",
  "qwen2.5-coder:32B",
  "qwq:latest",
];

function handleFileUpload(event) {
  selectedFile.value = event.target.files[0];
}

async function generateSummary() {
  if (!selectedFile.value) {
    alert("Please upload an Excel file.");
    return;
  }

  loading.value = true;

  const formData = new FormData();
  formData.append("file", selectedFile.value);
  formData.append("model", selectedModel.value);

  try {
    const response = await API.post("/summary", formData, {
      responseType: "blob",
    });

    downloadFile(response.data, "summary_report.pdf");
  } catch (err) {
    alert("Error generating summary report.");
  }

  loading.value = false;
}

async function generateSources() {
  if (!selectedFile.value) {
    alert("Please upload an Excel file.");
    return;
  }

  loading.value = true;

  const formData = new FormData();
  formData.append("file", selectedFile.value);
  formData.append("model", selectedModel.value);

  try {
    const response = await API.post("/sources", formData, {
      responseType: "blob",
    });

    downloadFile(response.data, "sources_report.pdf");
  } catch (err) {
    alert("Error generating sources report.");
  }

  loading.value = false;
}

function downloadFile(blobData, filename) {
  const url = window.URL.createObjectURL(new Blob([blobData]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
}
</script>

<style scoped>
.container {
  padding: 40px;
  max-width: 700px;
}

.section {
  margin-bottom: 20px;
}

.buttons button {
  margin-right: 10px;
  padding: 8px 14px;
}

.loading {
  margin-top: 20px;
  font-weight: bold;
}
</style>