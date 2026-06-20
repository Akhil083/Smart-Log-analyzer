document.addEventListener("DOMContentLoaded", () => {
  registerEvents();
  initializePage();

  const modeSelect = document.getElementById("analysisMode");
  if (modeSelect) {
    modeSelect.addEventListener("change", () => {
      initializePage(); // Re-fetch logs, summary, and service count based on the new mode
    });
  }
});

let currentPage = 1;
let currentLimit = 20;
let totalPages = 1;

async function initializePage() {
  await Promise.all([
    loadLogs(),
    loadSummary(),
    loadServiceCount(),
    loadFilterOptions(),
  ]);
}

/* ==========================================
   EVENTS
========================================== */

function registerEvents() {
  document
    .getElementById("refreshLogsBtn")
    ?.addEventListener("click", refreshPage);

  document.getElementById("applyFiltersBtn")?.addEventListener("click", () => {
    currentPage = 1;
    loadLogs();
  });

  document
    .getElementById("clearFiltersBtn")
    ?.addEventListener("click", clearFilters);

  document.getElementById("uploadBtn")?.addEventListener("click", uploadLogs);

  document
    .getElementById("prevPageBtn")
    ?.addEventListener("click", previousPage);

  document.getElementById("nextPageBtn")?.addEventListener("click", nextPage);

  document
    .getElementById("closeLogModal")
    ?.addEventListener("click", () => closeModal("logDetailsModal"));

  document
    .getElementById("closeSimilarModal")
    ?.addEventListener("click", () => closeModal("similarLogsModal"));

  document.getElementById("selectFileBtn")?.addEventListener("click", () => {
    document.getElementById("logFile").click();
  });

  document.getElementById("logFile")?.addEventListener("change", (e) => {
    const file = e.target.files[0];

    document.getElementById("selectedFileName").textContent = file
      ? file.name
      : "No file selected";
  });
}

/* ==========================================
   SUMMARY CARDS
========================================== */

async function loadSummary() {
  try {
    const response = await fetch(getApiUrl("/analytics/summary"));

    const data = await response.json();

    document.getElementById("totalLogs").textContent = formatNumber(
      data.total_logs,
    );

    document.getElementById("errorLogs").textContent = formatNumber(
      data.error_logs,
    );

    document.getElementById("warningLogs").textContent = formatNumber(
      data.warning_logs,
    );

    document.getElementById("criticalLogs").textContent = formatNumber(
      data.critical_logs,
    );
  } catch (error) {
    console.error(error);
  }
}

async function loadServiceCount() {
  try {
    const response = await fetch(getApiUrl("/logs/service-count"));

    const data = await response.json();

    document.getElementById("serviceCount").textContent =
      data.service_count ?? 0;
  } catch (error) {
    console.error(error);
  }
}

/* ==========================================
   LOG LIST
========================================== */

async function loadLogs() {
  try {
    const params = buildFilterQuery();

    const response = await fetch(
      getApiUrl(`/logs?page=${currentPage}&limit=${currentLimit}${params}`),
    );

    const data = await response.json();

    renderLogsTable(data.item || []);

    updatePagination(data);

    updateLastRefresh();
  } catch (error) {
    console.error(error);
  }
}

function renderLogsTable(logs) {
  const tbody = document.getElementById("logsTableBody");

  tbody.innerHTML = "";

  if (!logs.length) {
    tbody.innerHTML = `
            <tr>
                <td colspan="8">
                    No logs found
                </td>
            </tr>
        `;

    return;
  }

  logs.forEach((log) => {
    const row = document.createElement("tr");

    row.innerHTML = `
            <td>${log.id}</td>

            <td>
                <span class="${getLevelBadge(log.level)}">
                    ${log.level}
                </span>
            </td>

            <td>${log.service || "-"}</td>

            <td>${log.environment || "-"}</td>

            <td>
                ${truncate(log.message, 80)}
            </td>

            <td>
                ${formatDate(log.emitted_at)}
            </td>

            <td>
                <button
                    class="btn-primary btn-sm"
                    onclick="viewLog(${log.id})"
                >
                    View
                </button>
            </td>

            <td>
                <button
                    class="btn-primary btn-sm"
                    onclick="showSimilarLogs(${log.id})"
                >
                    Similar
                </button>
            </td>
        `;

    tbody.appendChild(row);
  });
}

/* ==========================================
   LOG DETAILS
========================================== */

async function viewLog(logId) {
  try {
    const response = await fetch(getApiUrl(`/logs/${logId}`));

    const log = await response.json();

    const modalContent = document.getElementById("logDetailsContent");

    modalContent.innerHTML = `
            <div class="detail-grid">

                <p><strong>ID:</strong> ${log.id}</p>

                <p><strong>Level:</strong> ${log.level}</p>

                <p><strong>Service:</strong> ${log.service}</p>

                <p><strong>Environment:</strong> ${log.environment}</p>

                <p><strong>Host:</strong> ${log.host || "-"}</p>

                <p><strong>Trace ID:</strong> ${log.trace_id || "-"}</p>

                <p><strong>Request ID:</strong> ${log.request_id || "-"}</p>

                <p><strong>Source:</strong> ${log.source || "-"}</p>

                <p>
                    <strong>Emitted:</strong>
                    ${formatDate(log.emitted_at)}
                </p>

                <hr>

                <p>
                    <strong>Message:</strong><br>
                    ${log.message}
                </p>

            </div>
        `;

    openModal("logDetailsModal");
  } catch (error) {
    console.error(error);
  }
}

/* ==========================================
   SIMILAR LOGS
========================================== */

async function showSimilarLogs(logId) {
  try {
    const response = await fetch(getApiUrl(`/logs/${logId}/similar`));

    const data = await response.json();

    const container = document.getElementById("similarLogsContent");

    container.innerHTML = "";

    const results = data.results || [];

    if (!results.length) {
      container.innerHTML = "<p>No similar logs found.</p>";

      openModal("similarLogsModal");

      return;
    }

    results.forEach((match) => {
      const card = document.createElement("div");

      card.className = "similar-log-card";

      card.innerHTML = `
                <div class="similar-header">

                    <strong>
                        Score:
                        ${(match.score * 100).toFixed(2)}%
                    </strong>

                </div>

                <p>
                    <strong>Level:</strong>
                    ${match.log.level}
                </p>

                <p>
                    <strong>Service:</strong>
                    ${match.log.service}
                </p>

                <p class="similar-message">
                    ${truncate(match.log.message, 200)}
                </p>

                <div class="similar-meta">
                    ${match.log.level}
                    •
                    ${match.log.service}
                </div>
            `;

      container.appendChild(card);
    });

    openModal("similarLogsModal");
  } catch (error) {
    console.error(error);
  }
}

/* ==========================================
   FILE UPLOAD
========================================== */

async function uploadLogs(event) {
  event.preventDefault();

  try {
    const fileInput = document.getElementById("logFile");

    if (!fileInput.files.length) {
      alert("Please choose a file");
      return;
    }

    const formData = new FormData();

    formData.append("file", fileInput.files[0]);

    const response = await fetch(`${API_BASE_URL}/logs/upload`, {
      method: "POST",
      body: formData,
    });

    const result = await response.json();
    if (!response.ok) {
      alert(`Upload failed: ${result.detail || "Unknown error"}`);
      return;
    }

    alert(`Uploaded ${result.ingested_count} logs`);

    await Promise.all([loadLogs(), loadSummary(), loadServiceCount()]);
  } catch (error) {
    console.error("Network or system error:", error);
    alert("A network error occurred while uploading logs.");
  }
}

/* ==========================================
   FILTERS
========================================== */

function buildFilterQuery() {
  const filters = {
    keyword: document.getElementById("keyword")?.value,

    level: document.getElementById("level")?.value,

    service: document.getElementById("filterService")?.value,

    environment: document.getElementById("filterEnvironment")?.value,

    host: document.getElementById("host")?.value,

    trace_id: document.getElementById("traceId")?.value,

    request_id: document.getElementById("requestId")?.value,

    start_time: document.getElementById("startTime")?.value,

    end_time: document.getElementById("endTime")?.value,

    sort_order: document.getElementById("sortOrder")?.value,
  };

  currentLimit = parseInt(document.getElementById("pageSize")?.value || 20);

  let query = "";

  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      query += `&${key}=${encodeURIComponent(value)}`;
    }
  });

  return query;
}

function clearFilters() {
  [
    "keyword",
    "level",
    "filterService",
    "filterEnvironment",
    "host",
    "traceId",
    "requestId",
    "startTime",
    "endTime",
  ].forEach((id) => {
    const element = document.getElementById(id);

    if (element) {
      element.value = "";
    }
  });

  document.getElementById("sortOrder").value = "desc";

  document.getElementById("pageSize").value = "20";

  currentLimit = 20;
  currentPage = 1;

  loadLogs();
}

/* ==========================================
   PAGINATION
========================================== */

function updatePagination(data) {
  totalPages = data.pages || Math.ceil((data.total || 0) / currentLimit);

  const currentPageElement = document.getElementById("currentPage");

  const totalRecordsElement = document.getElementById("totalRecords");

  if (currentPageElement) {
    currentPageElement.textContent = data.page || currentPage;
  }

  if (totalRecordsElement) {
    totalRecordsElement.textContent = formatNumber(data.total || 0);
  }
}

function previousPage() {
  if (currentPage > 1) {
    currentPage--;

    loadLogs();
  }
}

function nextPage() {
  if (currentPage < totalPages) {
    currentPage++;

    loadLogs();
  }
}

/* ==========================================
   UTILITIES
========================================== */

function refreshPage() {
  loadLogs();
  loadSummary();
  loadServiceCount();
}

function updateLastRefresh() {
  const element = document.getElementById("lastUpdated");

  if (element) {
    element.textContent = new Date().toLocaleString();
  }
}

function formatDate(date) {
  if (!date) return "-";

  return new Date(date).toLocaleString();
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString();
}

function truncate(text, length) {
  if (!text) return "";

  return text.length > length ? text.substring(0, length) + "..." : text;
}

function getLevelBadge(level) {
  switch (level) {
    case "ERROR":
      return "badge badge-error";

    case "WARNING":
      return "badge badge-warning";

    case "CRITICAL":
      return "badge badge-critical";

    default:
      return "badge badge-info";
  }
}

/* ==========================================
   MODALS
========================================== */

function openModal(id) {
  const modal = document.getElementById(id);

  if (modal) {
    modal.style.display = "flex";
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);

  if (modal) {
    modal.style.display = "none";
  }
}

window.viewLog = viewLog;
window.showSimilarLogs = showSimilarLogs;
window.closeModal = closeModal;
