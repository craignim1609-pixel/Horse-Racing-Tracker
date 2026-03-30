from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app import models

router = APIRouter(prefix="/acca", tags=["Accumulator"])


# ---------------------------------------------------------
# GET ACCUMULATOR SUMMARY + PICKS
# (Matches JS: GET /api/acca)
# ---------------------------------------------------------
@router.get("/")
def get_acca(db: Session = Depends(get_db)):
    # Load all picks marked as ACCA
    picks = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.is_acca == True)
        .order_by(models.Pick.id.desc())
        .all()
    )

    # If no picks, return empty accumulator
    if not picks:
        return {
            "total_odds": "-",
            "ew_return": "-",
            "status_label": "No Bets",
            "status_class": "no-bets",
            "picks": [],
            "standings": [],
        }

    # -----------------------------------------------------
    # CALCULATE ACCA ODDS
    # -----------------------------------------------------
    total_odds = 1.0

    for p in picks:
        try:
            num, den = p.odds_fraction.split("/")
            total_odds *= (int(num) / int(den) + 1)
        except Exception:
            pass

    total_odds = round(total_odds, 2)

    # -----------------------------------------------------
    # DETERMINE ACCA STATUS
    # -----------------------------------------------------
    statuses = {p.status.lower() for p in picks}

    if "lose" in statuses:
        status_label = "Lost"
        status_class = "lost"
    elif "win" in statuses and len(statuses) == 1:
        status_label = "Won"
        status_class = "won"
    elif "pending" in statuses:
        status_label = "In Play"
        status_class = "in-play"
    else:
        status_label = "In Play"
        status_class = "in-play"

    # -----------------------------------------------------
    # BUILD PLAYER STANDINGS (simple version)
    # -----------------------------------------------------
    standings = []
    for p in picks:
        standings.append({
            "player": p.player.name,
            "status": p.status,
        })

    return {
        "total_odds": total_odds,
        "ew_return": "-",  # Add real EW logic later
        "status_label": status_label,
        "status_class": status_class,
        "picks": picks,
        "standings": standings,
    }
