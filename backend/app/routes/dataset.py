"""
Dataset Management & CSV Upload API Routes
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Any, List, Optional
import io
import pandas as pd

from backend.app.services.irrigation import (
    CROP_DATABASE,
    SOIL_DATABASE,
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
    if "et0_mm" not in df.columns:
        df["et0_mm"] = df.apply(
            lambda r: calculate_fao56_et0(
                temp_c=float(r["temperature_c"]),
                humidity_pct=float(r["humidity_pct"]),
                wind_speed_kmh=float(r["wind_speed_kmh"]),
                solar_radiation_mj=float(r.get("solar_radiation", 18.0))
            ), axis=1
        )
    if "irrigation_method" not in df.columns:
        df["irrigation_method"] = "Drip"

    processed_rows = []
    total_water_litres = 0.0

    for idx, row in df.head(100).iterrows():  # process up to 100 rows in preview/batch
        crop = str(row["crop_type"])
        stage = str(row["growth_stage"])
        area = float(row["area"])
        unit = str(row["area_unit"])
        soil = str(row["soil_type"])
        moisture = float(row["soil_moisture_pct"])
        temp = float(row["temperature_c"])
        hum = float(row["humidity_pct"])
        wind = float(row["wind_speed_kmh"])
        rain = float(row["rainfall_mm"])
        et0 = float(row["et0_mm"])
        method = str(row["irrigation_method"])

        rec_dict = {
            "crop_type": crop,
            "growth_stage": stage,
            "soil_type": soil,
            "soil_moisture_pct": moisture,
            "temperature_c": temp,
            "humidity_pct": hum,
            "wind_speed_kmh": wind,
            "rainfall_mm": rain,
            "solar_radiation": float(row.get("solar_radiation", 18.0)),
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
        "Wheat,Mid-season,2.5,hectares,Loamy,32.0,28.5,52.0,11.4,0.0,Drip\n"
        "Rice,Vegetative,4.0,hectares,Clay,45.0,31.0,78.0,8.2,12.0,Surface/Flood\n"
        "Maize,Initial,1.5,hectares,Sandy Loam,22.0,26.0,48.0,14.0,0.0,Sprinkler\n"
        "Cotton,Mid-season,5.0,hectares,Clay Loam,29.0,34.0,40.0,15.2,0.0,Drip\n"
        "Sugarcane,Mid-season,3.0,hectares,Loamy,35.0,32.5,60.0,9.0,5.0,Surface/Flood\n"
        "Tomato,Late,0.8,hectares,Silty,28.0,27.0,55.0,10.5,0.0,Drip\n"
        "Potato,Vegetative,1.2,hectares,Sandy Loam,25.0,22.0,65.0,12.0,2.0,Sprinkler\n"
        "Soybean,Mid-season,3.5,hectares,Loamy,30.0,29.0,58.0,11.0,0.0,Drip\n"
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
