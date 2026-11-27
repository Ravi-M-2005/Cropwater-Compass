"""
Dataset Management & CSV Upload API Routes
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Any, List, Optional, Callable
import hashlib
import io
import threading
import time
import uuid
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
from backend.app.services.ml_service import (
    predict_water_requirements,
    predict_water_requirements_batch
)
from backend.app.services.history import save_prediction, save_predictions_batch

router = APIRouter(prefix="/api/dataset", tags=["Dataset"])

REQUIRED_COLUMNS = [
    "crop_type", "growth_stage", "soil_type",
    "soil_moisture_pct", "temperature_c", "humidity_pct"
]


_UPLOAD_JOBS: Dict[str, Dict[str, Any]] = {}
_JOBS_LOCK = threading.Lock()


def _normalize_and_validate_df(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes CSV column headers and validates mandatory columns."""
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

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

    return df


def _process_dataframe(
    df: pd.DataFrame,
    run_prediction_records: bool = True,
    upload_id: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, int], None]] = None,
) -> Dict[str, Any]:
    """Validates dataframe columns and optionally processes predictions."""
    df = _normalize_and_validate_df(df)

    known_crops_lower = {k.lower() for k in CROP_DATABASE} | {k.lower() for k in CROP_ALIASES}

    MAX_BATCH_ROWS = 100_000
    CHUNK_SIZE = 5000

    total_rows = len(df)
    rows_to_process = df.head(MAX_BATCH_ROWS)

    preview_rows: List[Dict[str, Any]] = []
    row_errors: List[Dict[str, Any]] = []
    total_water_litres = 0.0
    processed_count = 0

    num_rows = len(rows_to_process)
    col_names = list(rows_to_process.columns)
    col_idx = {name: i + 1 for i, name in enumerate(col_names)}  # +1 because itertuples index is at 0

    idx_crop = col_idx.get("crop_type")
    idx_stage = col_idx.get("growth_stage")
    idx_soil = col_idx.get("soil_type")
    idx_unit = col_idx.get("area_unit")
    idx_method = col_idx.get("irrigation_method")
    idx_area = col_idx.get("area")
    idx_moist = col_idx.get("soil_moisture_pct")
    idx_temp = col_idx.get("temperature_c")
    idx_hum = col_idx.get("humidity_pct")
    idx_wind = col_idx.get("wind_speed_kmh")
    idx_rain = col_idx.get("rainfall_mm")
    idx_solar = col_idx.get("solar_radiation")
    idx_et0 = col_idx.get("et0_mm")

    for chunk_start in range(0, num_rows, CHUNK_SIZE):
        chunk_end = min(chunk_start + CHUNK_SIZE, num_rows)
        chunk_df = rows_to_process.iloc[chunk_start:chunk_end]

        valid_specs = []
        valid_rec_dicts = []

        for row_tuple in chunk_df.itertuples(index=True, name=None):
            row_num = int(row_tuple[0]) + 1
            errors_for_row: List[str] = []

            raw_val_crop = row_tuple[idx_crop] if idx_crop else ""
            raw_crop = "" if pd.isna(raw_val_crop) else str(raw_val_crop).strip()
            if not raw_crop or raw_crop.lower() == "nan":
                errors_for_row.append("Missing crop_type.")
                crop = ""
            elif raw_crop.lower() not in known_crops_lower:
                errors_for_row.append(f"Unsupported crop_type '{raw_crop}'.")
                crop = raw_crop
            else:
                crop = resolve_crop_name(raw_crop)

            raw_val_stage = row_tuple[idx_stage] if idx_stage else "Mid-season"
            stage = "" if pd.isna(raw_val_stage) else str(raw_val_stage).strip()
            if not stage or stage.lower() == "nan":
                errors_for_row.append("Missing growth_stage.")

            raw_val_soil = row_tuple[idx_soil] if idx_soil else "Loamy"
            soil = "" if pd.isna(raw_val_soil) else str(raw_val_soil).strip()
            if not soil or soil.lower() == "nan":
                errors_for_row.append("Missing soil_type.")

            raw_val_unit = row_tuple[idx_unit] if idx_unit else "hectares"
            unit = "hectares" if pd.isna(raw_val_unit) else str(raw_val_unit).strip() or "hectares"

            raw_val_method = row_tuple[idx_method] if idx_method else "Drip"
            method = "Drip" if pd.isna(raw_val_method) else str(raw_val_method).strip() or "Drip"

            def _parse_tuple_float(c_idx: Optional[int], col_name: str, default: Optional[float] = None) -> Optional[float]:
                if c_idx is None:
                    return default
                val = row_tuple[c_idx]
                if pd.isna(val):
                    return default
                try:
                    return float(val)
                except (ValueError, TypeError):
                    errors_for_row.append(f"Invalid numeric value for {col_name}: '{val}'.")
                    return None

            area = _parse_tuple_float(idx_area, "area", 1.0)
            moisture = _parse_tuple_float(idx_moist, "soil_moisture_pct")
            temp = _parse_tuple_float(idx_temp, "temperature_c")
            hum = _parse_tuple_float(idx_hum, "humidity_pct")
            wind = _parse_tuple_float(idx_wind, "wind_speed_kmh", 10.0)
            rain = _parse_tuple_float(idx_rain, "rainfall_mm", 0.0)
            solar = _parse_tuple_float(idx_solar, "solar_radiation", 18.0)
            et0_raw = _parse_tuple_float(idx_et0, "et0_mm", None)

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
            valid_rec_dicts.append(rec_dict)
            valid_specs.append((row_num, crop, stage, area, unit, soil, moisture, temp, hum, wind, rain, et0, method))

        if valid_rec_dicts:
            # Batch ML inference for high throughput
            batch_ml_preds = predict_water_requirements_batch(valid_rec_dicts)

            chunk_irr_results = []
            for i, (row_num, crop, stage, area, unit, soil, moisture, temp, hum, wind, rain, et0, method) in enumerate(valid_specs):
                primary_mm = batch_ml_preds[i][0] if i < len(batch_ml_preds) else None
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
                if upload_id:
                    irr_result["id"] = f"csv_{upload_id}_{row_num}"
                total_water_litres += irr_result["water_requirement_litres"]
                processed_count += 1
                if len(preview_rows) < 10:
                    preview_rows.append(irr_result)
                if run_prediction_records:
                    chunk_irr_results.append(irr_result)

            if run_prediction_records and chunk_irr_results:
                save_predictions_batch(chunk_irr_results)

            del chunk_irr_results, batch_ml_preds

        del valid_rec_dicts, valid_specs

        if progress_callback is not None:
            progress_callback(processed_count, len(row_errors), num_rows)

    crops_summary = df["crop_type"].value_counts().to_dict()
    soils_summary = df["soil_type"].value_counts().to_dict()

    response: Dict[str, Any] = {
        "total_rows": total_rows,
        "processed_rows_count": processed_count,
        "failed_rows_count": len(row_errors),
        "skipped_rows_count": max(0, total_rows - MAX_BATCH_ROWS) if total_rows > MAX_BATCH_ROWS else 0,
        "row_errors": row_errors,
        "total_water_required_litres": round(total_water_litres, 2),
        "crops_distribution": crops_summary,
        "soils_distribution": soils_summary,
        "preview": preview_rows,
    }
    if total_rows > MAX_BATCH_ROWS:
        response["processing_note"] = (
            f"Large dataset ({total_rows:,} rows). Processed the first {MAX_BATCH_ROWS:,} rows. "
            "For datasets exceeding 100,000 rows, consider splitting into batches."
        )
    return response


def _run_upload_job(job_id: str, df: pd.DataFrame, upload_id: str) -> None:
    """Background worker for async CSV batch processing."""
    def _on_progress(processed: int, failed: int, target_total: int) -> None:
        with _JOBS_LOCK:
            job = _UPLOAD_JOBS.get(job_id)
            if job:
                done_rows = processed + failed
                job["processed_rows"] = processed
                job["failed_rows"] = failed
                job["progress_pct"] = round((done_rows / max(1, target_total)) * 100.0, 1)

    try:
        result = _process_dataframe(
            df,
            run_prediction_records=True,
            upload_id=upload_id,
            progress_callback=_on_progress,
        )
        with _JOBS_LOCK:
            job = _UPLOAD_JOBS.get(job_id)
            if job:
                job["status"] = "completed"
                job["processed_rows"] = result["processed_rows_count"]
                job["failed_rows"] = result["failed_rows_count"]
                job["skipped_rows"] = result["skipped_rows_count"]
                job["progress_pct"] = 100.0
                job["result"] = result
    except Exception as exc:
        with _JOBS_LOCK:
            job = _UPLOAD_JOBS.get(job_id)
            if job:
                job["status"] = "failed"
                job["error"] = str(exc)


@router.post("/upload")
async def upload_dataset_csv(file: UploadFile = File(...)):
    """
    Accepts CSV dataset upload, parses agricultural variables,
    evaluates water requirements, and saves results into prediction history.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    contents = await file.read()
    upload_id = hashlib.sha256(contents).hexdigest()[:16]
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {e}")

    return _process_dataframe(df, run_prediction_records=True, upload_id=upload_id)


@router.post("/upload/async")
async def upload_dataset_csv_async(file: UploadFile = File(...)):
    """
    Starts an asynchronous CSV batch job and returns job_id immediately so
    large uploads (e.g. 100,000 rows) do not hit HTTP proxy timeouts.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    contents = await file.read()
    upload_id = hashlib.sha256(contents).hexdigest()[:16]

    try:
        df = pd.read_csv(io.BytesIO(contents))
        df = _normalize_and_validate_df(df)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {e}")

    total_rows = len(df)
    target_rows = min(total_rows, 100_000)

    with _JOBS_LOCK:
        # Prevent duplicate concurrent or repeated runs for the exact same file payload
        for existing_id, existing_job in _UPLOAD_JOBS.items():
            if existing_job.get("upload_id") == upload_id and existing_job.get("status") in ("processing", "completed"):
                return {
                    "job_id": existing_id,
                    "status": existing_job["status"],
                    "total_rows": existing_job["total_rows"],
                    "processed_rows": existing_job["processed_rows"],
                    "progress_pct": existing_job["progress_pct"],
                    "deduplicated": True,
                }

        # Prune oldest completed/failed jobs if store grows large
        if len(_UPLOAD_JOBS) >= 20:
            removable = [
                jid for jid, j in _UPLOAD_JOBS.items()
                if j.get("status") in ("completed", "failed")
            ]
            for jid in removable[:max(1, len(_UPLOAD_JOBS) - 10)]:
                _UPLOAD_JOBS.pop(jid, None)

        job_id = str(uuid.uuid4())[:12]
        _UPLOAD_JOBS[job_id] = {
            "job_id": job_id,
            "upload_id": upload_id,
            "status": "processing",
            "total_rows": total_rows,
            "target_rows": target_rows,
            "processed_rows": 0,
            "failed_rows": 0,
            "skipped_rows": max(0, total_rows - 100_000),
            "progress_pct": 0.0,
            "created_at": time.time(),
            "result": None,
            "error": None,
        }

    worker = threading.Thread(
        target=_run_upload_job,
        args=(job_id, df, upload_id),
        daemon=True,
    )
    worker.start()

    return {
        "job_id": job_id,
        "status": "processing",
        "total_rows": total_rows,
        "processed_rows": 0,
        "progress_pct": 0.0,
    }


@router.get("/upload/status/{job_id}")
def get_upload_job_status(job_id: str):
    """Returns live progress and final result for an async CSV batch upload job."""
    with _JOBS_LOCK:
        job = _UPLOAD_JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Upload job not found or expired.")
        return {
            "job_id": job["job_id"],
            "status": job["status"],
            "total_rows": job["total_rows"],
            "processed_rows": job["processed_rows"],
            "failed_rows": job["failed_rows"],
            "skipped_rows": job["skipped_rows"],
            "progress_pct": job["progress_pct"],
            "error": job["error"],
            "result": job["result"] if job["status"] == "completed" else None,
        }


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
