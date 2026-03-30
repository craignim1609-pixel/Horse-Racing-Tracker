from app.database import SessionLocal
from app import models


def seed_players():
    """
    Seeds the database with default players if they do not exist.
    Safe to run multiple times.
    """
    db = SessionLocal()

    try:
        default_players = ["Craig", "Donald", "Miller", "Nick", "Josh"]

        for name in default_players:
            exists = (
                db.query(models.Player)
                .filter(models.Player.name == name)
                .first()
            )
            if not exists:
                db.add(models.Player(name=name))

        db.commit()

    finally:
        db.close()


def run_startup_tasks():
    """
    Called from main.py on startup.
    Add more startup tasks here later.
    """
    seed_players()
