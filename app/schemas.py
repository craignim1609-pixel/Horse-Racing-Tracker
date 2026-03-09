from pydantic import BaseModel
from typing import Optional, List

class PickBase(BaseModel):
    player_id: int
    course: str
    horse_name: str
    horse_number: int
    odds_fraction: str
    race_time: str
    month: int
    year: int

@router.post("/", response_model=schemas.RaceDayOut)
def add_race_day_bet(data: schemas.RaceDayCreate, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.id == data.player_id).first()
    if not player:
        raise HTTPException(status_code=400, detail="Player not found")

    now = datetime.now()
    data.month = data.month or now.month
    data.year = data.year or now.year

    bet = models.RaceDay(**data.dict())
    db.add(bet)
    db.commit()
    db.refresh(bet)
    return bet


class PickCreate(PickBase):
    pass

class PickOut(PickBase):
    id: int
    status: str

    class Config:
        orm_mode = True


class PickUpdateStatus(BaseModel):
    status: str  # Win/Place/Lose/NR


class RaceDayBase(BaseModel):
    player_id: int
    course: str
    horse_number: int
    horse_name: str
    race_time: str
    odds_fraction: str
    amount_bet: float
    result: str
    month: int
    year: int


class RaceDayCreate(BaseModel):
    player_id: int
    course: str
    horse_number: int
    horse_name: str
    race_time: str
    odds_fraction: str
    amount_bet: float

    result: str = "Pending"
    month: int | None = None
    year: int | None = None


class RaceDayOut(RaceDayBase):
    id: int

    class Config:
        orm_mode = True



class AccumulatorOut(BaseModel):
    picks: List[PickOut]
    combined_decimal_odds: Optional[float]
    status: str
    ew_250_potential_return: Optional[float]
