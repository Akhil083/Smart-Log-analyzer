let timelineChart = null;

document.addEventListener("DOMContentLoaded", () => {
  initializeAnalytics();

  document
    .getElementById("refreshAnalyticsBtn")
    ?.addEventListener("click", initializeAnalytics);

  document
    .getElementById("semanticSearchBtn")
    ?.addEventListener("click", performSemanticSearch);

  document
    .getElementById("runClusterBtn")
    ?.addEventListener("click", loadClusters);

  document
    .getElementById("timelineInterval")
    ?.addEventListener("change", loadTimeline);

  document
    .getElementById("applyAnalyticsFiltersBtn")
    ?.addEventListener("click", initializeAnalytics);

  document
    .getElementById("clearAnalyticsFiltersBtn")
    ?.addEventListener("click", clearFilters);
});

async function initializeAnalytics() {
  try {
    updateLastRefresh();

    await Promise.all([
      loadSummary(),
      loadWarningCount(),
      loadCriticalCount(),
      loadTimeline(),
      loadAnomalies(),
      loadClusters(),
      loadServiceDistribution(),
      loadFilterOptions(),
    ]);
  } catch (error) {
    console.error("Analytics initialization failed", error);
  }
}

/* ======================================================
   FILTERS
====================================================== */

function getFilters() {
  const params = new URLSearchParams();

  const service = document.getElementById("filterService")?.value;

  const level = document.getElementById("filterLevel")?.value;

  const environment = document.getElementById("filterEnvironment")?.value;

  if (service) params.append("service", service);

  if (level) params.append("level", level);

  if (environment) params.append("environment", environment);

  return params.toString();
}

function clearFilters() {
  document.getElementById("filterService").value = "";
  document.getElementById("filterLevel").value = "";
  document.getElementById("filterEnvironment").value = "";

  initializeAnalytics();
}

/* ======================================================
   SUMMARY
====================================================== */

async function loadSummary() {
  const filters = getFilters();

  const response = await fetch(getApiUrl(`/analytics/summary?${filters}`));

  const data = await response.json();

  document.getElementById("totalLogs").textContent = formatNumber(
    data.total_logs,
  );

  document.getElementById("errorLogs").textContent = formatNumber(
    data.error_logs,
  );
}

/* ======================================================
   WARNING COUNT
====================================================== */

async function loadWarningCount() {
  const filters = getFilters();

  const response = await fetch(
    getApiUrl(`/analytics/warning-count?${filters}`),
  );

  const data = await response.json();

  document.getElementById("warningLogs").textContent = formatNumber(
    data.warning_logs,
  );
}

/* ======================================================
   CRITICAL COUNT
====================================================== */

async function loadCriticalCount() {
  const filters = getFilters();

  const response = await fetch(
    getApiUrl(`/analytics/critical-count?${filters}`),
  );

  const data = await response.json();

  document.getElementById("criticalLogs").textContent = formatNumber(
    data.critical_logs,
  );
}

/* ======================================================
   SERVICE DISTRIBUTION
====================================================== */

async function loadServiceDistribution() {
  const filters = getFilters();

  const [serviceResponse, errorResponse] = await Promise.all([
    fetch(getApiUrl(`/analytics/service?${filters}`)),

    fetch(getApiUrl(`/analytics/top-error-services?${filters}`)),
  ]);

  const serviceData = await serviceResponse.json();

  const errorData = await errorResponse.json();

  const container = document.getElementById("serviceDistribution");

  if (!container) {
    console.error("serviceDistribution container not found");
    return;
  }

  container.innerHTML = "";

  const errorMap = {};

  errorData.items.forEach((item) => {
    errorMap[item.service] = item.errors;
  });

  Object.entries(serviceData).forEach(([service, totalLogs]) => {
    const errors = errorMap[service] || 0;

    const errorRate =
      totalLogs > 0 ? ((errors / totalLogs) * 100).toFixed(1) : "0.0";

    const card = document.createElement("div");

    card.className = "distribution-card";

    card.innerHTML = `
    <h4>${service}</h4>

    <div class="service-health-metrics">

        <span class="service-total">
            ${totalLogs}
        </span>

        <span class="service-errors">
            ${errors}
        </span>

        <span class="service-error-rate">
            ${errorRate}%
        </span>

    </div>
`;

    container.appendChild(card);
  });
}

function renderDistribution(containerId, distribution) {
  const container = document.getElementById(containerId);

  container.innerHTML = "";

  if (!distribution) {
    container.innerHTML = `<div class="empty-state">
                No data available
            </div>`;

    return;
  }

  Object.entries(distribution).forEach(([key, value]) => {
    const card = document.createElement("div");

    card.className = "distribution-card";

    card.innerHTML = `
                <h4>${key}</h4>
                <span>${value}</span>
            `;

    container.appendChild(card);
  });
}

/* ======================================================
   TIMELINE
====================================================== */

async function loadTimeline() {
  const interval = document.getElementById("timelineInterval").value;
  const filters = getFilters();

  const response = await fetch(
    getApiUrl(`/analytics/timeline?interval=${interval}&${filters}`),
  );

  const data = await response.json();

  const canvas = document.getElementById("timelineChart");

  if (!canvas) {
    console.error("timelineChart not found");
    return;
  }

  const timelineData = data.item || [];

  if (!timelineData.length) {
    return;
  }

  const labels = timelineData.map((point) => formatDate(point.time));

  const values = timelineData.map((point) => point.total);
  const errors = timelineData.map((point) => point.errors);
  const warnings = timelineData.map((point) => point.warnings);
  const criticals = timelineData.map((point) => point.criticals);

  if (timelineChart) {
    timelineChart.destroy();
  }

  timelineChart = new Chart(canvas, {
    type: "line",

    data: {
      labels,

      datasets: [
        {
          label: "Total Logs",
          data: values,
          borderColor: "#2563eb",
          backgroundColor: "rgba(37, 99, 235, 0.05)",
          fill: true,
          tension: 0.35,
          pointRadius: 3,
        },
        {
          label: "Warnings",
          data: warnings,
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.05)",
          fill: true,
          tension: 0.35,
          pointRadius: 3,
        },
        {
          label: "Errors",
          data: errors,
          borderColor: "#dc2626",
          backgroundColor: "rgba(220, 38, 38, 0.05)",
          fill: true,
          tension: 0.35,
          pointRadius: 3,
        },
        {
          label: "Critical",
          data: criticals,
          borderColor: "#7f1d1d",
          backgroundColor: "rgba(127, 29, 29, 0.05)", // Deep red fill
          fill: true,
          tension: 0.35,
          pointRadius: 3,
        },
      ],
    },

    options: {
      responsive: true,

      maintainAspectRatio: false,

      plugins: {
        legend: {
          display: true,
          position: "top",
          labels: {
            usePointStyle: true,
            boxWidth: 10,
          },
        },
      },

      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });
}
/* ======================================================
   ANOMALIES
====================================================== */

async function loadAnomalies() {
  const filters = getFilters();

  const response = await fetch(
    getApiUrl(`/analytics/timeline/anomalies${filters}`),
  );

  const data = await response.json();

  const container = document.getElementById("anomalyContainer");

  container.innerHTML = "";

  const anomalies = data.item?.filter((item) => item.anomaly) || [];

  if (!anomalies.length) {
    container.innerHTML = `<div class="empty-state">
                No anomalies detected
            </div>`;

    return;
  }

  anomalies.forEach((item) => {
    const card = document.createElement("div");

    card.className = "anomaly-card";

    card.innerHTML = `
            <h4>Anomaly Detected</h4>
            <p>${formatDate(item.time)}</p>
            <strong>${item.total} logs</strong>
        `;

    container.appendChild(card);
  });
}

/* ======================================================
   CLUSTERS
====================================================== */

async function loadClusters() {
  const limit = document.getElementById("clusterLimit").value;

  const nClusters = document.getElementById("clusterCount").value;
  const filters = getFilters();

  const response = await fetch(
    getApiUrl(
      `/analytics/clusters?limit=${limit}&n_clusters=${nClusters}&${filters}`,
    ),
  );

  const data = await response.json();

  const container = document.getElementById("clusterResults");

  container.innerHTML = "";

  if (!data.clusters?.length) {
    container.innerHTML = `<div class="empty-state">
                No cluster data available
            </div>`;

    return;
  }

  data.clusters.forEach((cluster) => {
    const card = document.createElement("div");

    card.className = "cluster-card";

    card.innerHTML = `
            <h4>
                Cluster ${cluster.cluster_id}
            </h4>

            <p>
                ${cluster.sample_message}
            </p>

            <div class="cluster-size">
                ${cluster.size} logs
            </div>
        `;

    container.appendChild(card);
  });
}

/* ======================================================
   SEMANTIC SEARCH
====================================================== */

async function performSemanticSearch() {
  const query = document.getElementById("semanticQuery").value.trim();
  const topK = document.getElementById("topK").value;

  const candidateLimit = document.getElementById("candidateLimit").value;

  if (!query) return;

  const url = getApiUrl(
    `/analytics/semantic_search` +
      `?query=${encodeURIComponent(query)}` +
      `&top_k=${topK}` +
      `&candidate_limit=${candidateLimit}` +
      `&${filters}`,
  );

  const response = await fetch(url);

  const data = await response.json();

  const container = document.getElementById("semanticResults");

  container.innerHTML = "";

  if (!data.results?.length) {
    container.innerHTML = `<div class="empty-state">
                No matching logs found
            </div>`;

    return;
  }

  data.results.forEach((result) => {
    const card = document.createElement("div");

    card.className = "semantic-result-card";

    card.innerHTML = `
    <div class="score">
        Similarity:
        ${(result.score * 100).toFixed(2)}%
    </div>
    <div class="meta-row">
        <span>${result.log.service}</span>
        <span>${result.log.level}</span>
        <span>Trace: ${result.log.trace_id || "-"}</span>
        <span>Request: ${result.log.request_id || "-"}</span>
    </div>
    <div class="message">
        ${result.log.message}
    </div>

    
`;

    container.appendChild(card);
  });
}

/* ======================================================
   UTILITIES
====================================================== */

function updateLastRefresh() {
  const element = document.getElementById("lastUpdated");

  if (element) {
    element.textContent = new Date().toLocaleString();
  }
}

function formatDate(value) {
  return new Date(value).toLocaleString();
}

function formatNumber(value) {
  return Number(value).toLocaleString();
}
