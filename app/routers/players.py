from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/players", tags=["Players"])


@router.get("/", response_model=List[schemas.PlayerOut])
def get_players(db: Session = Depends(get_db)):
    return db.query(models.Player).order_by(models.Player.name.asc()).all()
