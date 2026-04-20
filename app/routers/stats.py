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


# ------------------------------------------------------------
# EXPORT: EXCEL (.xlsx)
# ------------------------------------------------------------
@router.get("/export/excel")
def export_excel(db: Session = Depends(get_db)):
    from openpyxl import Workbook
    from openpyxl.chart import BarChart, Reference

    wb = Workbook()
    ws = wb.active
    ws.title = "Player Performance"

    ws.append(["Player", "Wins", "Places", "Loses", "NR", "Profit"])

    players = db.query(models.Player).all()

    for p in players:
        picks = db.query(models.Pick).filter(models.Pick.player_id == p.id).all()

        wins = sum(1 for x in picks if x.status == "Win")
        places = sum(1 for x in picks if x.status == "Place")
        loses = sum(1 for x in picks if x.status == "Lose")
        nr = sum(1 for x in picks if x.status == "NR")
        profit = sum((x.winnings - x.stake) for x in picks if hasattr(x, "winnings"))

        ws.append([p.name, wins, places, loses, nr, float(profit or 0)])

    if ws.max_row > 1:
        chart = BarChart()
        data = Reference(ws, min_col=2, max_col=2, min_row=1, max_row=ws.max_row)
        cats = Reference(ws, min_col=1, min_row=2, max_row=ws.max_row)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        chart.title = "Wins by Player"
        ws.add_chart(chart, "H2")

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    return Response(
        content=stream.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=performance_report.xlsx"}
    )


# ------------------------------------------------------------
# EXPORT: PDF
# ------------------------------------------------------------
@router.get("/export/pdf")
def export_pdf(db: Session = Depends(get_db)):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    stream = BytesIO()
    c = canvas.Canvas(stream, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 40, "Performance Report")

    y = height - 80
    c.setFont("Helvetica", 10)

    players = db.query(models.Player).all()
    c.drawString(40, y, "Player Performance:")
    y -= 20

    for p in players:
        if y < 60:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 10)

        picks = db.query(models.Pick).filter(models.Pick.player_id == p.id).all()

        wins = sum(1 for x in picks if x.status == "Win")
        places = sum(1 for x in picks if x.status == "Place")
        loses = sum(1 for x in picks if x.status == "Lose")
        nr = sum(1 for x in picks if x.status == "NR")
        profit = sum((x.winnings - x.stake) for x in picks if hasattr(x, "winnings"))

        line = f"{p.name}: W {wins} / P {places} / L {loses} / NR {nr} / Profit £{float(profit or 0):.2f}"
        c.drawString(50, y, line)
        y -= 16

    c.showPage()
    c.save()
    stream.seek(0)

    return Response(
        content=stream.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=performance_report.pdf"}
    )
