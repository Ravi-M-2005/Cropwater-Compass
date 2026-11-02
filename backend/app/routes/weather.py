"""
Weather and Evapotranspiration API Routes
"""
from fastapi import APIRouter, Query
from typing import Dict, Any, List, Optional

from backend.app.schemas.schemas import (
    WeatherData,
    ET0CalculationRequest,
    ET0CalculationResponse
)
from backend.app.services.weather import (
    fetch_live_or_simulated_weather,
    calculate_fao56_et0,
    POPULAR_LOCATIONS
)

router = APIRouter(prefix="/api/weather", tags=["Weather"])


@router.get("/current", response_model=WeatherData)
def get_current_weather(
    lat: float = Query(28.6139, ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(77.2090, ge=-180.0, le=180.0, description="Longitude"),
    city: Optional[str] = Query(None, description="Optional city or region name")
):
    """
    Fetches real-time weather and FAO-56 Reference Evapotranspiration (ET0)
    from Open-Meteo or physically consistent climate engine.
    """
    lat_val = lat.default if hasattr(lat, "default") else lat
    lon_val = lon.default if hasattr(lon, "default") else lon
    city_val = city.default if hasattr(city, "default") else city
    if city_val is not None and hasattr(city_val, "default"):
        city_val = None

    return fetch_live_or_simulated_weather(float(lat_val), float(lon_val), city_val)


@router.get("/locations")
def get_preset_locations() -> Dict[str, Any]:
    """Returns preset agricultural farming regions with coordinates."""
    return {"locations": POPULAR_LOCATIONS}


@router.post("/calculate-et0", response_model=ET0CalculationResponse)
def calculate_custom_et0(request: ET0CalculationRequest):
    """
    Calculates Reference Evapotranspiration (ET0) using the standard FAO-56 Penman-Monteith method.
    """
    et0 = calculate_fao56_et0(
        temp_c=request.temperature_c,
        humidity_pct=request.humidity_pct,
        wind_speed_kmh=request.wind_speed_kmh,
        solar_radiation_mj=request.solar_radiation,
        lat_deg=request.latitude or 20.0,
        day_of_year=request.day_of_year or 180
    )

    return {
        "et0_mm": et0,
        "method_used": "FAO-56 Penman-Monteith",
        "details": {
            "temperature_c": request.temperature_c,
            "humidity_pct": request.humidity_pct,
            "wind_speed_kmh": request.wind_speed_kmh,
            "solar_radiation": request.solar_radiation
        }
    }
