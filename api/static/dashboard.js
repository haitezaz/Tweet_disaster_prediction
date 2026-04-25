const AUTO_REFRESH_MS = 30000;
const BUCKET_MINUTES = 5;

const refs = {
  windowSelect: document.getElementById("windowSelect"),
  refreshButton: document.getElementById("refreshButton"),
  statusDot: document.getElementById("statusDot"),
  statusText: document.getElementById("statusText"),
  updatedAt: document.getElementById("updatedAt"),
  metricTotal: document.getElementById("metricTotal"),
  metricTrue: document.getElementById("metricTrue"),
  metricFalse: document.getElementById("metricFalse"),
  metricTrueRate: document.getElementById("metricTrueRate"),
  metricConfidence: document.getElementById("metricConfidence"),
  recentTableBody: document.getElementById("recentTableBody"),
};

let timelineChart;
let sourceChart;
let refreshTimer;

function setStatus(text, ok) {
  refs.statusText.textContent = text;
  refs.statusDot.style.background = ok ? "#4ecdc4" : "#ff6b4a";
}

function formatPercent(value) {
  return `${Number(value).toFixed(2)}%`;
}

function formatConfidence(value) {
  return `${(Number(value) * 100).toFixed(1)}%`;
}

function formatUtcTime(timestamp) {
  const d = new Date(timestamp);
  if (Number.isNaN(d.getTime())) {
    return "-";
  }
  return d.toISOString().slice(11, 19);
}

function renderSummary(summary) {
  refs.metricTotal.textContent = summary.total ?? 0;
  refs.metricTrue.textContent = summary.true_count ?? 0;
  refs.metricFalse.textContent = summary.false_count ?? 0;
  refs.metricTrueRate.textContent = formatPercent(summary.true_rate ?? 0);
  refs.metricConfidence.textContent = formatConfidence(summary.avg_confidence ?? 0);
}

function renderTimeline(series) {
  const labels = series.map((item) => item.label);
  const trueVals = series.map((item) => item.true);
  const falseVals = series.map((item) => item.false);

  if (timelineChart) {
    timelineChart.destroy();
  }

  const ctx = document.getElementById("timelineChart");
  timelineChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "True",
          data: trueVals,
          borderColor: "#ff6b4a",
          backgroundColor: "rgba(255, 107, 74, 0.24)",
          fill: true,
          tension: 0.35,
          pointRadius: 2,
        },
        {
          label: "False",
          data: falseVals,
          borderColor: "#4ecdc4",
          backgroundColor: "rgba(78, 205, 196, 0.2)",
          fill: true,
          tension: 0.35,
          pointRadius: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          labels: { color: "#e6edf2" },
        },
      },
      scales: {
        x: {
          ticks: { color: "#b6c8d1" },
          grid: { color: "rgba(182, 200, 209, 0.12)" },
        },
        y: {
          beginAtZero: true,
          ticks: { color: "#b6c8d1", precision: 0 },
          grid: { color: "rgba(182, 200, 209, 0.12)" },
        },
      },
    },
  });
}

function renderSources(sources) {
  const labels = sources.map((item) => item.name);
  const vals = sources.map((item) => item.count);

  if (sourceChart) {
    sourceChart.destroy();
  }

  const ctx = document.getElementById("sourceChart");
  sourceChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data: vals,
          borderWidth: 1,
          borderColor: "rgba(15, 23, 32, 0.75)",
          backgroundColor: [
            "#ff6b4a",
            "#4ecdc4",
            "#f7b267",
            "#b4f8c8",
            "#7aa6ff",
          ],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#e6edf2" },
        },
      },
    },
  });
}

function badgeClass(disaster) {
  return disaster ? "badge badge-true" : "badge badge-false";
}

function badgeText(disaster) {
  return disaster ? "True" : "False";
}

function renderRecent(rows) {
  if (!rows || rows.length === 0) {
    refs.recentTableBody.innerHTML = '<tr><td colspan="6" class="empty-row">No records found for this window.</td></tr>';
    return;
  }

  refs.recentTableBody.innerHTML = rows
    .map((row) => {
      const confidence = `${(Number(row.confidence || 0) * 100).toFixed(1)}%`;
      return `
        <tr>
          <td>${formatUtcTime(row.timestamp)}</td>
          <td><span class="${badgeClass(row.disaster)}">${badgeText(row.disaster)}</span></td>
          <td>${confidence}</td>
          <td>${row.source || "unknown"}</td>
          <td>${row.location || "Unknown"}</td>
          <td title="${row.text || ""}">${row.text_preview || "-"}</td>
        </tr>
      `;
    })
    .join("");
}

async function loadData() {
  const windowMinutes = Number(refs.windowSelect.value) || 60;
  const url = `/dashboard/data?window_minutes=${windowMinutes}&bucket_minutes=${BUCKET_MINUTES}`;

  setStatus("Loading data", true);

  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  const payload = await response.json();

  renderSummary(payload.summary || {});
  renderTimeline(payload.series || []);
  renderSources(payload.sources || []);
  renderRecent(payload.recent || []);

  const generatedAt = payload.generated_at ? formatUtcTime(payload.generated_at) : "-";
  refs.updatedAt.textContent = `Updated: ${generatedAt} UTC`;

  setStatus("Live", true);
}

async function refreshDashboard() {
  try {
    await loadData();
  } catch (err) {
    setStatus("Data unavailable", false);
    refs.updatedAt.textContent = "Updated: failed";
  }
}

function setupAutoRefresh() {
  if (refreshTimer) {
    window.clearInterval(refreshTimer);
  }
  refreshTimer = window.setInterval(refreshDashboard, AUTO_REFRESH_MS);
}

function bootstrap() {
  refs.refreshButton.addEventListener("click", refreshDashboard);
  refs.windowSelect.addEventListener("change", refreshDashboard);
  refreshDashboard();
  setupAutoRefresh();
}

bootstrap();
