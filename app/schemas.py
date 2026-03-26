from pydantic import BaseModel
from typing import Optional, List


# -----------------------------
# PLAYER
# -----------------------------
class PlayerBase(BaseModel):
    name: str


class PlayerOut(PlayerBase):
    id: int

    class Config:
        orm_mode = True


# -----------------------------
# PICK (Accumulator + Current Picks)
# -----------------------------
class PickBase(BaseModel):
    course: str
    horse_name: str
    horse_number: Optional[int]
    odds_fraction: str
    race_time: str


class PickCreate(PickBase):
    player_id: int


class PickUpdateStatus(BaseModel):
    status: str


class PickOut(PickBase):
    id: int
    status: str
    player: PlayerOut

    class Config:
        orm_mode = True


# -----------------------------
# ACCUMULATOR OUTPUT
# -----------------------------
class AccaPickOut(BaseModel):
    id: int
    status: str
    horse_name: str
    horse_number: Optional[int]
    odds_fraction: str
    course: str
    race_time: str
    player: PlayerOut

    class Config:
        orm_mode = True


class AccumulatorOut(BaseModel):
    picks: List[AccaPickOut]
    combined_decimal_odds: Optional[float]
    ew_250_potential_return: Optional[float]
    status: str

    class Config:
        orm_mode = True


# -----------------------------
# RACE DAY BETS
# -----------------------------
class RaceDayBase(BaseModel):
    player_id: int
    course: str
    horse_name: str
    horse_number: Optional[int]
    odds_fraction: str
    race_time: str
    amount_bet: float


class RaceDayOut(RaceDayBase):
    id: int
    result: str
    player: PlayerOut

    class Config:
        orm_mode = True


# -----------------------------
# RACE DAY STATS
# -----------------------------
class RaceDayPlayerStats(BaseModel):
    player: str
    total_stake: float
    total_return: float
    profit: float


class RaceDayGroupStats(BaseModel):
    total_stake: float
    total_return: float
    profit: float


class RaceDayStatsOut(BaseModel):
    group: RaceDayGroupStats
    players: List[RaceDayPlayerStats]


# -----------------------------
# MONTHLY STATS
# -----------------------------
class MonthlyStats(BaseModel):
    player: str
    wins: int
    places: int
    loses: int
    nr: int


# -----------------------------
# PLAYER PROFILE
# -----------------------------
class PlayerProfileOut(BaseModel):
    player: str
    wins: int
    places: int
    loses: int
    nr: int
    win_rate: float
    profit: float
    recent_form: List[str]
    biggest_winner: Optional[PickOut]

    class Config:
        orm_mode = True
