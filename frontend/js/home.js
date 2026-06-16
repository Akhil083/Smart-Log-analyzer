document.addEventListener("DOMContentLoaded", () => {

    loadDashboard();

    const refreshBtn =
        document.getElementById("refreshBtn");

    if (refreshBtn) {
        refreshBtn.addEventListener(
            "click",
            loadDashboard
        );
    }
});



async function loadDashboard() {

    try {

        await Promise.all([
            loadSummary(),
            loadWarningCount(),
            loadCriticalCount(),
            loadServiceCount(),
            loadActiveAlertCount(),
            loadTopServices(),
            loadRecentAlerts(),
            loadRecentLogs(),
        ]);

    } catch (error) {

        console.error(
            "Dashboard loading failed:",
            error
        );
    }
}



async function loadSummary() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/analytics/summary`
        );

        const data =
            await response.json();

        document.getElementById(
            "totalLogs"
        ).textContent =
            formatNumber(
                data.total_logs
            );

        document.getElementById(
            "errorLogs"
        ).textContent =
            formatNumber(
                data.error_logs
            );

        const errorRate =
            data.total_logs > 0
                ? (
                    (
                        data.error_logs /
                        data.total_logs
                    ) * 100
                ).toFixed(2)
                : 0;

        document.getElementById(
            "errorRate"
        ).textContent =
            `${errorRate}%`;

    } catch (error) {

        console.error(
            "Summary loading failed:",
            error
        );
    }
}



async function loadWarningCount() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/analytics/warning-count`
        );

        const data =
            await response.json();

        document.getElementById(
            "warningLogs"
        ).textContent =
            formatNumber(
                data.warning_logs
            );

    } catch (error) {

        console.error(
            "Warning count failed:",
            error
        );
    }
}



async function loadCriticalCount() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/analytics/critical-count`
        );

        const data =
            await response.json();

        document.getElementById(
            "criticalLogs"
        ).textContent =
            formatNumber(
                data.critical_logs
            );

    } catch (error) {

        console.error(
            "Critical count failed:",
            error
        );
    }
}



async function loadServiceCount() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/logs/service-count`
        );

        const data =
            await response.json();

        document.getElementById(
            "serviceCount"
        ).textContent =
            formatNumber(
                data.service_count
            );

    } catch (error) {

        console.error(
            "Service count failed:",
            error
        );
    }
}



async function loadActiveAlertCount() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/alerts/active-count`
        );

        const data =
            await response.json();

        document.getElementById(
            "activeAlerts"
        ).textContent =
            formatNumber(
                data.active_alerts
            );

    } catch (error) {

        console.error(
            "Alert count failed:",
            error
        );
    }
}



async function loadTopServices() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/analytics/top-error-services`
        );

        const data =
            await response.json();

        const container =
            document.getElementById(
                "topServices"
            );

        container.innerHTML = "";

        if (
            !data.items ||
            data.items.length === 0
        ) {

            container.innerHTML =
                "<p>No service data available.</p>";

            return;
        }

        data.items.forEach(item => {

            const row =
                document.createElement("div");

            row.className =
                "service-item";

            row.innerHTML = `
                <span>${item.service}</span>
                <strong>${item.error_count}</strong>
            `;

            container.appendChild(row);
        });

    } catch (error) {

        console.error(
            "Top services failed:",
            error
        );
    }
}



async function loadRecentAlerts() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/alerts?limit=5`
        );

        const data =
            await response.json();

        const container =
            document.getElementById(
                "recentAlerts"
            );

        container.innerHTML = "";

        const alerts =
            data.items ||
            data.item ||
            [];

        if (
            alerts.length === 0
        ) {

            container.innerHTML =
                "<p>No active alerts.</p>";

            return;
        }

        alerts.forEach(alert => {

            const card =
                document.createElement("div");

            card.className =
                "alert-item";

            card.innerHTML = `
                <h4>${alert.metric}</h4>
                <p>${alert.message}</p>
                <small>${alert.service}</small>
            `;

            container.appendChild(card);
        });

    } catch (error) {

        console.error(
            "Recent alerts failed:",
            error
        );
    }
}



async function loadRecentLogs() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/logs?limit=5`
        );

        const data =
            await response.json();

        const tableBody =
            document.getElementById(
                "recentLogsBody"
            );

        tableBody.innerHTML = "";

        if (
            !data.item ||
            data.item.length === 0
        ) {

            tableBody.innerHTML =
                `
                <tr>
                    <td colspan="4">
                        No logs found
                    </td>
                </tr>
                `;

            return;
        }

        data.item.forEach(log => {

            const row =
                document.createElement("tr");

            row.innerHTML = `
                <td>
                    ${formatDate(
                        log.emitted_at
                    )}
                </td>

                <td>
                    ${log.level}
                </td>

                <td>
                    ${log.service}
                </td>

                <td>
                    ${truncate(
                        log.message,
                        80
                    )}
                </td>
            `;

            tableBody.appendChild(row);
        });

    } catch (error) {

        console.error(
            "Recent logs failed:",
            error
        );
    }
}



function formatDate(dateString) {

    return new Date(
        dateString
    ).toLocaleString();
}



function formatNumber(number) {

    return Number(
        number
    ).toLocaleString();
}



function truncate(
    text,
    length
) {

    if (!text) {
        return "";
    }

    return text.length > length
        ? text.substring(
            0,
            length
        ) + "..."
        : text;
}