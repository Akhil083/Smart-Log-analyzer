function initializeAnalysisMode() {
  const modeSelect = document.getElementById("analysisMode");
  const modeLabel = document.getElementById("currentModeLabel");

  if (!modeSelect || !modeLabel) return;

  const savedMode = getIngestionMode();

  modeSelect.value = savedMode;

  modeLabel.textContent =
    savedMode === "uploaded"
      ? "Working on Uploaded Logs"
      : "Working on Realtime Logs";

  modeSelect.addEventListener("change", () => {
    const mode = modeSelect.value;

    setIngestionMode(mode);

    modeLabel.textContent =
      mode === "uploaded"
        ? "Working on Uploaded Logs"
        : "Working on Realtime Logs";
  });
}

async function injectSidebar() {
  const mount = document.getElementById("appsidebar");
  if (!mount) return;

  try {
    const response = await fetch("/static/components/sidebar.html");
    if (!response.ok) throw new Error("Failed to fetch sidebar template");

    const template = await response.text();
    mount.innerHTML = template;
    initializeAnalysisMode();
    const currentPath = window.location.pathname;

    const navLinks = mount.querySelectorAll("nav a");

    navLinks.forEach((link) => {
      link.classList.remove("active");

      const linkPath = link.getAttribute("href");

      if (currentPath === linkPath) {
        link.classList.add("active");
      }
    });
  } catch (error) {
    mount.innerHTML =
      '<aside class="sidebar"><p>Sidebar could not be loaded.</p></aside>';
    console.error("Sidebar load failed:", error);
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", injectSidebar);
} else {
  injectSidebar();
}
