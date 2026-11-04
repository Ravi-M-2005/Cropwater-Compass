"""
ISRIC SoilGrids 250m Integration Service
Provides authentic soil information from ISRIC - World Soil Information SoilGrids250m.
Uses official OGC WCS 2.0.1 coverage services with local persistent SQLite caching
and USDA Soil Texture Triangle classification.
"""
import os
import io
import time
import math
import sqlite3
import logging
import urllib.request
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from pathlib import Path
from PIL import Image
import numpy as np

logger = logging.getLogger("soilgrids_service")

# Data depth intervals defined by ISRIC SoilGrids standards
SUPPORTED_DEPTH_INTERVALS = [
    "0-5cm",
    "5-15cm",
    "15-30cm",
    "30-60cm",
    "60-100cm",
    "100-200cm"
]

# Official property specifications, raw units, and conversion factors
# Source: https://docs.isric.org/globaldata/soilgrids/
SOILGRIDS_PROPERTIES = {
    "clay": {
        "display_name": "Clay Content",
        "description": "Fine earth fraction with diameter < 2 µm",
        "raw_units": "g/kg",
        "target_units": "%",
        "conversion_factor": 10.0,
        "citation": "Poggio et al. (2021) SoilGrids 2.0",
    },
    "sand": {
        "display_name": "Sand Content",
        "description": "Fine earth fraction with diameter 50–2000 µm",
        "raw_units": "g/kg",
        "target_units": "%",
        "conversion_factor": 10.0,
        "citation": "Poggio et al. (2021) SoilGrids 2.0",
    },
    "silt": {
        "display_name": "Silt Content",
        "description": "Fine earth fraction with diameter 2–50 µm",
        "raw_units": "g/kg",
        "target_units": "%",
        "conversion_factor": 10.0,
        "citation": "Poggio et al. (2021) SoilGrids 2.0",
    },
    "phh2o": {
        "display_name": "Soil pH (H2O)",
        "description": "Soil pH measured in 1:5 soil:water suspension",
        "raw_units": "pH*10",
        "target_units": "pH",
        "conversion_factor": 10.0,
        "citation": "Poggio et al. (2021) SoilGrids 2.0",
    },
    "soc": {
        "display_name": "Soil Organic Carbon",
        "description": "Organic carbon in the fine earth fraction",
        "raw_units": "dg/kg",
        "target_units": "g/kg",
        "conversion_factor": 10.0,
        "citation": "Poggio et al. (2021) SoilGrids 2.0",
    },
    "bdod": {
        "display_name": "Bulk Density",
        "description": "Bulk density of the fine earth fraction",
        "raw_units": "cg/cm³",
        "target_units": "kg/dm³ (g/cm³)",
        "conversion_factor": 100.0,
        "citation": "Poggio et al. (2021) SoilGrids 2.0",
    },
    "cec": {
        "display_name": "Cation Exchange Capacity",
        "description": "Cation exchange capacity of soil at pH 7",
        "raw_units": "mmol(c)/kg",
        "target_units": "cmol(c)/kg",
        "conversion_factor": 10.0,
        "citation": "Poggio et al. (2021) SoilGrids 2.0",
    },
    "cfvo": {
        "display_name": "Coarse Fragments",
        "description": "Volumetric fraction of coarse fragments (> 2 mm)",
        "raw_units": "cm³/dm³",
        "target_units": "%",
        "conversion_factor": 10.0,
        "citation": "Poggio et al. (2021) SoilGrids 2.0",
    },
    "nitrogen": {
        "display_name": "Total Nitrogen",
        "description": "Total nitrogen in the fine earth fraction",
        "raw_units": "cg/kg",
        "target_units": "g/kg",
        "conversion_factor": 100.0,
        "citation": "Poggio et al. (2021) SoilGrids 2.0",
    },
    "ocd": {
        "display_name": "Organic Carbon Density",
        "description": "Soil organic carbon density",
        "raw_units": "hg/m³",
        "target_units": "kg/m³",
        "conversion_factor": 10.0,
        "citation": "Poggio et al. (2021) SoilGrids 2.0",
    },
    "wv0010": {
        "display_name": "Water Content (10 kPa)",
        "description": "Volumetric water content at 10 kPa suction",
        "raw_units": "10*vol%",
        "target_units": "% (vol)",
        "conversion_factor": 10.0,
        "citation": "Poggio et al. (2021) SoilGrids 2.0",
    },
    "wv0033": {
        "display_name": "Water Content (33 kPa / Field Capacity)",
        "description": "Volumetric water content at 33 kPa suction (Field Capacity)",
        "raw_units": "10*vol%",
        "target_units": "% (vol)",
        "conversion_factor": 10.0,
        "citation": "Poggio et al. (2021) SoilGrids 2.0",
    },
    "wv1500": {
        "display_name": "Water Content (1500 kPa / Wilting Point)",
        "description": "Volumetric water content at 1500 kPa suction (Permanent Wilting Point)",
        "raw_units": "10*vol%",
        "target_units": "% (vol)",
        "conversion_factor": 10.0,
        "citation": "Poggio et al. (2021) SoilGrids 2.0",
    },
}

# Mapping from USDA derived texture classes to Cropwater Compass 6 agronomic categories
USDA_TO_CROPWATER_SOIL = {
    "Sand": "Sandy",
    "Loamy Sand": "Sandy",
    "Sandy Loam": "Sandy Loam",
    "Loam": "Loamy",
    "Silt Loam": "Silty",
    "Silt": "Silty",
    "Sandy Clay Loam": "Clay Loam",
    "Clay Loam": "Clay Loam",
    "Silty Clay Loam": "Clay Loam",
    "Sandy Clay": "Clay",
    "Silty Clay": "Clay",
    "Clay": "Clay",
}

# Cache DB Path
DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DB_PATH = os.getenv("SOILGRIDS_DB_PATH", str(DB_DIR / "soilgrids_cache.sqlite"))


def init_soil_cache(db_path: str = CACHE_DB_PATH):
    """Initializes SQLite database table for SoilGrids response caching."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS soilgrids_cache (
                coord_key TEXT,
                depth_interval TEXT,
                response_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (coord_key, depth_interval)
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not initialize SoilGrids cache DB: {e}")


# Initialize cache schema
init_soil_cache()


def classify_usda_texture(sand: float, silt: float, clay: float) -> str:
    """
    Standard USDA Soil Texture Triangle classification algorithm.
    Takes Sand %, Silt %, and Clay % and maps to one of the 12 recognised USDA texture classes.
    """
    total = sand + silt + clay
    if total <= 0:
        return "Unknown"

    # Normalize to 100%
    s = (sand / total) * 100.0
    si = (silt / total) * 100.0
    c = (clay / total) * 100.0

    if c >= 40.0:
        if s >= 45.0:
            return "Sandy Clay"
        elif si >= 40.0:
            return "Silty Clay"
        else:
            return "Clay"
    elif c >= 27.0:
        if s < 20.0:
            return "Silty Clay Loam"
        elif s <= 45.0:
            return "Clay Loam"
        else:
            return "Sandy Clay Loam"
    elif c >= 20.0:
        if s >= 45.0 and si < 28.0:
            return "Sandy Clay Loam"
        elif s < 20.0 and si >= 50.0:
            return "Silty Clay Loam"
        elif si >= 50.0:
            return "Silt Loam"
        elif s <= 52.0 and si >= 28.0:
            return "Loam"
        else:
            return "Sandy Loam"
    elif c >= 7.0:
        if si >= 80.0 and c < 12.0:
            return "Silt"
        elif si >= 50.0:
            return "Silt Loam"
        elif s <= 52.0 and si >= 28.0:
            return "Loam"
        elif s >= 45.0:
            return "Sandy Loam"
        else:
            return "Loam"
    else:
        if si >= 80.0:
            return "Silt"
        elif si >= 50.0:
            return "Silt Loam"
        elif s >= 85.0 and (si + 1.5 * c < 15.0):
            return "Sand"
        elif s >= 70.0:
            return "Loamy Sand"
        else:
            return "Sandy Loam"


def _query_wcs_property_single(
    prop_name: str,
    depth: str,
    lat: float,
    lon: float,
    timeout_sec: float = 6.0
) -> Optional[float]:
    """
    Performs an official OGC WCS 2.0.1 coverage query to ISRIC maps server for a property layer.
    """
    coverage_id = f"{prop_name}_{depth}_mean"
    delta = 0.015  # ~1.6km bbox window ensuring at least one 250m pixel is captured
    url = (
        f"https://maps.isric.org/mapserv?map=/map/{prop_name}.map"
        f"&SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage"
        f"&COVERAGEID={coverage_id}"
        f"&SUBSET=Long({lon - delta:.4f},{lon + delta:.4f})"
        f"&SUBSET=Lat({lat - delta:.4f},{lat + delta:.4f})"
        f"&SUBSETTINGCRS=http://www.opengis.net/def/crs/EPSG/0/4326"
        f"&OUTPUTCRS=http://www.opengis.net/def/crs/EPSG/0/4326"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CropwaterCompass/2.0 (Agriculture SoilGrids Client)"}
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            if response.status == 200:
                img_data = response.read()
                img = Image.open(io.BytesIO(img_data))
                arr = np.array(img)
                # Ignore non-data / negative values
                valid = arr[arr > 0]
                if len(valid) > 0:
                    return float(np.median(valid))
    except Exception as e:
        logger.debug(f"WCS request for {coverage_id} failed: {e}")
    return None


def get_soilgrids_properties(
    lat: float,
    lon: float,
    depth_interval: str = "0-5cm",
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Retrieves authentic 250m resolution ISRIC SoilGrids properties for the specified
    farm coordinates and depth interval.
    """
    # Validate depth interval
    depth = depth_interval if depth_interval in SUPPORTED_DEPTH_INTERVALS else "0-5cm"
    coord_key = f"{round(lat, 3)}_{round(lon, 3)}"

    # 1. Check local persistent SQLite cache
    if use_cache:
        try:
            conn = sqlite3.connect(CACHE_DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT response_json FROM soilgrids_cache WHERE coord_key = ? AND depth_interval = ?",
                (coord_key, depth)
            )
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                import json
                cached_data = json.loads(row[0])
                cached_data["source"] = "ISRIC SoilGrids 250m (Cached)"
                return cached_data
        except Exception as e:
            logger.warning(f"Error querying SoilGrids cache: {e}")

    # 2. Query ISRIC Live WCS Service
    properties_output: Dict[str, Any] = {}
    properties_to_query = [
        "clay", "sand", "silt", "phh2o", "soc",
        "bdod", "cec", "cfvo", "nitrogen", "ocd",
        "wv0010", "wv0033", "wv1500"
    ]

    t0 = time.time()
    successful_fetches = 0

    for prop in properties_to_query:
        spec = SOILGRIDS_PROPERTIES[prop]
        raw_val = _query_wcs_property_single(prop, depth, lat, lon)
        if raw_val is not None:
            conv_val = round(raw_val / spec["conversion_factor"], 2)
            successful_fetches += 1
            properties_output[prop] = {
                "display_name": spec["display_name"],
                "description": spec["description"],
                "raw_value": round(raw_val, 1),
                "raw_units": spec["raw_units"],
                "converted_value": conv_val,
                "target_units": spec["target_units"],
                "conversion_factor": spec["conversion_factor"],
                "citation": spec["citation"]
            }

    # 3. Handle live query outcome
    if successful_fetches >= 3 and "clay" in properties_output and "sand" in properties_output:
        # Authentic SoilGrids data successfully retrieved!
        clay_pct = properties_output["clay"]["converted_value"]
        sand_pct = properties_output["sand"]["converted_value"]
        silt_pct = properties_output["silt"]["converted_value"] if "silt" in properties_output else max(0.0, 100.0 - clay_pct - sand_pct)

        derived_texture = classify_usda_texture(sand_pct, silt_pct, clay_pct)
        cropwater_soil = USDA_TO_CROPWATER_SOIL.get(derived_texture, "Loamy")

        # Hydrology water retention
        fc_pct = properties_output.get("wv0033", {}).get("converted_value")
        pwp_pct = properties_output.get("wv1500", {}).get("converted_value")

        if fc_pct is None or pwp_pct is None:
            # Fallback to empirical defaults calibrated to the derived texture class
            if cropwater_soil == "Sandy":
                fc_pct, pwp_pct = 12.0, 5.0
            elif cropwater_soil == "Sandy Loam":
                fc_pct, pwp_pct = 18.0, 8.0
            elif cropwater_soil in ["Loamy", "Silty"]:
                fc_pct, pwp_pct = 26.0, 12.0
            elif cropwater_soil == "Clay Loam":
                fc_pct, pwp_pct = 32.0, 18.0
            else:
                fc_pct, pwp_pct = 38.0, 24.0

        awc_mm_per_m = round((fc_pct - pwp_pct) * 10.0, 1)

        result: Dict[str, Any] = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "depth_interval": depth,
            "spatial_resolution": "250m",
            "is_available": True,
            "source": "ISRIC SoilGrids 250m (Live WCS 2.0.1)",
            "citation": "ISRIC - World Soil Information, SoilGrids 250m v2.0 (CC BY 4.0)",
            "retrieval_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "properties": properties_output,
            "derived_usda_texture": derived_texture,
            "cropwater_soil_type": cropwater_soil,
            "field_capacity_pct": fc_pct,
            "wilting_point_pct": pwp_pct,
            "available_water_capacity_mm_per_m": awc_mm_per_m,
            "error_message": None,
        }

        # Cache valid response in SQLite
        try:
            import json
            conn = sqlite3.connect(CACHE_DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO soilgrids_cache (coord_key, depth_interval, response_json) VALUES (?, ?, ?)",
                (coord_key, depth, json.dumps(result))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Could not cache SoilGrids result: {e}")

        return result

    # 4. If live query failed or coordinates are masked (e.g. water/dense urban or offline)
    # Never invent arbitrary numbers while labeling them SoilGrids
    logger.info(f"SoilGrids live query unavailable for ({lat}, {lon})")
    return {
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "depth_interval": depth,
        "spatial_resolution": "250m",
        "is_available": False,
        "source": "unavailable",
        "citation": "ISRIC - World Soil Information, SoilGrids 250m v2.0",
        "retrieval_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "properties": {},
        "derived_usda_texture": "Unavailable",
        "cropwater_soil_type": "Loamy",  # neutral fallback
        "field_capacity_pct": 26.0,
        "wilting_point_pct": 12.0,
        "available_water_capacity_mm_per_m": 140.0,
        "error_message": "ISRIC SoilGrids live coverage is currently unreachable or coordinates fall outside mapped land area. Please verify internet connection or input soil properties manually.",
    }
