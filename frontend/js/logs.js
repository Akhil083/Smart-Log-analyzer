const API_BASE = "http://127.0.0.1:8000/api/v1";

const state = {
  page: 1,
  limit: 20,
  sortOrder: "desc",
  total: 0,
  selectedLogId: null,
};

function buildQueryString(extra = {}) {
  const params = new URLSearchParams();
  
  const service = document.getElementById("serviceFilter")?.value.trim();
  const level = document.getElementById("levelFilter")?.value;
  const environment = document.getElementById("environmentFilter")?.value.trim();
  const keyword = document.getElementById("keywordFilter")?.value.trim();
  const start = document.getElementById("startFilter")?.value;
  const end = document.getElementById("endFilter")?.value;
  
  if (service) params.set("service", service);
  if (level) params.set("level", level);
  if (environment) params.set("environment", environment);
  if (keyword) params.set("keyword", keyword);
  if (start) params.set("start_time", new Date(start).toISOString());
  if (end) params.set("end_time", new Date(end).toISOString());
  
  params.set("page", String(extra.page ?? state.page));
  params.set("limit", String(extra.limit ?? state.limit));
  params.set("sort_order", extra.sortOrder ?? state.sortOrder);
  
  if (extra.candidateLimit) params.set("candidate_limit", String(extra.candidateLimit));
  if (extra.topK) params.set("top_k", String(extra.topK));
  if (extra.sameServiceOnly) params.set("same_service_only", "true");
  
  return params.toString();
}


function levelClass(level) {
  const normalized = (level || "").toUpperCase();
  if (normalized === "ERROR") return "level-pill level-error";
  if (normalized === "CRITICAL") return "level-pill level-critical";
  if (normalized === "WARNING") return "level-pill level-warning";
  return "level-pill level-info";
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function formatMetadata(metadata) {
  try {
    return JSON.stringify(metadata ?? {}, null, 2);
  } catch {
    return "{}";
  }
}

function updateTableMeta() {
  const start = state.total === 0 ? 0 : (state.page - 1) * state.limit + 1;
  const end = Math.min(state.page * state.limit, state.total);
  const meta = document.getElementById("tableMeta");
  meta.textContent = state.total
    ? `Showing ${start}-${end} of ${state.total} matching logs`
    : "No logs found for the selected filters.";
    
  document.getElementById("pageIndicator").textContent = `Page ${state.page}`;
  document.getElementById("prevPageBtn").disabled = state.page === 1;
  document.getElementById("nextPageBtn").disabled = end >= state.total;
}

// Utility function to prevent XSS injections
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderLogsTable(items) {
  const tbody = document.getElementById("logsTableBody");
  tbody.innerHTML = "";

  const safeItems = Array.isArray(items) ? items : [];
  
  if (!safeItems.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state">No logs match the selected filters.</td>
      </tr>
    `;
    return;
  }
  
  safeItems.forEach((log) => {
    const row = document.createElement("tr");
    
    // levelClass and formatDate are safe as they return controlled system strings,
    // but raw data fields like message, service, environment, and ID must be escaped.
    row.innerHTML = `
      <td>${escapeHtml(log.id)}</td>
      <td>${formatDate(log.emitted_at)}</td>
      <td><span class="${levelClass(log.level)}">${escapeHtml(log.level)}</span></td>
      <td>${escapeHtml(log.service)}</td>
      <td>${escapeHtml(log.environment)}</td>
      <td class="message-cell" title="${escapeHtml(log.message)}">${escapeHtml(log.message)}</td>
      <td>
        <div class="actions-cell">
          <button class="btn btn-ghost" data-action="view" data-id="${escapeHtml(log.id)}">View</button>
          <button class="btn btn-ghost" data-action="similar" data-id="${escapeHtml(log.id)}">Similar</button>
        </div>
      </td>
    `;
    tbody.appendChild(row);
  });
}


function renderLogDetails(log) {
  const detailsState = document.getElementById("detailsState");
  const container = document.getElementById("logDetails");
  
  detailsState.textContent = `Log #${escapeHtml(log.id)}`;
  
  container.classList.remove("empty-state");
  container.innerHTML = `
    <div class="detail-grid">
      <div class="detail-item">
        <h4>Message</h4>
        <p>${escapeHtml(log.message)}</p>
      </div>
    </div>
    
    <div class="detail-grid">
      <div class="detail-item"><h4>Service</h4><p>${escapeHtml(log.service)}</p></div>
      <div class="detail-item"><h4>Level</h4><p>${escapeHtml(log.level)}</p></div>
      <div class="detail-item"><h4>Environment</h4><p>${escapeHtml(log.environment)}</p></div>
      <div class="detail-item"><h4>Emitted At</h4><p>${formatDate(log.emitted_at)}</p></div>
      <div class="detail-item"><h4>Ingested At</h4><p>${formatDate(log.ingested_at)}</p></div>
      <div class="detail-item"><h4>Trace ID</h4><p>${escapeHtml(log.trace_id || "-")}</p></div>
      <div class="detail-item"><h4>Request ID</h4><p>${escapeHtml(log.request_id || "-")}</p></div>
      <div class="detail-item"><h4>Host</h4><p>${escapeHtml(log.host || "-")}</p></div>
      <div class="detail-item"><h4>Source</h4><p>${escapeHtml(log.source || "-")}</p></div>
      
      <div class="detail-item">
        <h4>Metadata</h4>
        <pre>${escapeHtml(formatMetadata(log.metadata))}</pre>
      </div>
    </div>
  `;
}


function renderSimilarLogs(results) {
  const stateBadge = document.getElementById("similarState");
  const container = document.getElementById("similarLogs");
  
  if (!results.length) {
    stateBadge.textContent = "No results";
    container.classList.add("empty-state");
    container.innerHTML = "No similar logs found for the selected record.";
    return;
  }
  
  stateBadge.textContent = `${results.length} matches`;
  container.classList.remove("empty-state");
  
  container.innerHTML = results.map((item) => `
    <article class="similar-item">
      <div class="similar-score">Similarity score: ${Number(item.score).toFixed(4)}</div>
      <div class="similar-meta">
        <span>#${escapeHtml(item.log.id)}</span>
        <span>${escapeHtml(item.log.service)}</span>
        <span>${escapeHtml(item.log.level)}</span>
        <span>${formatDate(item.log.emitted_at)}</span>
      </div>
      <div class="similar-message">${escapeHtml(item.log.message)}</div>
    </article>
  `).join("");
}

async function loadLogs() {
  const query = buildQueryString();
  const response = await fetch(`${API_BASE}/logs?${query}`);
  const data = await response.json();
  
  state.total = data.total;
  renderLogsTable(data.items);
  updateTableMeta();
}


async function loadLogDetails(logId) {
  const response = await fetch(`${API_BASE}/logs/${logId}`);
  if (!response.ok) {
    document.getElementById("detailsState").textContent = "Not found";
    document.getElementById("logDetails").classList.add("empty-state");
    document.getElementById("logDetails").textContent = "Could not load log details.";
    return;
  }
  
  const data = await response.json();
  state.selectedLogId = logId;
  renderLogDetails(data);
}

async function loadSimilarLogs(logId, sameServiceOnly = true) {
  const query = buildQueryString({
    candidateLimit: 200,
    topK: 8,
    sameServiceOnly,
    page: 1,
    limit: state.limit,
    sortOrder: state.sortOrder,
  });
  
  const response = await fetch(`${API_BASE}/logs/${logId}/similar?${query}`);
  if (!response.ok) {
    document.getElementById("similarState").textContent = "Error";
    document.getElementById("similarLogs").classList.add("empty-state");
    document.getElementById("similarLogs").textContent = "Could not load similar logs.";
    return;
  }
  
  const data = await response.json();
  renderSimilarLogs(data.results);
}

function resetFilters() {
  document.getElementById("serviceFilter").value = "";
  document.getElementById("levelFilter").value = "";
  document.getElementById("environmentFilter").value = "";
  document.getElementById("keywordFilter").value = "";
  document.getElementById("startFilter").value = "";
  document.getElementById("endFilter").value = "";
  state.page = 1;
}

async function initLogsPage() {
  await loadLogs();
  document.getElementById("detailsState").textContent = "No log selected";
  document.getElementById("similarState").textContent = "No results";
}

document.getElementById("applyFiltersBtn")?.addEventListener("click", async () => {
  state.page = 1;
  await loadLogs();
});

document.getElementById("resetFiltersBtn")?.addEventListener("click", async () => {
  resetFilters();
  await loadLogs();
});

document.getElementById("limitSelect")?.addEventListener("change", async (event) => {
  state.limit = Number(event.target.value);
  state.page = 1;
  await loadLogs();
});

document.getElementById("sortSelect")?.addEventListener("change", async (event) => {
  state.sortOrder = event.target.value;
  state.page = 1;
  await loadLogs();
});

document.getElementById("prevPageBtn")?.addEventListener("click", async () => {
  if (state.page > 1) {
    state.page -= 1;
    await loadLogs();
  }
});

document.getElementById("nextPageBtn")?.addEventListener("click", async () => {
  const currentEnd = state.page * state.limit;
  if (currentEnd < state.total) {
    state.page += 1;
    await loadLogs();
  }
});

document.getElementById("logsTableBody")?.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  
  const { action, id } = button.dataset;
  const logId = Number(id);
  
  if (action === "view") {
    await loadLogDetails(logId);
  }
  
  if (action === "similar") {
    await loadLogDetails(logId);
    await loadSimilarLogs(logId, true);
  }
});

initLogsPage();

