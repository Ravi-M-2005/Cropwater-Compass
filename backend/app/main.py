"""
Cropwater Compass - Smart Irrigation Management System API
Main FastAPI Application Entrypoint
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.routes import (
    prediction_router,
    weather_router,
    dataset_router,
    history_router,
    reports_router,
)
from backend.app.services.history import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema
    init_db()
    yield


app = FastAPI(
    title="Cropwater Compass API",
    description="Smart Irrigation Management System Using Machine Learning & FAO-56 CROPWAT Standards",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS origins: environment-based with local development defaults
DEFAULT_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

cors_env = os.getenv("CORS_ORIGINS", "").strip()
extra_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()] if cors_env else []
allowed_origins = list(dict.fromkeys(DEFAULT_DEV_ORIGINS + extra_origins))

is_wildcard = "*" in allowed_origins

# Do not combine wildcard origins with credentials enabled
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if is_wildcard else allowed_origins,
    allow_credentials=not is_wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount feature routers
app.include_router(prediction_router)
app.include_router(weather_router)
app.include_router(dataset_router)
app.include_router(history_router)
app.include_router(reports_router)


@app.get("/")
def root():
    return {
        "project": "Cropwater Compass",
        "description": "Smart Irrigation Management System Using Machine Learning",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "target_output": "Estimated irrigation water requirement in Litres"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "sqlite_ready",
        "ml_engine": "active"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
