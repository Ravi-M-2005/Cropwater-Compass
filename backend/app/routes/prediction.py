"""
Prediction and Agronomic API Routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from backend.app.schemas.schemas import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    ModelsComparisonResponse,
    ShapExplanationResponse,
    CropInfo,
    SoilInfo,
    IrrigationMethodInfo
)
from backend.app.services.irrigation import (
    CROP_DATABASE,
    SOIL_DATABASE,
    IRRIGATION_METHODS,
    calculate_irrigation_recommendation
)
from backend.app.services.weather import calculate_fao56_et0
from backend.app.services.ml_service import (
    predict_water_requirements,
    get_shap_explanation,
    get_models_benchmark_metrics
)
from backend.app.services.history import save_prediction

router = APIRouter(prefix="/api", tags=["Prediction"])


@router.post("/predict", response_model=PredictionResponse)
def predict_irrigation(request: PredictionRequest):
    """
    Predicts required irrigation water amount in Litres for a specific crop and farm setup.
    Combines machine learning regressors with FAO-56 CROPWAT agronomic guidelines.
    """
    # 1. Resolve ET0 if not explicitly supplied
    et0 = request.et0_mm
    if et0 is None or et0 <= 0:
        et0 = calculate_fao56_et0(
            temp_c=request.temperature_c,
            humidity_pct=request.humidity_pct,
            wind_speed_kmh=request.wind_speed_kmh,
            solar_radiation_mj=request.solar_radiation
        )

    # 2. ML Model inference
    input_dict = request.model_dump()
    input_dict["et0_mm"] = et0
    primary_predicted_mm, all_model_predictions = predict_water_requirements(input_dict)

    # 3. Calculate full agronomic recommendation & exact litres
    result = calculate_irrigation_recommendation(
        crop_type=request.crop_type,
        growth_stage=request.growth_stage,
        area=request.area,
        area_unit=request.area_unit,
        soil_type=request.soil_type,
        soil_moisture_pct=request.soil_moisture_pct,
        temperature_c=request.temperature_c,
        humidity_pct=request.humidity_pct,
        wind_speed_kmh=request.wind_speed_kmh,
        rainfall_mm=request.rainfall_mm,
        reference_et0_mm=et0,
        irrigation_method=request.irrigation_method,
        ml_predicted_mm=primary_predicted_mm
    )

    result["model_used"] = request.model_name or "xgboost"
    result["model_predictions"] = all_model_predictions

    # 4. Save to persistent history database
    pred_id = save_prediction(result)
    result["id"] = pred_id

    return result


@router.post("/predict/batch", response_model=BatchPredictionResponse)
def predict_batch(request: BatchPredictionRequest):
    """
    Runs batch predictions for a list of farm plots or seasonal crop schedules.
    """
    predictions = []
    total_water = 0.0

    for rec in request.records:
        et0 = rec.et0_mm or calculate_fao56_et0(
            temp_c=rec.temperature_c,
            humidity_pct=rec.humidity_pct,
            wind_speed_kmh=rec.wind_speed_kmh,
            solar_radiation_mj=rec.solar_radiation
        )
        rec_dict = rec.model_dump()
        rec_dict["et0_mm"] = et0
        primary_mm, all_preds = predict_water_requirements(rec_dict)

        single_res = calculate_irrigation_recommendation(
            crop_type=rec.crop_type,
            growth_stage=rec.growth_stage,
            area=rec.area,
            area_unit=rec.area_unit,
            soil_type=rec.soil_type,
            soil_moisture_pct=rec.soil_moisture_pct,
            temperature_c=rec.temperature_c,
            humidity_pct=rec.humidity_pct,
            wind_speed_kmh=rec.wind_speed_kmh,
            rainfall_mm=rec.rainfall_mm,
            reference_et0_mm=et0,
            irrigation_method=rec.irrigation_method,
            ml_predicted_mm=primary_mm
        )
        single_res["model_used"] = rec.model_name or "xgboost"
        single_res["model_predictions"] = all_preds
        pred_id = save_prediction(single_res)
        single_res["id"] = pred_id

        total_water += single_res["water_requirement_litres"]
        predictions.append(single_res)

    return {
        "total_records": len(predictions),
        "total_water_litres": round(total_water, 2),
        "predictions": predictions
    }


@router.get("/models/comparison", response_model=ModelsComparisonResponse)
def get_model_comparison():
    """
    Returns comparative evaluation metrics (R2, RMSE, MAE, latency) for XGBoost, ANN, and LSTM models.
    """
    return get_models_benchmark_metrics()


@router.post("/explainability/shap", response_model=ShapExplanationResponse)
def get_shap_analysis(request: PredictionRequest):
    """
    Computes SHAP-based feature importance breakdown showing which parameters
    drive the water requirement up or down for the specific farm condition.
    """
    req_dict = request.model_dump()
    if not req_dict.get("et0_mm"):
        req_dict["et0_mm"] = calculate_fao56_et0(
            temp_c=request.temperature_c,
            humidity_pct=request.humidity_pct,
            wind_speed_kmh=request.wind_speed_kmh,
            solar_radiation_mj=request.solar_radiation
        )
    return get_shap_explanation(req_dict)


@router.get("/crops", response_model=List[CropInfo])
def get_crops():
    """Returns database of supported crops with Kc coefficients and root depths."""
    crop_list = []
    for name, data in CROP_DATABASE.items():
        crop_list.append({
            "name": name,
            "category": data["category"],
            "kc_initial": data["kc_initial"],
            "kc_mid": data["kc_mid"],
            "kc_late": data["kc_late"],
            "root_depth_meters": data["root_depth_meters"],
            "critical_depletion_fraction": data["critical_depletion_fraction"],
            "typical_yield_season_days": data["typical_yield_season_days"]
        })
    return crop_list


@router.get("/soils", response_model=List[SoilInfo])
def get_soils():
    """Returns physical properties for all supported agricultural soil types."""
    soil_list = []
    for name, data in SOIL_DATABASE.items():
        soil_list.append({
            "name": name,
            "field_capacity_pct": data["field_capacity_pct"],
            "wilting_point_pct": data["wilting_point_pct"],
            "available_water_capacity_mm_per_m": data["available_water_capacity_mm_per_m"],
            "infiltration_rate_mm_per_hr": data["infiltration_rate_mm_per_hr"],
            "description": data["description"]
        })
    return soil_list


@router.get("/irrigation-methods", response_model=List[IrrigationMethodInfo])
def get_irrigation_methods():
    """Returns supported irrigation delivery methods with operational efficiency ratings."""
    method_list = []
    for name, data in IRRIGATION_METHODS.items():
        method_list.append({
            "name": name,
            "efficiency_pct": data["efficiency_pct"],
            "typical_pressure_bar": data["typical_pressure_bar"],
            "suitable_crops": data["suitable_crops"],
            "description": data["description"]
        })
    return method_list
