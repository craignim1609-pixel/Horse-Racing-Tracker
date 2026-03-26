from pydantic import BaseModel
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


class PickCreate(PickBase):
    pass

class PickOut(PickBase):
    id: int
    status: str

    class Config:
        orm_mode = True

class PickUpdateStatus(BaseModel):
    status: str  # Win / Place / Lose / NR


# -------------------------
# RACEDAY MODELS (CLEAN + MATCHING FRONTEND)
# -------------------------

class RaceDayBase(BaseModel):
    player_id: int
    course: str
    horse_number: int
    horse_name: str
    race_time: str
    odds_fraction: str
    amount_bet: float

    # Optional because DB sets defaults
    result: Optional[str] = None
    winnings: Optional[float] = None


class RaceDayCreate(BaseModel):
    player_id: int
    course: str
    horse_number: int
    horse_name: str
    race_time: str
    odds_fraction: str
    amount_bet: float


class RaceDayOut(RaceDayBase):
    id: int

    class Config:
        orm_mode = True


class RaceDayResultUpdate(BaseModel):
    result: str  # Win / Place / Lose / NR


# -------------------------
# ACCUMULATOR
# -------------------------

class AccumulatorOut(BaseModel):
    picks: List[PickOut]
    combined_decimal_odds: Optional[float]
    status: str
    ew_250_potential_return: Optional[float]
