console.log("APP.JS VERSION: 10001");

/* ============================================================
   GLOBALS + HELPERS
   ============================================================ */

const API = "https://horse-racing-tracker-production.up.railway.app";

let PLAYER_MAP = {};
let ALL_BETS = [];
let FILTER_MODE = "all"; // "all" or "today"

function getIcons() {
    return {
        Win: "🟢",
        Place: "🔵",
        Lose: "🔴",
        NR: "⚪",
        Pending: "⏳"
    };
}

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

    if (!frac.includes("/")) {
        const d = parseFloat(frac);
        return isNaN(d) ? 1.0 : d;
    }

    const [a, b] = frac.split("/").map(Number);
    if (!a || !b) return 1.0;

    return a / b + 1;
}

function placeOdds(decimalOdds) {
    const frac = decimalOdds - 1;
    return frac / 4 + 1;
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
    return 2.5 * accaDecimal + 2.5 * place;
}

function calculateWinnings(bet) {
    const dec = fractionalToDecimal(bet.odds_fraction);
    const stake = parseFloat(bet.amount_bet || 0);

    if (bet.result === "Win") return stake * dec;
    if (bet.result === "Place") return stake * placeOdds(dec);
    if (bet.result === "NR") return stake;
    return 0;
}

function renderRaceCard(b, icons) {
    return `
        <div class="race-card">
            <div class="race-stake">Stake: £${b.amount_bet}</div>

            <div class="race-horse">
                ${b.horse_number ? `(${b.horse_number}) ` : ""}${b.horse_name} @ ${b.odds_fraction}
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
                    class="status-btn status-win ${b.result === "Win" ? "active" : ""}"
                    onclick="updateRaceResult(${b.id}, 'Win')">
                    WIN
                </button>

                <button 
                    type="button"
                    class="status-btn status-place ${b.result === "Place" ? "active" : ""}"
                    onclick="updateRaceResult(${b.id}, 'Place')">
                    PLACE
                </button>

                <button 
                    type="button"
                    class="status-btn status-lose ${b.result === "Lose" ? "active" : ""}"
                    onclick="updateRaceResult(${b.id}, 'Lose')">
                    LOSE
                </button>

                <button 
                    type="button"
                    class="status-btn status-nr ${b.result === "NR" ? "active" : ""}"
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
    try {
        const month = new Date().getMonth() + 1;
        const year = new Date().getFullYear();

        const res = await fetch(`${API}/stats/month/${month}?year=${year}`);
        const stats = await res.json();

        const sorted = stats.sort((a, b) => b.wins - a.wins);

        const first = document.getElementById("firstPlayer");
        const second = document.getElementById("secondPlayer");
        const third = document.getElementById("thirdPlayer");

        if (first) first.innerText = sorted[0]?.player || "-";
        if (second) second.innerText = sorted[1]?.player || "-";
        if (third) third.innerText = sorted[2]?.player || "-";
    } catch (err) {
        console.error("Error loading podium:", err);
    }
}

/* ============================================================
   ADD PICK PAGE
   ============================================================ */

async function loadPlayersForAddPick() {
    try {
        const res = await fetch("/players");
        const players = await res.json();

        const select = document.getElementById("player");
        if (!select) return;

        select.innerHTML = '<option value="">Select Player</option>';

        players.forEach(p => {
            const opt = document.createElement("option");
            opt.value = p.id;
            opt.textContent = p.name;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error("Failed to load players:", err);
    }
}

function setupAddPickForm() {
    const form = document.getElementById("add-pick-form");
    if (!form) return;

    form.addEventListener("submit", async e => {
        e.preventDefault();

        const payload = {
            player_id: parseInt(document.getElementById("player").value),
            course: document.getElementById("course").value.trim(),
            horse_name: document.getElementById("horse_name").value.trim(),
            horse_number: document.getElementById("horse_number").value.trim() || null,
            odds_fraction: document.getElementById("odds_fraction").value.trim(),
            race_time: document.getElementById("race_time").value.trim()
        };

        if (
            !payload.player_id ||
            !payload.course ||
            !payload.horse_name ||
            !payload.odds_fraction ||
            !payload.race_time
        ) {
            alert("Please fill in all required fields.");
            return;
        }

        try {
            const res = await fetch("/picks/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const errData = await res.json();
                alert("Error: " + (errData.detail || "Failed to create pick."));
                return;
            }

            window.location.href = "/current-picks";
        } catch (err) {
            console.error("Failed to submit pick:", err);
            alert("Failed to submit pick.");
        }
    });
}

/* ============================================================
   CURRENT PICKS PAGE
   ============================================================ */

async function loadCurrentPicks() {
    const tbody = document.getElementById("current-picks-body");
    if (!tbody) return;

    try {
        const res = await fetch("/picks/current");
        const picks = await res.json();
        renderCurrentPicks(picks);
    } catch (err) {
        console.error("Error loading current picks:", err);
    }
}

function renderCurrentPicks(picks) {
    const tbody = document.getElementById("current-picks-body");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (!picks || picks.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">No current picks</td>
            </tr>
        `;
        return;
    }

    picks.forEach(p => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${p.player.name}</td>
            <td>${p.course}</td>
            <td>${p.horse_name}</td>
            <td>${p.horse_number ?? "-"}</td>
            <td>${p.odds_fraction}</td>
            <td>${p.race_time}</td>
            <td>
                <button class="btn btn-primary btn-sm" onclick="addAccaPick(${p.id})">
                    Add to Acca
                </button>
            </td>
        `;

        tbody.appendChild(row);
    });
}

/* ============================================================
   STATS PAGE
   ============================================================ */

function setupStatsForm() {
    const form = document.getElementById("statsForm");
    const summaryBox = document.getElementById("statsSummary");
    const grid = document.getElementById("statsGrid");
    if (!form) return;

    const now = new Date();
    form.month.value = now.getMonth() + 1;
    form.year.value = now.getFullYear();

    form.onsubmit = async e => {
        e.preventDefault();

        const month = form.month.value;
        const year = form.year.value;

        try {
            const res = await fetch(`${API}/stats/month/${month}?year=${year}`);
            const stats = await res.json();

            if (!stats.length) {
                if (summaryBox) {
                    summaryBox.style.display = "block";
                    summaryBox.innerHTML = "No stats available for this month.";
                }
                if (grid) grid.innerHTML = "";
                return;
            }

            stats.sort((a, b) => b.wins - a.wins);

            const top = stats[0];
            if (summaryBox) {
                summaryBox.style.display = "block";
                summaryBox.innerHTML = `
                    <strong>Player of the Month:</strong> ${top.player}<br>
                    <strong>Total Wins:</strong> ${top.wins}
                `;
            }

            if (grid) {
                grid.innerHTML = stats
                    .map(
                        s => `
                    <div class="stats-card">
                        <div class="player-name">${s.player}</div>

                        <div class="stat-row"><span>Month Wins:</span> <span>${s.wins}</span></div>
                        <div class="stat-row"><span>Wins:</span> <span>${s.wins}</span></div>
                        <div class="stat-row"><span>Places:</span> <span>${s.places}</span></div>
                        <div class="stat-row"><span>Loses:</span> <span>${s.loses}</span></div>
                        <div class="stat-row"><span>NR:</span> <span>${s.nr}</span></div>
                    </div>
                `
                    )
                    .join("");
            }
        } catch (err) {
            console.error("Error loading stats:", err);
        }
    };
}

function renderGroupBalance() {
    const box = document.getElementById("groupBalance");
    if (!box) return;

    const totalSpent = ALL_BETS.reduce((sum, b) => sum + parseFloat(b.amount_bet || 0), 0);
    const totalWon = ALL_BETS.reduce((sum, b) => sum + calculateWinnings(b), 0);
    const profit = totalWon - totalSpent;

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
            <strong style="color:${profit >= 0 ? "#0f7a0f" : "#7a0f0f"};">
                £${profit.toFixed(2)}
            </strong>
        </div>
    `;
}

function renderTodaySummary() {
    const box = document.getElementById("todaySummary");
    if (!box) return;

    const today = new Date().toISOString().split("T")[0];
    const todaysBets = ALL_BETS.filter(b => b.date === today);
    const total = todaysBets.length;
    const wins = todaysBets.filter(b => b.result === "Win").length;

    const profit = todaysBets.reduce((sum, b) => {
        const winnings = calculateWinnings(b);
        const stake = parseFloat(b.amount_bet || 0);
        return sum + (winnings - stake);
    }, 0);

    box.innerHTML = `
        <strong>Total Bets Today:</strong> ${total}<br>
        <strong>Wins Today:</strong> ${wins}<br>
        <strong>Profit Today:</strong> £${profit.toFixed(2)}
    `;
}

/* ============================================================
   PLAYER DETAILS PAGE
   ============================================================ */

function setupPlayerDetailsForm() {
    const form = document.getElementById("playerForm");
    const profile = document.getElementById("playerProfile");
    if (!form || !profile) return;

    form.onsubmit = async e => {
        e.preventDefault();

        const name = new FormData(form).get("name");

        try {
            const res = await fetch(`${API}/stats/player/${name}`);
            const data = await res.json();

            const profitColor =
                data.profit > 0 ? "#0f7a0f" : data.profit < 0 ? "#7a0f0f" : "#555";

            const formBadges = data.recent_form
                .map(r => {
                    const cls =
                        r === "W"
                            ? "form-win"
                            : r === "P"
                            ? "form-place"
                            : r === "L"
                            ? "form-lose"
                            : "form-nr";
                    return `<span class="${cls}">${r}</span>`;
                })
                .join("");

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
                    ${
                        data.biggest_winner
                            ? `${data.biggest_winner.horse_name} (${data.biggest_winner.odds_fraction})`
                            : "No wins yet."
                    }
                </div>

                <div class="profile-section">
                    <h3>Recent Form</h3>
                    <div class="recent-form">${formBadges}</div>
                </div>
            `;
        } catch (err) {
            console.error("Error loading player details:", err);
        }
    };
}

/* ============================================================
   RACE DAY — FORM SETUP
   ============================================================ */

async function setupRaceForm() {
    const form = document.getElementById("raceForm");
    const resultBox = document.getElementById("raceResult");
    const playerSelect = document.getElementById("playerSelect");
    if (!form || !resultBox || !playerSelect) return;

    try {
        const res = await fetch(`${API}/players/`);
        const players = await res.json();

        playerSelect.innerHTML = '<option value="">Select Player</option>';
        players.forEach(p => {
            PLAYER_MAP[p.id] = p.name;
            playerSelect.innerHTML += `<option value="${p.id}">${p.name}</option>`;
        });
    } catch (err) {
        console.error("Error loading race day players:", err);
    }

    form.onsubmit = async e => {
        e.preventDefault();

        const body = Object.fromEntries(new FormData(form).entries());

        try {
            const submitRes = await fetch(`${API}/api/raceday/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });

            let message = "Bet saved successfully!";

            try {
                const data = await submitRes.json();
                const playerName = PLAYER_MAP[data.player_id] || "Player";
                message = `${playerName}'s bet has been added!`;
            } catch {
                // ignore JSON parse errors
            }

            resultBox.style.display = "block";
            resultBox.innerText = message;

            form.reset();
            loadRaceStats();
        } catch (err) {
            console.error("Error submitting race bet:", err);
        }
    };
}

/* ============================================================
   RACE DAY — UPDATE RESULT
   ============================================================ */

async function updateRaceResult(id, result) {
    try {
        await fetch(`${API}/api/raceday/${id}/result`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ result })
        });

        loadRaceStats();
    } catch (err) {
        console.error("Error updating race result:", err);
    }
}

/* ============================================================
   RACE DAY — LOAD STATS + CARDS
   ============================================================ */

async function loadRaceStats() {
    const list = document.getElementById("raceList");
    const statsBox = document.getElementById("raceStats");
    if (!list || !statsBox) return;

    try {
        const listRes = await fetch(`${API}/api/raceday/`);
        ALL_BETS = await listRes.json();
        const bets = [...ALL_BETS];

        const grouped = groupBets(bets);
        const icons = getIcons();

        const accaDecimal = calculateAccaOdds(ALL_BETS);
        const ew = ewReturns(accaDecimal);

        const headerOdds = document.querySelector(
            ".header-stat:nth-child(1) .stat-value"
        );
        const headerReturn = document.querySelector(
            ".header-stat:nth-child(2) .stat-value"
        );

        if (headerOdds)
            headerOdds.innerText = `${(accaDecimal - 1).toFixed(2)}/1`;
        if (headerReturn) headerReturn.innerText = `£${ew.toFixed(2)}`;

        list.innerHTML = `
            <div class="race-list-wrapper">
                ${Object.keys(grouped)
                    .map(
                        course => `
                    <div class="race-course-header">${course}</div>

                    ${Object.keys(grouped[course])
                        .sort()
                        .map(
                            time => `
                        <div class="race-time-header">${time}</div>

                        ${grouped[course][time]
                            .map(b => renderRaceCard(b, icons))
                            .join("")}
                    `
                        )
                        .join("")}
                `
                    )
                    .join("")}
            </div>
        `;

        const statsRes = await fetch(`${API}/api/raceday/stats`);
        const stats = await statsRes.json();

        const totalBets = bets.length;
        const wins = bets.filter(b => b.result === "Win").length;
        const strikeRate = totalBets
            ? ((wins / totalBets) * 100).toFixed(1)
            : 0;

        statsBox.innerHTML = `
            <h3>Group Summary</h3>
            Total Bets: ${totalBets}<br>
            Strike Rate: ${strikeRate}%<br>
            Total Stake: £${stats.group.total_stake.toFixed(2)}<br>
            Total Return: £${stats.group.total_return.toFixed(2)}<br>
            Profit: £${stats.group.profit.toFixed(2)}<br><br>

            <h3>Players</h3>
            ${stats.players
                .map(p => {
                    const profitColor =
                        p.profit > 0
                            ? "#0f7a0f"
                            : p.profit < 0
                            ? "#7a0f0f"
                            : "#555";

                    return `
                    <div class="profile-section" style="border-left: 6px solid ${profitColor}; padding-left: 10px;">
                        <strong>${p.player.name}</strong><br>
                        Stake: £${p.total_stake.toFixed(2)}<br>
                        Return: £${p.total_return.toFixed(2)}<br>
                        Profit: £${p.profit.toFixed(2)}
                    </div>
                `;
                })
                .join("")}
        `;

        renderFilteredBets();
        loadRecentActivity();
        renderTodaySummary();
        renderGroupBalance();
    } catch (err) {
        console.error("Error loading race stats:", err);
    }
}

/* ============================================================
   RECENT ACTIVITY
   ============================================================ */

async function loadRecentActivity() {
    const box = document.getElementById("recentActivity");
    if (!box) return;

    try {
        const res = await fetch(`${API}/api/raceday/recent`);
        const items = await res.json();

        if (!items.length) {
            box.innerHTML = "No race day bets recorded yet.";
            return;
        }

        box.innerHTML = items
            .map(a => {
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
                            ${
                                a.horse_number
                                    ? `<span class="horse-number">(${a.horse_number})</span>`
                                    : ""
                            }
                            <span class="horse-name">${a.horse_name}</span>
                            <span class="horse-odds">@${a.odds_fraction}</span>
                        </div>

                        <div class="meta-line">
                            <span class="meta-player">${
                                PLAYER_MAP[a.player_id]
                            }</span>
                            <span>${a.course}</span>
                            <span>${a.race_time}</span>
                        </div>
                    </div>

                    <div class="activity-right">
                        <div class="winnings-label">Winnings</div>
                        <div class="winnings-value ${
                            profit > 0
                                ? "profit-pos"
                                : profit < 0
                                ? "profit-neg"
                                : ""
                        }">
                            £${winnings.toFixed(2)}
                        </div>
                    </div>
                </div>
            `;
            })
            .join("");
    } catch (err) {
        console.error("Error loading recent activity:", err);
    }
}

/* ============================================================
   FILTER BAR — TODAY ONLY / ALL BETS
   ============================================================ */

function filterToday() {
    FILTER_MODE = "today";

    document
        .querySelectorAll(".filter-btn")
        .forEach(btn => btn.classList.remove("active"));
    const btn = document.querySelector(".filter-btn:nth-child(1)");
    if (btn) btn.classList.add("active");

    renderFilteredBets();
}

function filterAll() {
    FILTER_MODE = "all";

    document
        .querySelectorAll(".filter-btn")
        .forEach(btn => btn.classList.remove("active"));
    const btn = document.querySelector(".filter-btn:nth-child(2)");
    if (btn) btn.classList.add("active");

    renderFilteredBets();
}

function renderFilteredBets() {
    const list = document.getElementById("raceList");
    if (!list) return;

    let bets = [...ALL_BETS];

    if (FILTER_MODE === "today") {
        const today = new Date().toISOString().split("T")[0];
        bets = bets.filter(b => b.date === today);
    }

    const grouped = groupBets(bets);
    const icons = getIcons();

    list.innerHTML = `
        <div class="race-list-wrapper">
            ${Object.keys(grouped)
                .map(
                    course => `
                <div class="race-course-header">${course}</div>

                ${Object.keys(grouped[course])
                    .sort()
                    .map(
                        time => `
                    <div class="race-time-header">${time}</div>

                    ${grouped[course][time]
                        .map(b => renderRaceCard(b, icons))
                        .join("")}
                `
                    )
                    .join("")}
            `
                )
                .join("")}
        </div>
    `;
}

async function deleteRaceBet(id) {
    if (!confirm("Delete this bet?")) return;

    try {
        await fetch(`${API}/api/raceday/${id}`, {
            method: "DELETE"
        });

        loadRaceStats();
    } catch (err) {
        console.error("Error deleting race bet:", err);
    }
}

/* ============================================================
   ACCUMULATOR PAGE
   ============================================================ */

async function loadAccumulator() {
    const statusEl = document.getElementById("acca-status");
    const oddsEl = document.getElementById("acca-odds");
    const ewEl = document.getElementById("acca-ew-return");
    const picksBox = document.getElementById("acca-current-picks");
    const standingsBox = document.getElementById("acca-standings");

    if (!statusEl || !oddsEl || !ewEl || !picksBox || !standingsBox) return;

    try {
        const [accaRes, playersRes] = await Promise.all([
            fetch("/accumulator"),
            fetch("/players")
        ]);

        const data = await accaRes.json();
        const players = await playersRes.json();

        renderAccaSummary(data);
        renderAccaCurrentPicks(data.picks || []);
        renderAccaStandings(players, data.picks || []);
    } catch (err) {
        console.error("Error loading accumulator:", err);
    }
}

function renderAccaSummary(data) {
    const statusEl = document.getElementById("acca-status");
    const oddsEl = document.getElementById("acca-odds");
    const ewEl = document.getElementById("acca-ew-return");
    if (!statusEl || !oddsEl || !ewEl) return;

    statusEl.innerText = data.status || "No Picks";

    if (!data.combined_decimal_odds) {
        oddsEl.innerText = "-";
        ewEl.innerText = "-";
        return;
    }

    oddsEl.innerText = data.combined_decimal_odds.toFixed(2);
    ewEl.innerText = data.ew_250_potential_return.toFixed(2);
}

function renderAccaCurrentPicks(picks) {
    const box = document.getElementById("acca-current-picks");
    if (!box) return;

    box.innerHTML = "";

    if (!picks || picks.length === 0) {
        box.innerHTML = `<div class="empty-message">No picks entered yet. Start by adding one.</div>`;
        return;
    }

    box.innerHTML = picks
        .map(p => {
            return `
            <div class="acca-pick-card">
                <div class="pick-main">
                    <div class="pick-horse">
                        ${p.horse_number ? `(${p.horse_number}) ` : ""}${p.horse_name}
                    </div>
                    <div class="pick-odds">@ ${p.odds_fraction}</div>
                </div>

                <div class="pick-meta">
                    <span>${p.player.name}</span>
                    <span>${p.course}</span>
                    <span>${p.race_time}</span>
                </div>

                <div class="pick-footer">
                    <span class="pick-status">${p.status}</span>
                    <button class="btn-remove" onclick="removeAccaPick(${p.id})">
                        Remove
                    </button>
                </div>
            </div>
        `;
        })
        .join("");
}

function renderAccaStandings(players, picks) {
    const box = document.getElementById("acca-standings");
    if (!box) return;

    const picksByPlayerId = new Map();
    picks.forEach(p => {
        picksByPlayerId.set(p.player.id, true);
    });

    box.innerHTML = players
        .map(p => {
            const hasPick = picksByPlayerId.has(p.id);
            const statusText = hasPick ? "Pick locked in" : "Waiting for pick...";
            const statusClass = hasPick ? "standing-ready" : "standing-waiting";

            return `
            <div class="standing-row ${statusClass}">
                <span class="standing-name">${p.name}</span>
                <span class="standing-status">${statusText}</span>
            </div>
        `;
        })
        .join("");
}

async function removeAccaPick(id) {
    try {
        await fetch(`/picks/${id}/acca/remove`, {
            method: "PATCH"
        });

        if (document.getElementById("acca-status")) {
            loadAccumulator();
        }
        if (document.getElementById("current-picks-body")) {
            loadCurrentPicks();
        }
    } catch (err) {
        console.error("Error removing acca pick:", err);
    }
}

async function addAccaPick(id) {
    try {
        await fetch(`/picks/${id}/acca/add`, {
            method: "PATCH"
        });

        if (document.getElementById("acca-status")) {
            loadAccumulator();
        }
        if (document.getElementById("current-picks-body")) {
            loadCurrentPicks();
        }
    } catch (err) {
        console.error("Error adding acca pick:", err);
    }
}

/* ============================================================
   GLOBAL PAGE INITIALISER
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("add-pick-form")) {
        loadPlayersForAddPick();
        setupAddPickForm();
    }

    if (document.getElementById("current-picks-body")) {
        loadCurrentPicks();
    }

    if (document.getElementById("acca-status")) {
        loadAccumulator();
    }

    if (document.getElementById("statsForm")) {
        setupStatsForm();
    }

    if (document.getElementById("playerForm")) {
        setupPlayerDetailsForm();
    }

    if (document.getElementById("raceForm")) {
        setupRaceForm();
        loadRaceStats();
    }

    if (document.getElementById("firstPlayer")) {
        loadPodium();
    }
});
