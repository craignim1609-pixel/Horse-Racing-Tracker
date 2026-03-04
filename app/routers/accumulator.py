from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
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
            .filter(models.Pick.player_id == p.id, models.Pick.status == "Pending")
            .order_by(models.Pick.id.desc())
            .first()
        )
        if pick:
            picks.append(pick)

    if len(picks) < 5:
        return schemas.AccumulatorOut(
            picks=picks,
            combined_decimal_odds=None,
            status="incomplete",
            ew_250_potential_return=None,
        )

    decimals = [odds_utils.fractional_to_decimal(p.odds_fraction) for p in picks]
    combined = odds_utils.accumulator_decimal(decimals)

    # Simple status: if any Lose → busted, if all Win → won, else live
    statuses = [p.status for p in picks]
    if any(s == "Lose" for s in statuses):
        status = "busted"
    elif all(s == "Win" for s in statuses):
        status = "won"
    else:
        status = "live"

    # For now, use win odds for e/w; you can refine with place terms later
    ew_return = odds_utils.ew_250_return(combined, combined)

    return schemas.AccumulatorOut(
        picks=picks,
        combined_decimal_odds=combined,
        status=status,
        ew_250_potential_return=ew_return,
    )
