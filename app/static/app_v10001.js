console.log("APP.JS VERSION: 10001");
console.log("History containers:", document.querySelectorAll("#accaHistory").length);


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
    const res = await fetch(`${API}/accumulator/`);
    const data = await res.json();
    document.getElementById("accumulator").innerHTML = JSON.stringify(data, null, 2);
}
/* ============================================================
   ADD PICK
   ============================================================ */

function setupAddPickForm() {
    const form = document.getElementById("pickForm");
    const resultBox = document.getElementById("resultBox");

    form.onsubmit = async (e) => {
        e.preventDefault();

        const body = Object.fromEntries(new FormData(form).entries());

        // Validate odds format
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

        if (!res.ok) {
            const errorText = await res.text();
            resultBox.style.display = "block";
            resultBox.style.background = "#5a0000";
            resultBox.innerText = errorText;
            return;
        }

        // Success
        resultBox.style.display = "block";
        resultBox.style.background = "#0f2a0f";
        resultBox.innerText = "Pick added successfully!";

        form.reset();
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
    const res = await fetch(`${API}/accumulator/`);
    const data = await res.json();
    const picks = data.picks;

    const container = document.getElementById("currentPicks");

    if (!picks.length) {
        container.innerHTML = "<p>No active picks right now.</p>";
        return;
    }

    container.innerHTML = picks.map(p => `
        <div class="pick-card">
            <div class="pick-header">${p.horse_name} <span style="color:white;">(${p.odds_fraction})</span></div>

            <div class="pick-meta">
                Player: ${p.player.name}<br>
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
    await fetch(`${API}/accumulator/${id}/status`, {
        method: "PATCH",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ status: result })
    });

    loadCurrentPicks();
}

/* ============================================================
   STATS PAGE
   ============================================================ */

/* ============================================================
   DASHBOARD LOADER (month + year)
   ============================================================ */
async function loadStatsDashboard(month, year) {
    try {
        const res = await fetch(`${API}/stats/dashboard?month=${month}&year=${year}`);
        if (!res.ok) {
            console.error("Failed to load stats dashboard", res.status);
            return;
        }

        const data = await res.json();

        renderPlayerTiles(data.players || []);
        // DO NOT render accas here — stats page uses loadStatsPageHistory()
    } catch (err) {
        console.error("Error loading stats dashboard", err);
    }
}


/* ============================================================
   PLAYER TILES
   ============================================================ */
function renderPlayerTiles(players) {
    const container = document.getElementById("playerStatsContainer");
    container.innerHTML = "";

    players.forEach(p => {
        const monthWins = p.wins;

        const tile = document.createElement("div");
        tile.className = "card player-tile";

        tile.innerHTML = `
            <div class="flex-between mb-2">
                <span class="font-serif text-lg">${p.player}</span>
                <span class="badge badge-win" style="opacity:${p.wins > 0 ? 1 : 0.2}">🏆</span>
            </div>

            <div class="flex-between text-small text-muted mt-1">
                <span>Month Wins</span>
                <span class="text-foreground font-bold">${monthWins}</span>
            </div>

            <div class="mt-2" style="display:grid; grid-template-columns:repeat(2,1fr); gap:0.5rem;">
                <div class="stat-block stat-wins">
                    <p class="text-[10px] uppercase font-bold">Wins</p>
                    <p class="text-sm font-bold">${p.wins}</p>
                </div>

                <div class="stat-block stat-places">
                    <p class="text-[10px] uppercase font-bold">Places</p>
                    <p class="text-sm font-bold">${p.places}</p>
                </div>

                <div class="stat-block stat-loses">
                    <p class="text-[10px] uppercase font-bold">Losses</p>
                    <p class="text-sm font-bold">${p.loses}</p>
                </div>

                <div class="stat-block stat-nr">
                    <p class="text-[10px] uppercase font-bold">NR</p>
                    <p class="text-sm font-bold">${p.nr}</p>
                </div>
            </div>
        `;

        container.appendChild(tile);
    });
}


/* ============================================================
   COMPLETED ACCAS — CLEAN TILE VERSION (MATCHES YOUR SCREENSHOT)
   ============================================================ */
function renderAccaHistory(grouped) {
    const container = document.getElementById("accaHistoryContainer");
    if (!container) return;

    container.innerHTML = "";

    const dates = Object.keys(grouped);
    if (!dates.length) {
        container.innerHTML = `<p>No completed accumulators yet.</p>`;
        return;
    }

    dates.forEach(date => {
        const accas = grouped[date];

        // Date header
        container.innerHTML += `
            <h3 class="font-serif text-muted" style="margin-top:1.5rem;">${date}</h3>
        `;

        accas.forEach(a => {
            const statusClass =
                a.status === "win" ? "acca-card-win" :
                a.status === "place" ? "acca-card-place" :
                "acca-card-lose";

            const badgeClass =
                a.status === "win" ? "acca-badge-win" :
                a.status === "place" ? "acca-badge-place" :
                "acca-badge-lose";

            const oddsFraction = (a.combined_decimal_odds != null)
                ? `${(a.combined_decimal_odds - 1).toFixed(2)}/1`
                : "—";

            const picks = a.picks_json || [];

            container.innerHTML += `
    <div class="acca-card ${statusClass}">
        
        <!-- HEADER -->
        <div class="acca-header">
            <div>
                <div class="acca-date">
                    ${new Date(a.created_at).toLocaleDateString("en-GB", {
                        weekday: "long",
                        year: "numeric",
                        month: "long",
                        day: "numeric"
                    })}
                </div>

                <div class="acca-sub">
                    Stake: £${(a.stake ?? 5).toFixed(2)} (E/W) • 
                    Odds: ${oddsFraction}
                </div>
            </div>

            <div class="acca-returns">
                <p class="returns-label">Returns</p>
                <p class="returns-value ${a.status}">
                    £${(a.total_return ?? 0).toFixed(2)}
                </p>

                <span class="acca-status-badge ${badgeClass}">
                    ${a.status === "win" ? "WINNER" :
                      a.status === "lose" ? "BUSTED" :
                      a.status.toUpperCase()}
                </span>
            </div>
        </div>

        <!-- PICKS GRID -->
        <div class="acca-picks-grid">
            ${picks.map(p => `
                <div class="pick-tile">
                    <div class="pick-header">
                        <span class="pick-player">${p.player}</span>
                        <span class="pick-badge ${p.result.toLowerCase()}">${p.result}</span>
                    </div>

                    <div class="pick-course">${p.course}</div>

                    <div class="pick-horse">
                        ${p.horse_number ? `(${p.horse_number}) ` : ""}${p.horse}
                    </div>

                    <div class="pick-odds">@${p.odds}</div>
                </div>
            `).join("")}
        </div>

    </div>
`;

        });
    });
}


/* ============================================================
   STATS PAGE — LOAD LAST 5 COMPLETED ACCAS
   ============================================================ */
async function loadStatsPageHistory() {
    const container = document.getElementById("accaHistoryContainer");
    if (!container) return;

    try {
        const res = await fetch(`${API}/accumulator/history`);
        if (!res.ok) {
            container.innerHTML = "<p>Failed to load history.</p>";
            return;
        }

        let history = await res.json();

        // Only show last 5
        history = history.slice(0, 5);

        // Group by date
        const grouped = {};
        history.forEach(h => {
            const date = new Date(h.created_at).toLocaleDateString();
            if (!grouped[date]) grouped[date] = [];
            grouped[date].push(h);
        });

        renderAccaHistory(grouped);

    } catch (err) {
        console.error("Failed to load stats history", err);
        container.innerHTML = "<p>Error loading history.</p>";
    }
}


/* ============================================================
   PLAYER DETAILS (unchanged)
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
        
       body.each_way = document.getElementById("eachWay").checked;
       
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

    /* BUILD RACE LIST */
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
                    <strong>${p.player.name}</strong><br>
                    Stake: £${p.total_stake.toFixed(2)}<br>
                    Return: £${p.total_return.toFixed(2)}<br>
                    Profit: £${p.profit.toFixed(2)}
                </div>
            `;
        }).join("")}
    `;

    renderFilteredBets();
    loadRecentActivity();
}


/* ============================================================
   STATS PAGE — SUMMARY TILES
   ============================================================ */

function renderStatsSummary(stats) {
    const box = document.getElementById("statsSummary");
    if (!box) return;

    box.innerHTML = `
        <div class="summary-tile">
            <div class="label">Accas</div>
            <div class="value">${stats.totalAccas}</div>
        </div>

        <div class="summary-tile">
            <div class="label">Wins</div>
            <div class="value" style="color:#0a4">${stats.wins}</div>
        </div>

        <div class="summary-tile">
            <div class="label">Places</div>
            <div class="value" style="color:#06c">${stats.places}</div>
        </div>

        <div class="summary-tile">
            <div class="label">Busted</div>
            <div class="value" style="color:#900">${stats.busted}</div>
        </div>

        <div class="summary-tile">
            <div class="label">Staked</div>
            <div class="value">£${stats.totalStaked.toFixed(2)}</div>
        </div>

        <div class="summary-tile">
            <div class="label">Returned</div>
            <div class="value">£${stats.totalReturned.toFixed(2)}</div>
        </div>

        <div class="summary-tile">
            <div class="label">Profit</div>
            <div class="value" style="color:${stats.profit >= 0 ? '#0a4' : '#900'}">
                £${stats.profit.toFixed(2)}
            </div>
        </div>
    `;
}


/* ============================================================
   STATS PAGE — MAIN DASHBOARD LOADER
   ============================================================ */

async function loadStatsDashboard(month, year) {
    try {
        const res = await fetch(`${API}/api/stats/${year}/${month}`);
        const stats = await res.json();

        renderStatsSummary({
            totalAccas: stats.total_accas,
            wins: stats.wins,
            places: stats.places,
            busted: stats.busted,
            totalStaked: stats.total_staked,
            totalReturned: stats.total_returned,
            profit: stats.profit
        });

        const container = document.getElementById("playerStatsContainer");
        if (container) {
            container.innerHTML = "";

            stats.players.forEach(p => {
                const profitColor =
                    p.profit > 0 ? "stat-wins" :
                    p.profit < 0 ? "stat-loses" :
                    "stat-nr";

                container.innerHTML += `
                    <div class="card">
                        <h3 class="font-serif text-lg mb-2">${p.player}</h3>

                        <div class="stat-block ${profitColor}">
                            <p>Profit: £${p.profit.toFixed(2)}</p>
                        </div>

                        <div class="mt-2 text-small text-muted">
                            Stake: £${p.total_stake.toFixed(2)}<br>
                            Return: £${p.total_return.toFixed(2)}<br>
                            Wins: ${p.wins} • Places: ${p.places} • Busted: ${p.busted}
                        </div>
                    </div>
                `;
            });
        }

        loadStatsPageHistory();
    } catch (err) {
        console.error("Error loading stats dashboard:", err);
    }
}


/* ============================================================
   STATS PAGE — COMPLETED ACCA HISTORY (REPLIT-STYLE TILES)
   ============================================================ */

async function loadStatsPageHistory() {
    try {
        const container = document.getElementById("accaHistoryContainer");
        if (!container) return;

        const res = await fetch(`${API}/accumulator/history`);
        const data = await res.json();

        if (!data.length) {
            container.innerHTML = "<p>No completed accumulators yet.</p>";
            return;
        }

        const grouped = {};

        data.forEach(a => {
            const d = new Date(a.created_at);
            const dateKey = d.toLocaleDateString("en-GB");
            if (!grouped[dateKey]) grouped[dateKey] = [];
            grouped[dateKey].push(a);
        });

        const dates = Object.keys(grouped).sort((a, b) => {
            const da = new Date(a.split("/").reverse().join("-"));
            const db = new Date(b.split("/").reverse().join("-"));
            return db - da;
        });

        container.innerHTML = "";

        dates.forEach(date => {
            const accas = grouped[date];

            container.innerHTML += `
                <h3 class="font-serif text-muted" style="margin-top:1.5rem;">${date}</h3>
            `;

            accas.forEach(a => {
                const statusClass =
                    a.status === "win" ? "acca-card-win" :
                    a.status === "place" ? "acca-card-place" :
                    "acca-card-lose";

                const badgeClass =
                    a.status === "win" ? "acca-badge-win" :
                    a.status === "place" ? "acca-badge-place" :
                    "acca-badge-lose";

                const oddsFraction = (a.combined_decimal_odds != null)
                    ? `${(a.combined_decimal_odds - 1).toFixed(2)}/1`
                    : "—";

                const picks = a.picks || [];

                container.innerHTML += `
                    <div class="acca-card ${statusClass}">
                        <div class="acca-header">
                            <div>
                                <div class="acca-date">
                                    ${new Date(a.created_at).toLocaleDateString("en-GB", {
                                        weekday: "long",
                                        year: "numeric",
                                        month: "long",
                                        day: "numeric"
                                    })}
                                </div>

                                <div class="acca-sub">
                                    Stake: £${(a.stake ?? 5).toFixed(2)} (E/W) • 
                                    Odds: ${oddsFraction}
                                </div>
                            </div>

                            <div class="acca-returns">
                                <p class="returns-label">Returns</p>
                                <p class="returns-value ${a.status}">
                                    £${(a.total_return ?? 0).toFixed(2)}
                                </p>

                                <span class="acca-status-badge ${badgeClass}">
                                    ${a.status === "win" ? "WINNER" :
                                      a.status === "lose" ? "BUSTED" :
                                      a.status.toUpperCase()}
                                </span>
                            </div>
                        </div>

                        <div class="acca-picks-grid">
                            ${picks.map(p => `
                                <div class="pick-tile">
                                    <div class="pick-header">
                                        <span class="pick-player">${p.player}</span>
                                        <span class="pick-badge ${p.result.toLowerCase()}">${p.result}</span>
                                    </div>

                                    <div class="pick-course">${p.course}</div>

                                    <div class="pick-horse">
                                        ${p.horse}
                                    </div>

                                    <div class="pick-odds">@${p.odds}</div>
                                </div>
                            `).join("")}
                        </div>
                    </div>
                `;
            });
        });
    } catch (err) {
        console.error("Error loading stats page history:", err);
    }
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


/* ============================================================
   RACE DAY — DELETE BET
   ============================================================ */

async function deleteRaceBet(id) {
    if (!confirm("Delete this bet?")) return;

    await fetch(`${API}/api/raceday/${id}`, {
        method: "DELETE"
    });

    loadRaceStats();
}


/* ============================================================
   ACCUMULATOR PAGE — CLEAN VERSION
   ============================================================ */

/* ------------------------------------------------------------
   LOAD ACCA HERO (Top summary box)
------------------------------------------------------------ */
async function loadAccaHero() {
    try {
        const oddsEl = document.getElementById("accaOdds");
        const returnsEl = document.getElementById("accaReturns");
        const statusEl = document.getElementById("accaStatus");

        if (!oddsEl || !returnsEl || !statusEl) return;

        const res = await fetch(`${API}/accumulator/`);
        const data = await res.json();

        if (data.status === "no picks" || data.status === "all non runners") {
            oddsEl.textContent = "0.00/1";
            returnsEl.textContent = "£0.00";
            statusEl.textContent = "No Picks";
            statusEl.className = "acca-hero-status acca-status-empty";
            updateAliveBanner(null);
            return;
        }

        if (data.win_acca_odds > 0) {
            oddsEl.textContent = `${(data.win_acca_odds - 1).toFixed(2)}/1`;
        } else if (data.place_acca_odds > 0) {
            oddsEl.textContent = `${(data.place_acca_odds - 1).toFixed(2)}/1 (Place)`;
        } else {
            oddsEl.textContent = "0.00/1";
        }

        const ew = Number(data.ew_250_potential_return) || 0;
        returnsEl.textContent = `£${ew.toFixed(2)}`;

        const status = data.status.toLowerCase();
        statusEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        statusEl.className = "acca-hero-status";

        if (status === "live") statusEl.classList.add("acca-status-live");
        else if (status === "win") statusEl.classList.add("acca-status-won");
        else if (status === "place") statusEl.classList.add("acca-status-place");
        else if (status === "lose") statusEl.classList.add("acca-status-busted");
        else statusEl.classList.add("acca-status-empty");

        updateAliveBanner(status);

    } catch (err) {
        console.error("Failed to load acca hero", err);
    }
}


/* ------------------------------------------------------------
   ALIVE BANNER
------------------------------------------------------------ */
function updateAliveBanner(status) {
    const banner = document.getElementById("accaAliveBanner");
    if (!banner) return;

    banner.style.display = (status === "live" || status === "place") ? "block" : "none";
}


/* ------------------------------------------------------------
   LOAD PICKS (Current acca picks)
------------------------------------------------------------ */
async function loadAccaPicks() {
    const container = document.getElementById("accaPicks");
    if (!container) return;

    try {
        const res = await fetch(`${API}/picks/current`);
        const picks = await res.json();

        container.innerHTML = "";

        if (!picks.length) {
            container.innerHTML = "<p>No picks yet.</p>";
            return;
        }

        picks.forEach(p => {
            container.innerHTML += `
                <div class="acca-card">
                    <div class="acca-card-header">
                        <span class="acca-player">${p.player.name}</span>
                        <button class="acca-delete-btn" onclick="deleteAccaPick(${p.id})">✕</button>
                    </div>

                    <div class="acca-horse-line">
                        ${p.horse_number ? `<span class="acca-horse-number">(${p.horse_number})</span>` : ""}
                        <span class="acca-horse-name">${p.horse_name}</span>
                        <span class="acca-horse-odds">@${p.odds_fraction}</span>
                    </div>

                    <div class="acca-meta">${p.course} — ${p.race_time}</div>

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
                </div>
            `;
        });

    } catch (err) {
        console.error("Failed to load acca picks", err);
    }
}


/* ------------------------------------------------------------
   LOAD STANDINGS
------------------------------------------------------------ */
async function loadAccaStandings() {
    const container = document.getElementById("accaStandings");
    if (!container) return;

    try {
        const res = await fetch(`${API}/accumulator/standings`);
        const standings = await res.json();

        container.innerHTML = "";

        if (!standings.length) {
            container.innerHTML = "<p>No standings available.</p>";
            return;
        }

        standings.forEach(s => {
            container.innerHTML += `
                <div class="acca-standing-item">
                    <span class="acca-standing-player">${s.player}</span>
                    <span class="acca-standing-status">${s.status}</span>
                </div>
            `;
        });

    } catch (err) {
        console.error("Failed to load acca standings", err);
    }
}


/* ------------------------------------------------------------
   UPDATE PICK STATUS
------------------------------------------------------------ */
async function updateAccaStatus(id, status) {
    try {
        await fetch(`${API}/accumulator/${id}/status`, {
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


/* ------------------------------------------------------------
   DELETE PICK
------------------------------------------------------------ */
async function deleteAccaPick(id) {
    if (!confirm("Delete this pick?")) return;

    try {
        await fetch(`${API}/accumulator/${id}`, { method: "DELETE" });

        loadAccaPicks();
        loadAccaHero();
        loadAccaStandings();

    } catch (err) {
        console.error("Failed to delete pick", err);
    }
}


/* ------------------------------------------------------------
   COMPLETE ACCA
------------------------------------------------------------ */
const completeBtn = document.getElementById("completeAccaBtn");
if (completeBtn) {
    completeBtn.onclick = async () => {
        if (!confirm("Mark this acca as complete and archive it?")) return;

        const res = await fetch(`${API}/accumulator/complete`, {
            method: "POST"
        });

        if (!res.ok) {
            alert("Could not complete acca.");
            return;
        }

        loadAccaHero();
        loadAccaPicks();
        loadAccaStandings();
    };
}


/* ------------------------------------------------------------
   RESET ACCA
------------------------------------------------------------ */
const resetBtn = document.getElementById("resetAccaBtn");
if (resetBtn) {
    resetBtn.onclick = async () => {
        if (!confirm("Reset the entire acca?")) return;

        await fetch(`${API}/accumulator/reset-all`, {
            method: "DELETE"
        });

        loadAccaHero();
        loadAccaPicks();
        loadAccaStandings();
    };
}


/* ------------------------------------------------------------
   PAGE INIT
------------------------------------------------------------ */
document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("accaOdds")) {
        loadAccaHero();
        loadAccaPicks();
        loadAccaStandings();
    }

    if (document.getElementById("accaHistoryContainer")) {
        loadStatsPageHistory();
    }
});
