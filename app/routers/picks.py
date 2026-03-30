from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/picks", tags=["Picks"])


# ---------------------------------------------------------
# GET ALL PICKS
# (Used by Current Picks page + Acca page)
# ---------------------------------------------------------
@router.get("/", response_model=List[schemas.PickOut])
def get_all_picks(db: Session = Depends(get_db)):
    picks = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .order_by(models.Pick.id.desc())
        .all()
    )
    return picks


# ---------------------------------------------------------
# CREATE PICK
# (Used by Add Pick page)
# ---------------------------------------------------------
@router.post("/", response_model=schemas.PickOut)
def create_pick(data: schemas.PickCreate, db: Session = Depends(get_db)):
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
        status="pending",
        is_acca=False,
    )

    db.add(pick)
    db.commit()
    db.refresh(pick)

    # reload with relationship
    pick = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.id == pick.id)
        .first()
    )

    return pick


# ---------------------------------------------------------
# UPDATE PICK STATUS
# (Used by Acca + Current Picks pages)
# ---------------------------------------------------------
@router.post("/{pick_id}/status", response_model=schemas.PickOut)
def update_pick_status(
    pick_id: int,
    data: schemas.PickUpdateStatus,
    db: Session = Depends(get_db),
):
    pick = db.query(models.Pick).filter(models.Pick.id == pick_id).first()
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")

    pick.status = data.status.lower()
    db.commit()
    db.refresh(pick)

    pick = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.id == pick_id)
        .first()
    )

    return pick


# ---------------------------------------------------------
# DELETE PICK
# (Used by Acca + Current Picks pages)
# ---------------------------------------------------------
@router.delete("/{pick_id}")
def delete_pick(pick_id: int, db: Session = Depends(get_db)):
    pick = db.query(models.Pick).filter(models.Pick.id == pick_id).first()
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")

    db.delete(pick)
    db.commit()

    return {"message": "Pick deleted"}
