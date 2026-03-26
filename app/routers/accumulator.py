from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, date
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/accumulator", tags=["Accumulator"])


# -----------------------------
# Helper: Convert fractional odds to decimal
# -----------------------------
def fractional_to_decimal(frac: str) -> float:
    if not frac:
        return 1.0

    if "/" not in frac:
        try:
            return float(frac)
        except:
            return 1.0

    a, b = frac.split("/")
    try:
        return (float(a) / float(b)) + 1
    except:
        return 1.0


# -----------------------------
# Helper: Calculate place odds (1/4 rule)
# -----------------------------
def place_decimal(decimal_odds: float) -> float:
    return ((decimal_odds - 1) / 4) + 1


# -----------------------------
# GET ACCUMULATOR STATUS + ODDS
# -----------------------------
@router.get("/", response_model=schemas.AccumulatorOut)
def get_accumulator(db: Session = Depends(get_db)):

    # -----------------------------
    # Load ONLY today's picks
    # -----------------------------
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())

    picks = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.created_at >= start_of_day)
        .all()
    )

    # -----------------------------
    # EMPTY STATE
    # -----------------------------
    if not picks:
        return schemas.AccumulatorOut(
            picks=[],
            combined_decimal_odds=None,
            ew_250_potential_return=None,
            status="empty",
        )

    # -----------------------------
    # CALCULATE COMBINED ODDS
    # -----------------------------
    combined = 1.0
    for p in picks:
        combined *= fractional_to_decimal(p.odds_fraction)

    # -----------------------------
    # CALCULATE EW RETURNS (£2.50 win + £2.50 place)
    # -----------------------------
    win_return = 2.5 * combined
    place_return = 2.5 * place_decimal(combined)
    ew_total = win_return + place_return

    # -----------------------------
    # DETERMINE ACCA STATUS
    # -----------------------------
    statuses = [p.status for p in picks]

    if "Lose" in statuses:
        acca_status = "busted"
    elif all(s in ["Win", "Place", "NR"] for s in statuses):
        acca_status = "won"
    elif any(s == "Pending" for s in statuses):
        acca_status = "live"
    else:
        acca_status = "live"

    return schemas.AccumulatorOut(
        picks=picks,
        combined_decimal_odds=combined,
        ew_250_potential_return=ew_total,
        status=acca_status,
    )


# -----------------------------
# DELETE PICK
# -----------------------------
@router.delete("/{pick_id}")
def delete_acca_pick(pick_id: int, db: Session = Depends(get_db)):
    pick = db.query(models.Pick).filter(models.Pick.id == pick_id).first()
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")

    db.delete(pick)
    db.commit()

    return {"message": "Pick deleted"}
