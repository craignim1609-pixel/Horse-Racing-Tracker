from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    picks = relationship("Pick", back_populates="player")
    race_bets = relationship("RaceDay", back_populates="player")


class Pick(Base):
    __tablename__ = "picks"
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    course = Column(String)
    horse_name = Column(String)
    horse_number = Column(Integer)
    odds_fraction = Column(String)
    race_time = Column(String)
    status = Column(String, default="Pending")
    month = Column(Integer)
    year = Column(Integer)

    player = relationship("Player", back_populates="picks")


class RaceDay(Base):
    __tablename__ = "race_day"
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    amount_bet = Column(Numeric)
    odds_fraction = Column(String)
    track = Column(String)
    time = Column(String)
    horse_name = Column(String)
    horse_number = Column(Integer)
    result = Column(String)
    month = Column(Integer)
    year = Column(Integer)

    player = relationship("Player", back_populates="race_bets")
