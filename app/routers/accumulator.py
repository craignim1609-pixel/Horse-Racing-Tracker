from fastapi import APIRouter

router = APIRouter(prefix="/accumulator", tags=["Accumulator"])

@router.get("/")
def get_accumulator():
    return {"message": "Accumulator endpoint"}
