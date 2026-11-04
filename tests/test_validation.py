"""
Tests for Error Validation on Prediction Inputs and Models
Reviewer Feedback Part A: Strict input validation on area, rainfall, soil moisture, coordinates, etc.
"""
import pytest
from pydantic import ValidationError
from backend.app.schemas.schemas import PredictionRequest

BASE_VALID_PAYLOAD = {
    "crop_type": "Wheat",
    "growth_stage": "Mid-season",
    "area": 2.5,
    "area_unit": "hectares",
    "soil_type": "Loamy",
    "soil_moisture_pct": 32.0,
    "soil_ph": 6.8,
    "temperature_c": 28.5,
    "humidity_pct": 52.0,
    "wind_speed_kmh": 11.4,
    "rainfall_mm": 0.0,
    "solar_radiation": 21.0,
    "et0_mm": 4.6,
    "irrigation_method": "Drip",
    "model_name": "xgboost"
}


def test_valid_prediction_request():
    """Valid request parses cleanly."""
    req = PredictionRequest(**BASE_VALID_PAYLOAD)
    assert req.area == 2.5
    assert req.rainfall_mm == 0.0


def test_reject_zero_or_negative_area():
    """Area <= 0 must fail validation."""
    with pytest.raises(ValidationError):
        PredictionRequest(**{**BASE_VALID_PAYLOAD, "area": 0.0})

    with pytest.raises(ValidationError):
        PredictionRequest(**{**BASE_VALID_PAYLOAD, "area": -1.5})


def test_reject_negative_rainfall():
    """Negative rainfall must fail validation."""
    with pytest.raises(ValidationError):
        PredictionRequest(**{**BASE_VALID_PAYLOAD, "rainfall_mm": -5.0})


def test_reject_out_of_range_soil_moisture():
    """Soil moisture outside 0-100% must fail validation."""
    with pytest.raises(ValidationError):
        PredictionRequest(**{**BASE_VALID_PAYLOAD, "soil_moisture_pct": -2.0})

    with pytest.raises(ValidationError):
        PredictionRequest(**{**BASE_VALID_PAYLOAD, "soil_moisture_pct": 105.0})


def test_reject_out_of_range_soil_ph():
    """Soil pH outside 3.0-11.0 must fail validation."""
    with pytest.raises(ValidationError):
        PredictionRequest(**{**BASE_VALID_PAYLOAD, "soil_ph": 2.1})

    with pytest.raises(ValidationError):
        PredictionRequest(**{**BASE_VALID_PAYLOAD, "soil_ph": 11.5})


def test_reject_out_of_range_temperature():
    """Temperature outside -20 to 60°C must fail validation."""
    with pytest.raises(ValidationError):
        PredictionRequest(**{**BASE_VALID_PAYLOAD, "temperature_c": -35.0})

    with pytest.raises(ValidationError):
        PredictionRequest(**{**BASE_VALID_PAYLOAD, "temperature_c": 75.0})


def test_reject_invalid_coordinates():
    """Coordinates outside -90/90 and -180/180 must fail validation."""
    with pytest.raises(ValidationError):
        PredictionRequest(**{**BASE_VALID_PAYLOAD, "latitude": 95.0, "longitude": 75.0})

    with pytest.raises(ValidationError):
        PredictionRequest(**{**BASE_VALID_PAYLOAD, "latitude": 20.0, "longitude": 200.0})


def test_validation_error_structure():
    """Verifies that ValidationError contains informative detail on negative rainfall."""
    bad_payload = {**BASE_VALID_PAYLOAD, "rainfall_mm": -10.0}
    with pytest.raises(ValidationError) as exc_info:
        PredictionRequest(**bad_payload)
    errors = exc_info.value.errors()
    assert any(err["loc"] == ("rainfall_mm",) for err in errors)
    assert any("Rainfall cannot be negative" in str(err["msg"]) or "greater than or equal to 0" in str(err["msg"]) for err in errors)
