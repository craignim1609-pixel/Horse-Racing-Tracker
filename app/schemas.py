from pydantic import BaseModel
from typing import Optional, List

# -------------------------
# RACEDAY MODELS (CLEANED)
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
    winnings: float


class RaceDayCreate(BaseModel):
    player_id: int
    course: str
    horse_number: int
    horse_name: str
    race_time: str
    odds_fraction: str
    amount_bet: float

    result: str = "Pending"


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
