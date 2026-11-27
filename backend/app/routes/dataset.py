"""
Dataset Management & CSV Upload API Routes
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Any, List, Optional
import io
import pandas as pd

from backend.app.services.irrigation import (
    CROP_DATABASE,
    CROP_ALIASES,
    SOIL_DATABASE,
    resolve_crop_name,
    calculate_irrigation_recommendation,
    convert_area_to_sq_meters
)
from backend.app.services.weather import calculate_fao56_et0
from backend.app.services.ml_service import predict_water_requirements
from backend.app.services.history import save_prediction

router = APIRouter(prefix="/api/dataset", tags=["Dataset"])

REQUIRED_COLUMNS = [
    "crop_type", "growth_stage", "soil_type",
    "soil_moisture_pct", "temperature_c", "humidity_pct"
]


def _process_dataframe(df: pd.DataFrame, run_prediction_records: bool = True) -> Dict[str, Any]:
    """Validates dataframe columns and optionally processes predictions."""
    # Standardize column headers
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded CSV is missing mandatory columns: {', '.join(missing)}. "
                   f"Required columns are: {', '.join(REQUIRED_COLUMNS)}"
        )

    # Fill defaults for optional columns
    if "area" not in df.columns:
        df["area"] = 1.0
    if "area_unit" not in df.columns:
        df["area_unit"] = "hectares"
    if "wind_speed_kmh" not in df.columns:
        df["wind_speed_kmh"] = 10.0
    if "rainfall_mm" not in df.columns:
        df["rainfall_mm"] = 0.0
    if "solar_radiation" not in df.columns:
        df["solar_radiation"] = 18.0
    if "irrigation_method" not in df.columns:
        df["irrigation_method"] = "Drip"

    known_crops_lower = {k.lower() for k in CROP_DATABASE} | {k.lower() for k in CROP_ALIASES}

    processed_rows = []
    row_errors: List[Dict[str, Any]] = []
    total_water_litres = 0.0

    for idx, row in df.head(100).iterrows():  # process up to 100 rows in preview/batch
        row_num = int(idx) + 1
        errors_for_row: List[str] = []

        raw_crop = str(row.get("crop_type", "")).strip()
        if not raw_crop or raw_crop.lower() == "nan":
            errors_for_row.append("Missing crop_type.")
            crop = ""
        elif raw_crop.lower() not in known_crops_lower:
            errors_for_row.append(f"Unsupported crop_type '{raw_crop}'.")
            crop = raw_crop
        else:
            crop = resolve_crop_name(raw_crop)

        stage = str(row.get("growth_stage", "Mid-season")).strip()
        if not stage or stage.lower() == "nan":
            errors_for_row.append("Missing growth_stage.")

        soil = str(row.get("soil_type", "Loamy")).strip()
        if not soil or soil.lower() == "nan":
            errors_for_row.append("Missing soil_type.")

        unit = str(row.get("area_unit", "hectares")).strip()
        method = str(row.get("irrigation_method", "Drip")).strip()

        def _parse_float(col_name: str, default: Optional[float] = None) -> Optional[float]:
            val = row.get(col_name, default)
            if pd.isna(val):
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                errors_for_row.append(f"Invalid numeric value for {col_name}: '{val}'.")
                return None

        area = _parse_float("area", 1.0)
        moisture = _parse_float("soil_moisture_pct")
        temp = _parse_float("temperature_c")
        hum = _parse_float("humidity_pct")
        wind = _parse_float("wind_speed_kmh", 10.0)
        rain = _parse_float("rainfall_mm", 0.0)
        solar = _parse_float("solar_radiation", 18.0)
        et0_raw = _parse_float("et0_mm", None) if "et0_mm" in df.columns else None

        if area is not None and area <= 0:
            errors_for_row.append(f"area must be > 0 (got {area}).")
        if moisture is None or not (0.0 <= moisture <= 100.0):
            errors_for_row.append(f"soil_moisture_pct must be between 0 and 100 (got {moisture}).")
        if temp is None or not (-20.0 <= temp <= 60.0):
            errors_for_row.append(f"temperature_c must be between -20 and 60 (got {temp}).")
        if hum is None or not (0.0 <= hum <= 100.0):
            errors_for_row.append(f"humidity_pct must be between 0 and 100 (got {hum}).")
        if wind is not None and wind < 0:
            errors_for_row.append(f"wind_speed_kmh cannot be negative (got {wind}).")
        if rain is not None and rain < 0:
            errors_for_row.append(f"rainfall_mm cannot be negative (got {rain}).")

        if errors_for_row:
            row_errors.append({"row": row_num, "crop_type": raw_crop, "errors": errors_for_row})
            continue

        et0 = et0_raw if (et0_raw is not None and et0_raw > 0) else calculate_fao56_et0(
            temp_c=temp,
            humidity_pct=hum,
            wind_speed_kmh=wind,
            solar_radiation_mj=solar
        )

        rec_dict = {
            "crop_type": crop,
            "growth_stage": stage,
            "soil_type": soil,
            "soil_moisture_pct": moisture,
            "temperature_c": temp,
            "humidity_pct": hum,
            "wind_speed_kmh": wind,
            "rainfall_mm": rain,
            "solar_radiation": solar,
            "et0_mm": et0,
            "irrigation_method": method
        }

        primary_mm, _ = predict_water_requirements(rec_dict)
        irr_result = calculate_irrigation_recommendation(
            crop_type=crop,
            growth_stage=stage,
            area=area,
            area_unit=unit,
            soil_type=soil,
            soil_moisture_pct=moisture,
            temperature_c=temp,
            humidity_pct=hum,
            wind_speed_kmh=wind,
            rainfall_mm=rain,
            reference_et0_mm=et0,
            irrigation_method=method,
            ml_predicted_mm=primary_mm
        )

        if run_prediction_records:
            save_prediction(irr_result)

        total_water_litres += irr_result["water_requirement_litres"]
        processed_rows.append(irr_result)

    crops_summary = df["crop_type"].value_counts().to_dict()
    soils_summary = df["soil_type"].value_counts().to_dict()

    return {
        "total_rows": len(df),
        "processed_rows_count": len(processed_rows),
        "failed_rows_count": len(row_errors),
        "row_errors": row_errors,
        "total_water_required_litres": round(total_water_litres, 2),
        "crops_distribution": crops_summary,
        "soils_distribution": soils_summary,
        "preview": processed_rows[:10]
    }


@router.post("/upload")
async def upload_dataset_csv(file: UploadFile = File(...)):
    """
    Accepts CSV dataset upload, parses agricultural variables,
    evaluates water requirements, and saves results into prediction history.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {e}")

    return _process_dataframe(df, run_prediction_records=True)


@router.get("/sample")
def get_sample_csv():
    """Returns sample CSV formatted text for users to copy or test."""
    sample_data = (
        "crop_type,growth_stage,area,area_unit,soil_type,soil_moisture_pct,temperature_c,humidity_pct,wind_speed_kmh,rainfall_mm,irrigation_method\n"
        "Wheat,Mid-season,2.5,hectares,Loamy,32.0,28.5,52.3,11.4,0.0,Drip\n"
        "Rice (Paddy),Vegetative,4.0,hectares,Clay,45.0,31.0,78.5,8.2,12.0,Surface/Flood\n"
        "Maize,Initial,1.5,hectares,Sandy Loam,22.0,26.0,48.7,14.0,0.0,Sprinkler\n"
        "Cotton,Mid-season,5.0,hectares,Clay Loam,29.0,34.0,40.0,15.2,0.0,Drip\n"
        "Sugarcane,Mid-season,3.0,hectares,Loamy,35.0,32.5,65.5,9.0,5.0,Surface/Flood\n"
        "Tomato,Late,0.8,hectares,Silty,28.0,27.0,55.0,10.5,0.0,Drip\n"
        "Potato,Vegetative,1.2,hectares,Sandy Loam,25.0,22.0,53.9,12.0,2.0,Sprinkler\n"
        "Soybean,Mid-season,3.5,hectares,Loamy,30.0,29.0,58.0,11.0,0.0,Drip\n"
        "Chickpea,Mid-season,2.0,hectares,Loamy,24.0,20.0,45.0,8.0,0.0,Drip\n"
        "Groundnut,Mid-season,1.8,hectares,Sandy Loam,26.0,33.0,72.3,10.0,3.0,Sprinkler\n"
        "Pearl Millet (Bajra),Mid-season,2.5,hectares,Sandy,18.0,38.0,35.0,16.0,0.0,Drip\n"
        "Finger Millet (Ragi),Mid-season,1.0,hectares,Loamy,28.0,25.0,60.0,9.5,0.0,Drip\n"
    )
    return {
        "filename": "cropwater_sample_dataset.csv",
        "csv_content": sample_data
    }


@router.get("/stats")
def get_dataset_stats():
    """Returns metadata about the benchmark training dataset."""
    return {
        "dataset_name": "Cropwater-Compass FAO-56 Synthetic Irrigation Benchmark",
        "total_samples": 5000,
        "features": [
            "crop_type", "growth_stage", "soil_type", "soil_moisture_pct",
            "soil_ph", "temperature_c", "humidity_pct", "wind_speed_kmh",
            "rainfall_mm", "solar_radiation", "et0_mm", "irrigation_method"
        ],
        "target": "water_requirement_mm",
        "supported_crops_count": len(CROP_DATABASE),
        "supported_soils_count": len(SOIL_DATABASE),
        "standard_reference": "FAO Irrigation and Drainage Paper No. 56 (CROPWAT)",
        "synthetic_notice": "Training and benchmark datasets are synthetically generated according to FAO-56 Penman-Monteith physical equations and empirical agronomic distributions."
    }
