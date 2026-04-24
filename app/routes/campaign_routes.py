from fastapi import APIRouter
from app.services.campaign_analysis import load_sample_data
from app.database.db import get_connection
from app.services.kpi_service import get_kpis

router = APIRouter()

@router.get("/test")
def test_route():
    return {"message": "Campaign route working"}


@router.get("/load-data")
def load_data():
    load_sample_data()
    return {"message": "Sample data loaded"}


@router.get("/check-data")
def check_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campaigns")
    data = cursor.fetchall()
    conn.close()
    return [dict(row) for row in data]

@router.get("/kpis")
def fetch_kpis():
    return get_kpis()