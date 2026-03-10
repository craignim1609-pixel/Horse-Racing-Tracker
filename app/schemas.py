from pydantic import BaseModel
from typing import Optional

class RaceDayCreate(BaseModel):
    player_id: int
    course: str
    horse_number: int
    horse_name: str
    race_time: str
    odds_fraction: str
    amount_bet: float

    result: str = "Pending"
    month: Optional[int] = None
    year: Optional[int] = None

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
