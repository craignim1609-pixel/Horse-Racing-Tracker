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

import os

# STATIC + TEMPLATES MUST COME BEFORE ROUTES
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# HOMEPAGE
@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# OTHER PAGES
@app.get("/raceday", response_class=HTMLResponse)
def raceday_page(request: Request):
    return templates.TemplateResponse("raceday.html", {"request": request})

@app.get("/current-picks", response_class=HTMLResponse)
def current_picks_page(request: Request):
    return templates.TemplateResponse("current-picks.html", {"request": request})

@app.get("/new-pick", response_class=HTMLResponse)
def new_pick_page(request: Request):
    return templates.TemplateResponse("new-pick.html", {"request": request})

@app.get("/player-details", response_class=HTMLResponse)
def player_details_page(request: Request):
    return templates.TemplateResponse("player-details.html", {"request": request})

@app.get("/stats", response_class=HTMLResponse)
def stats_page(request: Request):
    return templates.TemplateResponse("stats.html", {"request": request})

@app.get("/acca", response_class=HTMLResponse)
def acca_page(request: Request):
    return templates.TemplateResponse("acca.html", {"request": request})

