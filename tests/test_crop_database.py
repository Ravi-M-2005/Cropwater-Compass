"""
Tests for the expanded crop database and decimal humidity validation.
Verifies FAO-56 Kc values, alias resolution, and input validation for all 9 crop categories.
"""
import pytest
from backend.app.schemas.schemas import PredictionRequest
from backend.app.services.irrigation import (
    CROP_DATABASE,
    CROP_ALIASES,
    resolve_crop_name,
    get_crop_kc,
    calculate_effective_rainfall,
    calculate_irrigation_recommendation,
)


# ─────────────────────────────────────────────────────────────────
# Task 1: Humidity Decimal Validation Tests
# ─────────────────────────────────────────────────────────────────

BASE_REQUEST = {
    "crop_type": "Wheat",
    "growth_stage": "Mid-season",
    "area": 2.0,
    "area_unit": "hectares",
    "soil_type": "Loamy",
    "soil_moisture_pct": 26.0,
    "temperature_c": 28.0,
    "wind_speed_kmh": 10.0,
    "rainfall_mm": 0.0,
}


@pytest.mark.parametrize("humidity", [53.9, 65.5, 72.3, 48.7, 100.0, 0.0, 33.333, 99.9])
def test_humidity_accepts_decimal_values(humidity):
    """Backend Pydantic schema must accept decimal humidity values."""
    req = PredictionRequest(**{**BASE_REQUEST, "humidity_pct": humidity})
    assert abs(req.humidity_pct - humidity) < 0.001


@pytest.mark.parametrize("humidity", [-1.0, 101.0, 150.0, -0.1])
def test_humidity_rejects_out_of_range(humidity):
    """Humidity outside 0-100 must raise a Pydantic validation error."""
    with pytest.raises(Exception):
        PredictionRequest(**{**BASE_REQUEST, "humidity_pct": humidity})


@pytest.mark.parametrize("temp", [-15.5, 0.0, 26.8, 36.5, 55.0])
def test_temperature_accepts_decimal(temp):
    """Temperature must accept decimal values within -20 to 60°C."""
    req = PredictionRequest(**{**BASE_REQUEST, "humidity_pct": 50.0, "temperature_c": temp})
    assert abs(req.temperature_c - temp) < 0.001


@pytest.mark.parametrize("wind", [0.0, 5.5, 11.3, 25.7])
def test_wind_speed_accepts_decimal(wind):
    """Wind speed must accept decimal values."""
    req = PredictionRequest(**{**BASE_REQUEST, "humidity_pct": 50.0, "wind_speed_kmh": wind})
    assert abs(req.wind_speed_kmh - wind) < 0.001


# ─────────────────────────────────────────────────────────────────
# Task 2: Crop Database Coverage Tests
# ─────────────────────────────────────────────────────────────────

EXPECTED_CATEGORIES = [
    "Cereals and Millets",
    "Pulses and Legumes",
    "Oilseed Crops",
    "Commercial and Fibre Crops",
    "Vegetables",
    "Fruits",
    "Plantation and Spice Crops",
    "Fodder and Forage Crops",
    "Other Agricultural Crops",
]


def test_all_expected_categories_present():
    """All 9 required crop categories must be represented in CROP_DATABASE."""
    actual_categories = {data["category"] for data in CROP_DATABASE.values()}
    for cat in EXPECTED_CATEGORIES:
        assert cat in actual_categories, f"Category missing: {cat}"


def test_minimum_crop_count():
    """CROP_DATABASE must contain at least 80 crops."""
    assert len(CROP_DATABASE) >= 80, f"Only {len(CROP_DATABASE)} crops found; expected >= 80"


def test_minimum_alias_count():
    """CROP_ALIASES must contain at least 50 aliases."""
    assert len(CROP_ALIASES) >= 50, f"Only {len(CROP_ALIASES)} aliases found"


def test_all_crops_have_required_fields():
    """Every crop entry must have all required FAO-56 fields."""
    required_fields = [
        "category", "kc_initial", "kc_mid", "kc_late",
        "root_depth_meters", "critical_depletion_fraction",
        "typical_yield_season_days",
    ]
    for crop_name, data in CROP_DATABASE.items():
        for field in required_fields:
            assert field in data, f"Crop '{crop_name}' is missing field '{field}'"


def test_all_crops_have_valid_kc_ranges():
    """All Kc values must be within physically plausible FAO-56 bounds (0.1 to 1.5)."""
    for crop_name, data in CROP_DATABASE.items():
        for kc_key in ["kc_initial", "kc_mid", "kc_late"]:
            kc = data[kc_key]
            assert 0.1 <= kc <= 1.5, (
                f"Crop '{crop_name}' has implausible {kc_key}={kc}; must be 0.1-1.5"
            )


def test_all_crops_have_positive_root_depth():
    """Root depth must be strictly positive."""
    for crop_name, data in CROP_DATABASE.items():
        assert data["root_depth_meters"] > 0, \
            f"Crop '{crop_name}' has non-positive root depth: {data['root_depth_meters']}"


def test_all_crops_have_valid_depletion_fraction():
    """Critical depletion fraction must be between 0.1 and 0.9."""
    for crop_name, data in CROP_DATABASE.items():
        p = data["critical_depletion_fraction"]
        assert 0.1 <= p <= 0.9, \
            f"Crop '{crop_name}' has implausible depletion fraction: {p}"


def test_all_crops_have_data_source():
    """Every crop must declare a data_source for provenance transparency."""
    for crop_name, data in CROP_DATABASE.items():
        assert "data_source" in data, f"Crop '{crop_name}' missing 'data_source'"
        assert data["data_source"] in [
            "FAO-56", "FAO-56 EST", "ICAR", "NEEDS CALIBRATION"
        ], f"Crop '{crop_name}' has unknown data_source: {data['data_source']}"


# ─────────────────────────────────────────────────────────────────
# Task 2: Alias Resolution Tests
# ─────────────────────────────────────────────────────────────────

ALIAS_TEST_CASES = [
    ("Rice", "Rice (Paddy)"),
    ("Paddy", "Rice (Paddy)"),
    ("Ragi", "Finger Millet (Ragi)"),
    ("Bajra", "Pearl Millet (Bajra)"),
    ("Jowar", "Sorghum (Jowar)"),
    ("Moong", "Green Gram"),
    ("Urad", "Black Gram"),
    ("Masoor", "Lentil"),
    ("Rajma", "Kidney Bean"),
    ("Chana", "Chickpea"),
    ("Bengal Gram", "Chickpea"),
    ("Sarson", "Mustard"),
    ("Canola", "Rapeseed"),
    ("Til", "Sesame"),
    ("Bhindi", "Okra"),
    ("Lady's Finger", "Okra"),
    ("Karela", "Bitter Gourd"),
    ("Lauki", "Bottle Gourd"),
    ("Eggplant", "Brinjal"),
    ("Shimla Mirchi", "Capsicum"),
    ("Lucerne", "Alfalfa"),
    ("Methi", "Fenugreek"),
    ("Jeera", "Cumin"),
    ("Haldi", "Turmeric"),
]


@pytest.mark.parametrize("alias,expected_canonical", ALIAS_TEST_CASES)
def test_crop_alias_resolution(alias, expected_canonical):
    """Crop aliases must resolve to their correct canonical CROP_DATABASE key."""
    resolved = resolve_crop_name(alias)
    assert resolved == expected_canonical, \
        f"Alias '{alias}' resolved to '{resolved}' instead of '{expected_canonical}'"


# ─────────────────────────────────────────────────────────────────
# Task 3: FAO-56 Kc Coefficient Tests
# ─────────────────────────────────────────────────────────────────

KC_TESTS = [
    # (crop, stage, expected_kc)
    ("Wheat", "Initial", 0.35),
    ("Wheat", "Mid-season", 1.15),
    ("Wheat", "Late", 0.40),
    ("Rice (Paddy)", "Initial", 1.05),
    ("Rice (Paddy)", "Mid-season", 1.20),
    ("Rice (Paddy)", "Late", 0.90),
    ("Maize", "Mid-season", 1.20),
    ("Cotton", "Mid-season", 1.20),
    ("Sugarcane", "Mid-season", 1.25),
    ("Tomato", "Mid-season", 1.15),
    ("Potato", "Mid-season", 1.15),
    ("Sunflower", "Mid-season", 1.15),
    ("Alfalfa", "Mid-season", 1.20),
    ("Banana", "Mid-season", 1.20),
    ("Grapes", "Mid-season", 0.85),
    ("Lentil", "Mid-season", 1.10),
    ("Strawberry", "Mid-season", 0.85),
    ("Pineapple", "Mid-season", 0.60),
]


@pytest.mark.parametrize("crop,stage,expected_kc", KC_TESTS)
def test_fao56_kc_values(crop, stage, expected_kc):
    """Key FAO-56 published Kc values must match exactly."""
    actual_kc = get_crop_kc(crop, stage)
    assert abs(actual_kc - expected_kc) < 0.001, \
        f"Kc mismatch for {crop}/{stage}: expected {expected_kc}, got {actual_kc}"


def test_kc_mid_always_greater_than_or_equal_initial_for_most_crops():
    """For standard crops, Kc-mid should generally be >= Kc-initial."""
    exceptions = set()  # crops known to violate this (none expected)
    violations = []
    for name, data in CROP_DATABASE.items():
        if name not in exceptions:
            if data["kc_mid"] < data["kc_initial"] - 0.05:
                violations.append(f"{name}: kc_initial={data['kc_initial']}, kc_mid={data['kc_mid']}")
    assert not violations, f"Unexpected Kc-mid < Kc-initial for: {violations}"


# ─────────────────────────────────────────────────────────────────
# Task 5: FAO-56 Calculation Engine Tests
# ─────────────────────────────────────────────────────────────────

def test_effective_rainfall_below_5mm_is_zero():
    """Rainfall < 5mm should contribute 0 effective mm (FAO/USDA method)."""
    assert calculate_effective_rainfall(0.0) == 0.0
    assert calculate_effective_rainfall(4.9) == 0.0
    assert calculate_effective_rainfall(5.0) == 0.0


def test_effective_rainfall_above_5mm_partial_credit():
    """Rainfall between 5-50mm: (rain-5) * 0.75."""
    result = calculate_effective_rainfall(25.0)
    expected = (25.0 - 5.0) * 0.75  # = 15.0
    assert abs(result - expected) < 0.01


def test_effective_rainfall_above_50mm_diminishing():
    """Rainfall > 50mm: 45*0.75 for first 50mm, then 50% for excess."""
    result = calculate_effective_rainfall(80.0)
    expected = (45.0 * 0.75) + ((80.0 - 50.0) * 0.50)  # = 33.75 + 15 = 48.75
    assert abs(result - expected) < 0.01


def test_water_volume_conversion():
    """1mm over 1 hectare = 10,000 litres."""
    result = calculate_irrigation_recommendation(
        crop_type="Wheat",
        growth_stage="Mid-season",
        area=1.0,
        area_unit="hectares",
        soil_type="Loamy",
        soil_moisture_pct=20.0,
        temperature_c=30.0,
        humidity_pct=50.0,
        wind_speed_kmh=10.0,
        rainfall_mm=0.0,
        reference_et0_mm=5.0,
        irrigation_method="Drip",
        ml_predicted_mm=None,
    )
    # GIR (mm) * 10,000 m2 = litres
    expected_litres = result["gross_irrigation_requirement_mm"] * 10000.0
    assert abs(result["water_requirement_litres"] - expected_litres) < 1.0, \
        f"Volume mismatch: {result['water_requirement_litres']} vs expected {expected_litres}"


def test_water_m3_conversion():
    """water_m3 = water_litres / 1000."""
    result = calculate_irrigation_recommendation(
        crop_type="Rice (Paddy)",
        growth_stage="Mid-season",
        area=2.0,
        area_unit="hectares",
        soil_type="Clay",
        soil_moisture_pct=35.0,
        temperature_c=32.0,
        humidity_pct=75.0,
        wind_speed_kmh=8.0,
        rainfall_mm=0.0,
        reference_et0_mm=6.0,
        irrigation_method="Surface/Flood",
    )
    assert abs(result["water_requirement_m3"] - result["water_requirement_litres"] / 1000.0) < 0.001


def test_zero_rainfall_no_effective_rainfall_credit():
    """Zero rainfall should give zero effective_rainfall_mm."""
    result = calculate_irrigation_recommendation(
        crop_type="Wheat",
        growth_stage="Mid-season",
        area=1.0,
        area_unit="hectares",
        soil_type="Loamy",
        soil_moisture_pct=25.0,
        temperature_c=28.0,
        humidity_pct=50.0,
        wind_speed_kmh=10.0,
        rainfall_mm=0.0,
        reference_et0_mm=5.0,
        irrigation_method="Drip",
    )
    assert result["effective_rainfall_mm"] == 0.0


def test_high_soil_moisture_reduces_irrigation():
    """Very high soil moisture should reduce or eliminate irrigation need."""
    result_wet = calculate_irrigation_recommendation(
        crop_type="Wheat", growth_stage="Mid-season", area=1.0, area_unit="hectares",
        soil_type="Loamy", soil_moisture_pct=90.0, temperature_c=25.0,
        humidity_pct=60.0, wind_speed_kmh=8.0, rainfall_mm=0.0, reference_et0_mm=4.0,
        irrigation_method="Drip",
    )
    result_dry = calculate_irrigation_recommendation(
        crop_type="Wheat", growth_stage="Mid-season", area=1.0, area_unit="hectares",
        soil_type="Loamy", soil_moisture_pct=5.0, temperature_c=25.0,
        humidity_pct=60.0, wind_speed_kmh=8.0, rainfall_mm=0.0, reference_et0_mm=4.0,
        irrigation_method="Drip",
    )
    assert result_wet["net_irrigation_requirement_mm"] <= result_dry["net_irrigation_requirement_mm"]


# ─────────────────────────────────────────────────────────────────
# Task 6: Category-Specific FAO-56 Calculation Tests
# ─────────────────────────────────────────────────────────────────

CATEGORY_SAMPLE_CROPS = [
    ("Wheat", "Cereals and Millets"),
    ("Chickpea", "Pulses and Legumes"),
    ("Sunflower", "Oilseed Crops"),
    ("Cotton", "Commercial and Fibre Crops"),
    ("Tomato", "Vegetables"),
    ("Banana", "Fruits"),
    ("Coffee", "Plantation and Spice Crops"),
    ("Alfalfa", "Fodder and Forage Crops"),
    ("Quinoa", "Other Agricultural Crops"),
]


@pytest.mark.parametrize("crop_name,expected_category", CATEGORY_SAMPLE_CROPS)
def test_crop_category_assignment(crop_name, expected_category):
    """Each sample crop must belong to its declared category."""
    assert crop_name in CROP_DATABASE, f"Crop '{crop_name}' not in CROP_DATABASE"
    actual = CROP_DATABASE[crop_name]["category"]
    assert actual == expected_category, \
        f"Category mismatch for '{crop_name}': expected '{expected_category}', got '{actual}'"


@pytest.mark.parametrize("crop_name,_", CATEGORY_SAMPLE_CROPS)
def test_category_crop_runs_calculation(crop_name, _):
    """Every category sample crop should produce a valid irrigation recommendation."""
    result = calculate_irrigation_recommendation(
        crop_type=crop_name,
        growth_stage="Mid-season",
        area=1.0,
        area_unit="hectares",
        soil_type="Loamy",
        soil_moisture_pct=25.0,
        temperature_c=28.0,
        humidity_pct=55.0,
        wind_speed_kmh=10.0,
        rainfall_mm=0.0,
        reference_et0_mm=5.0,
        irrigation_method="Drip",
    )
    assert result["water_requirement_litres"] >= 0
    assert result["crop_kc"] > 0
    assert result["crop_evapotranspiration_etc_mm"] > 0
    assert "urgency_level" in result
    assert result["water_requirement_m3"] == round(result["water_requirement_litres"] / 1000.0, 3)


# ─────────────────────────────────────────────────────────────────
# Task 7: CSV Dataset Processing & Row-Level Validation Tests
# ─────────────────────────────────────────────────────────────────

def test_csv_processing_valid_multi_crop_and_decimals():
    """CSV processing must support aliases, expanded crops, and decimal humidity."""
    import pandas as pd
    from backend.app.routes.dataset import _process_dataframe

    df = pd.DataFrame([
        {
            "crop_type": "Rice",  # alias -> Rice (Paddy)
            "growth_stage": "Mid-season",
            "area": 2.0,
            "area_unit": "hectares",
            "soil_type": "Clay",
            "soil_moisture_pct": 35.5,
            "temperature_c": 30.2,
            "humidity_pct": 53.9,
            "wind_speed_kmh": 8.4,
            "rainfall_mm": 0.0,
            "irrigation_method": "Surface/Flood",
        },
        {
            "crop_type": "Jowar",  # alias -> Sorghum (Jowar)
            "growth_stage": "Initial",
            "area": 1.5,
            "area_unit": "hectares",
            "soil_type": "Loamy",
            "soil_moisture_pct": 22.3,
            "temperature_c": 27.8,
            "humidity_pct": 65.5,
            "wind_speed_kmh": 11.2,
            "rainfall_mm": 2.5,
            "irrigation_method": "Drip",
        },
        {
            "crop_type": "Coffee",
            "growth_stage": "Mid-season",
            "area": 3.0,
            "area_unit": "hectares",
            "soil_type": "Loamy",
            "soil_moisture_pct": 28.0,
            "temperature_c": 24.5,
            "humidity_pct": 72.3,
            "wind_speed_kmh": 6.0,
            "rainfall_mm": 0.0,
            "irrigation_method": "Drip",
        },
    ])

    result = _process_dataframe(df, run_prediction_records=False)
    assert result["total_rows"] == 3
    assert result["processed_rows_count"] == 3
    assert result["failed_rows_count"] == 0
    assert result["row_errors"] == []
    assert result["total_water_required_litres"] > 0


def test_csv_processing_reports_row_level_errors():
    """Invalid crop names or out-of-range decimals must be reported in row_errors."""
    import pandas as pd
    from backend.app.routes.dataset import _process_dataframe

    df = pd.DataFrame([
        {
            "crop_type": "Wheat",
            "growth_stage": "Mid-season",
            "soil_type": "Loamy",
            "soil_moisture_pct": 25.0,
            "temperature_c": 28.0,
            "humidity_pct": 53.9,
        },
        {
            "crop_type": "NonExistentCropXYZ",
            "growth_stage": "Mid-season",
            "soil_type": "Loamy",
            "soil_moisture_pct": 25.0,
            "temperature_c": 28.0,
            "humidity_pct": 150.0,  # out of range
        },
    ])

    result = _process_dataframe(df, run_prediction_records=False)
    assert result["total_rows"] == 2
    assert result["processed_rows_count"] == 1
    assert result["failed_rows_count"] == 1
    assert len(result["row_errors"]) == 1
    assert result["row_errors"][0]["row"] == 2
    assert any("Unsupported crop_type" in e for e in result["row_errors"][0]["errors"])
    assert any("humidity_pct" in e for e in result["row_errors"][0]["errors"])


def test_ml_blend_no_double_efficiency_division():
    """ML prediction is already GIR; verify blending does not double-divide by efficiency."""
    # For Wheat (ML-trained) with Surface/Flood (60% eff), base_gir = base_nir / 0.60
    # If ml_predicted_mm == base_gir, blended gir_mm should equal base_gir (not base_gir / 0.60!)
    res_phys = calculate_irrigation_recommendation(
        crop_type="Wheat", growth_stage="Mid-season", area=1.0, area_unit="hectares",
        soil_type="Loamy", soil_moisture_pct=20.0, temperature_c=28.0,
        humidity_pct=50.0, wind_speed_kmh=10.0, rainfall_mm=0.0, reference_et0_mm=5.0,
        irrigation_method="Surface/Flood", ml_predicted_mm=None,
    )
    base_gir = res_phys["gross_irrigation_requirement_mm"]
    res_ml = calculate_irrigation_recommendation(
        crop_type="Wheat", growth_stage="Mid-season", area=1.0, area_unit="hectares",
        soil_type="Loamy", soil_moisture_pct=20.0, temperature_c=28.0,
        humidity_pct=50.0, wind_speed_kmh=10.0, rainfall_mm=0.0, reference_et0_mm=5.0,
        irrigation_method="Surface/Flood", ml_predicted_mm=base_gir,
    )
    assert abs(res_ml["gross_irrigation_requirement_mm"] - base_gir) < 0.05


def test_newly_added_crop_uses_pure_fao56_balance_not_untrained_ml():
    """Newly added crops not in ML_TRAINED_CROPS must not be distorted by untrained ML."""
    res_none = calculate_irrigation_recommendation(
        crop_type="Pineapple", growth_stage="Mid-season", area=1.0, area_unit="hectares",
        soil_type="Loamy", soil_moisture_pct=20.0, temperature_c=28.0,
        humidity_pct=50.0, wind_speed_kmh=10.0, rainfall_mm=0.0, reference_et0_mm=5.0,
        irrigation_method="Drip", ml_predicted_mm=None,
    )
    res_with_ml = calculate_irrigation_recommendation(
        crop_type="Pineapple", growth_stage="Mid-season", area=1.0, area_unit="hectares",
        soil_type="Loamy", soil_moisture_pct=20.0, temperature_c=28.0,
        humidity_pct=50.0, wind_speed_kmh=10.0, rainfall_mm=0.0, reference_et0_mm=5.0,
        irrigation_method="Drip", ml_predicted_mm=25.0,  # extreme out-of-distribution ML value
    )
    assert res_with_ml["gross_irrigation_requirement_mm"] == res_none["gross_irrigation_requirement_mm"]
    assert any("ML Generalization Notice" in r for r in res_with_ml["recommendations"])
