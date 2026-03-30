from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/players", tags=["Players"])


# ---------------------------------------------------------
# GET ALL PLAYER NAMES
# Matches JS: GET /api/players
# ---------------------------------------------------------
@router.get("/")
def get_players(db: Session = Depends(get_db)):
    players = db.query(models.Player).order_by(models.Player.name.asc()).all()
    return [p.name for p in players]
