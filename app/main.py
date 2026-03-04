from fastapi import FastAPI
from app.routers import picks, accumulator, stats, raceday, export

app = FastAPI()

app.include_router(picks.router)
app.include_router(accumulator.router)
app.include_router(stats.router)
app.include_router(raceday.router)
app.include_router(export.router)

@app.get("/")
def home():
    return {"message": "Horse Racing Tracker API running"}
