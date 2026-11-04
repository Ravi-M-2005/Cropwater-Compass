"""
Tests for ISRIC SoilGrids 250m Integration and USDA Soil Texture Classification
"""
import pytest
import asyncio
from backend.app.schemas.schemas import TextureClassifyRequest
from backend.app.services.soilgrids import (
    classify_usda_texture,
    USDA_TO_CROPWATER_SOIL,
    SUPPORTED_DEPTH_INTERVALS,
    SOILGRIDS_PROPERTIES,
)
from backend.app.routes.soil import (
    list_depth_intervals,
    classify_soil_texture,
    get_soil_properties
)


def test_usda_texture_classification_all_12_classes():
    """Verifies that all 12 standard USDA Soil Texture Triangle classes are recognized correctly."""
    textbook_points = [
        {"sand": 92.0, "silt": 5.0, "clay": 3.0, "expected": "Sand"},
        {"sand": 82.0, "silt": 12.0, "clay": 6.0, "expected": "Loamy Sand"},
        {"sand": 65.0, "silt": 25.0, "clay": 10.0, "expected": "Sandy Loam"},
        {"sand": 40.0, "silt": 40.0, "clay": 20.0, "expected": "Loam"},
        {"sand": 20.0, "silt": 65.0, "clay": 15.0, "expected": "Silt Loam"},
        {"sand": 5.0, "silt": 88.0, "clay": 7.0, "expected": "Silt"},
        {"sand": 60.0, "silt": 15.0, "clay": 25.0, "expected": "Sandy Clay Loam"},
        {"sand": 32.0, "silt": 34.0, "clay": 34.0, "expected": "Clay Loam"},
        {"sand": 10.0, "silt": 55.0, "clay": 35.0, "expected": "Silty Clay Loam"},
        {"sand": 52.0, "silt": 6.0, "clay": 42.0, "expected": "Sandy Clay"},
        {"sand": 8.0, "silt": 47.0, "clay": 45.0, "expected": "Silty Clay"},
        {"sand": 20.0, "silt": 20.0, "clay": 60.0, "expected": "Clay"},
    ]

    for pt in textbook_points:
        derived = classify_usda_texture(pt["sand"], pt["silt"], pt["clay"])
        assert derived == pt["expected"], f"Failed on Sand={pt['sand']} Silt={pt['silt']} Clay={pt['clay']}: got '{derived}' expected '{pt['expected']}'"
        assert derived in USDA_TO_CROPWATER_SOIL, f"USDA texture {derived} missing Cropwater soil mapping"


def test_supported_depth_intervals():
    """Ensures standard ISRIC depth intervals are present."""
    expected = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
    assert SUPPORTED_DEPTH_INTERVALS == expected


def test_property_conversion_specifications():
    """Ensures raw units, target units, and scale factors are properly defined for all 13 SoilGrids layers."""
    assert len(SOILGRIDS_PROPERTIES) == 13
    assert "clay" in SOILGRIDS_PROPERTIES
    assert SOILGRIDS_PROPERTIES["clay"]["raw_units"] == "g/kg"
    assert SOILGRIDS_PROPERTIES["clay"]["target_units"] == "%"
    assert SOILGRIDS_PROPERTIES["clay"]["conversion_factor"] == 10.0
    assert "phh2o" in SOILGRIDS_PROPERTIES
    assert SOILGRIDS_PROPERTIES["phh2o"]["conversion_factor"] == 10.0
    assert "bdod" in SOILGRIDS_PROPERTIES
    assert SOILGRIDS_PROPERTIES["bdod"]["conversion_factor"] == 100.0


def test_api_soil_endpoints():
    """Tests /api/soil/depth-intervals and /api/soil/classify-texture."""
    depths = list_depth_intervals()
    assert "0-5cm" in depths

    req = TextureClassifyRequest(sand_pct=33.3, silt_pct=29.5, clay_pct=37.2)
    data = classify_soil_texture(req)
    assert data.usda_texture_class == "Clay Loam"
    assert data.mapped_cropwater_soil == "Clay Loam"
    assert data.field_capacity_pct > data.wilting_point_pct
    assert data.awc_mm_per_m > 0


def test_api_soil_properties_retrieval():
    """Tests get_soil_properties for Mandya agricultural coordinate."""
    res = get_soil_properties(lat=12.5218, lon=76.8951, depth_interval="0-5cm", use_cache=True)
    assert "latitude" in res
    assert "longitude" in res
    assert "properties" in res
    assert "citation" in res
