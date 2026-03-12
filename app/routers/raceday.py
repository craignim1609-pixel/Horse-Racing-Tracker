from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.utils import odds as odds_utils

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
# GROUP STATS
# ------------------------------------------------------------
@router.get("/stats")
def race_day_stats(db: Session = Depends(get_db)):
    players = db.query(models.Player).all()
    result = []

    for p in players:
        bets = db.query(models.RaceDay).filter(models.RaceDay.player_id == p.id).all()

        total_stake = sum(float(b.amount_bet) for
