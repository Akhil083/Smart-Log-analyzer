const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

async function fetchJSON(endpoint) {

    const response = await fetch(
        `${API_BASE_URL}${endpoint}`
    );

    if (!response.ok) {
        throw new Error(
            `API Error: ${response.status}`
        );
    }

    return await response.json();
}

function formatDate(value) {

    return new Date(value)
        .toLocaleString();
}