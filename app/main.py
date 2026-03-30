from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from app.routers.picks import router as picks_router
from app.routers.accumulator import router as acca_router
from app.routers.stats import router as stats_router
from app.routers.raceday import router as raceday_router
from app.routers.players import router as players_router
from app.routers.export import router as export_router


# Startup logic (optional)
from app.startup import run_startup_tasks

@app.get("/")
def root():
    return {"status": "ok", "message": "Racing API is running"}

def create_app():
    app = FastAPI(
        title="Racing App API",
        version="1.0.0",
        description="Backend API for the Racing Tracker App"
    )

    # -----------------------------------------------------
    # CORS (allow frontend templates to call API)
    # -----------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],       # tighten for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -----------------------------------------------------
    # REGISTER ROUTERS
    # -----------------------------------------------------
    app.include_router(picks_router, prefix="/api")
    app.include_router(acca_router, prefix="/api")
    app.include_router(stats_router, prefix="/api")
    app.include_router(raceday_router, prefix="/api")
    app.include_router(players_router, prefix="/api")
    app.include_router(export_router, prefix="/api")

    # -----------------------------------------------------
    # STARTUP TASKS (optional)
    # -----------------------------------------------------
    @app.on_event("startup")
    async def startup_event():
        run_startup_tasks()

    return app


app = create_app()
