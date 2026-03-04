const API = "https://horse-racing-tracker-production.up.railway.app";

// HOME PAGE
async function loadPodium() {
    const res = await fetch(`${API}/stats/month/3?year=2026`);
    const data = await res.json();
    document.getElementById("podium").innerHTML =
        data.map(p => `<div class="card">${p.player}: ${p.wins} wins</div>`).join("");
}

async function loadAccumulator() {
    const res = await fetch(`${API}/accumulator`);
    const data = await res.json();
    document.getElementById("accumulator").innerHTML = JSON.stringify(data, null, 2);
}

// ADD PICK
function setupAddPickForm() {
    document.getElementById("pickForm").onsubmit = async (e) => {
        e.preventDefault();
        const form = new FormData(e.target);
        const body = Object.fromEntries(form.entries());

        const res = await fetch(`${API}/picks/`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(body)
        });

        document.getElementById("result").innerText = await res.text();
    };
}

// CURRENT PICKS
async function loadCurrentPicks() {
    const res = await fetch(`${API}/picks/current`);
    const picks = await res.json();

    document.getElementById("currentPicks").innerHTML =
        picks.map(p => `
            <div class="card">
                <b>${p.horse_name}</b> (${p.odds_fraction})<br>
                <button onclick="updateResult(${p.id}, 'Win')">Win</button>
                <button onclick="updateResult(${p.id}, 'Place')">Place</button>
                <button onclick="updateResult(${p.id}, 'Lose')">Lose</button>
                <button onclick="updateResult(${p.id}, 'NR')">NR</button>
            </div>
        `).join("");
}

async function updateResult(id, status) {
    await fetch(`${API}/picks/${id}/result`, {
        method: "PATCH",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({status})
    });
    loadCurrentPicks();
}

// STATS
function setupStatsForm() {
    document.getElementById("statsForm").onsubmit = async (e) => {
        e.preventDefault();
        const form = new FormData(e.target);
        const month = form.get("month");
        const year = form.get("year");

        const res = await fetch(`${API}/stats/month/${month}?year=${year}`);
        const data = await res.json();

        document.getElementById("statsOutput").innerHTML =
            data.map(p => `<div class="card">${p.player}: ${p.wins} wins</div>`).join("");
    };
}

// PLAYER DETAILS
function setupPlayerDetailsForm() {
    document.getElementById("playerForm").onsubmit = async (e) => {
        e.preventDefault();
        const name = new FormData(e.target).get("name");

        const res = await fetch(`${API}/stats/player/${name}`);
        const data = await res.json();

        document.getElementById("playerDetails").innerHTML =
            `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    };
}

// RACE DAY
function setupRaceForm() {
    document.getElementById("raceForm").onsubmit = async (e) => {
        e.preventDefault();
        const body = Object.fromEntries(new FormData(e.target).entries());

        await fetch(`${API}/raceday/`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(body)
        });

        loadRaceStats();
    };
}

async function loadRaceStats() {
    const res = await fetch(`${API}/raceday/stats`);
    const data = await res.json();
    document.getElementById("raceStats").innerHTML =
        `<pre>${JSON.stringify(data, null, 2)}</pre>`;
}
// Highlight active nav link
document.addEventListener("DOMContentLoaded", () => {
    const current = window.location.pathname;
    document.querySelectorAll(".navbar a").forEach(link => {
        if (link.getAttribute("href") === current) {
            link.classList.add("active");
        }
    });
});

