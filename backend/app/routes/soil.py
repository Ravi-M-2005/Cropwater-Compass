"""
SoilGrids API Routes for Cropwater Compass
Provides authentic ISRIC SoilGrids 250m soil property retrieval,
USDA Soil Texture Triangle classification, and available water capacity calculations.
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Query, HTTPException
try:
    from backend.app.schemas.schemas import (
        SoilPropertiesResponse,
        SoilPropertyItem,
        TextureClassifyRequest,
        TextureClassifyResponse
    )
    from backend.app.services.soilgrids import (
        get_soilgrids_properties,
        classify_usda_texture,
        USDA_TO_CROPWATER_SOIL,
        SUPPORTED_DEPTH_INTERVALS,
        SOILGRIDS_PROPERTIES
    )
except ImportError:
    from app.schemas.schemas import (
        SoilPropertiesResponse,
        SoilPropertyItem,
        TextureClassifyRequest,
        TextureClassifyResponse
    )
    from app.services.soilgrids import (
        get_soilgrids_properties,
        classify_usda_texture,
        USDA_TO_CROPWATER_SOIL,
        SUPPORTED_DEPTH_INTERVALS,
        SOILGRIDS_PROPERTIES
    )

router = APIRouter(prefix="/api/soil", tags=["SoilGrids & Soil Classification"])


@router.get("/depth-intervals", response_model=List[str])
def list_depth_intervals():
    """Returns the standard 6 ISRIC SoilGrids depth intervals."""
    return SUPPORTED_DEPTH_INTERVALS


@router.get("/properties-info", response_model=Dict[str, Any])
def list_properties_info():
    """Returns metadata, descriptions, raw units, target units, and conversion factors for all SoilGrids layers."""
    return SOILGRIDS_PROPERTIES


@router.get("/properties")
def get_soil_properties(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
    depth_interval: str = Query("0-5cm", description="Soil depth interval (e.g. 0-5cm, 5-15cm, 15-30cm, 30-60cm, 60-100cm, 100-200cm)"),
    use_cache: bool = Query(True, description="Whether to check local persistent SQLite cache first")
):
    """
    Retrieves authentic 250m resolution soil properties from ISRIC SoilGrids
    for the specified farm coordinates and depth interval.
    """
    if depth_interval not in SUPPORTED_DEPTH_INTERVALS:
        depth_interval = "0-5cm"

    result = get_soilgrids_properties(lat, lon, depth_interval=depth_interval, use_cache=use_cache)
    return result


@router.post("/classify-texture", response_model=TextureClassifyResponse)
def classify_soil_texture(payload: TextureClassifyRequest):
    """
    Classifies a soil sample into one of the 12 USDA Soil Texture Triangle classes
    from Sand %, Silt %, and Clay % fractions, and calculates field capacity,
    wilting point, and available water capacity (AWC).
    """
    total = payload.sand_pct + payload.silt_pct + payload.clay_pct
    if total <= 0:
        raise HTTPException(status_code=400, detail="Sum of sand, silt, and clay must be greater than 0")

    # Normalize to 100%
    s = (payload.sand_pct / total) * 100.0
    si = (payload.silt_pct / total) * 100.0
    c = (payload.clay_pct / total) * 100.0

    usda_texture = classify_usda_texture(s, si, c)
    cropwater_soil = USDA_TO_CROPWATER_SOIL.get(usda_texture, "Loamy")

    # Empirical hydrological values by USDA soil class
    # (Saxton & Rawls / FAO-56 standard hydrology)
    hydrology_lookup = {
        "Sand": (10.0, 4.0),
        "Loamy Sand": (14.0, 6.0),
        "Sandy Loam": (20.0, 9.0),
        "Loam": (27.0, 12.0),
        "Silt Loam": (30.0, 13.0),
        "Silt": (32.0, 11.0),
        "Sandy Clay Loam": (28.0, 15.0),
        "Clay Loam": (32.0, 18.0),
        "Silty Clay Loam": (35.0, 20.0),
        "Sandy Clay": (34.0, 21.0),
        "Silty Clay": (38.0, 24.0),
        "Clay": (40.0, 26.0),
    }

    fc_pct, wp_pct = hydrology_lookup.get(usda_texture, (26.0, 12.0))
    awc_mm_per_m = round((fc_pct - wp_pct) * 10.0, 1)

    return TextureClassifyResponse(
        sand_pct=round(s, 1),
        silt_pct=round(si, 1),
        clay_pct=round(c, 1),
        usda_texture_class=usda_texture,
        mapped_cropwater_soil=cropwater_soil,
        field_capacity_pct=fc_pct,
        wilting_point_pct=wp_pct,
        awc_mm_per_m=awc_mm_per_m
    )
