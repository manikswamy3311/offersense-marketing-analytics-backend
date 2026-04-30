from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.campaign_routes import router as campaign_router

app = FastAPI(title="OfferSense API")

# ✅ ADD CORS IMMEDIATELY AFTER APP CREATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # DO NOT USE "*" NOW
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ THEN ADD ROUTES
app.include_router(campaign_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "OfferSense Backend Running"}