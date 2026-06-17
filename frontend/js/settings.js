document.addEventListener("DOMContentLoaded", initializeSettings);

function initializeSettings() {
  loadSettings();

  registerEvents();
}

/* ==========================================
   EVENTS
========================================== */

function registerEvents() {
  document
    .getElementById("saveSettingsBtn")
    ?.addEventListener("click", saveSettings);

  document
    .getElementById("resetSettingsBtn")
    ?.addEventListener("click", resetSettings);

  document
    .getElementById("exportSettingsBtn")
    ?.addEventListener("click", exportSettings);
}

/* ==========================================
   LOAD SETTINGS
========================================== */

function loadSettings() {
  const settings = JSON.parse(localStorage.getItem("smartlog_settings")) || {};

  setValue("defaultPageSize", settings.defaultPageSize || 20);

  setValue("autoRefresh", settings.autoRefresh || 60);

  setValue("timelineInterval", settings.timelineInterval || "minute");

  setValue("errorThreshold", settings.errorThreshold || 50);

  setValue("warningThreshold", settings.warningThreshold || 100);

  setValue("criticalThreshold", settings.criticalThreshold || 10);

  setValue("clusterCount", settings.clusterCount || 5);

  setValue("clusterLimit", settings.clusterLimit || 200);

  setValue("semanticLimit", settings.semanticLimit || 10);
}

/* ==========================================
   SAVE SETTINGS
========================================== */

function saveSettings() {
  const settings = {
    defaultPageSize: getValue("defaultPageSize"),

    autoRefresh: getValue("autoRefresh"),

    timelineInterval: getValue("timelineInterval"),

    errorThreshold: getValue("errorThreshold"),

    warningThreshold: getValue("warningThreshold"),

    criticalThreshold: getValue("criticalThreshold"),

    clusterCount: getValue("clusterCount"),

    clusterLimit: getValue("clusterLimit"),

    semanticLimit: getValue("semanticLimit"),
  };

  localStorage.setItem("smartlog_settings", JSON.stringify(settings));

  alert("Settings saved successfully.");
}

/* ==========================================
   RESET SETTINGS
========================================== */

function resetSettings() {
  const confirmed = confirm("Reset all settings to defaults?");

  if (!confirmed) {
    return;
  }

  localStorage.removeItem("smartlog_settings");

  loadSettings();

  alert("Settings reset successfully.");
}

/* ==========================================
   EXPORT SETTINGS
========================================== */

function exportSettings() {
  const settings = JSON.parse(localStorage.getItem("smartlog_settings")) || {};

  const blob = new Blob([JSON.stringify(settings, null, 2)], {
    type: "application/json",
  });

  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");

  link.href = url;

  link.download = "smartlog-settings.json";

  document.body.appendChild(link);

  link.click();

  link.remove();

  URL.revokeObjectURL(url);
}

/* ==========================================
   HELPERS
========================================== */

function getValue(id) {
  return document.getElementById(id)?.value;
}

function setValue(id, value) {
  const element = document.getElementById(id);

  if (element) {
    element.value = value;
  }
}
