from app.database import engine, SessionLocal
from app.models import Base, Player

def create_tables():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

def seed_players():
    print("Seeding players...")
    db = SessionLocal()
    players = ["Donald", "Miller", "Nick", "Josh", "Craig"]

    for name in players:
        exists = db.query(Player).filter(Player.name == name).first()
        if not exists:
            db.add(Player(name=name))

    db.commit()
    db.close()
    print("Players inserted.")

if __name__ == "__main__":
    create_tables()
    seed_players()
    print("Database setup complete.")
