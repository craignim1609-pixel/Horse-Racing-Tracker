from sqlalchemy.orm import Session
from datetime import date
from app import models


# ---------------------------------------------------------
# PLAYER STATS (used by modal + stats page)
# ---------------------------------------------------------
def update_player_stats(db: Session, player_id: int):
    picks = (
        db.query(models.Pick)
        .filter(models.Pick.player_id == player_id)
        .all()
    )

    total = len(picks)

    wins = len([p for p in picks if p.status == "win"])
    places = len([p for p in picks if p.status == "place"])
    losses = len([p for p in picks if p.status == "lose"])
    nrs = len([p for p in picks if p.status == "nr"])

    return {
        "total": total,
        "wins": wins,
        "places": places,
        "loses": losses,
        "nr": nrs,
        "win_rate": round((wins / total) * 100, 1) if total else 0,
    }


# ---------------------------------------------------------
# GROUP STANDINGS (used by stats page)
# ---------------------------------------------------------
def update_group_standings(db: Session):
    players = db.query(models.Player).all()
    standings = []

    for player in players:
        picks = (
            db.query(models.Pick)
            .filter(models.Pick.player_id == player.id)
            .all()
        )

        wins = len([p for p in picks if p.status == "win"])
        places = len([p for p in picks if p.status == "place"])
        losses = len([p for p in picks if p.status == "lose"])

        standings.append({
            "player": player.name,
            "wins": wins,
            "places": places,
            "loses": losses,
            "score": wins * 3 + places * 1,  # simple scoring system
        })

    standings.sort(key=lambda x: x["score"], reverse=True)
    return standings


# ---------------------------------------------------------
# MONTHLY STATS (used by export + dashboard)
# ---------------------------------------------------------
def update_monthly_stats(db: Session):
    today = date.today()
    start_of_month = today.replace(day=1)

    picks = (
        db.query(models.Pick)
        .filter(models.Pick.created_at >= start_of_month)
        .all()
    )

    wins = len([p for p in picks if p.status == "win"])
    places = len([p for p in picks if p.status == "place"])
    losses = len([p for p in picks if p.status == "lose"])

    return {
        "month": today.strftime("%B %Y"),
        "wins": wins,
        "places": places,
        "loses": losses,
        "total": len(picks),
    }


# ---------------------------------------------------------
# MASTER FUNCTION (optional)
# ---------------------------------------------------------
def update_all_stats(db: Session, player_id: int):
    return {
        "player_stats": update_player_stats(db, player_id),
        "group_stats": update_group_standings(db),
        "monthly_stats": update_monthly_stats(db),
    }
