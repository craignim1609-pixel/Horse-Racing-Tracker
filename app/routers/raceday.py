from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/raceday", tags=["Race Day"])

# ------------------------------------------------------------
# CREATE RACE DAY BET
# ------------------------------------------------------------
@router.post("/", response_model=schemas.RaceDayOut)
def add_race_day_bet(data: schemas.RaceDayCreate, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.id == data.player_id).first()
    if not player:
        raise HTTPException(status_code=400, detail="Player not found")

    bet = models.RaceDay(**data.dict())
    db.add(bet)
    db.commit()
    db.refresh(bet)
    return bet


# ------------------------------------------------------------
# LIST ALL RACE DAY BETS
# ------------------------------------------------------------
@router.get("/", response_model=List[schemas.RaceDayOut])
def list_race_day_bets(db: Session = Depends(get_db)):
    return db.query(models.RaceDay).all()


# ------------------------------------------------------------
# RECENT ACTIVITY (Frontend expects this)
# ------------------------------------------------------------
@router.get("/recent")
def get_recent_activity(db: Session = Depends(get_db)):
    recent = (
        db.query(models.RaceDay)
        .order_by(models.RaceDay.id.desc())
        .limit(10)
        .all()
    )
    return recent


# ------------------------------------------------------------
# GROUP + PLAYER STATS (Frontend expects this shape)
# ------------------------------------------------------------
@router.get("/stats")
def race_day_stats(db: Session = Depends(get_db)):
    players = db.query(models.Player).all()
    result = []

    for p in players:
        bets = db.query(models.RaceDay).filter(models.RaceDay.player_id == p.id).all()

        total_stake = sum(float(b.amount_bet) for b in bets)
        total_return = sum(float(b.winnings) for b in bets)
        profit = total_return - total_stake

        result.append({
            "player": p.name,
            "total_stake": total_stake,
            "total_return": total_return,
            "profit": profit,
        })

    group_stake = sum(r["total_stake"] for r in result)
    group_return = sum(r["total_return"] for r in result)
    group_profit = group_return - group_stake

    return {
        "players": result,
        "group": {
            "total_stake": group_stake,
            "total_return": group_return,
            "profit": group_profit,
        }
    }
