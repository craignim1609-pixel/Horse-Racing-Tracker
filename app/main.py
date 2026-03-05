from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.routers import picks, accumulator, stats, raceday, export
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse


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

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/home", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
@app.get("/raceday", response_class=HTMLResponse)
def raceday_page(request: Request):
    return templates.TemplateResponse("raceday.html", {"request": request})

@app.get("/current", response_class=HTMLResponse)
def current_page(request: Request):
    return templates.TemplateResponse("current.html", {"request": request})

@app.get("/players", response_class=HTMLResponse)
def players_page(request: Request):
    return templates.TemplateResponse("players.html", {"request": request})

@app.get("/accumulator", response_class=HTMLResponse)
def accumulator_page(request: Request):
    return templates.TemplateResponse("accumulator.html", {"request": request})

@app.get("/stats", response_class=HTMLResponse)
def stats_page(request: Request):
    return templates.TemplateResponse("stats.html", {"request": request})


