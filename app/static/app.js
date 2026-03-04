const API = "https://horse-racing-tracker-production.up.railway.app";

// HOME PAGE
async function loadPodium() {
    const month = new Date().getMonth() + 1;
    const year = new Date().getFullYear();

    const res = await fetch(`${API}/stats/month/${month}?year=${year}`);
    const stats = await res.json();

    const sorted = stats.sort((a, b) => b.wins - a.wins);

    document.getElementById("firstPlayer").innerText = sorted[0]?.player || "-";
    document.getElementById("secondPlayer").innerText = sorted[1]?.player || "-";
    document.getElementById("thirdPlayer").innerText = sorted[2]?.player || "-";
}


async function loadAccumulator() {
    const res = await fetch(`${API}/accumulator`);
    const data = await res.json();
    document.getElementById("accumulator").innerHTML = JSON.stringify(data, null, 2);
}

// ADD PICK
function setupAddPickForm() {
    const form = document.getElementById("pickForm");
    const resultBox = document.getElementById("result");

    // Auto-fill month/year
    const now = new Date();
    form.month.value = now.getMonth() + 1;
    form.year.value = now.getFullYear();

    form.onsubmit = async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const body = Object.fromEntries(formData.entries());

        // Validate odds format (e.g. 5/2)
        if (!/^\d+\/\d+$/.test(body.odds_fraction)) {
            resultBox.style.display = "block";
            resultBox.style.background = "#5a0000";
            resultBox.innerText = "Odds must be in fraction format (e.g. 5/2).";
            return;
        }

        const res = await fetch(`${API}/picks/`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(body)
        });

        const text = await res.text();

        resultBox.style.display = "block";
        resultBox.style.background = "#0f2a0f";
        resultBox.innerText = text;

        form.reset();
        form.month.value = now.getMonth() + 1;
        form.year.value = now.getFullYear();
    };
}


// CURRENT PICKS
async function loadCurrentPicks() {
    const res = await fetch(`${API}/picks/current`);
    const picks = await res.json();

    const container = document.getElementById("currentPicks");

    if (!picks.length) {
        container.innerHTML = "<p>No active picks right now.</p>";
        return;
    }

    container.innerHTML = picks.map(p => `
        <div class="pick-card">
            <div class="pick-header">${p.horse_name} <span style="color:white;">(${p.odds_fraction})</span></div>
            <div class="pick-meta">
                Player: ${p.player_id}<br>
                Course: ${p.course}<br>
                Time: ${p.race_time}<br>
                Horse No: ${p.horse_number}
            </div>

            <div class="result-buttons">
                <button class="btn-win" onclick="updateResult(${p.id}, 'Win')">Win</button>
                <button class="btn-place" onclick="updateResult(${p.id}, 'Place')">Place</button>
                <button class="btn-lose" onclick="updateResult(${p.id}, 'Lose')">Lose</button>
                <button class="btn-nr" onclick="updateResult(${p.id}, 'NR')">NR</button>
            </div>
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

