from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import get_db
from app import models, schemas
from app.utils import odds as odds_utils

router = APIRouter(prefix="/accumulator", tags=["Accumulator"])


@router.get("/", response_model=schemas.AccumulatorOut)
def get_accumulator(db: Session = Depends(get_db)):
    # Get one active pick per player
    players = db.query(models.Player).all()
    picks: List[models.Pick] = []

    for p in players:
        pick = (
            db.query(models.Pick)
            .options(joinedload(models.Pick.player))   # <-- IMPORTANT
            .filter(models.Pick.player_id == p.id, models.Pick.status == "Pending")
            .order_by(models.Pick.id.desc())
            .first()
        )
        if pick:
            picks.append(pick)

    # If not all 5 players have a pick
    if len(picks) < 5:
        return schemas.AccumulatorOut(
            picks=picks,
            combined_decimal_odds=None,
            status="incomplete",
            ew_250_potential_return=None,
        )

    # Convert fractional odds to decimals
    decimals = [odds_utils.fractional_to_decimal(p.odds_fraction) for p in picks]
    combined = odds_utils.accumulator_decimal(decimals)

    # Determine accumulator status
    statuses = [p.status for p in picks]
    if any(s == "Lose" for s in statuses):
        status = "busted"
    elif all(s == "Win" for s in statuses):
        status = "won"
    else:
        status = "live"

    # E/W return calculation
    ew_return = odds_utils.ew_250_return(combined, combined)

    return schemas.AccumulatorOut(
        picks=picks,
        combined_decimal_odds=combined,
        status=status,
        ew_250_potential_return=ew_return,
    )
