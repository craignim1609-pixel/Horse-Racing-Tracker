from app.database import Base, engine, SessionLocal
from app import models


def seed_players():
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
    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Seed default players
    seed_players()
