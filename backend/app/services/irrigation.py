"""
Irrigation Agronomic Service (FAO-56 CROPWAT compliant calculations)
Calculates Crop Evapotranspiration (ETc), Effective Rainfall, Soil Water Depletion,
Net & Gross Irrigation Requirements, and final required volume in Litres.
"""
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta


CROP_DATABASE: Dict[str, Dict[str, Any]] = {
    "Wheat": {
        "category": "Cereal",
        "kc_initial": 0.35,
        "kc_mid": 1.15,
        "kc_late": 0.40,
        "kc_vegetative": 0.75,
        "root_depth_meters": 1.2,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 130
    },
    "Rice": {
        "category": "Cereal",
        "kc_initial": 1.05,
        "kc_mid": 1.20,
        "kc_late": 0.90,
        "kc_vegetative": 1.10,
        "root_depth_meters": 0.6,
        "critical_depletion_fraction": 0.20,
        "typical_yield_season_days": 120
    },
    "Maize": {
        "category": "Cereal",
        "kc_initial": 0.40,
        "kc_mid": 1.20,
        "kc_late": 0.60,
        "kc_vegetative": 0.80,
        "root_depth_meters": 1.2,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 110
    },
    "Cotton": {
        "category": "Fiber",
        "kc_initial": 0.35,
        "kc_mid": 1.20,
        "kc_late": 0.65,
        "kc_vegetative": 0.75,
        "root_depth_meters": 1.4,
        "critical_depletion_fraction": 0.65,
        "typical_yield_season_days": 180
    },
    "Sugarcane": {
        "category": "Cash Crop",
        "kc_initial": 0.40,
        "kc_mid": 1.25,
        "kc_late": 0.75,
        "kc_vegetative": 0.85,
        "root_depth_meters": 1.5,
        "critical_depletion_fraction": 0.65,
        "typical_yield_season_days": 360
    },
    "Tomato": {
        "category": "Vegetable",
        "kc_initial": 0.45,
        "kc_mid": 1.15,
        "kc_late": 0.80,
        "kc_vegetative": 0.80,
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.40,
        "typical_yield_season_days": 105
    },
    "Potato": {
        "category": "Tuber",
        "kc_initial": 0.40,
        "kc_mid": 1.15,
        "kc_late": 0.75,
        "kc_vegetative": 0.75,
        "root_depth_meters": 0.6,
        "critical_depletion_fraction": 0.35,
        "typical_yield_season_days": 100
    },
    "Soybean": {
        "category": "Legume",
        "kc_initial": 0.40,
        "kc_mid": 1.15,
        "kc_late": 0.50,
        "kc_vegetative": 0.75,
        "root_depth_meters": 1.0,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 115
    },
    "Barley": {
        "category": "Cereal",
        "kc_initial": 0.30,
        "kc_mid": 1.15,
        "kc_late": 0.25,
        "kc_vegetative": 0.70,
        "root_depth_meters": 1.0,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 120
    },
    "Onion": {
        "category": "Vegetable",
        "kc_initial": 0.50,
        "kc_mid": 1.05,
        "kc_late": 0.85,
        "kc_vegetative": 0.75,
        "root_depth_meters": 0.4,
        "critical_depletion_fraction": 0.30,
        "typical_yield_season_days": 95
    }
}

SOIL_DATABASE: Dict[str, Dict[str, Any]] = {
    "Sandy": {
        "field_capacity_pct": 12.0,
        "wilting_point_pct": 5.0,
        "available_water_capacity_mm_per_m": 70.0,
        "infiltration_rate_mm_per_hr": 30.0,
        "description": "Coarse-textured soil with high drainage and low moisture retention."
    },
    "Sandy Loam": {
        "field_capacity_pct": 18.0,
        "wilting_point_pct": 8.0,
        "available_water_capacity_mm_per_m": 100.0,
        "infiltration_rate_mm_per_hr": 20.0,
        "description": "Permeable soil balancing drainage and moisture retention well."
    },
    "Loamy": {
        "field_capacity_pct": 26.0,
        "wilting_point_pct": 12.0,
        "available_water_capacity_mm_per_m": 140.0,
        "infiltration_rate_mm_per_hr": 12.0,
        "description": "Ideal agricultural soil with balanced aeration and high nutrient/moisture capacity."
    },
    "Clay Loam": {
        "field_capacity_pct": 32.0,
        "wilting_point_pct": 18.0,
        "available_water_capacity_mm_per_m": 140.0,
        "infiltration_rate_mm_per_hr": 8.0,
        "description": "Moderately heavy soil with very high water storage capacity."
    },
    "Silty": {
        "field_capacity_pct": 30.0,
        "wilting_point_pct": 14.0,
        "available_water_capacity_mm_per_m": 160.0,
        "infiltration_rate_mm_per_hr": 10.0,
        "description": "Fine-textured fertile soil with high available water content."
    },
    "Clay": {
        "field_capacity_pct": 38.0,
        "wilting_point_pct": 24.0,
        "available_water_capacity_mm_per_m": 140.0,
        "infiltration_rate_mm_per_hr": 4.0,
        "description": "Heavy soil with slow infiltration, prone to waterlogging if over-irrigated."
    }
}

IRRIGATION_METHODS: Dict[str, Dict[str, Any]] = {
    "Drip": {
        "efficiency_pct": 90.0,
        "typical_pressure_bar": 1.5,
        "suitable_crops": ["Tomato", "Potato", "Cotton", "Sugarcane", "Wheat", "Maize", "Soybean"],
        "description": "Micro-irrigation delivering water directly to root zones with minimal evaporative loss (90% efficiency)."
    },
    "Sprinkler": {
        "efficiency_pct": 75.0,
        "typical_pressure_bar": 2.5,
        "suitable_crops": ["Wheat", "Barley", "Maize", "Soybean", "Onion"],
        "description": "Overhead pressurized spray system imitating rainfall (75% efficiency)."
    },
    "Surface/Flood": {
        "efficiency_pct": 60.0,
        "typical_pressure_bar": 0.5,
        "suitable_crops": ["Rice", "Sugarcane", "Wheat"],
        "description": "Gravity flow surface distribution with standard furrow/basin losses (60% efficiency)."
    }
}


def convert_area_to_sq_meters(area: float, unit: str) -> float:
    """Convert input farm area to square meters."""
    unit_lower = unit.lower().strip()
    if unit_lower in ["ha", "hectare", "hectares"]:
        return area * 10000.0
    elif unit_lower in ["ac", "acre", "acres"]:
        return area * 4046.8564224
    elif unit_lower in ["sq_m", "sqm", "sq_meters", "m2", "square_meters"]:
        return area
    return area * 10000.0  # default hectares


def get_crop_kc(crop_name: str, growth_stage: str) -> float:
    """Retrieve Kc coefficient based on crop and growth stage."""
    crop = CROP_DATABASE.get(crop_name)
    if not crop:
        # Fallback default
        return 0.85

    stage_lower = growth_stage.lower()
    if "init" in stage_lower:
        return crop["kc_initial"]
    elif "mid" in stage_lower or "flower" in stage_lower:
        return crop["kc_mid"]
    elif "late" in stage_lower or "matur" in stage_lower or "harvest" in stage_lower:
        return crop["kc_late"]
    elif "veg" in stage_lower or "develop" in stage_lower:
        return crop.get("kc_vegetative", (crop["kc_initial"] + crop["kc_mid"]) / 2.0)
    else:
        return crop["kc_mid"]


def calculate_effective_rainfall(rainfall_mm: float) -> float:
    """
    FAO/USDA method for effective daily rainfall.
    Small rain showers below 5mm evaporate without contributing to root zone.
    """
    if rainfall_mm <= 5.0:
        return 0.0
    elif rainfall_mm <= 50.0:
        return (rainfall_mm - 5.0) * 0.75
    else:
        return (45.0 * 0.75) + ((rainfall_mm - 50.0) * 0.50)


def calculate_soil_water_balance(
    soil_type: str,
    soil_moisture_pct: float,
    root_depth_m: float,
    critical_depletion_p: float
) -> Tuple[float, float, float, float]:
    """
    Computes soil moisture metrics:
    - total_available_water_mm (TAW)
    - readily_available_water_mm (RAW)
    - root_zone_depletion_mm (Dr)
    - depletion_fraction
    """
    soil = SOIL_DATABASE.get(soil_type, SOIL_DATABASE["Loamy"])
    fc = soil["field_capacity_pct"]
    pwp = soil["wilting_point_pct"]

    # TAW in mm = 1000 * (FC - PWP)/100 * Zr
    taw = max(10.0, 10.0 * (fc - pwp) * root_depth_m)
    raw = taw * critical_depletion_p

    # Current moisture relative to FC
    if soil_moisture_pct >= fc:
        depletion_mm = 0.0
    else:
        depletion_mm = min(taw, max(0.0, 10.0 * (fc - soil_moisture_pct) * root_depth_m))

    depletion_fraction = min(1.0, max(0.0, depletion_mm / taw if taw > 0 else 0.0))
    return taw, raw, depletion_mm, depletion_fraction


def calculate_irrigation_recommendation(
    crop_type: str,
    growth_stage: str,
    area: float,
    area_unit: str,
    soil_type: str,
    soil_moisture_pct: float,
    temperature_c: float,
    humidity_pct: float,
    wind_speed_kmh: float,
    rainfall_mm: float,
    reference_et0_mm: float,
    irrigation_method: str = "Drip",
    ml_predicted_mm: float = None
) -> Dict[str, Any]:
    """
    Complete FAO-56 Agronomic calculation engine.
    Computes required water depth in mm, converts to total litres for farm area,
    and returns schedule and urgency.
    """
    crop = CROP_DATABASE.get(crop_type, CROP_DATABASE["Wheat"])
    soil = SOIL_DATABASE.get(soil_type, SOIL_DATABASE["Loamy"])
    irr_info = IRRIGATION_METHODS.get(irrigation_method, IRRIGATION_METHODS["Drip"])

    area_sq_meters = convert_area_to_sq_meters(area, area_unit)
    kc = get_crop_kc(crop_type, growth_stage)
    etc_mm = reference_et0_mm * kc

    peff_mm = calculate_effective_rainfall(rainfall_mm)

    root_depth = crop["root_depth_meters"]
    p_depletion = crop["critical_depletion_fraction"]
    taw, raw, depletion_mm, depletion_fraction = calculate_soil_water_balance(
        soil_type, soil_moisture_pct, root_depth, p_depletion
    )

    # Net Irrigation Requirement (NIR) in mm/day
    # If ML prediction is provided, harmonize with agronomic boundaries
    base_nir = max(0.0, etc_mm - peff_mm)
    if depletion_mm > raw:
        # Moisture is depleted past readily available threshold: add depletion replenishment
        base_nir += (depletion_mm - raw) * 0.4

    if ml_predicted_mm is not None and ml_predicted_mm > 0:
        # Blend ML prediction with physical balance (75% ML, 25% physical balance for physical safety)
        nir_mm = max(0.0, (0.75 * ml_predicted_mm) + (0.25 * base_nir))
    else:
        nir_mm = base_nir

    # Gross Irrigation Requirement (GIR) accounting for application efficiency
    efficiency = irr_info["efficiency_pct"] / 100.0
    gir_mm = round(nir_mm / efficiency, 2) if efficiency > 0 else nir_mm

    # Convert to Litres:
    # 1 mm depth on 1 m2 = 1 Litre
    water_litres = round(gir_mm * area_sq_meters, 2)
    water_m3 = round(water_litres / 1000.0, 3)

    # Urgency & Recommendation logic
    irrigation_recommended = gir_mm > 0.5
    if depletion_mm >= raw * 1.2 or soil_moisture_pct <= (soil["wilting_point_pct"] + 2.0):
        urgency = "Critical"
    elif depletion_mm >= raw or gir_mm >= 6.0:
        urgency = "High"
    elif gir_mm >= 2.5:
        urgency = "Moderate"
    elif gir_mm > 0.5:
        urgency = "Low"
    else:
        urgency = "None"
        irrigation_recommended = False

    # Irrigation Scheduling
    if gir_mm > 0:
        # Frequency based on soil infiltration and RAW
        if soil_type in ["Sandy", "Sandy Loam"]:
            freq_days = 1  # lighter soil needs more frequent, shorter pulses
            duration_hrs = round(min(6.0, max(1.0, (gir_mm / 3.0))), 1)
        elif soil_type in ["Clay", "Clay Loam"]:
            freq_days = 3  # heavier soil holds moisture longer
            duration_hrs = round(min(8.0, max(1.5, (gir_mm / 2.0))), 1)
        else:
            freq_days = 2
            duration_hrs = round(min(6.0, max(1.0, (gir_mm / 2.5))), 1)
    else:
        freq_days = 0
        duration_hrs = 0.0

    best_time = "Early Morning (5:00 AM - 8:00 AM)" if temperature_c >= 26.0 else "Late Afternoon (4:30 PM - 7:00 PM)"
    next_date = (datetime.now() + timedelta(days=max(1, freq_days) if irrigation_recommended else 2)).strftime("%Y-%m-%d")

    # Generate tailored agronomic tips
    recommendations: List[str] = []
    if irrigation_recommended:
        recommendations.append(
            f"Apply approximately {water_litres:,.0f} litres ({gir_mm:.1f} mm) across {area} {area_unit} using {irrigation_method} irrigation."
        )
        recommendations.append(
            f"Optimal application window: {best_time} to minimize evaporative losses."
        )
        if rainfall_mm > 5:
            recommendations.append(
                f"Recent rainfall of {rainfall_mm:.1f} mm provided {peff_mm:.1f} mm effective moisture, reducing irrigation needs."
            )
        if soil_moisture_pct < soil["wilting_point_pct"] + 4.0:
            recommendations.append(
                f"Soil moisture ({soil_moisture_pct:.1f}%) is nearing wilting point ({soil['wilting_point_pct']}%). Irrigate promptly."
            )
        if temperature_c > 35.0:
            recommendations.append(
                f"Elevated temperatures ({temperature_c:.1f}°C) heighten ETc ({etc_mm:.1f} mm/day). Avoid mid-day water applications."
            )
    else:
        recommendations.append(
            f"Current root zone moisture ({soil_moisture_pct:.1f}%) and weather conditions do not require immediate irrigation."
        )
        recommendations.append(
            f"Next recommended soil moisture inspection on {next_date}."
        )

    return {
        "crop_type": crop_type,
        "growth_stage": growth_stage,
        "area": area,
        "area_unit": area_unit,
        "area_sq_meters": area_sq_meters,
        "soil_type": soil_type,
        "soil_moisture_pct": soil_moisture_pct,
        "reference_et0_mm": round(reference_et0_mm, 2),
        "crop_kc": round(kc, 3),
        "crop_evapotranspiration_etc_mm": round(etc_mm, 2),
        "effective_rainfall_mm": round(peff_mm, 2),
        "soil_depletion_fraction": round(depletion_fraction, 3),
        "net_irrigation_requirement_mm": round(nir_mm, 2),
        "gross_irrigation_requirement_mm": gir_mm,
        "water_requirement_mm": gir_mm,
        "water_requirement_litres": water_litres,
        "water_requirement_m3": water_m3,
        "irrigation_efficiency_pct": irr_info["efficiency_pct"],
        "irrigation_recommended": irrigation_recommended,
        "urgency_level": urgency,
        "recommended_schedule": {
            "frequency_days": freq_days,
            "duration_hours": duration_hrs,
            "best_time": best_time,
            "emitter_discharge_lph": 4.0 if irrigation_method == "Drip" else None,
            "next_irrigation_date": next_date
        },
        "recommendations": recommendations,
        "timestamp": datetime.now().isoformat()
    }
