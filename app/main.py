from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.routers import picks, accumulator, stats, raceday, export, players
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse
from app.routers.players import seed_players

app = FastAPI()

# Create tables first
Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def startup_event():
    seed_players()


app.include_router(picks.router)
app.include_router(accumulator.router)
app.include_router(stats.router)
app.include_router(raceday.router)
app.include_router(export.router)
app.include_router(players.router)

@app.get("/")
def home():
    return {"message": "Horse Racing Tracker API running"}

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/home", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
    
@app.get("/raceday", response_class=HTMLResponse)
def raceday_page(request: Request):
    return templates.TemplateResponse("raceday.html", {"request": request})

@app.get("/current-picks", response_class=HTMLResponse)
def current_picks_page(request: Request):
    return templates.TemplateResponse("current-picks.html", {"request": request})

@app.get("/add-pick", response_class=HTMLResponse)
def add_pick_page(request: Request):
    return templates.TemplateResponse("add-pick.html", {"request": request})

@app.get("/player-details", response_class=HTMLResponse)
def player_details_page(request: Request):
    return templates.TemplateResponse("player-details.html", {"request": request})

@app.get("/stats", response_class=HTMLResponse)
def stats_page(request: Request):
    return templates.TemplateResponse("stats.html", {"request": request})



