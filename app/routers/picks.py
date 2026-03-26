from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/picks", tags=["Picks"])


# CREATE PICK
@router.post("/", response_model=schemas.PickOut)
def add_pick(data: schemas.PickCreate, db: Session = Depends(get_db)):
    # Validate player exists
    player = db.query(models.Player).filter(models.Player.id == data.player_id).first()
    if not player:
        raise HTTPException(status_code=400, detail="Player not found")

    pick = models.Pick(
        player_id=data.player_id,
        course=data.course,
        horse_name=data.horse_name,
        horse_number=data.horse_number,
        odds_fraction=data.odds_fraction,
        race_time=data.race_time,
        status="Pending"
    )

    db.add(pick)
    db.commit()

    # Reload WITH player relationship
    db.refresh(pick)
    pick = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.id == pick.id)
        .first()
    )

    return pick


# GET CURRENT PENDING PICKS
@router.get("/current", response_model=List[schemas.PickOut])
def get_current_picks(db: Session = Depends(get_db)):
    picks = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.status == "Pending")
        .all()
    )
    return picks


# UPDATE PICK RESULT
@router.patch("/{pick_id}/result", response_model=schemas.PickOut)
def update_pick_result(
    pick_id: int,
    data: schemas.PickUpdateStatus,
    db: Session = Depends(get_db),
):
    pick = db.query(models.Pick).filter(models.Pick.id == pick_id).first()
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")

    pick.status = data.status
    db.commit()

    # Reload WITH player relationship
    pick = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.id == pick_id)
        .first()
    )

    return pick


# CANCEL PICK (NR)
@router.patch("/{pick_id}/cancel", response_model=schemas.PickOut)
def cancel_pick(pick_id: int, db: Session = Depends(get_db)):
    pick = db.query(models.Pick).filter(models.Pick.id == pick_id).first()
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")

    pick.status = "NR"
    db.commit()

    # Reload WITH player relationship
    pick = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.id == pick_id)
        .first()
    )

    return pick
