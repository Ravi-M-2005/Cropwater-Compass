"""
Comprehensive Unit and Integration Tests for Cropwater Compass Backend Routes and Endpoints
"""
import pytest
from backend.app.schemas import (
    PredictionRequest,
    BatchPredictionRequest,
    ET0CalculationRequest,
)
from backend.app.main import root, health_check, get_stats_alias
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
    get_preset_locations,
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
    delete_single_prediction,
    clear_all_history,
)
from backend.app.routes.reports import generate_summary_report
import pandas as pd


def test_root_and_health_routes():
    r = root()
    assert r["project"] == "Cropwater Compass"
    assert "target_output" in r

    h = health_check()
    assert h["status"] == "healthy"
    assert h["database"] == "sqlite_ready"

    s = get_stats_alias()
    assert "total_predictions" in s
    assert s["total_predictions"] >= 0


def test_crops_metadata():
    crops = get_crops()
    assert len(crops) >= 8
    crop_names = [c["name"] for c in crops]
    assert "Wheat" in crop_names
    assert "Rice" in crop_names
    assert "Maize" in crop_names


def test_soils_metadata():
    soils = get_soils()
    assert len(soils) >= 5
    soil_names = [s["name"] for s in soils]
    assert "Loamy" in soil_names
    assert "Sandy" in soil_names
    assert "Clay" in soil_names


def test_irrigation_methods_metadata():
    methods = get_irrigation_methods()
    assert len(methods) >= 3
    method_names = [m["name"] for m in methods]
    assert "Drip" in method_names
    assert "Sprinkler" in method_names


def test_predict_irrigation_output_in_litres():
    req = PredictionRequest(
        crop_type="Wheat",
        growth_stage="Mid-season",
        area=2.0,
        area_unit="hectares",
        soil_type="Loamy",
        soil_moisture_pct=26.0,
        temperature_c=29.0,
        humidity_pct=48.0,
        wind_speed_kmh=12.0,
        rainfall_mm=0.0,
        irrigation_method="Drip",
        model_name="xgboost"
    )

    res = predict_irrigation(req)

    # Core requirement: Output must be estimated water requirement in litres
    assert "water_requirement_litres" in res
    assert res["water_requirement_litres"] > 0
    assert "water_requirement_m3" in res
    assert "water_requirement_mm" in res
    assert res["area_sq_meters"] == 20000.0  # 2 ha = 20,000 m2
    assert res["model_used"] == "xgboost"
    assert res["irrigation_recommended"] in [True, False]
    assert "recommended_schedule" in res
    assert "urgency_level" in res
    assert "id" in res


def test_batch_prediction():
    req = BatchPredictionRequest(
        records=[
            PredictionRequest(
                crop_type="Wheat",
                growth_stage="Mid-season",
                area=1.0,
                area_unit="hectares",
                soil_type="Loamy",
                soil_moisture_pct=30.0,
                temperature_c=28.0,
                humidity_pct=50.0,
                wind_speed_kmh=10.0,
                rainfall_mm=0.0,
                irrigation_method="Drip"
            ),
            PredictionRequest(
                crop_type="Tomato",
                growth_stage="Vegetative",
                area=0.5,
                area_unit="hectares",
                soil_type="Sandy Loam",
                soil_moisture_pct=22.0,
                temperature_c=27.0,
                humidity_pct=60.0,
                wind_speed_kmh=8.0,
                rainfall_mm=0.0,
                irrigation_method="Drip"
            )
        ]
    )

    res = predict_batch(req)
    assert res["total_records"] == 2
    assert res["total_water_litres"] > 0
    assert len(res["predictions"]) == 2


def test_model_comparison_structure():
    comp = get_model_comparison()
    assert "models" in comp
    assert len(comp["models"]) == 3
    names = [m["model_name"] for m in comp["models"]]
    assert any("XGBoost" in n for n in names)
    assert any("ANN" in n for n in names)
    assert any("LSTM" in n for n in names)


def test_shap_feature_importance():
    req = PredictionRequest(
        crop_type="Maize",
        growth_stage="Mid-season",
        area=1.5,
        area_unit="hectares",
        soil_type="Sandy Loam",
        soil_moisture_pct=24.0,
        temperature_c=32.0,
        humidity_pct=42.0,
        wind_speed_kmh=14.0,
        rainfall_mm=0.0,
        irrigation_method="Sprinkler"
    )
    shap_res = get_shap_analysis(req)
    assert "feature_importances" in shap_res
    assert len(shap_res["feature_importances"]) > 0
    assert "base_value" in shap_res
    assert "predicted_value" in shap_res


def test_weather_and_et0_routes():
    weather = get_current_weather(lat=28.6139, lon=77.2090, city="New Delhi")
    assert weather["temperature_c"] is not None
    assert weather["humidity_pct"] is not None
    assert weather["et0_mm"] > 0
    assert len(weather["forecast_daily"]) == 7

    et0_calc = calculate_custom_et0(
        ET0CalculationRequest(
            temperature_c=32.0,
            humidity_pct=45.0,
            wind_speed_kmh=15.0,
            solar_radiation=22.0
        )
    )
    assert et0_calc["et0_mm"] > 0


def test_dataset_routes():
    sample = get_sample_csv()
    assert "cropwater_sample_dataset.csv" in sample["filename"]
    assert "crop_type,growth_stage" in sample["csv_content"]

    stats = get_dataset_stats()
    assert stats["total_samples"] > 0

    # Test processing small dataframe
    df = pd.DataFrame([
        {
            "crop_type": "Wheat",
            "growth_stage": "Mid-season",
            "area": 1.0,
            "soil_type": "Loamy",
            "soil_moisture_pct": 28.0,
            "temperature_c": 28.0,
            "humidity_pct": 50.0
        }
    ])
    df_res = _process_dataframe(df, run_prediction_records=False)
    assert df_res["total_rows"] == 1
    assert df_res["total_water_required_litres"] > 0


def test_history_and_reports():
    # Retrieve stats
    stats = get_stats()
    assert "total_predictions" in stats
    assert stats["total_predictions"] >= 1

    # Retrieve history list
    history_items = list_history(limit=10)
    assert len(history_items) >= 1
    first_id = history_items[0]["id"]

    single = get_single_prediction(first_id)
    assert single["id"] == first_id

    # Report generation
    report = generate_summary_report()
    assert "Cropwater Compass" in report["title"]
    assert "key_metrics" in report
    assert report["key_metrics"]["total_water_recommended_litres"] >= 0
