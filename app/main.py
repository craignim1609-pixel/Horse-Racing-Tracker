from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import Base, engine
from app import models

from app.routers import picks, accumulator, raceday, players, stats
from app.routers.players import seed_players


app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)


# Seed players on startup
@app.on_event("startup")
def startup_event():
    seed_players()


# ============================
# ROUTERS
# ============================
app.include_router(picks.router)
app.include_router(accumulator.router)
app.include_router(raceday.router)
app.include_router(players.router)
app.include_router(stats.router)   # <-- REQUIRED


# ============================
# STATIC + TEMPLATES
# ============================
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ============================
# PAGE ROUTES
# ============================

# HOME
@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# RACE DAY
@app.get("/raceday", response_class=HTMLResponse)
def raceday_page(request: Request):
    return templates.TemplateResponse("raceday.html", {"request": request})


# CURRENT PICKS
@app.get("/current-picks", response_class=HTMLResponse)
def current_picks_page(request: Request):
    return templates.TemplateResponse("current-picks.html", {"request": request})


# ADD PICK
@app.get("/add-pick", response_class=HTMLResponse)
def add_pick_page(request: Request):
    return templates.TemplateResponse("add-pick.html", {"request": request})


# ACCA PAGE
@app.get("/acca", response_class=HTMLResponse)
def acca_page(request: Request):
    return templates.TemplateResponse("acca.html", {"request": request})
