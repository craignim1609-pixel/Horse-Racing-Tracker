from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


# ---------------------------------------------------------
# PLAYER
# ---------------------------------------------------------
class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    # Relationships
    picks = relationship("Pick", back_populates="player")
    racedays = relationship("RaceDay", back_populates="player")


# ---------------------------------------------------------
# PICK (Accumulator + Current Picks)
# ---------------------------------------------------------
class Pick(Base):
    __tablename__ = "picks"

    id = Column(Integer, primary_key=True, index=True)

    player_id = Column(Integer, ForeignKey("players.id"))
    course = Column(String)
    horse_name = Column(String)
    horse_number = Column(Integer, nullable=True)
    odds_fraction = Column(String)
    race_time = Column(String)
    status = Column(String, default="Pending")  # Pending / Win / Place / Lose / NR

    # Timestamp for daily filtering
    created_at = Column(DateTime, default=datetime.utcnow)

    # NEW — accumulator flag
    is_acca = Column(Boolean, default=False, nullable=False)

    # Relationship
    player = relationship("Player", back_populates="picks")


# ---------------------------------------------------------
# RACE DAY BETS
# ---------------------------------------------------------
class RaceDay(Base):
    __tablename__ = "raceday"

    id = Column(Integer, primary_key=True, index=True)

    player_id = Column(Integer, ForeignKey("players.id"))
    course = Column(String)
    horse_name = Column(String)
    horse_number = Column(Integer, nullable=True)
    odds_fraction = Column(String)
    race_time = Column(String)
    amount_bet = Column(Float)
    result = Column(String, default="Pending")  # Win / Place / Lose / NR / Pending

    # Timestamp for stats/history
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    player = relationship("Player", back_populates="racedays")
