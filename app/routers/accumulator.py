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
    # Load all pending picks with player relationship
    picks = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.status == "Pending")
        .all()
    )

    # Must have 5 unique players
    unique_players = {p.player_id for p in picks}
    if len(unique_players) < 5:
        return schemas.AccumulatorOut(
            picks=picks,
            combined_decimal_odds=None,
            ew_250_potential_return=None,
            status="incomplete",
        )

    # Calculate combined decimal odds
    combined = 1.0
    for p in picks:
        combined *= fractional_to_decimal(p.odds_fraction)

    # Calculate EW returns (£2.50 win + £2.50 place)
    win_return = 2.5 * combined
    place_return = 2.5 * place_decimal(combined)
    ew_total = win_return + place_return

    return schemas.AccumulatorOut(
        picks=picks,
        combined_decimal_odds=combined,
        ew_250_potential_return=ew_total,
        status="live",
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
    standings = (
        db.query(
            models.Player.name.label("player"),
            models.Pick.status.label("status")
        )
        .join(models.Player, models.Player.id == models.Pick.player_id)
        .filter(models.Pick.status.in_(["Pending", "Win", "Place", "Lose", "NR"]))
        .all()
    )

    return standings

