from fastapi import APIRouter

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("/month/{month}")
def month_stats(month: int):
    return {"message": "Monthly stats"}
