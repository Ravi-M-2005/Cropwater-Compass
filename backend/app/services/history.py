"""
Prediction History Service using SQLite for persistent audit trail and dashboard analytics.
"""
import sqlite3
import json
import uuid
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DB_DIR / "cropwater.db"


def get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables if not already present."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                crop_type TEXT NOT NULL,
                growth_stage TEXT NOT NULL,
                area REAL NOT NULL,
                area_unit TEXT NOT NULL,
                soil_type TEXT NOT NULL,
                soil_moisture_pct REAL NOT NULL,
                temperature_c REAL NOT NULL,
                humidity_pct REAL NOT NULL,
                wind_speed_kmh REAL NOT NULL,
                rainfall_mm REAL NOT NULL,
                et0_mm REAL NOT NULL,
                irrigation_method TEXT NOT NULL,
                model_used TEXT NOT NULL,
                water_requirement_litres REAL NOT NULL,
                water_requirement_mm REAL NOT NULL,
                net_irrigation_requirement_mm REAL NOT NULL,
                irrigation_recommended INTEGER NOT NULL,
                urgency_level TEXT NOT NULL,
                details_json TEXT NOT NULL
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crop ON predictions(crop_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON predictions(timestamp);")
        conn.commit()


def save_prediction(record: Dict[str, Any]) -> str:
    """Saves a prediction record to SQLite."""
    init_db()
    pred_id = record.get("id") or str(uuid.uuid4())[:8]
    record["id"] = pred_id

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO predictions (
                id, timestamp, crop_type, growth_stage, area, area_unit,
                soil_type, soil_moisture_pct, temperature_c, humidity_pct,
                wind_speed_kmh, rainfall_mm, et0_mm, irrigation_method,
                model_used, water_requirement_litres, water_requirement_mm,
                net_irrigation_requirement_mm, irrigation_recommended,
                urgency_level, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pred_id,
            record.get("timestamp"),
            record.get("crop_type"),
            record.get("growth_stage"),
            float(record.get("area", 1.0)),
            record.get("area_unit", "hectares"),
            record.get("soil_type"),
            float(record.get("soil_moisture_pct", 30.0)),
            float(record.get("temperature_c", 25.0)),
            float(record.get("humidity_pct", 50.0)),
            float(record.get("wind_speed_kmh", 10.0)),
            float(record.get("rainfall_mm", 0.0)),
            float(record.get("reference_et0_mm", 4.0)),
            record.get("irrigation_method", "Drip"),
            record.get("model_used", "xgboost"),
            float(record.get("water_requirement_litres", 0.0)),
            float(record.get("water_requirement_mm", 0.0)),
            float(record.get("net_irrigation_requirement_mm", 0.0)),
            1 if record.get("irrigation_recommended") else 0,
            record.get("urgency_level", "Moderate"),
            json.dumps(record)
        ))
        conn.commit()
    return pred_id


def get_history(
    limit: int = 50,
    offset: int = 0,
    crop_type: Optional[str] = None,
    soil_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves paginated prediction history records."""
    init_db()
    query = "SELECT details_json FROM predictions WHERE 1=1"
    params: List[Any] = []

    if crop_type:
        query += " AND crop_type = ?"
        params.append(crop_type)
    if soil_type:
        query += " AND soil_type = ?"
        params.append(soil_type)

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_connection() as conn:
        cursor = conn.cursor()
        rows = cursor.execute(query, params).fetchall()
        results = [json.loads(r["details_json"]) for r in rows]
    return results


def get_history_by_id(pred_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single prediction by ID."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT details_json FROM predictions WHERE id = ?", (pred_id,)).fetchone()
        if row:
            return json.loads(row["details_json"])
    return None


def delete_prediction(pred_id: str) -> bool:
    """Deletes a single prediction record."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM predictions WHERE id = ?", (pred_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
    return deleted


def clear_history() -> int:
    """Deletes all records from history."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM predictions")
        count = cursor.rowcount
        conn.commit()
    return count


def get_history_stats() -> Dict[str, Any]:
    """Computes aggregated dashboard statistics from past predictions."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        total_predictions = cursor.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]

        if total_predictions == 0:
            return {
                "total_predictions": 0,
                "total_water_litres": 0.0,
                "avg_water_litres_per_hectare": 0.0,
                "water_by_crop": {},
                "water_by_soil": {},
                "predictions_by_model": {},
                "urgency_distribution": {}
            }

        total_water = cursor.execute("SELECT SUM(water_requirement_litres) FROM predictions").fetchone()[0] or 0.0
        avg_water = cursor.execute("SELECT AVG(water_requirement_litres) FROM predictions").fetchone()[0] or 0.0

        # Group by crop
        crop_rows = cursor.execute("SELECT crop_type, SUM(water_requirement_litres) FROM predictions GROUP BY crop_type").fetchall()
        water_by_crop = {row[0]: round(row[1] or 0.0, 1) for row in crop_rows}

        # Group by soil
        soil_rows = cursor.execute("SELECT soil_type, SUM(water_requirement_litres) FROM predictions GROUP BY soil_type").fetchall()
        water_by_soil = {row[0]: round(row[1] or 0.0, 1) for row in soil_rows}

        # Group by model
        model_rows = cursor.execute("SELECT model_used, COUNT(*) FROM predictions GROUP BY model_used").fetchall()
        predictions_by_model = {row[0]: row[1] for row in model_rows}

        # Group by urgency
        urgency_rows = cursor.execute("SELECT urgency_level, COUNT(*) FROM predictions GROUP BY urgency_level").fetchall()
        urgency_distribution = {row[0]: row[1] for row in urgency_rows}

    return {
        "total_predictions": total_predictions,
        "total_water_litres": round(total_water, 1),
        "avg_water_litres_per_hectare": round(avg_water, 1),
        "water_by_crop": water_by_crop,
        "water_by_soil": water_by_soil,
        "predictions_by_model": predictions_by_model,
        "urgency_distribution": urgency_distribution
    }
