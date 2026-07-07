from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.routes.campaign_routes import router as campaign_router
from app.routes.auth_routes import router as auth_router
from app.routes.oauth_routes import router as oauth_router
from app.database.db import get_connection
from app.limiter import limiter
import logging
import os
import time

_start_time = time.time()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

_startup_logger = logging.getLogger("offersense.startup")

def _validate_env():
    """Warn loudly if critical env vars are missing or left at insecure defaults."""
    warnings = []
    if os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production") == "your-secret-key-change-in-production":
        warnings.append("JWT_SECRET_KEY is not set — using insecure default. Set it before going to production.")
    if not os.getenv("DATABASE_URL"):
        warnings.append("DATABASE_URL is not set — using local SQLite (dev only).")
    for msg in warnings:
        _startup_logger.warning("CONFIG WARNING: %s", msg)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="OfferSense API",
    version="1.2.0",
    description="Marketing Analytics Backend with JWT Authentication"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_validate_env()

# ✅ ADD CORS IMMEDIATELY AFTER APP CREATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # DO NOT USE "*" NOW
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ THEN ADD ROUTES
# Authentication routes (public)
app.include_router(auth_router, prefix="/api/v1")

# OAuth routes (Google + GitHub)
app.include_router(oauth_router, prefix="/api/v1")

# Campaign routes (protected)
app.include_router(campaign_router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "message": "OfferSense Backend Running",
        "version": "1.2.0",
        "docs": "http://localhost:8000/docs",
        "auth": "Login at /api/v1/auth/login"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for liveness/readiness probes."""
    db_status = "ok"
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        db_status = "error"

    uptime_seconds = round(time.time() - _start_time, 1)

    status = "healthy" if db_status == "ok" else "degraded"

    return {
        "status": status,
        "version": "1.1.0",
        "uptime_seconds": uptime_seconds,
        "checks": {
            "database": db_status,
        }
    }