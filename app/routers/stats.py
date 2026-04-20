from fastapi import APIRouter, Depends, Request, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime
from io import BytesIO

from app.database import get_db
from app import models

router = APIRouter(prefix="/stats", tags=["Stats"])
templates = Jinja2Templates(directory="app/templates")


# ------------------------------------------------------------
# STATS PAGE (HTML)
# ------------------------------------------------------------
@router.get("")
def stats_home(request: Request):
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "active": "stats"
    })


# ------------------------------------------------------------
# MONTHLY STATS
# ------------------------------------------------------------
@router.get("/month/{month}")
def monthly_stats(month: int, year: int, db: Session = Depends(get_db)):
    players = db.query(models.Player).all()
    results = []

    for p in players:
        picks = db.query(models.Pick).filter(
            models.Pick.player_id == p.id
        ).all()

        wins = sum(1 for x in picks if x.status == "Win")
        places = sum(1 for x in picks if x.status == "Place")
        loses = sum(1 for x in picks if x.status == "Lose")
        nr = sum(1 for x in picks if x.status == "NR")

        results.append({
            "player": p.name,
            "wins": wins,
            "places": places,
            "loses": loses,
            "nr": nr
        })

    return results


# ------------------------------------------------------------
# PLAYER DETAILS
# ------------------------------------------------------------
@router.get("/player/{name}")
def player_details(name: str, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter_by(name=name).first()
    if not player:
        return {"error": "Player not found"}

    picks = db.query(models.Pick).filter_by(player_id=player.id).all()

    wins = sum(1 for p in picks if p.status == "Win")
    places = sum(1 for p in picks if p.status == "Place")
    loses = sum(1 for p in picks if p.status == "Lose")
    nr = sum(1 for p in picks if p.status == "NR")

    total = wins + places + loses
    win_rate = wins / total if total > 0 else 0

    biggest = None
    for p in picks:
        if p.status == "Win":
            try:
                frac = p.odds_fraction
                if "/" in frac:
                    a, b = frac.split("/")
                    dec = (float(a) / float(b)) + 1
                else:
                    dec = float(frac)

                if biggest is None or dec > biggest["decimal"]:
                    biggest = {
                        "horse_name": p.horse_name,
                        "odds_fraction": p.odds_fraction,
                        "decimal": dec
                    }
            except:
                continue

    recent = [p.status[0].upper() for p in picks[-5:]]

    return {
        "player": player.name,
        "wins": wins,
        "places": places,
        "loses": loses,
        "nr": nr,
        "win_rate": win_rate,
        "biggest_winner": biggest,
        "recent_form": recent
    }


# ------------------------------------------------------------
# ACCA PERFORMANCE CENTER
# ------------------------------------------------------------
@router.get("/acca")
def acca_stats(db: Session = Depends(get_db)):
    q = db.query(models.AccaHistory)

    total_accas = q.count()
    wins = q.filter(models.AccaHistory.status == "win").count()
    places = q.filter(models.AccaHistory.status == "place").count()
    loses = q.filter(models.AccaHistory.status == "lose").count()

    total_profit = db.query(
        func.coalesce(func.sum(models.AccaHistory.total_return), 0.0)
    ).scalar()

    biggest_return = db.query(
        func.coalesce(func.max(models.AccaHistory.total_return), 0.0)
    ).scalar()

    recent = (
        q.order_by(models.AccaHistory.created_at.desc())
         .limit(5)
         .all()
    )

    recent_payload = [
        {
            "status": r.status,
            "total_return": float(r.total_return or 0),
            "combined_decimal_odds": float(r.combined_decimal_odds or 0),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recent
    ]

    return {
        "total_accas": total_accas,
        "wins": wins,
        "places": places,
        "loses": loses,
        "total_profit": float(total_profit or 0),
        "biggest_return": float(biggest_return or 0),
        "recent": recent_payload,
        "player_contribution": [],
    }


# ------------------------------------------------------------
# DASHBOARD (used by stats.html)
# ------------------------------------------------------------
@router.get("/dashboard")
def stats_dashboard(db: Session = Depends(get_db)):

    players = db.query(models.Player).all()

    player_stats = {
        p.name: {"wins": 0, "places": 0, "loses": 0, "nr": 0}
        for p in players
    }

    history = db.query(models.AccaHistory).all()

    for h in history:
        for pick in h.picks_json:
            name = pick.get("player")
            result = pick.get("result")

            if name not in player_stats:
                continue

            if result == "Win":
                player_stats[name]["wins"] += 1
            elif result == "Place":
                player_stats[name]["places"] += 1
            elif result == "Lose":
                player_stats[name]["loses"] += 1
            elif result == "NR":
                player_stats[name]["nr"] += 1

    player_stats_list = [
        {"player": name, **stats}
        for name, stats in player_stats.items()
    ]

    history_rows = (
        db.query(models.AccaHistory)
        .order_by(models.AccaHistory.created_at.desc())
        .all()
    )

    grouped = {}

    for h in history_rows:
        if not h.created_at:
            continue

        date_key = h.created_at.strftime("%A, %d %B %Y")

        if date_key not in grouped:
            grouped[date_key] = []

        grouped[date_key].append({
            "status": h.status,
            "combined_decimal_odds": float(h.combined_decimal_odds or 0),
            "total_return": float(h.total_return or 0),
            "created_at": h.created_at.isoformat(),
            "picks": h.picks_json,
        })

    return {
        "players": player_stats_list,
        "accas": grouped
    }


# ------------------------------------------------------------
# COMPLETED RACE DAYS
# ------------------------------------------------------------
@router.get("/racedays")
def get_completed_racedays(db: Session = Depends(get_db)):
    racedays = (
        db.query(models.CompletedRaceDay)
        .options(joinedload(models.CompletedRaceDay.bets))
        .order_by(models.CompletedRaceDay.date.desc())
        .all()
    )

    result = []

    for rd in racedays:
        result.append({
            "id": rd.id,
            "date": rd.date,
            "total_stake": rd.total_stake,
            "total_return": rd.total_return,
            "profit": rd.profit,
            "bets": [
                {
                    "player_id": b.player_id,
                    "player_name": b.player_name,
                    "course": b.course,
                    "race_time": b.race_time,
                    "horse_name": b.horse_name,
                    "horse_number": b.horse_number,
                    "odds_fraction": b.odds_fraction,
                    "result": b.result,
                    "stake": b.stake,
                    "winnings": b.winnings
                }
                for b in rd.bets
            ]
        })

    return result


# ------------------------------------------------------------
# RACE DAY PLAYER PERFORMANCE
# ------------------------------------------------------------
@router.get("/raceday/players")
def raceday_player_stats(db: Session = Depends(get_db)):
    players = db.query(models.Player).all()
    racedays = db.query(models.CompletedRaceDay).options(
        joinedload(models.CompletedRaceDay.bets)
    ).all()

    stats = {
        p.name: {"wins": 0, "places": 0, "loses": 0, "nr": 0, "profit": 0}
        for p in players
    }

    for rd in racedays:
        for b in rd.bets:
            name = b.player_name
            if name not in stats:
                continue

            if b.result == "Win":
                stats[name]["wins"] += 1
            elif b.result == "Place":
                stats[name]["places"] += 1
            elif b.result == "Lose":
                stats[name]["loses"] += 1
            elif b.result == "NR":
                stats[name]["nr"] += 1

            stats[name]["profit"] += (b.winnings - b.stake)

    return [
        {"player": name, **values}
        for name, values in stats.items()
    ]


# ============================================================
# EXPORT HELPERS
# ============================================================
def get_raceday_data(db: Session):
    racedays = (
        db.query(models.CompletedRaceDay)
        .options(joinedload(models.CompletedRaceDay.bets))
        .order_by(models.CompletedRaceDay.date.desc())
        .all()
    )

    players = db.query(models.Player).all()

    player_stats = {
        p.name: {"wins": 0, "places": 0, "loses": 0, "nr": 0, "profit": 0}
        for p in players
    }

    for rd in racedays:
        for b in rd.bets:
            name = b.player_name
            if name not in player_stats:
                continue

            if b.result == "Win":
                player_stats[name]["wins"] += 1
            elif b.result == "Place":
                player_stats[name]["places"] += 1
            elif b.result == "Lose":
                player_stats[name]["loses"] += 1
            elif b.result == "NR":
                player_stats[name]["nr"] += 1

            player_stats[name]["profit"] += (b.winnings - b.stake)

    return racedays, player_stats


def get_acca_data(db: Session):
    accas = (
        db.query(models.AccaHistory)
        .order_by(models.AccaHistory.created_at.desc())
        .all()
    )

    players = db.query(models.Player).all()

    player_stats = {
        p.name: {"wins": 0, "places": 0, "loses": 0, "nr": 0}
        for p in players
    }

    for a in accas:
        for pick in a.picks_json:
            name = pick.get("player")
            result = pick.get("result")

            if name not in player_stats:
                continue

            if result == "Win":
                player_stats[name]["wins"] += 1
            elif result == "Place":
                player_stats[name]["places"] += 1
            elif result == "Lose":
                player_stats[name]["loses"] += 1
            elif result == "NR":
                player_stats[name]["nr"] += 1

    return accas, player_stats


def get_summary_data(db: Session):
    players = db.query(models.Player).all()
    picks = db.query(models.Pick).all()

    player_stats = {
        p.name: {"wins": 0, "places": 0, "loses": 0, "nr": 0}
        for p in players
    }

    for p in picks:
        player = db.query(models.Player).filter(models.Player.id == p.player_id).first()
        if not player:
            continue

        name = player.name

        if p.status == "Win":
            player_stats[name]["wins"] += 1
        elif p.status == "Place":
            player_stats[name]["places"] += 1
        elif p.status == "Lose":
            player_stats[name]["loses"] += 1
        elif p.status == "NR":
            player_stats[name]["nr"] += 1

    return player_stats


# ============================================================
# RACE DAY EXPORT — EXCEL
# ============================================================
@router.get("/export/raceday/excel")
def export_raceday_excel(db: Session = Depends(get_db)):
    from openpyxl import Workbook

    racedays, player_stats = get_raceday_data(db)

    wb = Workbook()
    ws = wb.active
    ws.title = "Race Day Summary"

    ws.append(["Date", "Stake", "Return", "Profit"])

    for rd in racedays:
        ws.append([
            rd.date.strftime("%Y-%m-%d"),
            float(rd.total_stake),
            float(rd.total_return),
            float(rd.profit)
        ])

    ws2 = wb.create_sheet("Player Performance")
    ws2.append(["Player", "Wins", "Places", "Loses", "NR", "Profit"])

    for name, stats in player_stats.items():
        ws2.append([
            name,
            stats["wins"],
            stats["places"],
            stats["loses"],
            stats["nr"],
            float(stats["profit"])
        ])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    return Response(
        content=stream.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=performance_raceday.xlsx"}
    )


# ============================================================
# RACE DAY EXPORT — PDF
# ============================================================
@router.get("/export/raceday/pdf")
def export_raceday_pdf(db: Session = Depends(get_db)):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from datetime import datetime

    racedays = (
        db.query(CompletedRaceDay)
        .order_by(CompletedRaceDay.date.desc())
        .all()
    )

    # Flatten all bets for summaries
    all_bets = []
    for rd in racedays:
        all_bets.extend(rd.bets)

    # -----------------------------
    # BUILD SUMMARIES
    # -----------------------------

    # Player performance summary
    player_stats = {}
    for bet in all_bets:
        name = bet.player_name
        if name not in player_stats:
            player_stats[name] = {
                "W": 0, "P": 0, "L": 0, "NR": 0,
                "stake": 0.0, "return": 0.0, "profit": 0.0
            }

        # Count result
        if bet.result in ["Win", "Place", "Lose", "NR"]:
            player_stats[name][bet.result[0]] += 1

        # Money
        player_stats[name]["stake"] += bet.stake or 0
        player_stats[name]["return"] += bet.winnings or 0
        player_stats[name]["profit"] = (
            player_stats[name]["return"] - player_stats[name]["stake"]
        )

    # Course summary
    course_counts = {}
    for bet in all_bets:
        course_counts[bet.course] = course_counts.get(bet.course, 0) + 1

    # Horse summary
    horse_counts = {}
    for bet in all_bets:
        key = f"{bet.horse_name} (#{bet.horse_number})"
        horse_counts[key] = horse_counts.get(key, 0) + 1

    # -----------------------------
    # PDF SETUP
    # -----------------------------
    stream = BytesIO()
    c = canvas.Canvas(stream, pagesize=A4)
    width, height = A4

    y = height - 40

    # -----------------------------
    # TITLE
    # -----------------------------
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, y, "Race Day Report")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d')}")
    y -= 40

    # -----------------------------
    # SECTION 1 — RACE DAY SUMMARY
    # -----------------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Race Day Summary")
    y -= 25

    c.setFont("Helvetica", 11)

    for rd in racedays:
        if y < 60:
            c.showPage()
            y = height - 60

        date_str = rd.date.strftime("%Y-%m-%d")
        stake = float(rd.total_stake or 0)
        ret = float(rd.total_return or 0)
        profit = float(rd.profit or 0)

        line = (
            f"{date_str} — Stake £{stake:g} | "
            f"Return £{ret:g} | Profit £{profit:g}"
        )
        c.drawString(50, y, line)
        y -= 16

    # PAGE BREAK
    c.showPage()
    y = height - 40

    # -----------------------------
    # SECTION 2 — PLAYER PERFORMANCE
    # -----------------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Player Performance")
    y -= 25

    c.setFont("Helvetica", 11)

    for player, stats in player_stats.items():
        if y < 60:
            c.showPage()
            y = height - 60

        line = (
            f"{player} — "
            f"W {stats['W']} | P {stats['P']} | L {stats['L']} | NR {stats['NR']} | "
            f"Stake £{stats['stake']:g} | Return £{stats['return']:g} | Profit £{stats['profit']:g}"
        )
        c.drawString(50, y, line)
        y -= 16

    # PAGE BREAK
    c.showPage()
    y = height - 40

    # -----------------------------
    # SECTION 3 — COURSE SUMMARY
    # -----------------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Course Summary")
    y -= 25

    c.setFont("Helvetica", 11)

    for course, count in sorted(course_counts.items(), key=lambda x: -x[1]):
        if y < 60:
            c.showPage()
            y = height - 60

        c.drawString(50, y, f"{course} — {count} bets")
        y -= 16

    # PAGE BREAK
    c.showPage()
    y = height - 40

    # -----------------------------
    # SECTION 4 — HORSE SUMMARY
    # -----------------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Horse Summary")
    y -= 25

    c.setFont("Helvetica", 11)

    for horse, count in sorted(horse_counts.items(), key=lambda x: -x[1]):
        if y < 60:
            c.showPage()
            y = height - 60

        c.drawString(50, y, f"{horse} — {count} picks")
        y -= 16

    # PAGE BREAK
    c.showPage()
    y = height - 40

    # -----------------------------
    # SECTION 5 — FULL BET BREAKDOWN
    # -----------------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Full Bet Breakdown")
    y -= 30

    for rd in racedays:
        if y < 120:
            c.showPage()
            y = height - 60

        # Race Day Header
        c.setFont("Helvetica-Bold", 13)
        c.drawString(40, y, rd.date.strftime("%Y-%m-%d"))
        y -= 10

        c.setLineWidth(0.5)
        c.line(40, y, width - 40, y)
        y -= 20

        # Bets
        for bet in rd.bets:
            if y < 100:
                c.showPage()
                y = height - 60

            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, f"{bet.player_name} — {bet.course} — {bet.race_time}")
            y -= 14

            c.setFont("Helvetica", 11)
            c.drawString(60, y, f"Horse: {bet.horse_name} (#{bet.horse_number})")
            y -= 14

            c.drawString(60, y, f"Odds: {bet.odds_fraction}")
            y -= 14

            # Highlight WIN only
            if bet.result == "Win":
                c.setFont("Helvetica-Bold", 11)
                c.drawString(60, y, "Result: WIN")
            else:
                c.setFont("Helvetica", 11)
                c.drawString(60, y, f"Result: {bet.result}")
            y -= 14

            c.setFont("Helvetica", 11)
            c.drawString(60, y, f"Stake: £{bet.stake:g}")
            y -= 14

            c.drawString(60, y, f"Winnings: £{bet.winnings:g}")
            y -= 18  # compact spacing

        y -= 10  # small gap between race days

    # FINALISE PDF
    c.save()
    stream.seek(0)

    return Response(
        content=stream.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=raceday_report.pdf"}
    )




# ============================================================
# SUMMARY EXPORT — EXCEL
# ============================================================
@router.get("/export/summary/excel")
def export_summary_excel(db: Session = Depends(get_db)):
    from openpyxl import Workbook

    player_stats = get_summary_data(db)

    wb = Workbook()
    ws = wb.active
    ws.title = "Overall Summary"

    ws.append(["Player", "Wins", "Places", "Loses", "NR"])

    for name, stats in player_stats.items():
        ws.append([
            name,
            stats["wins"],
            stats["places"],
            stats["loses"],
            stats["nr"]
        ])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    return Response(
        content=stream.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=performance_summary.xlsx"}
    )


# ============================================================
# SUMMARY EXPORT — PDF
# ============================================================
@router.get("/export/summary/pdf")
def export_summary_pdf(db: Session = Depends(get_db)):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    player_stats = get_summary_data(db)

    stream = BytesIO()
    c = canvas.Canvas(stream, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Overall Summary Report")

    y = height - 80
    c.setFont("Helvetica", 11)

    for name, stats in player_stats.items():
        if y < 60:
            c.showPage()
            y = height - 60

        line = (
            f"{name}: W {stats['wins']} | P {stats['places']} | "
            f"L {stats['loses']} | NR {stats['nr']}"
        )
        c.drawString(50, y, line)
        y -= 16

    c.showPage()
    c.save()
    stream.seek(0)

    return Response(
        content=stream.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=performance_summary.pdf"}
    )
