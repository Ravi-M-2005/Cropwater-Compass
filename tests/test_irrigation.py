"""
Unit Tests for Irrigation Agronomic Calculations and Units
"""
import pytest
from backend.app.services.irrigation import (
    convert_area_to_sq_meters,
    get_crop_kc,
    calculate_effective_rainfall,
    calculate_soil_water_balance,
    calculate_irrigation_recommendation
)


def test_area_conversions():
    # 1 hectare = 10,000 m2
    assert convert_area_to_sq_meters(1.0, "hectares") == 10000.0
    assert convert_area_to_sq_meters(2.5, "ha") == 25000.0
    
    # 1 acre ~ 4046.86 m2
    assert pytest.approx(convert_area_to_sq_meters(1.0, "acres"), 0.1) == 4046.86
    
    # Direct sq meters
    assert convert_area_to_sq_meters(500.0, "sq_meters") == 500.0


def test_crop_kc_stages():
    # Wheat mid season Kc ~ 1.15
    assert get_crop_kc("Wheat", "Mid-season") == 1.15
    # Wheat initial Kc ~ 0.35
    assert get_crop_kc("Wheat", "Initial") == 0.35
    # Rice mid season Kc ~ 1.20
    assert get_crop_kc("Rice", "Mid-season") == 1.20


def test_effective_rainfall():
    # Light rain under 5mm evaporates
    assert calculate_effective_rainfall(3.0) == 0.0
    # Moderate rain
    assert calculate_effective_rainfall(25.0) == (25.0 - 5.0) * 0.75


def test_water_requirement_in_litres():
    """
    Core business logic check:
    1 mm of water depth on 1 m2 equals exactly 1 litre.
    For 1 hectare (10,000 m2), 1 mm depth equals 10,000 litres.
    If gross requirement is 4.0 mm, total water requirement must be 40,000 litres.
    """
    res = calculate_irrigation_recommendation(
        crop_type="Wheat",
        growth_stage="Mid-season",
        area=1.0,
        area_unit="hectares",
        soil_type="Loamy",
        soil_moisture_pct=25.0,
        temperature_c=30.0,
        humidity_pct=45.0,
        wind_speed_kmh=12.0,
        rainfall_mm=0.0,
        reference_et0_mm=4.5,
        irrigation_method="Drip"
    )

    assert res["water_requirement_litres"] > 0
    # Verify litres = gross mm * 10,000 for 1 ha
    expected_litres = round(res["gross_irrigation_requirement_mm"] * 10000.0, 2)
    assert pytest.approx(res["water_requirement_litres"], 1.0) == expected_litres
    assert res["water_requirement_m3"] == round(res["water_requirement_litres"] / 1000.0, 3)
    assert res["urgency_level"] in ["Critical", "High", "Moderate", "Low", "None"]
    assert "recommended_schedule" in res
