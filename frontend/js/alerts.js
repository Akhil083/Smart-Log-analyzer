document.addEventListener("DOMContentLoaded", () => {
  initializeAlertsPage();
});

let currentFilters = {};

async function initializeAlertsPage() {
  registerEvents();

  await Promise.all([
    loadAlertStatistics(),
    loadAlerts(),
    loadRecentAlertsFeed(),
  ]);

  updateLastRefreshTime();
}

/* ==========================================
   EVENT LISTENERS
========================================== */

function registerEvents() {
  document
    .getElementById("refreshAlertsBtn")
    .addEventListener("click", refreshPage);

  document
    .getElementById("applyFiltersBtn")
    .addEventListener("click", applyFilters);

  document
    .getElementById("clearFiltersBtn")
    .addEventListener("click", clearFilters);

  document
    .getElementById("alertCheckForm")
    .addEventListener("submit", runAlertCheck);
}

/* ==========================================
   REFRESH
========================================== */

async function refreshPage() {
  await Promise.all([
    loadAlertStatistics(),
    loadAlerts(),
    loadRecentAlertsFeed(),
  ]);

  updateLastRefreshTime();
}

/* ==========================================
   ALERT STATISTICS
========================================== */

async function loadAlertStatistics() {
  try {
    const alertsResponse = await fetch(`${API_BASE_URL}/alerts?limit=500`);

    const alertsData = await alertsResponse.json();

    const alerts = alertsData.items || [];

    document.getElementById("totalAlerts").textContent = formatNumber(
      alertsData.total || alerts.length,
    );

    let criticalCount = 0;
    let highCount = 0;

    alerts.forEach((alert) => {
      if (alert.severity === "CRITICAL") {
        criticalCount++;
      }

      if (alert.severity === "HIGH") {
        highCount++;
      }
    });

    document.getElementById("criticalAlerts").textContent =
      formatNumber(criticalCount);

    document.getElementById("highSeverityAlerts").textContent =
      formatNumber(highCount);

    try {
      const activeResponse = await fetch(`${API_BASE_URL}/alerts/active-count`);

      const activeData = await activeResponse.json();

      document.getElementById("activeAlerts").textContent = formatNumber(
        activeData.active_alerts,
      );
    } catch {
      document.getElementById("activeAlerts").textContent = formatNumber(
        alerts.length,
      );
    }
  } catch (error) {
    console.error("Failed to load alert statistics", error);
  }
}

/* ==========================================
   LOAD ALERTS TABLE
========================================== */

async function loadAlerts() {
  try {
    const query = new URLSearchParams();

    Object.entries(currentFilters).forEach(([key, value]) => {
      if (value) {
        query.append(key, value);
      }
    });

    query.append("limit", "500");

    const response = await fetch(`${API_BASE_URL}/alerts?${query.toString()}`);

    const data = await response.json();

    renderAlertsTable(data.items || []);
  } catch (error) {
    console.error("Failed to load alerts", error);
  }
}

/* ==========================================
   ALERT TABLE
========================================== */

function renderAlertsTable(alerts) {
  const tbody = document.getElementById("alertsTableBody");

  tbody.innerHTML = "";

  if (!alerts.length) {
    tbody.innerHTML = `
            <tr>
                <td colspan="8">
                    No alerts found
                </td>
            </tr>
        `;

    return;
  }

  alerts.forEach((alert) => {
    const row = document.createElement("tr");

    row.innerHTML = `
            <td>${alert.id}</td>
            <td>${alert.service}</td>
            <td>${alert.metric}</td>

            <td>
                <span class="badge ${getSeverityClass(alert.severity)}">
                    ${alert.severity}
                </span>
            </td>

            <td>${alert.value}</td>
            <td>${alert.threshold}</td>

            <td>
                ${truncate(alert.message, 60)}
            </td>

            <td>
                ${formatDate(alert.created_at)}
            </td>
        `;

    tbody.appendChild(row);
  });
}

/* ==========================================
   RECENT ALERT FEED
========================================== */

async function loadRecentAlertsFeed() {
  try {
    const response = await fetch(`${API_BASE_URL}/alerts?limit=5`);

    const data = await response.json();

    const alerts = data.items || [];

    const container = document.getElementById("recentAlertsFeed");

    container.innerHTML = "";

    if (!alerts.length) {
      container.innerHTML = `<p>No recent alerts.</p>`;

      return;
    }

    alerts.forEach((alert) => {
      const item = document.createElement("div");

      item.className = "alert-feed-item";

      item.innerHTML = `
                <div class="alert-feed-header">

                    <span class="badge ${getSeverityClass(alert.severity)}">
                        ${alert.severity}
                    </span>

                    <small>
                        ${formatDate(alert.created_at)}
                    </small>

                </div>

                <p>${alert.message}</p>

                <small>
                    ${alert.service}
                </small>
            `;

      container.appendChild(item);
    });
  } catch (error) {
    console.error("Failed to load alert feed", error);
  }
}

/* ==========================================
   RUN ALERT CHECK
========================================== */

async function runAlertCheck(event) {
  event.preventDefault();

  try {
    const threshold = document.getElementById("threshold").value;

    const service = document.getElementById("service").value;

    const interval = document.getElementById("interval").value;

    const params = new URLSearchParams();

    params.append("threshold", threshold);

    params.append("interval", interval);

    if (service) {
      params.append("service", service);
    }

    const response = await fetch(
      `${API_BASE_URL}/alerts/check?${params.toString()}`,
    );

    const result = await response.json();

    const container = document.getElementById("alertCheckResult");

    container.innerHTML = `
            <div class="success-message">
                Alert evaluation completed.
                Triggered:
                <strong>
                    ${result.alert_triggered}
                </strong>
            </div>
        `;

    await refreshPage();
  } catch (error) {
    console.error(error);

    document.getElementById("alertCheckResult").innerHTML = `
            <div class="error-message">
                Failed to run alert evaluation.
            </div>
        `;
  }
}

/* ==========================================
   FILTERS
========================================== */

function applyFilters() {
  currentFilters = {
    service: document.getElementById("filterService").value.trim(),

    metric: document.getElementById("filterMetric").value.trim(),

    severity: document.getElementById("filterSeverity").value,
  };

  loadAlerts();
}

function clearFilters() {
  document.getElementById("filterService").value = "";

  document.getElementById("filterMetric").value = "";

  document.getElementById("filterSeverity").value = "";

  currentFilters = {};

  loadAlerts();
}

/* ==========================================
   UTILITIES
========================================== */

function updateLastRefreshTime() {
  document.getElementById("lastUpdated").textContent =
    new Date().toLocaleString();
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleString();
}

function formatNumber(number) {
  return Number(number).toLocaleString();
}

function truncate(text, length) {
  if (!text) {
    return "";
  }

  return text.length > length ? text.substring(0, length) + "..." : text;
}

function getSeverityClass(severity) {
  switch (severity) {
    case "CRITICAL":
      return "badge-critical";

    case "HIGH":
      return "badge-error";

    case "MEDIUM":
      return "badge-warning";

    default:
      return "badge-info";
  }
}
