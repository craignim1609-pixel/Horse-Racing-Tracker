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
    amount_bet: float
    odds_fraction: str
    track: str
    time: str
    horse_name: str
    horse_number: int
    result: str
    month: int
    year: int

class RaceDayCreate(RaceDayBase):
    pass

class RaceDayOut(RaceDayBase):
    id: int

    class Config:
        orm_mode = True


class AccumulatorOut(BaseModel):
    picks: List[PickOut]
    combined_decimal_odds: Optional[float]
    status: str
    ew_250_potential_return: Optional[float]
