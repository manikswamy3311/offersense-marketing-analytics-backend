from fastapi import FastAPI
from app.routes.campaign_routes import router as campaign_router

app = FastAPI(title="OfferSense API")

app.include_router(campaign_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "OfferSense Backend Running"}