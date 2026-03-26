from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date, datetime
from app.database import get_db
from app import models

router = APIRouter(prefix="/stats", tags=["Stats"])


# ---------------------------------------------------------
# OVERVIEW: Performance Center
# ---------------------------------------------------------
@router.get("/overview")
def get_stats_overview(db: Session = Depends(get_db)):
    today = date.today()
    start_of_month = today.replace(day=1)

    players = db.query(models.Player).all()
    results = []

    for player in players:
        picks = (
            db.query(models.Pick)
            .filter(models.Pick.player_id == player.id)
            .all()
        )

        month_picks = (
            db.query(models.Pick)
            .filter(models.Pick.player_id == player.id)
            .filter(models.Pick.created_at >= start_of_month)
            .all()
        )

        results.append({
            "player_id": player.id,
            "player_name": player.name,
            "month_wins": len([p for p in month_picks if p.status == "Win"]),
            "wins": len([p for p in picks if p.status == "Win"]),
            "places": len([p for p in picks if p.status == "Place"]),
            "losses": len([p for p in picks if p.status == "Lose"]),
            "nr": len([p for p in picks if p.status == "NR"]),
        })

    return results


# ---------------------------------------------------------
# PLAYER DETAIL VIEW
# ---------------------------------------------------------
@router.get("/player/{player_id}")
def get_player_detail(player_id: int, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if not player:
        return {"error": "Player not found"}

    picks = (
        db.query(models.Pick)
        .filter(models.Pick.player_id == player_id)
        .all()
    )

    # Group by racetrack
    track_map = {}
    for p in picks:
        if p.course not in track_map:
            track_map[p.course] = {
                "track": p.course,
                "bets": 0,
                "horses": []
            }
        track_map[p.course]["bets"] += 1
        track_map[p.course]["horses"].append(p.horse_name)

    return {
        "player_id": player.id,
        "player_name": player.name,
        "wins": len([p for p in picks if p.status == "Win"]),
        "places": len([p for p in picks if p.status == "Place"]),
        "losses": len([p for p in picks if p.status == "Lose"]),
        "nr": len([p for p in picks if p.status == "NR"]),
        "tracks": list(track_map.values())
    }
