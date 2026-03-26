console.log("APP.JS VERSION: 10001");

/* ============================================================
   GLOBALS + HELPERS
   ============================================================ */

const API = "https://horse-racing-tracker-production.up.railway.app";

let PLAYER_MAP = {};
let ALL_BETS = [];
let FILTER_MODE = "all"; // "all" or "today"

/* Icons for results */
function getIcons() {
    return {
        "Win": "🟢",
        "Place": "🔵",
        "Lose": "🔴",
        "NR": "⚪",
        "Pending": "⏳"
    };
}

/* Group bets by course → time */
function groupBets(bets) {
    const grouped = {};
    bets.forEach(b => {
        if (!grouped[b.course]) grouped[b.course] = {};
        if (!grouped[b.course][b.race_time]) grouped[b.course][b.race_time] = [];
        grouped[b.course][b.race_time].push(b);
    });
    return grouped;
}

function fractionalToDecimal(frac) {
    if (!frac) return 1.0;

    // If user enters decimal already (e.g. "3.5")
    if (!frac.includes("/")) {
        const d = parseFloat(frac);
        return isNaN(d) ? 1.0 : d;
    }

    // Fractional odds: A/B → decimal = (A/B) + 1
    const [a, b] = frac.split("/").map(Number);
    if (!a || !b) return 1.0;

    return (a / b) + 1;
}

function placeOdds(decimalOdds) {
    // fractional odds = decimal - 1
    const frac = decimalOdds - 1;
    return (frac / 4) + 1;
}

function calculateAccaOdds(bets) {
    const active = bets.filter(b => b.result !== "Lose");

    if (!active.length) return 1.0;

    return active.reduce((acc, b) => {
        const dec = fractionalToDecimal(b.odds_fraction);
        return acc * dec;
    }, 1);
}

function ewReturns(accaDecimal) {
    const place = placeOdds(accaDecimal);
    return (2.5 * accaDecimal) + (2.5 * place);
}

function calculateWinnings(bet) {
    const dec = fractionalToDecimal(bet.odds_fraction);
    const stake = parseFloat(bet.amount_bet || 0);

    if (bet.result === "Win") {
        return stake * dec;
    }

    if (bet.result === "Place") {
        return stake * placeOdds(dec);
    }

    if (bet.result === "NR") {
        return stake; // stake returned
    }

    return 0;
}

/* Render a single race card */
function renderRaceCard(b, icons) {
    return `
        <div class="race-card">

            <div class="race-stake">Stake: £${b.amount_bet}</div>

            <div class="race-horse">
                (${b.horse_number}) ${b.horse_name} @ ${b.odds_fraction}
            </div>

            <div class="race-meta">
                Player: ${PLAYER_MAP[b.player_id]}<br>
                Course: ${b.course}<br>
                Race Time: ${b.race_time}<br>
                Winnings: £${calculateWinnings(b).toFixed(2)}
            </div>

            <div class="race-status">
                <span class="result-${b.result.toLowerCase()}">
                    ${icons[b.result]} ${b.result}
                </span>
            </div>

            <div class="race-buttons">
                <button 
                    type="button"
                    class="status-btn status-win ${b.result === 'Win' ? 'active' : ''}"
                    onclick="updateRaceResult(${b.id}, 'Win')">
                    WIN
                </button>

                <button 
                    type="button"
                    class="status-btn status-place ${b.result === 'Place' ? 'active' : ''}"
                    onclick="updateRaceResult(${b.id}, 'Place')">
                    PLACE
                </button>

                <button 
                    type="button"
                    class="status-btn status-lose ${b.result === 'Lose' ? 'active' : ''}"
                    onclick="updateRaceResult(${b.id}, 'Lose')">
                    LOSE
                </button>

                <button 
                    type="button"
                    class="status-btn status-nr ${b.result === 'NR' ? 'active' : ''}"
                    onclick="updateRaceResult(${b.id}, 'NR')">
                    NR
                </button>

                <button 
                    type="button"
                    class="status-btn"
                    style="background:#7a0f0f; opacity:1;"
                    onclick="deleteRaceBet(${b.id})">
                    DELETE
                </button>
            </div>

        </div>
    `;
}

/* ============================================================
   HOME PAGE
   ============================================================ */

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
/* ============================================================
   ADD PICK
   ============================================================ */

function setupAddPickForm() {
    const form = document.getElementById("pickForm");
    const resultBox = document.getElementById("resultBox");

    const now = new Date();
    form.month.value = now.getMonth() + 1;
    form.year.value = now.getFullYear();

    form.onsubmit = async (e) => {
        e.preventDefault();

        const body = Object.fromEntries(new FormData(form).entries());

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

async function loadPlayersForAddPick() {
    const dropdown = document.getElementById("playerSelect");

    const res = await fetch(`${API}/players/`);
    const players = await res.json();

    dropdown.innerHTML = '<option value="">Select Player</option>';

    players.forEach(p => {
        dropdown.innerHTML += `<option value="${p.id}">${p.name}</option>`;
    });
}

/* ============================================================
   CURRENT PICKS
   ============================================================ */

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
                <button type="button" onclick="updateResult(${p.id}, 'Win')">Win</button>
                <button type="button" onclick="updateResult(${p.id}, 'Place')">Place</button>
                <button type="button" onclick="updateResult(${p.id}, 'Lose')">Lose</button>
                <button type="button" onclick="updateResult(${p.id}, 'NR')">NR</button>
            </div>
        </div>
    `).join("");
}

async function updateResult(id, result) {
    await fetch(`${API}/api/raceday/${id}/result`, {
        method: "PATCH",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ result })
    });

    loadCurrentPicks();
}
/* ============================================================
   STATS PAGE
   ============================================================ */

function setupStatsForm() {
    const form = document.getElementById("statsForm");
    const summaryBox = document.getElementById("statsSummary");

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
            return;
        }

        stats.sort((a, b) => b.wins - a.wins);

        const top = stats[0];
        summaryBox.style.display = "block";
        summaryBox.innerHTML = `
            <strong>Player of the Month:</strong> ${top.player}<br>
            <strong>Total Wins:</strong> ${top.wins}
        `;

        const grid = document.getElementById("statsGrid");

        grid.innerHTML = stats.map(s => `
            <div class="stats-card">
                <div class="player-name">${s.player}</div>

                <div class="stat-row"><span>Month Wins:</span> <span>${s.wins}</span></div>
                <div class="stat-row"><span>Wins:</span> <span>${s.wins}</span></div>
                <div class="stat-row"><span>Places:</span> <span>${s.places}</span></div>
                <div class="stat-row"><span>Loses:</span> <span>${s.loses}</span></div>
                <div class="stat-row"><span>NR:</span> <span>${s.nr}</span></div>
            </div>
        `).join("");
    };
}

function renderGroupBalance() {
    const totalSpent = ALL_BETS.reduce((sum, b) => sum + parseFloat(b.amount_bet || 0), 0);
    const totalWon = ALL_BETS.reduce((sum, b) => sum + calculateWinnings(b), 0);
    const profit = totalWon - totalSpent;

    const box = document.getElementById("groupBalance");

    box.innerHTML = `
        <div class="summary-row">
            <span>Total Spent:</span>
            <strong>£${totalSpent.toFixed(2)}</strong>
        </div>

        <div class="summary-row">
            <span>Total Won:</span>
            <strong style="color:#f7c600;">£${totalWon.toFixed(2)}</strong>
        </div>

        <div class="summary-row" style="border-top:1px solid #333;padding-top:8px;margin-top:8px;">
            <span style="font-weight:bold;">Net Profit:</span>
            <strong style="color:${profit >= 0 ? '#0f7a0f' : '#7a0f0f'};">
                £${profit.toFixed(2)}
            </strong>
        </div>
    `;
}

//summary section//
function renderTodaySummary() {
    const today = new Date().toISOString().split("T")[0];

    const todaysBets = ALL_BETS.filter(b => b.date === today);
    const total = todaysBets.length;
    const wins = todaysBets.filter(b => b.result === "Win").length;

    const profit = todaysBets.reduce((sum, b) => {
        const p = parseFloat(b.winnings || 0) - parseFloat(b.amount_bet || 0);
        return sum + p;
    }, 0);

    const box = document.getElementById("todaySummary");

    box.innerHTML = `
        <strong>Total Bets Today:</strong> ${total}<br>
        <strong>Wins Today:</strong> ${wins}<br>
        <strong>Profit Today:</strong> £${profit.toFixed(2)}
    `;
}

/* ============================================================
   PLAYER DETAILS
   ============================================================ */

function setupPlayerDetailsForm() {
    const form = document.getElementById("playerForm");
    const profile = document.getElementById("playerProfile");

    form.onsubmit = async (e) => {
        e.preventDefault();

        const name = new FormData(form).get("name");

        const res = await fetch(`${API}/stats/player/${name}`);
        const data = await res.json();

        const profitColor =
            data.profit > 0 ? "#0f7a0f" :
            data.profit < 0 ? "#7a0f0f" :
            "#555";

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

            <div class="profile-section" style="border-left: 6px solid ${profitColor}">
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

//group balance
function renderGroupBalance() {
    const totalSpent = ALL_BETS.reduce((sum, b) => sum + parseFloat(b.amount_bet || 0), 0);
    const totalWon = ALL_BETS.reduce((sum, b) => sum + calculateWinnings(b), 0);
    const profit = totalWon - totalSpent;

    const box = document.getElementById("groupBalance");

    box.innerHTML = `
        <div class="summary-row">
            <span>Total Spent:</span>
            <strong>£${totalSpent.toFixed(2)}</strong>
        </div>

        <div class="summary-row">
            <span>Total Won:</span>
            <strong style="color:#f7c600;">£${totalWon.toFixed(2)}</strong>
        </div>

        <div class="summary-row" style="border-top:1px solid #333;padding-top:8px;margin-top:8px;">
            <span style="font-weight:bold;">Net Profit:</span>
            <strong style="color:${profit >= 0 ? '#0f7a0f' : '#7a0f0f'};">
                £${profit.toFixed(2)}
            </strong>
        </div>
    `;
}

/* ============================================================
   RACE DAY — FORM SETUP
   ============================================================ */

async function setupRaceForm() {
    const form = document.getElementById("raceForm");
    const resultBox = document.getElementById("raceResult");
    const playerSelect = document.getElementById("playerSelect");

    const res = await fetch(`${API}/players/`);
    const players = await res.json();

    playerSelect.innerHTML = '<option value="">Select Player</option>';
    players.forEach(p => {
        PLAYER_MAP[p.id] = p.name;
        playerSelect.innerHTML += `<option value="${p.id}">${p.name}</option>`;
    });

    form.onsubmit = async (e) => {
        e.preventDefault();

        const body = Object.fromEntries(new FormData(form).entries());

        const submitRes = await fetch(`${API}/api/raceday/`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(body)
        });

        let message = "Bet saved successfully!";

        try {
            const data = await submitRes.json();
            const playerName = PLAYER_MAP[data.player_id] || "Player";
            message = `${playerName}'s bet has been added!`;
        } catch {}

        resultBox.style.display = "block";
        resultBox.innerText = message;

        form.reset();
        loadRaceStats();
    };
}
/* ============================================================
   RACE DAY — UPDATE RESULT
   ============================================================ */

async function updateRaceResult(id, result) {
    await fetch(`${API}/api/raceday/${id}/result`, {
        method: "PATCH",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ result })
    });

    loadRaceStats();
}
/* ============================================================
   RACE DAY — LOAD STATS + CARDS
   ============================================================ */

async function loadRaceStats() {
    const listRes = await fetch(`${API}/api/raceday/`);
    ALL_BETS = await listRes.json();
    let bets = [...ALL_BETS];

    const list = document.getElementById("raceList");

    const grouped = groupBets(bets);
    const icons = getIcons();

   const accaDecimal = calculateAccaOdds(ALL_BETS);
   const ew = ewReturns(accaDecimal);
  
   /* UPDATE HEADER VALUES */
document.querySelector(".header-stat:nth-child(1) .stat-value").innerText =
    `${(accaDecimal - 1).toFixed(2)}/1`;

document.querySelector(".header-stat:nth-child(2) .stat-value").innerText =
    `£${ew.toFixed(2)}`;

    list.innerHTML = `
        <div class="race-list-wrapper">
            ${Object.keys(grouped).map(course => `
                <div class="race-course-header">${course}</div>

                ${Object.keys(grouped[course]).sort().map(time => `
                    <div class="race-time-header">${time}</div>

                    ${grouped[course][time].map(b => renderRaceCard(b, icons)).join("")}

                `).join("")}

            `).join("")}
        </div>
    `;

    /* GROUP STATS */
    const statsRes = await fetch(`${API}/api/raceday/stats`);
    const stats = await statsRes.json();

    const box = document.getElementById("raceStats");

    const totalBets = bets.length;
    const wins = bets.filter(b => b.result === "Win").length;
    const strikeRate = totalBets ? (wins / totalBets * 100).toFixed(1) : 0;

    box.innerHTML = `
        <h3>Group Summary</h3>
        Total Bets: ${totalBets}<br>
        Strike Rate: ${strikeRate}%<br>
        Total Stake: £${stats.group.total_stake.toFixed(2)}<br>
        Total Return: £${stats.group.total_return.toFixed(2)}<br>
        Profit: £${stats.group.profit.toFixed(2)}<br><br>

        <h3>Players</h3>
        ${stats.players.map(p => {
            const profitColor =
                p.profit > 0 ? "#0f7a0f" :
                p.profit < 0 ? "#7a0f0f" :
                "#555";

            return `
                <div class="profile-section" style="border-left: 6px solid ${profitColor}; padding-left: 10px;">
                    <strong>${p.player}</strong><br>
                    Stake: £${p.total_stake.toFixed(2)}<br>
                    Return: £${p.total_return.toFixed(2)}<br>
                    Profit: £${p.profit.toFixed(2)}
                </div>
            `;
        }).join("")}
    `;

   renderFilteredBets();
   loadRecentActivity();
   renderTodaySummary();
   renderGroupBalance();

}

/* ============================================================
   RECENT ACTIVITY
   ============================================================ */

async function loadRecentActivity() {
    const res = await fetch(`${API}/api/raceday/recent`);
    const items = await res.json();

    const box = document.getElementById("recentActivity");

    if (!items.length) {
        box.innerHTML = "No race day bets recorded yet.";
        return;
    }

    const icons = getIcons();

   box.innerHTML = items.map(a => {
    const winnings = calculateWinnings(a);
    const stake = parseFloat(a.amount_bet || 0);
    const profit = winnings - stake;

    return `
        <div class="activity-card-modern">

            <div class="activity-left">
                <div class="stake-box">
                    <span class="stake-label">Stake</span>
                    <span class="stake-value">£${stake.toFixed(2)}</span>
                </div>
            </div>

            <div class="activity-middle">
                <div class="horse-line">
                    ${a.horse_number ? `<span class="horse-number">(${a.horse_number})</span>` : ""}
                    <span class="horse-name">${a.horse_name}</span>
                    <span class="horse-odds">@${a.odds_fraction}</span>
                </div>

                <div class="meta-line">
                    <span class="meta-player">${PLAYER_MAP[a.player_id]}</span>
                    <span>${a.course}</span>
                    <span>${a.race_time}</span>
                </div>
            </div>

            <div class="activity-right">
                <div class="winnings-label">Winnings</div>
                <div class="winnings-value ${profit > 0 ? "profit-pos" : profit < 0 ? "profit-neg" : ""}">
                    £${winnings.toFixed(2)}
                </div>
            </div>

        </div>
    `;
}).join("");
}

/* ============================================================
   FILTER BAR — TODAY ONLY / ALL BETS
   ============================================================ */

function filterToday() {
    FILTER_MODE = "today";

    document.querySelectorAll(".filter-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelector(".filter-btn:nth-child(1)").classList.add("active");

    renderFilteredBets();
}

function filterAll() {
    FILTER_MODE = "all";

    document.querySelectorAll(".filter-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelector(".filter-btn:nth-child(2)").classList.add("active");

    renderFilteredBets();
}

function renderFilteredBets() {
    let bets = [...ALL_BETS];

    if (FILTER_MODE === "today") {
        const today = new Date().toISOString().split("T")[0];
        bets = bets.filter(b => b.date === today);
    }

    const grouped = groupBets(bets);
    const icons = getIcons();

    const list = document.getElementById("raceList");

    list.innerHTML = `
        <div class="race-list-wrapper">
            ${Object.keys(grouped).map(course => `
                <div class="race-course-header">${course}</div>

                ${Object.keys(grouped[course]).sort().map(time => `
                    <div class="race-time-header">${time}</div>

                    ${grouped[course][time].map(b => renderRaceCard(b, icons)).join("")}

                `).join("")}

            `).join("")}
        </div>
    `;
}

//delete button
async function deleteRaceBet(id) {
    if (!confirm("Delete this bet?")) return;

    await fetch(`${API}/api/raceday/${id}`, {
        method: "DELETE"
    });

    loadRaceStats();
}

/* ============================================================
   ACCUMULATOR PAGE
   ============================================================ */

async function loadAccaHero() {
    try {
        const oddsEl = document.getElementById("accaOdds");
        const returnsEl = document.getElementById("accaReturns");
        const statusEl = document.getElementById("accaStatus");

        // If ANY of the required elements are missing, skip this function
        if (!oddsEl || !returnsEl || !statusEl) return;

        const res = await fetch(`${API}/accumulator`);
        const data = await res.json();

        oddsEl.textContent = `${data.odds.toFixed(2)}/1`;
        returnsEl.textContent = `£${data.ew_returns.toFixed(2)}`;

        statusEl.textContent = data.status;
        statusEl.className = "acca-hero-status";

        if (data.status === "Live") statusEl.classList.add("acca-status-live");
        else if (data.status === "Won") statusEl.classList.add("acca-status-won");
        else if (data.status === "Busted") statusEl.classList.add("acca-status-busted");
        else statusEl.classList.add("acca-status-empty");

    } catch (err) {
        console.error("Failed to load acca hero", err);
    }
}

async function loadAccaPicks() {
    const container = document.getElementById("accaPicks");
    if (!container) return;  // <-- FIX: prevents crashes on pages without this element

    try {
        const res = await fetch(`${API}/picks/current`);
        const picks = await res.json();

        container.innerHTML = "";

        if (!picks.length) {
            container.innerHTML = "<p>No picks yet.</p>";
            return;
        }

        picks.forEach(p => {
            const card = document.createElement("div");
            card.className = "acca-card";

            card.innerHTML = `
                <div class="acca-card-header">
                    <span class="acca-player">${p.player}</span>
                    <button class="acca-delete-btn" onclick="deleteAccaPick(${p.id})">✕</button>
                </div>

                <div class="acca-horse-line">
                    ${p.horse_number ? `<span class="acca-horse-number">(${p.horse_number})</span>` : ""}
                    <span class="acca-horse-name">${p.horse_name}</span>
                    <span class="acca-horse-odds">@${p.odds_fraction}</span>
                </div>

                <div class="acca-meta">
                    ${p.course} — ${p.race_time}
                </div>

                <div class="acca-status-buttons">
                    ${["Pending", "Win", "Place", "Lose", "NR"].map(s => `
                        <button 
                            class="acca-status-btn ${p.status === s ? 'active' : ''}"
                            onclick="updateAccaStatus(${p.id}, '${s}')"
                        >
                            ${s.toUpperCase()}
                        </button>
                    `).join("")}
                </div>
            `;

            container.appendChild(card);
        });

    } catch (err) {
        console.error("Failed to load acca picks", err);
    }
}

async function loadAccaStandings() {
    const container = document.getElementById("accaStandings");
    if (!container) return;  // <-- Prevents crashes on pages without this element

    try {
        const res = await fetch(`${API}/accumulator/standings`);
        const standings = await res.json();

        container.innerHTML = "";

        if (!standings.length) {
            container.innerHTML = "<p>No standings available.</p>";
            return;
        }

        standings.forEach(s => {
            const row = document.createElement("div");
            row.className = "acca-standing-item";

            row.innerHTML = `
                <span class="acca-standing-player">${s.player}</span>
                <span class="acca-standing-status">${s.status}</span>
            `;

            container.appendChild(row);
        });

    } catch (err) {
        console.error("Failed to load acca standings", err);
    }
}


async function updateAccaStatus(id, status) {
    try {
        await fetch(`${API}/picks/${id}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status })
        });

        loadAccaPicks();
        loadAccaHero();
        loadAccaStandings();

    } catch (err) {
        console.error("Failed to update acca status", err);
    }
}

async function deleteAccaPick(id) {
    if (!confirm("Delete this pick?")) return;

    try {
        await fetch(`${API}/picks/${id}`, { method: "DELETE" });

        loadAccaPicks();
        loadAccaHero();
        loadAccaStandings();

    } catch (err) {
        console.error("Failed to delete pick", err);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("accaOdds")) {
        loadAccaHero();
        loadAccaPicks();
        loadAccaStandings();
    }
});





