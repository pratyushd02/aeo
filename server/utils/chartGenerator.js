const { ChartJSNodeCanvas } = require("chartjs-node-canvas");
const fs = require("fs");

async function generateBarChart(data, filePath) {
  const width = 800;
  const height = 600;
  const chartJSNodeCanvas = new ChartJSNodeCanvas({ width, height });

  const configuration = {
    type: "bar",
    data: {
      labels: Object.keys(data),
      datasets: [{
        label: "Mentions",
        data: Object.values(data)
      }]
    }
  };

  const buffer = await chartJSNodeCanvas.renderToBuffer(configuration);
  fs.writeFileSync(filePath, buffer);
}

module.exports = generateBarChart;