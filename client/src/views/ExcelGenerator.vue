<template>
  <div>
    <h2>AI Visibility Generator</h2>

    <textarea v-model="promptText" rows="6"></textarea>

    <div v-for="model in models" :key="model">
      <input type="checkbox" :value="model" v-model="selectedModels">
      {{ model }}
    </div>

    <button @click="generateExcel">Generate Excel</button>
  </div>
</template>

<script setup>
import { ref } from "vue";
import API from "../services/api";

const models = [
  "gpt-oss:120b",
  "mixtral:8x22b",
  "llama3.1:70B"
];

const selectedModels = ref([]);
const promptText = ref("");

async function generateExcel() {
  const prompts = promptText.value.split("\n");

  const response = await API.post(
    "/excel",
    {
      models: selectedModels.value,
      prompts
    },
    { responseType: "blob" }
  );

  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", "results.xlsx");
  document.body.appendChild(link);
  link.click();
}
</script>