const API_BASE = "http://127.0.0.1:8000/api/v1";


function getFilters() {
    const service = document.getElementById("filterService").value ;
    const level = document.getElementById("filterLevel").value ;
    const start = document.getElementById("filterStart").value ;
    const end = document.getElementById("filterEnd").value ;

    let query = []

    if (service) query.push(`service = ${service}`);
    if (level) query.push(`level = ${level}`);
    if (start) query.push(`start_time = ${new Date(start).toISOString()}`);
    if (end) query.push(`end_time = ${new Date(end).toISOString()}`);

    return query.length ? `?${query.join("&")}` : "";


}

async function loadSummary() {
    const filters = getFilters();
    const res = await fetch(`${API_BASE}/analytics/summary`);
    const data = await res.json();

    document.getElementById("totalLogs").innerText = data.total_logs;
    document.getElementById("errorLogs").innerText = data.error_logs
}


async function loadLevels() {
    const filters = getFilters();
    const res =await fetch(`${API_BASE}/analytics/level`);
    const data = await res.json()

    const container = document.getElementById("levelContainer")
    container.innerHTML = ""

    Object.entries(data).forEach(([level , count]) => {
        const div = document.createElement("div");
        div.className = "level-card";
        div.innerHTML = `
        <h4>${level}</h4>
        <p>${count}</p>
        `
        ;
        container.appendChild(div);
    });
    
}


async function loadTimeline() {
    const filters = getFilters();
    const res =await fetch(`${API_BASE}/analytics/timeline`);
    const data = await res.json()

    const labels = data.item.map(item => item.time);
    const totals = data.item.map(item => item.total);
    const errors = data.item.map(item => item.errors);

    const ctx = document.getElementById("timelineChart").getContext("2d");

    if (window.timelineChart && typeof window.timelineChart.destroy === 'function') {
    window.timelineChart.destroy();
    }

    window.timelineChart = new Chart (ctx, {
        type: "line",
        data: {
            labels :labels,
            datasets: [
                {
                    label: "Total Logs",
                    data : totals,
                    borderColor : "#4a6cf7",
                    backgroundColor :"rgba(74,108,247,0.1)",
                    fill: true,
                },
                {
                    label: "Error Logs",
                    data : errors,
                    borderColor : "#e74c3c",
                    backgroundColor :"rgba(231,76,60,0.1)",
                    fill: true,  
                }
            ]
        },
        options : {
            responsive : true,
            plugins : {
                legend : {
                    position : "top"
                }
            },
            scales : {
                x: {
                    ticks : {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });

    
}


async function init() {
    try{
        await Promise.all([

            loadSummary(),
            loadLevels(),
            loadTimeline()
        ]);
    }catch (err) {
        console.error("failed to load dashboard data component" , err)
    }  
}

document.getElementById("applyFilters").addEventListener("click", async () => {
    await init();
});

init();