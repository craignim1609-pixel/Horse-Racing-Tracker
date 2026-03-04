from fastapi import APIRouter

router = APIRouter(prefix="/raceday", tags=["Race Day"])

@router.post("/")
def add_race_day():
    return {"message": "Race day add"}
