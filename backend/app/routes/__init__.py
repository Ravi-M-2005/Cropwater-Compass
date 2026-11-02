"""
API Routes Package
"""
from backend.app.routes.prediction import router as prediction_router
from backend.app.routes.weather import router as weather_router
from backend.app.routes.dataset import router as dataset_router
from backend.app.routes.history import router as history_router
from backend.app.routes.reports import router as reports_router

__all__ = [
    "prediction_router",
    "weather_router",
    "dataset_router",
    "history_router",
    "reports_router",
]
