from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# ---------------------------------------------------------
# DATABASE URL
# ---------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# ---------------------------------------------------------
# ENGINE + SESSION
# ---------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # avoids stale connections
    pool_recycle=1800        # refresh connections every 30 mins
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ---------------------------------------------------------
# BASE MODEL
# ---------------------------------------------------------
Base = declarative_base()


# ---------------------------------------------------------
# DEPENDENCY: GET DB SESSION
# ---------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
