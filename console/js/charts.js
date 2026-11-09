import { fetchSensorHistory } from "./api.js";

let tempChart = null;
let humChart = null;

function renderChart(canvasId, label, dataArray, borderColor, existingChart) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) {
    return existingChart;
  }
  if (existingChart) {
    existingChart.destroy();
  }
  const ctx = canvas.getContext("2d");
  return new Chart(ctx, {
    type: "line",
    data: {
      labels: dataArray.labels,
      datasets: [
        {
          label,
          data: dataArray.values,
          borderColor,
          tension: 0.1,
          fill: false,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { display: false },
        y: {
          beginAtZero: false,
          title: { display: false },
        },
      },
    },
  });
}

export async function refreshCharts() {
  try {
    const rawData = await fetchSensorHistory();
    const data = rawData.reverse();
    const labels = data.map((d) => d.timestamp.replace("_", " "));
    const temperatures = data.map((d) => d.temperature);
    const humidities = data.map((d) => d.humidity);
    tempChart = renderChart(
      "tempChart",
      "Temperature",
      { labels, values: temperatures },
      "rgb(255, 99, 132)",
      tempChart
    );
    humChart = renderChart(
      "humChart",
      "Humidity",
      { labels, values: humidities },
      "rgb(75, 192, 192)",
      humChart
    );
  } catch (error) {
    console.error("Error fetching or processing data:", error);
  }
}

export function startChartPolling(intervalMs = 300000) {
  refreshCharts();
  setInterval(refreshCharts, intervalMs);
}
