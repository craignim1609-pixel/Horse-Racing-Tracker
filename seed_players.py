from app.database import SessionLocal
from app.models import Player

def seed_players():
    db = SessionLocal()

    players = ["Donald", "Miller", "Nick", "Josh", "Craig"]

    for name in players:
        exists = db.query(Player).filter(Player.name == name).first()
        if not exists:
            db.add(Player(name=name))

    db.commit()
    db.close()
