from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app import models

router = APIRouter(prefix="/raceday", tags=["Race Day"])


# ---------------------------------------------------------
# GET RACE DAY DATA
# Matches JS: GET /api/raceday
# ---------------------------------------------------------
@router.get("/")
def get_raceday(db: Session = Depends(get_db)):
    # Load all picks that are still pending
    races = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.status == "pending")
        .order_by(models.Pick.race_time.asc())
        .all()
    )

    # Load recent activity (last 20 results)
    activity = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.status != "pending")
        .order_by(models.Pick.id.desc())
        .limit(20)
        .all()
    )

    # Format races for front‑end
    race_cards = [
        {
            "id": r.id,
            "horse_number": r.horse_number,
            "horse_name": r.horse_name,
            "course": r.course,
            "time": r.race_time,
            "odds": r.odds_fraction,
            "stake": 1,  # placeholder — add real stake logic later
            "status": r.status.lower(),
            "player": r.player.name,
        }
        for r in races
    ]

    # Format activity feed
    activity_cards = [
        {
            "horse_number": a.horse_number,
            "horse_name": a.horse_name,
            "odds": a.odds_fraction,
            "course": a.course,
            "time": a.race_time,
            "player": a.player.name,
            "profit": calculate_profit(a),  # helper below
        }
        for a in activity
    ]

    return {
        "races": race_cards,
        "activity": activity_cards,
    }


# ---------------------------------------------------------
# UPDATE RACE STATUS
# Matches JS: POST /api/raceday/{id}/status
# ---------------------------------------------------------
@router.post("/{pick_id}/status")
def update_race_status(
    pick_id: int,
    data: dict,
    db: Session = Depends(get_db)
):
    status = data.get("status")
    if status not in ["win", "place", "lose", "nr"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    pick = db.query(models.Pick).filter(models.Pick.id == pick_id).first()
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")

    pick.status = status
    db.commit()
    db.refresh(pick)

    return {"message": "Status updated", "status": status}


# ---------------------------------------------------------
# HELPER: SIMPLE PROFIT CALCULATION
# ---------------------------------------------------------
def calculate_profit(pick: models.Pick):
    """
    Placeholder profit logic.
    You can replace this with your real staking rules.
    """
    try:
        num, den = pick.odds_fraction.split("/")
        odds = int(num) / int(den)
    except Exception:
        odds = 0

    if pick.status == "win":
        return round(odds * 1, 2)  # stake = 1
    if pick.status == "place":
        return round((odds / 4) * 1, 2)  # simple EW placeholder
    if pick.status == "lose":
        return -1
    if pick.status == "nr":
        return 0

    return 0
