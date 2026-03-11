const API = "https://horse-racing-tracker-production.up.railway.app";
let PLAYER_MAP = {};

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
    const resultBox = document.getElementById("result");

    const now = new Date();
    form.month.value = now.getMonth() + 1;
    form.year.value = now.getFullYear();

    form.onsubmit = async (e) => {
        e.preventDefault();

         const body = Object.fromEntries(new FormData(form).entries());
       console.log("FORM BODY:", body);
   
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
        body: JSON.stringify({ status })
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

        const submitRes = await fetch(`${API}/raceday/`, {
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
async function loadRecentActivity() {
    const res = await fetch(`${API}/raceday/recent`);
    const items = await res.json();

    const box = document.getElementById("recentActivity");

    if (!items.length) {
        box.innerHTML = "No race day bets recorded yet.";
        return;
    }

    const icons = {
        "Win": "🟢",
        "Place": "🔵",
        "Lose": "🔴",
        "NR": "⚪",
        "Pending": "⏳"
    };

    box.innerHTML = items.map(a => `
        <div class="activity-card">

            <div class="activity-top">
                (${a.horse_number}) ${a.horse_name} @ ${a.odds_fraction}
            </div>

            <div class="activity-meta">
                Player: ${PLAYER_MAP[a.player_id]}<br>
                Course: ${a.course}<br>
                Time: ${a.race_time}<br>
                Stake: £${a.amount_bet}
            </div>

            <div class="activity-status">
                <span class="result-${a.result.toLowerCase()}">
                    ${icons[a.result]} ${a.result}
                </span>
            </div>

        </div>
    `).join("");
}

/* ============================================================
   RACE DAY — UPDATE RESULT
   ============================================================ */

async function updateRaceResult(id, result) {
    await fetch(`${API}/raceday/${id}/result`, {
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
    const month = new Date().getMonth() + 1;
    const year = new Date().getFullYear();

    // Fetch all bets for this month
    const listRes = await fetch(`${API}/raceday/?month=${month}&year=${year}`);
    let bets = await listRes.json();

   console.log("BETS:", bets);

    // Today-only filter
    const todayOnly = document.getElementById("todayOnly")?.checked;
    if (todayOnly) {
        const today = new Date().toISOString().slice(0, 10);
        bets = bets.filter(b => b.date === today);
    }

    // Sort by course → race_time
    bets.sort((a, b) => {
        if (a.course !== b.course) return a.course.localeCompare(b.course);
        return a.race_time.localeCompare(b.race_time);
    });

    const list = document.getElementById("raceList");

    // Group by course → race_time
    const grouped = {};
    bets.forEach(b => {
        if (!grouped[b.course]) grouped[b.course] = {};
        if (!grouped[b.course][b.race_time]) grouped[b.course][b.race_time] = [];
        grouped[b.course][b.race_time].push(b);
    });

    const icons = {
        "Win": "🟢",
        "Place": "🔵",
        "Lose": "🔴",
        "NR": "⚪",
        "Pending": "⏳"
    };

    // Build Race Day cards
    list.innerHTML = Object.keys(grouped).map(course => `
        <div class="race-course-header">${course}</div>

        ${Object.keys(grouped[course]).sort().map(time => `
            <div class="race-time-header">${time}</div>

            ${grouped[course][time].map(b => `
                <div class="race-card">

                    <div class="race-stake">Stake: £${b.amount_bet}</div>

                    <div class="race-horse">
                        (${b.horse_number}) ${b.horse_name} @ ${b.odds_fraction}
                    </div>

                    <div class="race-meta">
                        Player: ${PLAYER_MAP[b.player_id]}<br>
                        Course: ${b.course}<br>
                        Race Time: ${b.race_time}<br>
                        Winnings: £${b.winnings || "0.00"}
                    </div>

                    <div class="race-status">
                        <span class="result-${b.result.toLowerCase()}">
                            ${icons[b.result]} ${b.result}
                        </span>
                    </div>

                    <div class="race-buttons">
                        <button class="btn-win" onclick="updateRaceResult(${b.id}, 'Win')">WIN</button>
                        <button onclick="updateRaceResult(${b.id}, 'Place')">PLACE</button>
                        <button onclick="updateRaceResult(${b.id}, 'Lose')">LOSE</button>
                        <button onclick="updateRaceResult(${b.id}, 'NR')">NR</button>
                    </div>

                </div>
            `).join("")}

        `).join("")}

    `).join("");

    /* ============================================================
       GROUP STATS
       ============================================================ */

    const statsRes = await fetch(`${API}/raceday/stats?month=${month}&year=${year}`);
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

    // Update Recent Activity
    loadRecentActivity();
}


