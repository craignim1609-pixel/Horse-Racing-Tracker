from sqlalchemy.orm import Session
from datetime import date, datetime
from app import models


# ---------------------------------------------------------
# PLAYER STATS
# ---------------------------------------------------------
def update_player_stats(db: Session, player_id: int):
    picks = (
        db.query(models.Pick)
        .filter(models.Pick.player_id == player_id)
        .all()
    )

    total = len(picks)
    wins = len([p for p in picks if p.status == "Win"])
    places = len([p for p in picks if p.status == "Place"])
    losses = len([p for p in picks if p.status == "Lose"])
    nrs = len([p for p in picks if p.status == "NR"])

    return {
        "total": total,
        "wins": wins,
        "places": places,
        "losses": losses,
        "nr": nrs,
        "win_rate": (wins / total) * 100 if total else 0,
    }


# ---------------------------------------------------------
# GROUP STANDINGS (for Performance Center)
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

        wins = len([p for p in picks if p.status == "Win"])
        places = len([p for p in picks if p.status == "Place"])
        losses = len([p for p in picks if p.status == "Lose"])

        standings.append({
            "player": player.name,
            "wins": wins,
            "places": places,
            "losses": losses,
            "score": wins * 3 + places * 1
        })

    standings.sort(key=lambda x: x["score"], reverse=True)
    return standings


# ---------------------------------------------------------
# MONTHLY STATS
# ---------------------------------------------------------
def update_monthly_stats(db: Session, pick: models.Pick):
    today = date.today()
    start_of_month = today.replace(day=1)

    picks = (
        db.query(models.Pick)
        .filter(models.Pick.created_at >= start_of_month)
        .all()
    )

    wins = len([p for p in picks if p.status == "Win"])
    places = len([p for p in picks if p.status == "Place"])
    losses = len([p for p in picks if p.status == "Lose"])

    return {
        "month": today.strftime("%B %Y"),
        "wins": wins,
        "places": places,
        "losses": losses,
        "total": len(picks),
    }


# ---------------------------------------------------------
# MASTER FUNCTION
# ---------------------------------------------------------
def update_all_stats(db: Session, pick: models.Pick):
    return {
        "player_stats": update_player_stats(db, pick.player_id),
        "group_stats": update_group_standings(db),
        "monthly_stats": update_monthly_stats(db, pick),
    }
