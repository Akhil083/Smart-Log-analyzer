const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

async function fetchJSON(endpoint) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return await response.json();
}

/* ==========================================
   INGESTION MODE
========================================== */

const DEFAULT_INGESTION_MODE = "realtime";

function getIngestionMode() {
  return localStorage.getItem("ingestionMode") || DEFAULT_INGESTION_MODE;
}

function setIngestionMode(mode) {
  localStorage.setItem("ingestionMode", mode);
}

/* ==========================================
   ANALYSIS MODE UI
========================================== */

function initializeAnalysisMode() {
  const modeSelect = document.getElementById("analysisMode");
  const modeLabel = document.getElementById("currentModeLabel");

  if (!modeSelect) return;

  const savedMode = getIngestionMode();

  modeSelect.value = savedMode;

  if (modeLabel) {
    modeLabel.textContent =
      savedMode === "uploaded"
        ? "Working on Uploaded Logs"
        : "Working on Realtime Logs";
  }

  modeSelect.addEventListener("change", () => {
    const selectedMode = modeSelect.value;

    setIngestionMode(selectedMode);

    if (modeLabel) {
      modeLabel.textContent =
        selectedMode === "uploaded"
          ? "Working on Uploaded Logs"
          : "Working on Realtime Logs";
    }

    console.log("Ingestion Mode Changed:", getIngestionMode());
  });
}

/* ==========================================
   API URL BUILDER
========================================== */

function getApiUrl(endpoint) {
  const separator = endpoint.includes("?") ? "&" : "?";

  return `${API_BASE_URL}${endpoint}${separator}ingestion_mode=${encodeURIComponent(
    getIngestionMode(),
  )}`;
}

/* ==========================================
   UTILITIES
========================================== */

function formatDate(value) {
  return new Date(value).toLocaleString();
}

async function loadFilterOptions() {
  console.log("Loading filter options...");

  const response = await fetch(getApiUrl("/analytics/filter-options"));

  const data = await response.json();

  const serviceSelect = document.getElementById("filterService");
  const environmentSelect = document.getElementById("filterEnvironment");

  serviceSelect.innerHTML = '<option value="">All Services</option>';

  environmentSelect.innerHTML = '<option value="">All Environments</option>';

  data.services.forEach((service) => {
    serviceSelect.innerHTML += `
      <option value="${service}">
        ${service}
      </option>
    `;
  });

  data.environments.forEach((environment) => {
    environmentSelect.innerHTML += `
      <option value="${environment}">
        ${environment}
      </option>
    `;
  });
}
