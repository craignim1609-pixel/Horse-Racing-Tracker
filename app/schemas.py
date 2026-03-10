from pydantic import BaseModel, validator
from typing import Optional, List

# -------------------------
# PICK MODELS
# -------------------------

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


# -------------------------
# RACEDAY MODELS
# -------------------------

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
    month: Optional[int] = None
    year: Optional[int] = None

    @validator("month", "year", pre=True)
    def empty_to_none(cls, v):
        if v in ("", None):
            return None
        return int(v)

class RaceDayOut(RaceDayBase):
    id: int

    class Config:
        orm_mode = True


# -------------------------
# ACCUMULATOR
# -------------------------

class AccumulatorOut(BaseModel):
    picks: List[PickOut]
    combined_decimal_odds: Optional[float]
    status: str
    ew_250_potential_return: Optional[float]
