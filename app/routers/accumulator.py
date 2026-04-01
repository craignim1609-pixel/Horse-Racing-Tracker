from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/accumulator", tags=["Accumulator"])


# ------------------------------------------------------------
# Helper: Convert fractional odds to decimal
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# Helper: Place odds (¼ rule)
# ------------------------------------------------------------
def place_decimal(decimal_odds: float) -> float:
    return ((decimal_odds - 1) / 4) + 1


# ------------------------------------------------------------
# GET ACCUMULATOR STATUS + ODDS (READ‑ONLY)
# ------------------------------------------------------------
@router.get("/", response_model=schemas.AccumulatorOut)
def get_accumulator(db: Session = Depends(get_db)):
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
            win_acca_odds=None,
            place_acca_odds=None,
            status="no picks",
        )

    active = [p for p in picks if p.status != "NR"]

    if not active:
        return schemas.AccumulatorOut(
            picks=picks,
            combined_decimal_odds=None,
            ew_250_potential_return=None,
            win_acca_odds=None,
            place_acca_odds=None,
            status="all non runners",
        )

    # --------------------------------------------------------
    # REAL EACH-WAY ACCA LOGIC
    # --------------------------------------------------------
    win_acca = 1.0
    place_acca = 1.0

    for p in active:
        dec = fractional_to_decimal(p.odds_fraction)
        place_dec = place_decimal(dec)

        if p.status == "Win":
            win_acca *= dec
            place_acca *= place_dec

        elif p.status == "Place":
            win_acca = 0
            place_acca *= place_dec

        elif p.status == "Lose":
            win_acca = 0
            place_acca = 0
            break

        elif p.status == "Pending":
            win_acca *= dec
            place_acca *= place_dec

    # --------------------------------------------------------
    # DETERMINE ACCA STATUS
    # --------------------------------------------------------
    if win_acca == 0 and place_acca == 0:
        status = "lose"
    elif all(p.status == "Win" for p in active):
        status = "win"
    elif any(p.status == "Place" for p in active):
        status = "place"
    else:
        status = "live"

    # --------------------------------------------------------
    # £2.50 E/W stake = £2.50 win + £2.50 place
    # --------------------------------------------------------
    win_return = 2.5 * win_acca
    place_return = 2.5 * place_acca
    ew_total = win_return + place_return

    # --------------------------------------------------------
    # IMPORTANT: NO AUTO‑ARCHIVING HERE ANYMORE
    # --------------------------------------------------------

    return schemas.AccumulatorOut(
        picks=picks,
        combined_decimal_odds=win_acca,
        ew_250_potential_return=ew_total,
        win_acca_odds=win_acca,
        place_acca_odds=place_acca,
        status=status,
    )


# ------------------------------------------------------------
# UPDATE PICK STATUS
# ------------------------------------------------------------
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

    pick = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.id == pick_id)
        .first()
    )

    return pick


# ------------------------------------------------------------
# DELETE PICK
# ------------------------------------------------------------
@router.delete("/{pick_id}")
def delete_acca_pick(pick_id: int, db: Session = Depends(get_db)):
    pick = db.query(models.Pick).filter(models.Pick.id == pick_id).first()
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")

    db.delete(pick)
    db.commit()

    return {"message": "Pick deleted"}


# ------------------------------------------------------------
# GROUP STANDINGS
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# ACCA HISTORY
# ------------------------------------------------------------
@router.get("/history", response_model=List[schemas.AccaHistoryOut])
def get_acca_history(db: Session = Depends(get_db)):
    history = (
        db.query(models.AccaHistory)
        .order_by(models.AccaHistory.id.desc())
        .limit(50)
        .all()
    )
    return history


# ------------------------------------------------------------
# RESET ACCA (TEMPORARY UNTIL STEP 2)
# ------------------------------------------------------------
@router.delete("/reset")
def reset_acca(db: Session = Depends(get_db)):
    db.query(models.Pick).delete()
    db.commit()
    return {"message": "Acca reset"}
