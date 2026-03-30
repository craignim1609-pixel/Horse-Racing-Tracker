from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---------------------------------------------------------
# PLAYER SCHEMAS
# ---------------------------------------------------------
class PlayerBase(BaseModel):
    name: str


class PlayerOut(PlayerBase):
    id: int

    class Config:
        orm_mode = True


# ---------------------------------------------------------
# PICK SCHEMAS
# ---------------------------------------------------------
class PickBase(BaseModel):
    player_id: int
    course: str
    horse_name: str
    horse_number: Optional[int] = None
    odds_fraction: str
    race_time: str


class PickCreate(PickBase):
    pass


class PickUpdateStatus(BaseModel):
    status: str  # "win", "place", "lose", "nr", "pending"


class PickOut(BaseModel):
    id: int
    player: PlayerOut
    course: str
    horse_name: str
    horse_number: Optional[int]
    odds_fraction: str
    race_time: str
    status: str
    is_acca: bool
    created_at: datetime

    class Config:
        orm_mode = True


# ---------------------------------------------------------
# RACE DAY SCHEMAS
# ---------------------------------------------------------
class RaceDayBase(BaseModel):
    player_id: int
    course: str
    horse_name: str
    horse_number: Optional[int] = None
    odds_fraction: str
    race_time: str
    amount_bet: float = 1.0


class RaceDayCreate(RaceDayBase):
    pass


class RaceDayUpdate(BaseModel):
    result: str  # "win", "place", "lose", "nr", "pending"


class RaceDayOut(BaseModel):
    id: int
    player: PlayerOut
    course: str
    horse_name: str
    horse_number: Optional[int]
    odds_fraction: str
    race_time: str
    amount_bet: float
    result: str
    created_at: datetime

    class Config:
        orm_mode = True


# ---------------------------------------------------------
# STATS SCHEMAS
# ---------------------------------------------------------
class PlayerStats(BaseModel):
    name: str
    wins: int
    places: int
    loses: int
    nr: int
    total: int


class PlayerStatsDetail(PlayerStats):
    win_rate: float
    courses: List[dict]
    profit: List[dict]


# ---------------------------------------------------------
# EXPORT SCHEMAS (optional)
# ---------------------------------------------------------
class ExportPick(BaseModel):
    player: str
    course: str
    horse_name: str
    horse_number: Optional[int]
    odds_fraction: str
    race_time: str
    status: str
    month: Optional[int] = None
    year: Optional[int] = None
