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

# ============================================================
# RACE DAY EXPORT — EXCEL (PREMIUM BOOKMAKER STYLE)
# ============================================================
@router.get("/export/raceday/excel")
def export_raceday_excel(db: Session = Depends(get_db)):
    from fastapi import Response
    import xlsxwriter
    from io import BytesIO

    racedays, player_stats = get_raceday_data(db)

    # Colours
    RACING_GREEN = "#004225"
    GOLD = "#D4AF37"
    CREAM = "#FAF7F0"

    # Create workbook
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    # ============================================================
    # SHEET 1 — RACE DAY SUMMARY
    # ============================================================
    ws = workbook.add_worksheet("Race Day Summary")

    headers = ["Date", "Stake", "Return", "Profit"]

    # Header style
    header_fmt = workbook.add_format({
        "bold": True,
        "font_color": GOLD,
        "bg_color": RACING_GREEN,
        "border": 1,
        "border_color": GOLD,
        "align": "center",
        "valign": "vcenter"
    })

    # Body style
    body_fmt = workbook.add_format({
        "border": 1,
        "border_color": "#CCCCCC",
        "bg_color": CREAM
    })

    # Write headers
    for col, h in enumerate(headers):
        ws.write(0, col, h, header_fmt)

    # Write rows
    for r, rd in enumerate(racedays, start=1):
        ws.write(r, 0, rd.date.strftime("%Y-%m-%d"), body_fmt)
        ws.write(r, 1, float(rd.total_stake), body_fmt)
        ws.write(r, 2, float(rd.total_return), body_fmt)
        ws.write(r, 3, float(rd.profit), body_fmt)

    # Auto-fit columns
    for col in range(len(headers)):
        ws.set_column(col, col, max(12, len(headers[col]) + 2))

    # Auto-filter
    ws.autofilter(0, 0, len(racedays), len(headers) - 1)

    # ============================================================
    # SHEET 2 — PLAYER PERFORMANCE
    # ============================================================
    ws2 = workbook.add_worksheet("Player Performance")

    headers2 = ["Player", "Wins", "Places", "Loses", "NR", "Profit"]

    # Write headers
    for col, h in enumerate(headers2):
        ws2.write(0, col, h, header_fmt)

    # Write rows
    for r, (name, stats) in enumerate(player_stats.items(), start=1):
        ws2.write(r, 0, name, body_fmt)
        ws2.write(r, 1, stats["wins"], body_fmt)
        ws2.write(r, 2, stats["places"], body_fmt)
        ws2.write(r, 3, stats["loses"], body_fmt)
        ws2.write(r, 4, stats["nr"], body_fmt)
        ws2.write(r, 5, float(stats["profit"]), body_fmt)

    # Auto-fit columns
    for col in range(len(headers2)):
        ws2.set_column(col, col, max(12, len(headers2[col]) + 2))

    # Auto-filter
    ws2.autofilter(0, 0, len(player_stats), len(headers2) - 1)

    # ============================================================
    # FINALISE
    # ============================================================
    workbook.close()
    output.seek(0)

    return Response(
        content=output.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=raceday_summary.xlsx"}
    )


# ============================================================
# RACE DAY EXPORT — PDF (FIXED LAYOUT)
# ============================================================
@router.get("/export/raceday/pdf")
def export_raceday_pdf(db: Session = Depends(get_db)):
    from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER, TA_LEFT

RACING_GREEN = colors.HexColor("#0B3D2E")
GOLD = colors.HexColor("#D4AF37")
CREAM = colors.HexColor("#FAF7F0")

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

# -----------------------------
# Rounded Tile Helper
# -----------------------------
def draw_tile(c, x, y, w, h, header_text=None):
    radius = 6

    # Background
    c.setFillColor(CREAM)
    c.roundRect(x, y, w, h, radius, stroke=1, fill=1)

    # Border
    c.setStrokeColor(GOLD)
    c.roundRect(x, y, w, h, radius, stroke=1, fill=0)

    # Header bar
    if header_text:
        c.setFillColor(RACING_GREEN)
        c.roundRect(x, y + h - 14*mm, w, 14*mm, radius, stroke=0, fill=1)

        c.setFillColor(GOLD)
        c.setFont(FONT_BOLD, 12)
        c.drawString(x + 4*mm, y + h - 9*mm, header_text)

        # Divider
        c.setStrokeColor(GOLD)
        c.setLineWidth(1)
        c.line(x, y + h - 14*mm, x + w, y + h - 14*mm)

# -----------------------------
# Text Helper
# -----------------------------
def draw_text(c, x, y, text, size=10, bold=False):
    c.setFont(FONT_BOLD if bold else FONT, size)
    c.setFillColor(colors.black)
    c.drawString(x, y, text)

# -----------------------------
# MAIN PDF FUNCTION
# -----------------------------
def generate_raceday_pdf(buffer, summary, players, courses, bets, horses):
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # -----------------------------------
    # PAGE 1 — DASHBOARD
    # -----------------------------------

    # Header bar
    c.setFillColor(RACING_GREEN)
    c.rect(0, height - 20*mm, width, 20*mm, fill=1, stroke=0)

    c.setFillColor(GOLD)
    c.setFont(FONT_BOLD, 18)
    c.drawCentredString(width/2, height - 8*mm, f"RACE DAY REPORT — {summary['date']}")

    y = height - 35*mm

    # -----------------------------
    # SUMMARY TILES (3 across)
    # -----------------------------
    tile_w = (width - 40*mm) / 3
    tile_h = 25*mm
    x_start = 15*mm

    summary_items = [
        ("Total Bets", summary["total_bets"]),
        ("Total Stake", f"£{summary['total_stake']}"),
        ("Total Return", f"£{summary['total_return']}"),
        ("Total Profit", f"£{summary['total_profit']}"),
    ]

    for i, (label, value) in enumerate(summary_items):
        col = i % 3
        row = i // 3

        x = x_start + col * (tile_w + 5*mm)
        y_tile = y - row * (tile_h + 5*mm)

        draw_tile(c, x, y_tile, tile_w, tile_h, header_text=label)
        draw_text(c, x + 4*mm, y_tile + 8*mm, str(value), size=12, bold=True)

    y -= 2 * (tile_h + 10*mm)

    # -----------------------------
    # PLAYER PERFORMANCE (2 columns)
    # -----------------------------
    tile_w = (width - 40*mm) / 2
    tile_h = 30*mm

    for i, p in enumerate(players):
        col = i % 2
        row = i // 2

        x = x_start + col * (tile_w + 10*mm)
        y_tile = y - row * (tile_h + 8*mm)

        draw_tile(c, x, y_tile, tile_w, tile_h, header_text=p["name"])

        body_y = y_tile + tile_h - 20*mm
        draw_text(c, x + 4*mm, body_y, f"W{p['W']} | P{p['P']} | L{p['L']} | NR{p['NR']}")
        draw_text(c, x + 4*mm, body_y - 6*mm,
                  f"Stake £{p['stake']} | Return £{p['return']} | Profit £{p['profit']}")

    # -----------------------------
    # COURSE SUMMARY TILE
    # -----------------------------
    y_course = y - ((len(players)+1)//2) * (tile_h + 10*mm) - 10*mm
    tile_h_course = 25*mm

    draw_tile(c, x_start, y_course, tile_w, tile_h_course, header_text="Course Summary")

    cy = y_course + tile_h_course - 20*mm
    for course, count in courses.items():
        draw_text(c, x_start + 4*mm, cy, f"{course} — {count} bets")
        cy -= 6*mm

    c.showPage()

    # -----------------------------------
    # PAGE 2 — FULL BET BREAKDOWN
    # -----------------------------------

    c.setFillColor(RACING_GREEN)
    c.rect(0, height - 20*mm, width, 20*mm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.setFont(FONT_BOLD, 18)
    c.drawCentredString(width/2, height - 8*mm, "FULL BET BREAKDOWN")

    y = height - 35*mm
    tile_w = (width - 40*mm) / 2
    tile_h = 28*mm

    for i, b in enumerate(bets):
        col = i % 2
        row = i // 2

        x = x_start + col * (tile_w + 10*mm)
        y_tile = y - row * (tile_h + 8*mm)

        header = f"{b['player']} — {b['course']} — {b['time']}"
        draw_tile(c, x, y_tile, tile_w, tile_h, header_text=header)

        body_y = y_tile + tile_h - 20*mm
        draw_text(c, x + 4*mm, body_y,
                  f"{b['horse']} — {b['odds']} — {b['result']}")
        draw_text(c, x + 4*mm, body_y - 6*mm,
                  f"Stake £{b['stake']} → £{b['return']}")

    c.showPage()
    c.save()

    
# ============================================================
# ACCA EXPORT — PREMIUM BOOKMAKER LAYOUT (PARENT TILE + 2-COL MINI-TILES)
# ============================================================
@router.get("/export/acca/pdf")
def export_acca_pdf(db: Session = Depends(get_db)):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from datetime import datetime
    from io import BytesIO
    from fastapi import Response

    # Load all accas
    accas = (
        db.query(models.AccaHistory)
        .order_by(models.AccaHistory.created_at.desc())
        .all()
    )

    # Summary stats
    total_accas = len(accas)
    wins = sum(1 for a in accas if a.status == "win")
    places = sum(1 for a in accas if a.status == "place")
    loses = sum(1 for a in accas if a.status == "lose")

    total_stake = sum((a.stake or 0) for a in accas)
    total_return = sum((a.total_return or 0) for a in accas)
    total_profit = total_return - total_stake
    biggest_return = max(((a.total_return or 0) for a in accas), default=0)

    # PDF setup
    stream = BytesIO()
    c = canvas.Canvas(stream, pagesize=A4)
    width, height = A4

    # Colours
    RACING_GREEN = colors.HexColor("#004225")
    GOLD = colors.HexColor("#D4AF37")
    CREAM = colors.HexColor("#FAF7F0")
    PALE_GREEN = colors.HexColor("#E6F4EA")
    PALE_RED = colors.HexColor("#FDE7E9")
    PALE_BLUE = colors.HexColor("#E5F0FF")
    PALE_GREY = colors.HexColor("#F2F2F2")

    # Tile widths
    PARENT_W = width * 0.80
    PARENT_X = (width - PARENT_W) / 2

    MINI_W = (PARENT_W - 30) / 2   # 2 tiles per row inside parent
    MINI_H = 80
    MINI_RADIUS = 6

    # Header bar
    def header(title):
        c.setFillColor(RACING_GREEN)
        c.rect(0, height - 40, width, 40, stroke=0, fill=1)
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, height - 27, title)

    # Page number
    def page_number(n):
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.grey)
        c.drawRightString(width - 40, 25, f"Page {n}")

    # Page engine
    page = 1

    def new_page(title):
        nonlocal page
        if page > 1:
            page_number(page)
            c.showPage()
        page += 1
        header(title)
        return height - 60

    y = new_page("ACCA Report")

    # Generated date
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(40, y, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d')}")
    y -= 25

    # -----------------------------
    # SUMMARY TILES (3 across)
    # -----------------------------
    TILE_W = (width - 60) / 3
    TILE_H = 30
    TILE_RADIUS = 6

    summary_items = [
        ("Total Accas", total_accas),
        ("Wins", wins),
        ("Places", places),
        ("Loses", loses),
        ("Total Stake", f"£{total_stake:g}"),
        ("Total Return", f"£{total_return:g}"),
        ("Profit", f"£{total_profit:g}"),
        ("Biggest Return", f"£{biggest_return:g}"),
    ]

    x_start = 40
    for i, (label, value) in enumerate(summary_items):
        col = i % 3
        row = i // 3

        x = x_start + col * (TILE_W + 10)
        y_tile = y - row * (TILE_H + 15)

        # Tile background
        c.setFillColor(CREAM)
        c.setStrokeColor(GOLD)
        c.roundRect(x, y_tile, TILE_W, TILE_H, TILE_RADIUS, stroke=1, fill=1)

        # Header bar
        c.setFillColor(RACING_GREEN)
        c.roundRect(x, y_tile + TILE_H - 12, TILE_W, 12, TILE_RADIUS, stroke=0, fill=1)

        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 4, y_tile + TILE_H - 9, label)

        # Value
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x + 4, y_tile + 8, str(value))

    y -= 3 * (TILE_H + 20)

    # -----------------------------
    # SECTION TITLE
    # -----------------------------
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.black)
    c.drawString(40, y, "Accumulator Breakdown")
    y -= 8
    c.setStrokeColor(GOLD)
    c.line(40, y, width - 40, y)
    y -= 25

    # -----------------------------
    # ACCA LOOP
    # -----------------------------
    for acca in accas:

        picks = acca.picks_json or []
        rows = (len(picks) + 1) // 2
        parent_h = 120 + rows * (MINI_H + 10)

        # Page break
        if y - parent_h < 80:
            y = new_page("ACCA Report")
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Accumulator Breakdown (cont.)")
            y -= 8
            c.setStrokeColor(GOLD)
            c.line(40, y, width - 40, y)
            y -= 25

        parent_y = y - parent_h

        # Parent tile
        c.setFillColor(CREAM)
        c.setStrokeColor(GOLD)
        c.roundRect(PARENT_X, parent_y, PARENT_W, parent_h, 10, stroke=1, fill=1)

        # Header bar
        c.setFillColor(RACING_GREEN)
        c.roundRect(PARENT_X, parent_y + parent_h - 30, PARENT_W, 30, 10, stroke=0, fill=1)

        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 12)
        created = acca.created_at.strftime("%Y-%m-%d") if acca.created_at else "-"
        header_text = f"ACCA #{acca.id} — {created} — {acca.status.upper()}"
        c.drawString(PARENT_X + 12, parent_y + parent_h - 20, header_text)

        # Parent body
        ty = parent_y + parent_h - 50
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(PARENT_X + 12, ty, f"Combined Odds: {acca.combined_decimal_odds:g}")
        ty -= 16
        c.drawString(PARENT_X + 12, ty, f"Stake: £{(acca.stake or 0):g}")
        ty -= 16
        c.drawString(PARENT_X + 12, ty, f"Return: £{(acca.total_return or 0):g}")
        ty -= 25

        # -----------------------------
        # MINI-TILES (2 per row)
        # -----------------------------
        for i, pick in enumerate(picks):
            col = i % 2
            row = i // 2

            mx = PARENT_X + 12 + col * (MINI_W + 12)
            my = ty - row * (MINI_H + 10)

            # Safe fields
            player = pick.get("player", "Unknown")
            course = pick.get("course", "Unknown")
            race_time = pick.get("race_time", "-")
            hn = pick.get("horse_name", "Unknown")
            num = pick.get("horse_number", "-")
            odds = pick.get("odds_fraction", "-")
            result = pick.get("result", "Pending")

            # Colour coding
            if result == "Win":
                bg = PALE_GREEN
                rc = colors.green
            elif result == "Lose":
                bg = PALE_RED
                rc = colors.HexColor("#B00020")
            elif result == "Place":
                bg = PALE_BLUE
                rc = colors.HexColor("#0047AB")
            elif result == "NR":
                bg = PALE_GREY
                rc = colors.grey
            else:
                bg = colors.white
                rc = colors.black

            # Mini tile
            c.setFillColor(bg)
            c.setStrokeColor(GOLD)
            c.roundRect(mx, my, MINI_W, MINI_H, MINI_RADIUS, stroke=1, fill=1)

            # Text
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(colors.black)
            c.drawString(mx + 6, my + MINI_H - 16, f"{player} — {course} — {race_time}")

            c.setFont("Helvetica", 10)
            c.drawString(mx + 6, my + MINI_H - 32, f"Horse: {hn} (#{num})")
            c.drawString(mx + 6, my + MINI_H - 46, f"Odds: {odds}")

            c.setFillColor(rc)
            c.drawString(mx + 6, my + MINI_H - 60, f"Result: {result}")

        y = parent_y - 40

    page_number(page)
    c.save()
    stream.seek(0)

    return Response(
        content=stream.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=acca_report.pdf"}
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
