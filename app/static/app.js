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
    const form = document.getElementById("statsForm");
    const summaryBox = document.getElementById("statsSummary");
    const table = document.getElementById("statsTable");
    const tbody = table.querySelector("tbody");

    // Auto-fill month/year
    const now = new Date();
    form.month.value = now.getMonth() + 1;
    form.year.value = now.getFullYear();

    form.onsubmit = async (e) => {
        e.preventDefault();

        const month = form.month.value;
        const year = form.year.value;

        const res = await fetch(`${API}/stats/month/${month}?year=${year}`);
        const stats = await res.json();

        if (!stats.length) {
            summaryBox.style.display = "block";
            summaryBox.innerHTML = "No stats available for this month.";
            table.style.display = "none";
            return;
        }

        // Sort by wins
        stats.sort((a, b) => b.wins - a.wins);

        // Summary
        const top = stats[0];
        summaryBox.style.display = "block";
        summaryBox.innerHTML = `
            <strong>Player of the Month:</strong> ${top.player}<br>
            <strong>Total Wins:</strong> ${top.wins}
        `;

        // Table
        tbody.innerHTML = stats.map(s => `
            <tr>
                <td>${s.player}</td>
                <td>${s.wins}</td>
                <td>${s.places}</td>
                <td>${s.loses}</td>
                <td>${s.nr}</td>
            </tr>
        `).join("");

        table.style.display = "table";
    };
}


// PLAYER DETAILS
function setupPlayerDetailsForm() {
    const form = document.getElementById("playerForm");
    const profile = document.getElementById("playerProfile");

    form.onsubmit = async (e) => {
        e.preventDefault();
        const name = new FormData(form).get("name");

        const res = await fetch(`${API}/stats/player/${name}`);
        const data = await res.json();

        // Build recent form badges
        const formBadges = data.recent_form.map(r => {
            const cls =
                r === "W" ? "form-win" :
                r === "P" ? "form-place" :
                r === "L" ? "form-lose" :
                "form-nr";
            return `<span class="${cls}">${r}</span>`;
        }).join("");

        profile.innerHTML = `
            <div class="profile-header">${data.player}</div>

            <div class="profile-section">
                <h3>Overall Performance</h3>
                Wins: ${data.wins}<br>
                Places: ${data.places}<br>
                Loses: ${data.loses}<br>
                NR: ${data.nr}<br>
                Win Rate: ${(data.win_rate * 100).toFixed(1)}%
            </div>

            <div class="profile-section">
                <h3>Biggest Priced Winner</h3>
                ${data.biggest_winner ? `
                    ${data.biggest_winner.horse_name} (${data.biggest_winner.odds_fraction})
                ` : "No wins yet."}
            </div>

            <div class="profile-section">
                <h3>Recent Form</h3>
                <div class="recent-form">${formBadges}</div>
            </div>
        `;
    };
}


// RACE DAY
function setupRaceForm() {
    const form = document.getElementById("raceForm");
    const resultBox = document.getElementById("raceResult");

    const now = new Date();
    form.month.value = now.getMonth() + 1;
    form.year.value = now.getFullYear();

    form.onsubmit = async (e) => {
        e.preventDefault();

        const body = Object.fromEntries(new FormData(form).entries());

        const res = await fetch(`${API}/raceday/`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(body)
        });

        const text = await res.text();

        resultBox.style.display = "block";
        resultBox.innerText = text;

        form.reset();
        form.month.value = now.getMonth() + 1;
        form.year.value = now.getFullYear();

        loadRaceStats();
    };
}

async function loadRaceStats() {
    const month = new Date().getMonth() + 1;
    const year = new Date().getFullYear();

    const listRes = await fetch(`${API}/raceday/?month=${month}&year=${year}`);
    const bets = await listRes.json();

    const list = document.getElementById("raceList");

    list.innerHTML = bets.map(b => `
        <div class="race-card">
            <div class="race-header">${b.horse_name} (${b.odds_fraction})</div>
            <div class="race-meta">
                Player: ${b.player_id}<br>
                Course: ${b.course}<br>
                Time: ${b.race_time}<br>
                Amount: £${b.amount_bet}
            </div>
            <span class="result-${b.result.toLowerCase()}">${b.result}</span>
        </div>
    `).join("");

    const statsRes = await fetch(`${API}/raceday/stats`);
    const stats = await statsRes.json();

    const box = document.getElementById("raceStats");

    box.innerHTML = `
        <h3>Group Summary</h3>
        Total Stake: £${stats.group.total_stake.toFixed(2)}<br>
        Total Return: £${stats.group.total_return.toFixed(2)}<br>
        Profit: £${stats.group.profit.toFixed(2)}<br><br>

        <h3>Players</h3>
        ${stats.players.map(p => `
            <div class="profile-section">
                <strong>${p.player}</strong><br>
                Stake: £${p.total_stake.toFixed(2)}<br>
                Return: £${p.total_return.toFixed(2)}<br>
                Profit: £${p.profit.toFixed(2)}
            </div>
        `).join("")}
    `;
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

