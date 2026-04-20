from fastapi import APIRouter, Depends, Request, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime
from io import BytesIO
from app.models import CompletedRaceDay, CompletedRaceDayBet

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
    from io import BytesIO
    from fastapi import Response

    # -----------------------------
    # FETCH DATA
    # -----------------------------
    racedays = (
        db.query(CompletedRaceDay)
        .order_by(CompletedRaceDay.date.desc())
        .all()
    )

    all_bets = []
    for rd in racedays:
        all_bets.extend(rd.bets)

    # -----------------------------
    # BUILD SUMMARIES
    # -----------------------------
    total_racedays = len(racedays)
    total_bets = len(all_bets)
    total_stake = sum((b.stake or 0) for b in all_bets)
    total_return = sum((b.winnings or 0) for b in all_bets)
    total_profit = total_return - total_stake

    # Player performance summary
    player_stats = {}
    for bet in all_bets:
        name = bet.player_name or "Unknown"
        if name not in player_stats:
            player_stats[name] = {
                "W": 0, "P": 0, "L": 0, "NR": 0,
                "stake": 0.0, "return": 0.0, "profit": 0.0
            }

        if bet.result in ["Win", "Place", "Lose", "NR"]:
            player_stats[name][bet.result[0]] += 1

        player_stats[name]["stake"] += bet.stake or 0
        player_stats[name]["return"] += bet.winnings or 0
        player_stats[name]["profit"] = (
            player_stats[name]["return"] - player_stats[name]["stake"]
        )

    # Course summary
    course_counts = {}
    for bet in all_bets:
        course = bet.course or "Unknown"
        course_counts[course] = course_counts.get(course, 0) + 1

    # Horse summary
    horse_counts = {}
    for bet in all_bets:
        hn = bet.horse_name or "Unknown"
        num = bet.horse_number if bet.horse_number is not None else "-"
        key = f"{hn} (#{num})"
        horse_counts[key] = horse_counts.get(key, 0) + 1

    # -----------------------------
    # PDF SETUP
    # -----------------------------
    stream = BytesIO()
    c = canvas.Canvas(stream, pagesize=A4)
    width, height = A4

    # Colours
    racing_green = colors.HexColor("#004225")
    gold = colors.HexColor("#D4AF37")
    pale_green = colors.HexColor("#E6F4EA")
    pale_red = colors.HexColor("#FDE7E9")
    pale_blue = colors.HexColor("#E5F0FF")
    pale_grey = colors.HexColor("#F2F2F2")

    # Tile width (60% of page), centred
    tile_width = width * 0.6
    tile_x = (width - tile_width) / 2

    def draw_header_bar(page_title: str):
        c.setFillColor(racing_green)
        c.rect(0, height - 40, width, 40, stroke=0, fill=1)
        c.setFillColor(gold)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, height - 27, page_title)

    def draw_page_number(page_num: int, total_pages: int = None):
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.grey)
        if total_pages:
            text = f"Page {page_num} of {total_pages}"
        else:
            text = f"Page {page_num}"
        c.drawRightString(width - 40, 25, text)

    # We'll track page numbers manually
    page_num = 1

    def new_page(title: str):
        nonlocal page_num
        if c.getPageNumber() > 1:
            draw_page_number(page_num)
            c.showPage()
            page_num += 1
        draw_header_bar(title)
        return height - 60  # initial y

    # -----------------------------
    # PAGE 1 — TITLE + DASHBOARD + RACE DAY SUMMARY
    # -----------------------------
    y = new_page("Race Day Report")

    # Generated date
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(40, y, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d')}")
    y -= 25

    # Summary dashboard box
    box_height = 70
    c.setFillColor(pale_grey)
    c.setStrokeColor(gold)
    c.setLineWidth(1)
    c.roundRect(40, y - box_height, width - 80, box_height, 8, stroke=1, fill=1)

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 18, "Summary")
    c.setFont("Helvetica", 10)

    c.drawString(50, y - 35, f"Total Race Days: {total_racedays}")
    c.drawString(220, y - 35, f"Total Bets: {total_bets}")
    c.drawString(50, y - 50, f"Total Stake: £{total_stake:g}")
    c.drawString(220, y - 50, f"Total Return: £{total_return:g}")
    c.drawString(390, y - 50, f"Total Profit: £{total_profit:g}")

    y -= (box_height + 30)

    # Section: Race Day Summary
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.black)
    c.drawString(40, y, "Race Day Summary")
    y -= 8
    c.setStrokeColor(gold)
    c.setLineWidth(1)
    c.line(40, y, width - 40, y)
    y -= 20

    c.setFont("Helvetica", 11)
    for rd in racedays:
        if y < 80:
            draw_page_number(page_num)
            y = new_page("Race Day Report")

            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(colors.black)
            c.drawString(40, y, "Race Day Summary (cont.)")
            y -= 8
            c.setStrokeColor(gold)
            c.line(40, y, width - 40, y)
            y -= 20
            c.setFont("Helvetica", 11)

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

    # -----------------------------
    # PAGE 2 — PLAYER PERFORMANCE
    # -----------------------------
    draw_page_number(page_num)
    y = new_page("Race Day Report")

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.black)
    c.drawString(40, y, "Player Performance")
    y -= 8
    c.setStrokeColor(gold)
    c.line(40, y, width - 40, y)
    y -= 20

    c.setFont("Helvetica", 11)
    for player, stats in player_stats.items():
        if y < 80:
            draw_page_number(page_num)
            y = new_page("Race Day Report")
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Player Performance (cont.)")
            y -= 8
            c.setStrokeColor(gold)
            c.line(40, y, width - 40, y)
            y -= 20
            c.setFont("Helvetica", 11)

        line = (
            f"{player} — "
            f"W {stats['W']} | P {stats['P']} | L {stats['L']} | NR {stats['NR']} | "
            f"Stake £{stats['stake']:g} | Return £{stats['return']:g} | Profit £{stats['profit']:g}"
        )
        c.drawString(50, y, line)
        y -= 16

    # -----------------------------
    # PAGE 3 — COURSE SUMMARY
    # -----------------------------
    draw_page_number(page_num)
    y = new_page("Race Day Report")

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.black)
    c.drawString(40, y, "Course Summary")
    y -= 8
    c.setStrokeColor(gold)
    c.line(40, y, width - 40, y)
    y -= 20

    c.setFont("Helvetica", 11)
    for course, count in sorted(course_counts.items(), key=lambda x: -x[1]):
        if y < 80:
            draw_page_number(page_num)
            y = new_page("Race Day Report")
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Course Summary (cont.)")
            y -= 8
            c.setStrokeColor(gold)
            c.line(40, y, width - 40, y)
            y -= 20
            c.setFont("Helvetica", 11)

        c.drawString(50, y, f"{course} — {count} bets")
        y -= 16

    # -----------------------------
    # PAGE 4 — HORSE SUMMARY
    # -----------------------------
    draw_page_number(page_num)
    y = new_page("Race Day Report")

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.black)
    c.drawString(40, y, "Horse Summary")
    y -= 8
    c.setStrokeColor(gold)
    c.line(40, y, width - 40, y)
    y -= 20

    c.setFont("Helvetica", 11)
    for horse, count in sorted(horse_counts.items(), key=lambda x: -x[1]):
        if y < 80:
            draw_page_number(page_num)
            y = new_page("Race Day Report")
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Horse Summary (cont.)")
            y -= 8
            c.setStrokeColor(gold)
            c.line(40, y, width - 40, y)
            y -= 20
            c.setFont("Helvetica", 11)

        c.drawString(50, y, f"{horse} — {count} picks")
        y -= 16

    # -----------------------------
    # FULL BET BREAKDOWN — PREMIUM TILES
    # -----------------------------
    draw_page_number(page_num)
    y = new_page("Race Day Report")

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.black)
    c.drawString(40, y, "Full Bet Breakdown")
    y -= 8
    c.setStrokeColor(gold)
    c.line(40, y, width - 40, y)
    y -= 25

    for rd in racedays:
        # Race Day title card
        if y < 140:
            draw_page_number(page_num)
            y = new_page("Race Day Report")
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Full Bet Breakdown (cont.)")
            y -= 8
            c.setStrokeColor(gold)
            c.line(40, y, width - 40, y)
            y -= 25

        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.black)
        date_str = rd.date.strftime("%Y-%m-%d")

        # Race day card (simple framed line)
        c.setStrokeColor(gold)
        c.setLineWidth(1)
        card_height = 24
        card_width = width - 80
        card_x = 40
        card_y = y - card_height + 4
        c.roundRect(card_x, card_y, card_width, card_height, 6, stroke=1, fill=0)
        c.drawCentredString(card_x + card_width / 2, card_y + 7, f"RACE DAY — {date_str}")
        y -= (card_height + 20)

        # Bets for this race day
        for bet in rd.bets:
            if y < 140:
                draw_page_number(page_num)
                y = new_page("Race Day Report")
                c.setFont("Helvetica-Bold", 14)
                c.drawString(40, y, "Full Bet Breakdown (cont.)")
                y -= 8
                c.setStrokeColor(gold)
                c.line(40, y, width - 40, y)
                y -= 25

                # Re-draw race day card on new page
                c.setFont("Helvetica-Bold", 12)
                c.setFillColor(colors.black)
                c.setStrokeColor(gold)
                c.setLineWidth(1)
                card_height = 24
                card_width = width - 80
                card_x = 40
                card_y = y - card_height + 4
                c.roundRect(card_x, card_y, card_width, card_height, 6, stroke=1, fill=0)
                c.drawCentredString(card_x + card_width / 2, card_y + 7, f"RACE DAY — {date_str}")
                y -= (card_height + 20)

            # Determine tile background colour based on result
            result = bet.result or "Pending"
            if result == "Win":
                bg_color = pale_green
                result_color = colors.green
            elif result == "Lose":
                bg_color = pale_red
                result_color = colors.HexColor("#B00020")
            elif result == "Place":
                bg_color = pale_blue
                result_color = colors.HexColor("#0047AB")
            elif result == "NR":
                bg_color = pale_grey
                result_color = colors.grey
            else:
                bg_color = colors.white
                result_color = colors.black

            tile_height = 80
            tile_y = y - tile_height

            # Tile background
            c.setFillColor(bg_color)
            c.setStrokeColor(gold)
            c.setLineWidth(1)
            c.roundRect(tile_x, tile_y, tile_width, tile_height, 8, stroke=1, fill=1)

            # Tile content
            inner_x = tile_x + 10
            text_y = tile_y + tile_height - 16

            # Header line
            c.setFont("Helvetica-Bold", 11)
            c.setFillColor(colors.black)
            course = bet.course or "Unknown"
            race_time = bet.race_time or "-"
            player_name = bet.player_name or "Unknown"
            c.drawString(inner_x, text_y, f"{player_name} — {course} — {race_time}")
            text_y -= 16

            # Horse line
            c.setFont("Helvetica", 10)
            hn = bet.horse_name or "Unknown"
            num = bet.horse_number if bet.horse_number is not None else "-"
            c.setFillColor(colors.black)
            c.drawString(inner_x, text_y, f"Horse: {hn} (#{num})")
            text_y -= 14

            # Odds
            odds = bet.odds_fraction or "-"
            c.drawString(inner_x, text_y, f"Odds: {odds}")
            text_y -= 14

            # Result (colour-coded, WIN bold)
            if result == "Win":
                c.setFont("Helvetica-Bold", 10)
                c.setFillColor(result_color)
                c.drawString(inner_x, text_y, "Result: WIN")
            else:
                c.setFont("Helvetica", 10)
                c.setFillColor(result_color)
                c.drawString(inner_x, text_y, f"Result: {result}")
            text_y -= 14

            # Money
            c.setFont("Helvetica", 10)
            c.setFillColor(colors.black)
            stake_val = bet.stake or 0
            win_val = bet.winnings or 0
            c.drawString(inner_x, text_y, f"Stake: £{stake_val:g}")
            text_y -= 14
            c.drawString(inner_x, text_y, f"Winnings: £{win_val:g}")

            y = tile_y - 20  # space below tile

    # FINALISE
    draw_page_number(page_num)
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
