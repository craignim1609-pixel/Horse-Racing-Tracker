from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.utils import odds as odds_utils
from datetime import datetime


router = APIRouter(prefix="/raceday", tags=["Race Day"])

@router.post("/", response_model=schemas.RaceDayOut)
def add_race_day_bet(data: schemas.RaceDayCreate, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.id == data.player_id).first()
    if not player:
        raise HTTPException(status_code=400, detail="Player not found")

    now = datetime.now()
    data.month = data.month or now.month
    data.year = data.year or now.year

    bet = models.RaceDay(**data.dict())
    db.add(bet)
    db.commit()
    db.refresh(bet)
    return bet
  
@router.get("/", response_model=List[schemas.RaceDayOut])
def list_race_day_bets(month: int, year: int, db: Session = Depends(get_db)):
    bets = (
        db.query(models.RaceDay)
        .filter(models.RaceDay.month == month, models.RaceDay.year == year)
        .all()
    )
    return bets


@router.get("/stats")
def race_day_stats(db: Session = Depends(get_db)):
    players = db.query(models.Player).all()
    result = []

    for p in players:
        bets = db.query(models.RaceDay).filter(models.RaceDay.player_id == p.id).all()
        total_stake = sum(float(b.amount_bet) for b in bets)
        total_return = 0.0
        for b in bets:
            dec = odds_utils.fractional_to_decimal(b.odds_fraction)
            if b.result == "Win":
                total_return += float(b.amount_bet) * dec
            elif b.result == "Place":
                place_dec = odds_utils.place_decimal(b.odds_fraction)
                total_return += float(b.amount_bet) * place_dec

        profit = total_return - total_stake
        result.append(
            {
                "player": p.name,
                "total_stake": total_stake,
                "total_return": total_return,
                "profit": profit,
            }
        )

    group_stake = sum(r["total_stake"] for r in result)
    group_return = sum(r["total_return"] for r in result)
    group_profit = group_return - group_stake

    return {"players": result, "group": {
        "total_stake": group_stake,
        "total_return": group_return,
        "profit": group_profit,
    }}
@router.get("/seed-players")
def seed_players(db: Session = Depends(get_db)):
    players = ["Donald", "Miller", "Nick", "Josh", "Craig"]
    inserted = []

    for name in players:
        exists = db.query(models.Player).filter(models.Player.name == name).first()
        if not exists:
            db.add(models.Player(name=name))
            inserted.append(name)

    db.commit()
    return {"inserted": inserted}

@router.get("/recent")
def recent_activity(db: Session = Depends(get_db)):
    return (
        db.query(models.RaceDay)
        .order_by(models.RaceDay.id.desc())
        .limit(10)
        .all()
    )
    
   @router.patch("/{id}/result")
def update_race_day_result(id: int, status: str, db: Session = Depends(get_db)):
    bet = db.query(models.RaceDay).filter(models.RaceDay.id == id).first()

    if not bet:
        raise HTTPException(status_code=404, detail="Race Day bet not found")

    bet.result = status

    dec = odds_utils.fractional_to_decimal(bet.odds_fraction)

    if status == "WIN":
        bet.winnings = float(bet.amount_bet) * dec
    elif status == "PLACE":
        bet.winnings = float(bet.amount_bet) * odds_utils.place_decimal(bet.odds_fraction)
    else:
        bet.winnings = 0.0

    db.commit()
    db.refresh(bet)
    return bet


