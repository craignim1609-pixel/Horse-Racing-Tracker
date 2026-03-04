from fastapi import APIRouter

router = APIRouter(prefix="/export", tags=["Export"])

@router.get("/month/{month}")
def export_month(month: int):
    return {"message": "Export month"}
