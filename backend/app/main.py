"""
Cropwater Compass - Smart Irrigation Management System API
Main FastAPI Application Entrypoint
"""
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

# Enable CORS for frontend Vite/React integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local and networked dev
    allow_credentials=True,
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
