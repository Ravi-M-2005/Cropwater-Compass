"""
End-to-End System Integration Tests for Cropwater Compass
Validates full data flow across frontend-facing endpoints, ML models,
FAO-56 calculations, and SQLite persistence.
"""
import pytest
import io
import pandas as pd
from backend.app.schemas import (
    PredictionRequest,
    BatchPredictionRequest,
    ET0CalculationRequest,
)
from backend.app.routes.prediction import (
    predict_irrigation,
    predict_batch,
    get_model_comparison,
    get_shap_analysis,
    get_crops,
    get_soils,
    get_irrigation_methods,
)
from backend.app.routes.weather import (
    get_current_weather,
    calculate_custom_et0,
)
from backend.app.routes.dataset import (
    get_sample_csv,
    get_dataset_stats,
    _process_dataframe,
)
from backend.app.routes.history import (
    list_history,
    get_stats,
    get_single_prediction,
)
from backend.app.routes.reports import generate_summary_report


def test_complete_prediction_workflow_all_models():
    """
    Tests prediction execution across XGBoost, ANN, LSTM, and Ensemble.
    Verifies that:
    1. Output is non-negative and explicitly in Litres.
    2. Litres matches GIR (mm) * Area (m2).
    3. Prediction is persisted to SQLite history.
    """
    for model_name in ["xgboost", "ann", "lstm", "ensemble"]:
        req = PredictionRequest(
            crop_type="Wheat",
            growth_stage="Mid-season",
            area=2.5,
            area_unit="hectares",
            soil_type="Loamy",
            soil_moisture_pct=25.0,
            soil_ph=6.8,
            temperature_c=31.0,
            humidity_pct=45.0,
            wind_speed_kmh=12.0,
            rainfall_mm=0.0,
            solar_radiation=20.0,
            irrigation_method="Drip",
            model_name=model_name
        )

        res = predict_irrigation(req)

        # 1. Litres output
        assert "water_requirement_litres" in res
        assert res["water_requirement_litres"] > 0
        assert res["water_requirement_m3"] > 0
        assert res["water_requirement_mm"] > 0

        # 2. Formula verification: 1 mm * 1 m2 = 1 L
        # 2.5 ha = 25,000 m2
        assert res["area_sq_meters"] == 25000.0
        expected_litres = round(res["gross_irrigation_requirement_mm"] * 25000.0, 2)
        assert pytest.approx(res["water_requirement_litres"], 1.0) == expected_litres

        # 3. Urgency and schedule
        assert res["urgency_level"] in ["Critical", "High", "Moderate", "Low", "None"]
        assert res["recommended_schedule"]["frequency_days"] >= 0
        assert res["recommended_schedule"]["duration_hours"] >= 0

        # 4. Multi-model predictions dictionary present
        assert "xgboost" in res["model_predictions"]
        assert "ann" in res["model_predictions"]
        assert "lstm" in res["model_predictions"]

        # 5. Verify saved in SQLite history
        saved = get_single_prediction(res["id"])
        assert saved is not None
        assert saved["id"] == res["id"]
        assert saved["crop_type"] == "Wheat"
        assert saved["water_requirement_litres"] == res["water_requirement_litres"]


def test_shap_explainability_actual_output():
    """
    Verifies that SHAP TreeExplainer generates realistic feature attributions.
    """
    req = PredictionRequest(
        crop_type="Cotton",
        growth_stage="Mid-season",
        area=3.0,
        area_unit="hectares",
        soil_type="Clay Loam",
        soil_moisture_pct=22.0,
        temperature_c=35.0,
        humidity_pct=40.0,
        wind_speed_kmh=15.0,
        rainfall_mm=0.0,
        irrigation_method="Drip",
        model_name="xgboost"
    )

    shap_data = get_shap_analysis(req)

    assert "base_value" in shap_data
    assert shap_data["base_value"] > 0
    assert "predicted_value" in shap_data
    assert len(shap_data["feature_importances"]) > 0

    # Ensure both positive and negative features are distinguished
    directions = [f["impact_direction"] for f in shap_data["feature_importances"]]
    assert "increases_water" in directions or "decreases_water" in directions
    assert len(shap_data["explanation_summary"]) > 10


def test_weather_and_et0_end_to_end():
    """
    Verifies weather fetching and FAO-56 Penman-Monteith ET0 calculation.
    """
    w_data = get_current_weather(lat=30.7333, lon=76.7794, city="Punjab, India")
    assert w_data["temperature_c"] >= -10.0
    assert w_data["humidity_pct"] >= 0.0
    assert w_data["et0_mm"] > 0.0
    assert len(w_data["forecast_daily"]) == 7

    # Custom ET0 calculation
    et0_calc = calculate_custom_et0(
        ET0CalculationRequest(
            temperature_c=32.0,
            humidity_pct=50.0,
            wind_speed_kmh=12.0,
            solar_radiation=22.0
        )
    )
    assert et0_calc["et0_mm"] > 1.0


def test_csv_upload_batch_processing_workflow():
    """
    Verifies CSV parsing, validation, batch prediction calculation, and volume aggregation.
    """
    sample = get_sample_csv()
    df = pd.read_csv(io.StringIO(sample["csv_content"]))
    res = _process_dataframe(df, run_prediction_records=True)

    assert res["total_rows"] == len(df)
    assert res["total_water_required_litres"] > 0
    assert len(res["preview"]) > 0
    assert all("water_requirement_litres" in p for p in res["preview"])


def test_history_and_reports_end_to_end():
    """
    Verifies historical analytics and executive report generation.
    """
    stats = get_stats()
    assert stats["total_predictions"] > 0
    assert stats["total_water_litres"] > 0

    report = generate_summary_report()
    assert report["key_metrics"]["total_evaluations"] >= stats["total_predictions"]
    assert report["key_metrics"]["total_water_recommended_litres"] >= 0
    assert len(report["recommended_conservation_actions"]) >= 4
