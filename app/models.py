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
    picks = relationship("Pick", back_populates="player", cascade="all, delete-orphan")
    racedays = relationship("RaceDay", back_populates="player", cascade="all, delete-orphan")


# ---------------------------------------------------------
# PICK (Accumulator + Current Picks)
# ---------------------------------------------------------
class Pick(Base):
    __tablename__ = "picks"

    id = Column(Integer, primary_key=True, index=True)

    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    course = Column(String, nullable=False)
    horse_name = Column(String, nullable=False)
    horse_number = Column(Integer, nullable=True)
    odds_fraction = Column(String, nullable=False)
    race_time = Column(String, nullable=False)

    # Status values used by your new JS:
    # "pending", "win", "place", "lose", "nr"
    status = Column(String, default="pending", index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Accumulator flag
    is_acca = Column(Boolean, default=False, nullable=False)

    # Relationship
    player = relationship("Player", back_populates="picks")


# ---------------------------------------------------------
# RACE DAY (Activity Feed + Live Bets)
# ---------------------------------------------------------
class RaceDay(Base):
    __tablename__ = "raceday"

    id = Column(Integer, primary_key=True, index=True)

    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    course = Column(String, nullable=False)
    horse_name = Column(String, nullable=False)
    horse_number = Column(Integer, nullable=True)
    odds_fraction = Column(String, nullable=False)
    race_time = Column(String, nullable=False)

    amount_bet = Column(Float, default=1.0)

    # Status values:
    # "pending", "win", "place", "lose", "nr"
    result = Column(String, default="pending", index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    player = relationship("Player", back_populates="racedays")
