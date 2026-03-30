from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
import tempfile
from app.database import get_db
from app import models
from app.utils.excel import export_to_excel

router = APIRouter(prefix="/export", tags=["Export"])


# ---------------------------------------------------------
# EXPORT PICKS FOR A GIVEN MONTH + YEAR
# Matches: GET /api/export/month/{month}?year=2025
# ---------------------------------------------------------
@router.get("/month/{month}")
def export_month(month: int, year: int, db: Session = Depends(get_db)):
    # Validate month
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid month")

    # Query picks
    picks = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.month == month, models.Pick.year == year)
        .order_by(models.Pick.id.asc())
        .all()
    )

    if not picks:
        raise HTTPException(status_code=404, detail="No picks found for this month")

    # Convert to exportable dicts
    data = [
        {
            "player": p.player.name,
            "course": p.course,
            "horse_name": p.horse_name,
            "horse_number": p.horse_number,
            "odds_fraction": p.odds_fraction,
            "race_time": p.race_time,
            "status": p.status,
            "month": p.month,
            "year": p.year,
        }
        for p in picks
    ]

    # Create temporary Excel file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    export_to_excel(data, tmp.name)

    return FileResponse(
        tmp.name,
        filename=f"picks_{year}_{month}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
