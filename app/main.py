from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.routers import picks, accumulator, stats, raceday, export

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(picks.router)
app.include_router(accumulator.router)
app.include_router(stats.router)
app.include_router(raceday.router)
app.include_router(export.router)

@app.get("/")
def home():
    return {"message": "Horse Racing Tracker API running"}
