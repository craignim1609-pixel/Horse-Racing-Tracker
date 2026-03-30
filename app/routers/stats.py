from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app import models

router = APIRouter(prefix="/stats", tags=["Stats"])


# ---------------------------------------------------------
# INTERNAL: BUILD PLAYER STATS DICTIONARY
# ---------------------------------------------------------
def build_stats(db: Session):
    stats = {}

    picks = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .all()
    )

    for p in picks:
        name = p.player.name

        if name not in stats:
            stats[name] = {
                "name": name,
                "wins": 0,
                "places": 0,
                "loses": 0,
                "nr": 0,
                "total": 0,
                "courses": {},
                "profit": 0,   # placeholder for future logic
            }

        s = stats[name]
        s["total"] += 1

        # status counts
        status = p.status.lower()
        if status == "win":
            s["wins"] += 1
        elif status == "place":
            s["places"] += 1
        elif status == "lose":
            s["loses"] += 1
        elif status == "nr":
            s["nr"] += 1

        # course breakdown
        course = p.course
        if course not in s["courses"]:
            s["courses"][course] = {"runs": 0, "wins": 0, "places": 0}

        s["courses"][course]["runs"] += 1
        if status == "win":
            s["courses"][course]["wins"] += 1
        if status == "place":
            s["courses"][course]["places"] += 1

    return stats


# ---------------------------------------------------------
# GET ALL PLAYER STATS (for stats cards)
# Matches JS: GET /api/stats
# ---------------------------------------------------------
@router.get("/")
def get_all_stats(db: Session = Depends(get_db)):
    stats = build_stats(db)

    # Convert to list for JSON
    return [
        {
            "name": s["name"],
            "wins": s["wins"],
            "places": s["places"],
            "loses": s["loses"],
            "nr": s["nr"],
            "total": s["total"],
        }
        for s in stats.values()
    ]


# ---------------------------------------------------------
# GET SINGLE PLAYER STATS (for modal)
# Matches JS: GET /api/stats/{name}
# ---------------------------------------------------------
@router.get("/{player_name}")
def get_player_stats(player_name: str, db: Session = Depends(get_db)):
    stats = build_stats(db)

    if player_name not in stats:
        raise HTTPException(status_code=404, detail="Player not found")

    s = stats[player_name]

    # Win rate
    win_rate = (s["wins"] / s["total"] * 100) if s["total"] else 0

    # Convert course dict → list
    course_list = [
        {
            "course": c,
            "runs": d["runs"],
            "wins": d["wins"],
            "places": d["places"],
        }
        for c, d in s["courses"].items()
    ]

    # Profit breakdown placeholder (can be expanded later)
    profit_chart = [
        {"label": "Wins", "value": s["wins"] * 5},     # example placeholder
        {"label": "Places", "value": s["places"] * 2}, # example placeholder
        {"label": "Loses", "value": -s["loses"] * 5},  # example placeholder
    ]

    return {
        "name": s["name"],
        "wins": s["wins"],
        "places": s["places"],
        "loses": s["loses"],
        "nr": s["nr"],
        "total": s["total"],
        "win_rate": round(win_rate, 1),
        "courses": course_list,
        "profit": profit_chart,
    }
