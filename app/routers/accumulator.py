from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
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
    # Load all picks regardless of status
    picks = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.status.in_(["Pending", "Win", "Place", "Lose", "NR"]))
        .all()
    )

    if not picks:
        return schemas.AccumulatorOut(
            picks=[],
            combined_decimal_odds=None,
            ew_250_potential_return=None,
            status="no picks",
        )

    # Remove NR horses
    active_picks = [p for p in picks if p.status != "NR"]

    # If all NR → no acca
    if not active_picks:
        return schemas.AccumulatorOut(
            picks=picks,
            combined_decimal_odds=None,
            ew_250_potential_return=None,
            status="all non runners",
        )

    statuses = [p.status for p in active_picks]

    # If any lose → bust
    if "Lose" in statuses:
        return schemas.AccumulatorOut(
            picks=picks,
            combined_decimal_odds=0,
            ew_250_potential_return=0,
            status="lose",
        )

    # Calculate base combined odds
    combined = 1.0
    for p in active_picks:
        combined *= fractional_to_decimal(p.odds_fraction)

    # If any place → reduce odds to 1/3
    if "Place" in statuses:
        combined = combined / 3
        status = "place"
    # If all win
    elif all(s == "Win" for s in statuses):
        status = "win"
    else:
        status = "live"

    # EW return (£2.50 win + £2.50 place)
    win_return = 2.5 * combined
    place_return = 2.5 * place_decimal(combined)
    ew_total = win_return + place_return

    return schemas.AccumulatorOut(
        picks=picks,
        combined_decimal_odds=combined,
        ew_250_potential_return=ew_total,
        status=status,
    )

# -----------------------------
# UPDATE PICK STATUS (Win/Place/Lose/NR)
# -----------------------------
@router.patch("/{pick_id}/status", response_model=schemas.PickOut)
def update_acca_pick_status(
    pick_id: int,
    data: schemas.PickUpdateStatus,
    db: Session = Depends(get_db),
):
    pick = db.query(models.Pick).filter(models.Pick.id == pick_id).first()
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")

    pick.status = data.status
    db.commit()

    # Reload with player relationship
    pick = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.id == pick_id)
        .first()
    )

    return pick


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

# -----------------------------
# GROUP STANDINGS
# -----------------------------
@router.get("/standings")
def get_standings(db: Session = Depends(get_db)):
    picks = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .all()
    )

    standings = [
        {
            "player": p.player.name if p.player else "Unknown",
            "status": p.status
        }
        for p in picks
    ]

    return standings

