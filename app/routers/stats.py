from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/month/{month}")
def month_stats(month: int, year: int, db: Session = Depends(get_db)):
    players = db.query(models.Player).all()
    out = []

    for p in players:
        picks = (
            db.query(models.Pick)
            .filter(
                models.Pick.player_id == p.id,
                models.Pick.month == month,
                models.Pick.year == year,
            )
            .all()
        )
        wins = sum(1 for x in picks if x.status == "Win")
        places = sum(1 for x in picks if x.status == "Place")
        losses = sum(1 for x in picks if x.status == "Lose")
        nr = sum(1 for x in picks if x.status == "NR")
        total = len(picks)
        win_rate = (wins / total * 100) if total > 0 else 0

        out.append(
            {
                "player": p.name,
                "wins": wins,
                "places": places,
                "losses": losses,
                "nr": nr,
                "total": total,
                "win_rate": win_rate,
            }
        )

    return out
