"""
Agro-Climatic Dataset Generator for Cropwater Compass
Generates a physics-grounded agricultural dataset based on FAO-56 CROPWAT standards,
soil moisture depletion dynamics, and microclimatic variance.
"""
import math
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from backend.app.services.irrigation import (
    CROP_DATABASE,
    SOIL_DATABASE,
    IRRIGATION_METHODS,
    get_crop_kc,
    calculate_effective_rainfall,
    calculate_soil_water_balance
)
from backend.app.services.weather import calculate_fao56_et0

DATASETS_DIR = Path(__file__).resolve().parent.parent / "datasets"


def generate_agro_climatic_dataset(num_samples: int = 5000, random_seed: int = 42) -> pd.DataFrame:
    """
    Synthesizes a realistic, physically-consistent agricultural dataset.
    Features:
    - crop_type, growth_stage, soil_type, soil_moisture_pct, soil_ph
    - temperature_c, humidity_pct, wind_speed_kmh, rainfall_mm, solar_radiation, et0_mm
    - irrigation_method
    Target:
    - water_requirement_mm (Gross Irrigation Requirement in mm)
    """
    np.random.seed(random_seed)
    crops = list(CROP_DATABASE.keys())
    stages = ["Initial", "Vegetative", "Mid-season", "Late"]
    soils = list(SOIL_DATABASE.keys())
    methods = list(IRRIGATION_METHODS.keys())

    records = []

    for i in range(num_samples):
        crop = np.random.choice(crops)
        stage = np.random.choice(stages)
        soil = np.random.choice(soils)
        method = np.random.choice(methods, p=[0.45, 0.35, 0.20])  # Drip, Sprinkler, Surface

        # Realistic climate distributions
        temp = float(np.random.normal(loc=27.5, scale=6.0))
        temp = max(10.0, min(44.0, round(temp, 1)))

        # Humidity negatively correlated with temperature
        hum_base = 85.0 - (temp - 10.0) * 1.3 + np.random.normal(0, 7)
        hum = max(20.0, min(95.0, round(hum_base, 1)))

        wind = float(np.random.gamma(shape=2.5, scale=4.0))
        wind = max(2.0, min(35.0, round(wind, 1)))

        # Rainfall occurrence: 20% chance of rain
        has_rain = np.random.rand() < 0.22
        rain = float(np.random.exponential(scale=14.0)) if has_rain else 0.0
        rain = max(0.0, min(75.0, round(rain, 1)))

        solar = float(np.random.normal(loc=19.0, scale=4.0))
        solar = max(10.0, min(28.0, round(solar, 1)))

        # FAO-56 Reference ET0
        doy = int(np.random.randint(1, 365))
        et0 = calculate_fao56_et0(temp, hum, wind, solar, lat_deg=28.0, day_of_year=doy)

        # Soil moisture sampling around Field Capacity & Wilting Point
        fc = SOIL_DATABASE[soil]["field_capacity_pct"]
        pwp = SOIL_DATABASE[soil]["wilting_point_pct"]
        # Moisture between slightly below PWP and slightly above FC
        moisture = float(np.random.uniform(pwp - 2.0, fc + 6.0))
        moisture = max(4.0, min(50.0, round(moisture, 1)))

        soil_ph = float(np.random.normal(loc=6.8, scale=0.6))
        soil_ph = max(5.0, min(8.5, round(soil_ph, 2)))

        # Physical FAO-56 Water Requirement Calculation
        kc = get_crop_kc(crop, stage)
        etc = et0 * kc
        peff = calculate_effective_rainfall(rain)

        crop_info = CROP_DATABASE[crop]
        taw, raw, depletion, _ = calculate_soil_water_balance(
            soil, moisture, crop_info["root_depth_meters"], crop_info["critical_depletion_fraction"]
        )

        # Net irrigation requirement
        base_nir = max(0.0, etc - peff)
        if depletion > raw:
            base_nir += (depletion - raw) * 0.35

        # Gross irrigation requirement with efficiency
        eff = IRRIGATION_METHODS[method]["efficiency_pct"] / 100.0
        gir = base_nir / eff if eff > 0 else base_nir

        # Add realistic microclimate measurement stochasticity (+/- 5% noise)
        noise = np.random.normal(0, 0.15)
        target_water_mm = max(0.0, round(gir + noise, 2))

        records.append({
            "crop_type": crop,
            "growth_stage": stage,
            "soil_type": soil,
            "soil_moisture_pct": moisture,
            "soil_ph": soil_ph,
            "temperature_c": temp,
            "humidity_pct": hum,
            "wind_speed_kmh": wind,
            "rainfall_mm": rain,
            "solar_radiation": solar,
            "et0_mm": et0,
            "irrigation_method": method,
            "water_requirement_mm": target_water_mm
        })

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    df = generate_agro_climatic_dataset(num_samples=5000, random_seed=42)
    csv_path = DATASETS_DIR / "cropwater_dataset.csv"
    df.to_csv(csv_path, index=False)
    print(f"Generated {len(df)} samples saved to {csv_path}")
    print("Dataset Summary:")
    print(df.describe())
