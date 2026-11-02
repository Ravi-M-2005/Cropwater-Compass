"""
Services Package
"""
from backend.app.services.irrigation import (
    CROP_DATABASE,
    SOIL_DATABASE,
    IRRIGATION_METHODS,
    calculate_irrigation_recommendation,
    convert_area_to_sq_meters,
)
from backend.app.services.weather import (
    calculate_fao56_et0,
    fetch_live_or_simulated_weather,
)
from backend.app.services.history import (
    save_prediction,
    get_history,
    get_history_stats,
)
from backend.app.services.ml_service import (
    predict_water_requirements,
    get_shap_explanation,
    get_models_benchmark_metrics,
)

__all__ = [
    "CROP_DATABASE",
    "SOIL_DATABASE",
    "IRRIGATION_METHODS",
    "calculate_irrigation_recommendation",
    "convert_area_to_sq_meters",
    "calculate_fao56_et0",
    "fetch_live_or_simulated_weather",
    "save_prediction",
    "get_history",
    "get_history_stats",
    "predict_water_requirements",
    "get_shap_explanation",
    "get_models_benchmark_metrics",
]
