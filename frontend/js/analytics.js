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
            loadTopServices(),
            loadLevelDistribution(),
            loadServiceDistribution(),
            loadTimeline(),
            loadAnomalies(),
            loadClusters()
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

    const service =
        document.getElementById("filterService")?.value;

    const level =
        document.getElementById("filterLevel")?.value;

    const environment =
        document.getElementById("filterEnvironment")?.value;

    if (service)
        params.append("service", service);

    if (level)
        params.append("level", level);

    if (environment)
        params.append("environment", environment);

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

    const response = await fetch(
        `${API_BASE_URL}/analytics/summary?${filters}`
    );

    const data = await response.json();

    document.getElementById("totalLogs").textContent =
        formatNumber(data.total_logs);

    document.getElementById("errorLogs").textContent =
        formatNumber(data.error_logs);
}

/* ======================================================
   WARNING COUNT
====================================================== */

async function loadWarningCount() {

    const filters = getFilters();

    const response = await fetch(
        `${API_BASE_URL}/analytics/warning-count?${filters}`
    );

    const data = await response.json();

    document.getElementById("warningLogs").textContent =
        formatNumber(data.warning_logs);
}

/* ======================================================
   CRITICAL COUNT
====================================================== */

async function loadCriticalCount() {

    const filters = getFilters();

    const response = await fetch(
        `${API_BASE_URL}/analytics/critical-count?${filters}`
    );

    const data = await response.json();

    document.getElementById("criticalLogs").textContent =
        formatNumber(data.critical_logs);
}

/* ======================================================
   TOP SERVICES
====================================================== */

async function loadTopServices() {

    const response = await fetch(
        `${API_BASE_URL}/analytics/top-error-services`
    );

    const data = await response.json();

    const container =
        document.getElementById("topServicesContainer");

    container.innerHTML = "";

    if (!data.items?.length) {

        container.innerHTML =
            `<div class="empty-state">
                No service data available
            </div>`;

        return;
    }

    data.items.forEach(item => {

        const card = document.createElement("div");

        card.className = "service-card";

        card.innerHTML = `
            <h4>${item.service}</h4>
            <span>${item.error_count}</span>
        `;

        container.appendChild(card);
    });
}

/* ======================================================
   LEVEL DISTRIBUTION
====================================================== */

async function loadLevelDistribution() {

    const filters = getFilters();

    const response = await fetch(
        `${API_BASE_URL}/analytics/level?${filters}`
    );

    const data = await response.json();

    renderDistribution(
        "levelDistribution",
        data
    );
}

/* ======================================================
   SERVICE DISTRIBUTION
====================================================== */

async function loadServiceDistribution() {

    const filters = getFilters();

    const response = await fetch(
        `${API_BASE_URL}/analytics/service?${filters}`
    );

    const data = await response.json();

    renderDistribution(
        "serviceDistribution",
        data
    );
}

function renderDistribution(
    containerId,
    distribution
) {

    const container =
        document.getElementById(containerId);

    container.innerHTML = "";

    if (!distribution) {

        container.innerHTML =
            `<div class="empty-state">
                No data available
            </div>`;

        return;
    }

    Object.entries(distribution)
        .forEach(([key, value]) => {

            const card =
                document.createElement("div");

            card.className =
                "distribution-card";

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

    const interval =
        document.getElementById(
            "timelineInterval"
        ).value;

    const response = await fetch(
        `${API_BASE_URL}/analytics/timeline?interval=${interval}`
    );

    const data = await response.json();

    const body =
        document.getElementById(
            "timelineTableBody"
        );

    body.innerHTML = "";

    if (!data.item?.length) {

        body.innerHTML =
            `<tr>
                <td colspan="2">
                    No timeline data
                </td>
            </tr>`;

        return;
    }

    data.item.forEach(point => {

        const row =
            document.createElement("tr");

        row.innerHTML = `
            <td>${formatDate(point.time)}</td>
            <td>${point.total}</td>
        `;

        body.appendChild(row);
    });
}

/* ======================================================
   ANOMALIES
====================================================== */

async function loadAnomalies() {

    const response = await fetch(
        `${API_BASE_URL}/analytics/timeline/anomalies`
    );

    const data = await response.json();

    const container =
        document.getElementById(
            "anomalyContainer"
        );

    container.innerHTML = "";

    const anomalies =
        data.item?.filter(
            item => item.anomaly
        ) || [];

    if (!anomalies.length) {

        container.innerHTML =
            `<div class="empty-state">
                No anomalies detected
            </div>`;

        return;
    }

    anomalies.forEach(item => {

        const card =
            document.createElement("div");

        card.className =
            "anomaly-card";

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

    const limit =
        document.getElementById(
            "clusterLimit"
        ).value;

    const nClusters =
        document.getElementById(
            "clusterCount"
        ).value;

    const response = await fetch(
        `${API_BASE_URL}/analytics/clusters?limit=${limit}&n_clusters=${nClusters}`
    );

    const data = await response.json();

    const container =
        document.getElementById(
            "clusterResults"
        );

    container.innerHTML = "";

    if (!data.clusters?.length) {

        container.innerHTML =
            `<div class="empty-state">
                No cluster data available
            </div>`;

        return;
    }

    data.clusters.forEach(cluster => {

        const card =
            document.createElement("div");

        card.className =
            "cluster-card";

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

    const query =
        document.getElementById(
            "semanticQuery"
        ).value.trim();

    if (!query)
        return;

    const response = await fetch(
        `${API_BASE_URL}/analytics/semantic_search?query=${encodeURIComponent(query)}`
    );

    const data = await response.json();

    const container =
        document.getElementById(
            "semanticResults"
        );

    container.innerHTML = "";

    if (!data.results?.length) {

        container.innerHTML =
            `<div class="empty-state">
                No matching logs found
            </div>`;

        return;
    }

    data.results.forEach(result => {

        const card =
            document.createElement("div");

        card.className =
            "semantic-result-card";

        card.innerHTML = `
            <div class="score">
                Similarity:
                ${(result.score * 100).toFixed(2)}%
            </div>

            <div class="message">
                ${result.log.message}
            </div>

            <div class="meta">
                ${result.log.service}
                •
                ${result.log.level}
            </div>
        `;

        container.appendChild(card);
    });
}

/* ======================================================
   UTILITIES
====================================================== */

function updateLastRefresh() {

    const element =
        document.getElementById(
            "lastUpdated"
        );

    if (element) {

        element.textContent =
            new Date().toLocaleString();
    }
}

function formatDate(value) {

    return new Date(value)
        .toLocaleString();
}

function formatNumber(value) {

    return Number(value)
        .toLocaleString();
}