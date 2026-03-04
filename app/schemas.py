from pydantic import BaseModel

class PickCreate(BaseModel):
    player_id: int
    course: str
    horse_name: str
    horse_number: int
    odds_fraction: str
    race_time: str
    month: int
    year: int

class PickUpdate(BaseModel):
    status: str

class RaceDayCreate(BaseModel):
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
