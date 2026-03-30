from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("/month/{month}")
def monthly_stats(month: int, year: int, db: Session = Depends(get_db)):
    players = db.query(models.Player).all()
    results = []

    for p in players:
        wins = db.query(models.Pick).filter_by(player_id=p.id, month=month, year=year, result="Win").count()
        places = db.query(models.Pick).filter_by(player_id=p.id, month=month, year=year, result="Place").count()
        loses = db.query(models.Pick).filter_by(player_id=p.id, month=month, year=year, result="Lose").count()
        nr = db.query(models.Pick).filter_by(player_id=p.id, month=month, year=year, result="NR").count()

        results.append({
            "player": p.name,
            "wins": wins,
            "places": places,
            "loses": loses,
            "nr": nr
        })

    return results


@router.get("/player/{name}")
def player_details(name: str, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter_by(name=name).first()
    if not player:
        return {"error": "Player not found"}

    picks = db.query(models.Pick).filter_by(player_id=player.id).all()

    wins = sum(1 for p in picks if p.result == "Win")
    places = sum(1 for p in picks if p.result == "Place")
    loses = sum(1 for p in picks if p.result == "Lose")
    nr = sum(1 for p in picks if p.result == "NR")

    total = wins + places + loses
    win_rate = wins / total if total > 0 else 0

    # biggest winner
    biggest = None
    for p in picks:
        if p.result == "Win":
            if biggest is None or p.decimal_odds > biggest.decimal_odds:
                biggest = p

    # recent form (last 5 picks)
    recent = [p.result[0].upper() for p in picks[-5:]]

    return {
        "player": player.name,
        "wins": wins,
        "places": places,
        "loses": loses,
        "nr": nr,
        "win_rate": win_rate,
        "biggest_winner": {
            "horse_name": biggest.horse_name,
            "odds_fraction": biggest.odds_fraction
        } if biggest else None,
        "recent_form": recent
    }

