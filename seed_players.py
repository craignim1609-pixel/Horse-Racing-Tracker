from app.database import SessionLocal
from app.models import Player


def seed_players():
    """
    Seeds the database with default players.
    Safe to run multiple times.
    """
    db = SessionLocal()

    try:
        default_players = ["Donald", "Miller", "Nick", "Josh", "Craig"]

        for name in default_players:
            exists = db.query(Player).filter(Player.name == name).first()
            if not exists:
                db.add(Player(name=name))

        db.commit()

    finally:
        db.close()
