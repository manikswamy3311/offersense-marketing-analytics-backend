from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_route():
    return {"message": "Campaign route working"}