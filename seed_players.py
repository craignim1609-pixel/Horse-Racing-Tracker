from app.database import SessionLocal, engine
from app.models import Base, Player

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

players = ["Donald", "Miller", "Nick", "Josh", "Craig"]

for name in players:
    exists = db.query(Player).filter(Player.name == name).first()
    if not exists:
        db.add(Player(name=name))

db.commit()
db.close()

print("Players inserted successfully.")
