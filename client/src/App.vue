<template>
  <div>
    <nav class="navbar">
      <button @click="currentView = 'excel'">Excel Generator</button>
      <button @click="currentView = 'reports'">Reports</button>
    </nav>

    <ExcelGenerator v-if="currentView === 'excel'" />
    <Reports v-if="currentView === 'reports'" />
  </div>
</template>

<script setup>
import { ref } from "vue";
import ExcelGenerator from "./views/ExcelGenerator.vue";
import Reports from "./views/Reports.vue";

const currentView = ref("excel");
</script>

<style>
.navbar {
  padding: 20px;
  background: #f5f5f5;
}

.navbar button {
  margin-right: 10px;
  padding: 8px 12px;
}
</style>