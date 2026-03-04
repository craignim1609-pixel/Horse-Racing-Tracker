from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/picks", tags=["Picks"])

@router.post("/")
def add_pick(data, db: Session = Depends(get_db)):
    return {"message": "Add pick endpoint"}
