/* ============================================================
   GLOBAL FETCH WRAPPER
   ============================================================ */

async function api(url, options = {}) {
    const res = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...options
    });
    return res.json();
}

/* ============================================================
   ACCA PAGE
   ============================================================ */

async function loadAccumulator() {
    const data = await api("/api/acca/");

    updateAccaHero(data);
    renderAccaPicks(data.picks);
    renderAccaStandings(data.standings);
}

function updateAccaHero(data) {
    document.getElementById("acca-odds").textContent = data.total_odds || "-";
    document.getElementById("acca-ew-return").textContent = data.ew_return || "-";

    const statusEl = document.getElementById("acca-status");
    statusEl.textContent = data.status_label;

    statusEl.className = "acca-hero-status " + data.status_class;
}

function renderAccaPicks(picks) {
    const container = document.getElementById("acca-current-picks");
    container.innerHTML = "";

    if (!picks.length) {
        container.innerHTML = `<div class="empty-message">No picks yet.</div>`;
        return;
    }

    picks.forEach(pick => container.appendChild(buildAccaCard(pick)));
}

function buildAccaCard(pick) {
    const div = document.createElement("div");
    div.className = "acca-card";
    div.innerHTML = `
        <div class="acca-card-header">
            <div class="acca-player">${pick.player}</div>
            <button class="acca-delete-btn" onclick="deletePick('${pick.id}')">×</button>
        </div>

        <div class="acca-horse-line">
            <span class="acca-horse-number">${pick.horse_number}</span>
            <span class="acca-horse-name">${pick.horse_name}</span>
            <span class="acca-horse-odds">${pick.odds}</span>
        </div>

        <div class="acca-meta">${pick.course} — ${pick.race_time}</div>

        <div class="acca-status-buttons">
            ${["win","place","lose","nr"].map(s => `
                <button 
                    class="acca-status-btn ${pick.status === s ? "active" : ""}"
                    onclick="updatePickStatus('${pick.id}', '${s}')"
                >${s.toUpperCase()}</button>
            `).join("")}
        </div>
    `;
    return div;
}

async function deletePick(id) {
    await api(`/api/picks/${id}`, { method: "DELETE" });
    loadAccumulator();
}

async function updatePickStatus(id, status) {
    await api(`/api/picks/${id}/status`, {
        method: "POST",
        body: JSON.stringify({ status })
    });
    loadAccumulator();
}

function renderAccaStandings(standings) {
    const container = document.getElementById("acca-standings");
    container.innerHTML = "";

    standings.forEach(s => {
        const div = document.createElement("div");
        div.className = "acca-standing-item";
        div.innerHTML = `
            <div class="acca-standing-player">${s.player}</div>
            <div class="acca-standing-status">${s.status}</div>
        `;
        container.appendChild(div);
    });
}

/* ============================================================
   ADD PICK PAGE
   ============================================================ */

async function loadPlayersForAddPick() {
    const players = await api("/api/players/");
    const select = document.getElementById("player");

    players.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p;
        opt.textContent = p;
        select.appendChild(opt);
    });
}

function setupAddPickForm() {
    document.getElementById("add-pick-form").addEventListener("submit", async e => {
        e.preventDefault();

        const payload = {
            player: document.getElementById("player").value,
            course: document.getElementById("course").value,
            horse_number: document.getElementById("horse_number").value,
            horse_name: document.getElementById("horse_name").value,
            race_time: document.getElementById("race_time").value,
            odds: document.getElementById("odds_fraction").value
        };

        await api("/api/picks", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        window.location.href = "/acca";

    });
}

/* ============================================================
   CURRENT PICKS PAGE
   ============================================================ */

async function loadCurrentPicks() {
    const picks = await api("/api/picks");
    const container = document.getElementById("current-picks-body");

    container.innerHTML = "";

    if (!picks.length) {
        container.innerHTML = `<div class="empty-message">No picks yet.</div>`;
        return;
    }

    picks.forEach(pick => container.appendChild(buildAccaCard(pick)));
}

/* ============================================================
   RACE DAY PAGE
   ============================================================ */

async function loadRaceDay() {
    const data = await api("/api/raceday/");

    renderRaceCards(data.races);
    renderRecentActivity(data.activity);

    setupRaceFilters();
}

function renderRaceCards(races) {
    const container = document.getElementById("race-container");
    container.innerHTML = "";

    races.forEach(r => {
        const div = document.createElement("div");
        div.className = "race-card";
        div.innerHTML = `
            <div class="race-horse">${r.horse_name}</div>
            <div class="race-meta">${r.course} — ${r.time}</div>
            <div class="race-stake">Stake: £${r.stake}</div>

            <div class="race-buttons">
                ${["win","place","lose","nr"].map(s => `
                    <button 
                        class="status-btn ${r.status === s ? "active" : ""} status-${s}"
                        onclick="updateRaceStatus('${r.id}', '${s}')"
                    >${s.toUpperCase()}</button>
                `).join("")}
            </div>
        `;
        container.appendChild(div);
    });
}

async function updateRaceStatus(id, status) {
    await api(`/api/raceday/${id}/status`, {
        method: "POST",
        body: JSON.stringify({ status })
    });
    loadRaceDay();
}

function renderRecentActivity(list) {
    const container = document.getElementById("recent-activity");
    container.innerHTML = "";

    list.forEach(a => {
        const div = document.createElement("div");
        div.className = "activity-card-modern";
        div.innerHTML = `
            <div class="activity-left">
                <div class="horse-line">
                    <span class="horse-number">${a.horse_number}</span>
                    ${a.horse_name}
                    <span class="horse-odds">${a.odds}</span>
                </div>
                <div class="meta-line">
                    <span>${a.course}</span>
                    <span>${a.time}</span>
                    <span class="meta-player">${a.player}</span>
                </div>
            </div>

            <div class="winnings-value ${a.profit >= 0 ? "profit-pos" : "profit-neg"}">
                £${a.profit}
            </div>
        `;
        container.appendChild(div);
    });
}

function setupRaceFilters() {
    document.querySelectorAll(".filter-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
        });
    });
}

/* ============================================================
   STATS PAGE
   ============================================================ */

async function loadStatsPage() {
    const players = await api("/api/stats/");
    const container = document.getElementById("stats-cards");

    container.innerHTML = "";

    players.forEach(p => {
        const div = document.createElement("div");
        div.className = "stats-card";
        div.onclick = () => openStatsModal(p.name);

        div.innerHTML = `
            <div class="player-name">${p.name}</div>
            <div class="stat-line">Wins: ${p.wins}</div>
            <div class="stat-line">Places: ${p.places}</div>
            <div class="stat-line">Loses: ${p.loses}</div>
        `;
        container.appendChild(div);
    });
}

async function openStatsModal(name) {
    const data = await api(`/api/stats/${name}`);

    document.getElementById("modalPlayerName").textContent = name;
    document.getElementById("modalWins").textContent = data.wins;
    document.getElementById("modalPlaces").textContent = data.places;
    document.getElementById("modalLoses").textContent = data.loses;
    document.getElementById("modalNR").textContent = data.nr;
    document.getElementById("modalTotal").textContent = data.total;
    document.getElementById("modalWinRate").textContent = data.win_rate + "%";

    renderCourseTable(data.courses);
    renderProfitChart(data.profit);

    document.getElementById("statsModal").classList.remove("hidden");
}

function renderCourseTable(courses) {
    const tbody = document.getElementById("modalCourseTable");
    tbody.innerHTML = "";

    courses.forEach(c => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${c.course}</td>
            <td class="center">${c.runs}</td>
            <td class="center">${c.wins}</td>
            <td class="center">${c.places}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderProfitChart(list) {
    const container = document.getElementById("modalProfitChart");
    container.innerHTML = "";

    list.forEach(row => {
        const div = document.createElement("div");
        div.className = "bar-row";
        div.innerHTML = `
            <div class="bar-label">${row.label}</div>
            <div class="bar-track">
                <div class="bar-fill ${row.value >= 0 ? "bar-positive" : "bar-negative"}"
                     style="width:${Math.min(Math.abs(row.value), 100)}%">
                </div>
            </div>
            <div class="bar-value">£${row.value}</div>
        `;
        container.appendChild(div);
    });
}

document.getElementById("closeStatsModal")?.addEventListener("click", () => {
    document.getElementById("statsModal").classList.add("hidden");
});

/* ============================================================
   PLAYER DETAILS PAGE
   ============================================================ */

function setupPlayerDetailsForm() {
    document.getElementById("playerForm").addEventListener("submit", async e => {
        e.preventDefault();

        const name = e.target.name.value;
        const data = await api(`/api/stats/${name}`);

        const container = document.getElementById("playerProfile");
        container.innerHTML = `
            <h2>${name}</h2>
            <p>Wins: ${data.wins}</p>
            <p>Places: ${data.places}</p>
            <p>Loses: ${data.loses}</p>
            <p>NR: ${data.nr}</p>
            <p>Total Bets: ${data.total}</p>
        `;
    });
}
