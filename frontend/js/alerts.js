const API = "http://127.0.0";

async function loadAlerts() {
    try {
        const res = await fetch(`${API}/alerts`);
        if (!res.ok) throw new Error("Failed to fetch alerts");
        
        const data = await res.json();
        const table = document.getElementById('alertstable');
        
        if (table) {
            table.innerHTML = "";
            data.items.forEach(a => {
                table.innerHTML += `
                    <tr>
                        <td>${a.id}</td>
                        <td>${a.service}</td>
                        <td>${a.metric}</td>
                        <td>${a.value}</td>
                        <td>${a.message}</td>
                    </tr>
                `;
            });
        }

        const totalAlertsEl = document.getElementById('totalAlerts');
        const errorAlertsEl = document.getElementById('errorAlerts');
        const anomalyAlertsEl = document.getElementById('anomalyAlerts');

        if (totalAlertsEl) totalAlertsEl.innerText = data.items.length;
        if (errorAlertsEl) errorAlertsEl.innerText = data.items.filter(x => x.metric === 'error_count').length;
        if (anomalyAlertsEl) anomalyAlertsEl.innerText = data.items.filter(x => x.metric === 'anomaly').length;

    } catch (error) {
        console.error("Error loading alerts:", error);
    }
}

const refreshAlertsBtn = document.getElementById('refreshAlertsBtn');
const runAlertCheckBtn = document.getElementById('runAlertCheckBtn');

if (refreshAlertsBtn) {
    refreshAlertsBtn.onclick = loadAlerts;
}

if (runAlertCheckBtn) {
    runAlertCheckBtn.onclick = async () => {
        try {
            await fetch(`${API}/alerts/check`);
            await loadAlerts();
        } catch (error) {
            console.error("Error checking alerts:", error);
        }
    };
}

loadAlerts();
