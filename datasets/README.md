# Agro-Climatic Irrigation Dataset

## Overview

This repository contains the training and benchmarking dataset used by **Cropwater Compass** to model crop water demand.

- **File**: `datasets/cropwater_dataset.csv`
- **Total Records**: 5,000 observations
- **Target Variable**: `water_requirement_mm` (Gross Irrigation Requirement in millimeters)
- **Primary Converted Output**: Volumetric water demand in **Litres** ($1\text{ mm} \times 1\text{ m}^2 = 1\text{ Litre}$).

---

## Provenance & Agronomic Physics Formulation

> [!NOTE]
> This dataset is synthetically compiled using calibrated FAO-56 Penman-Monteith physical models and empirical soil moisture depletion dynamics. It adheres to the agricultural standards in **FAO Irrigation and Drainage Paper No. 56 (CROPWAT)**, combined with stochastic microclimatic noise ($\pm 5\%$) representing real sensor field variance.
>
> While real-world IoT sensor networks (such as LoRaWAN capacitive soil probes and Davis weather stations) capture localized farm microclimates, this standardized benchmark dataset provides controlled, leak-free training for comparative regression across models.

### Target Equation (Gross Irrigation Requirement):
$$GIR = \frac{\max\left(0, ET_c - P_{eff} + \text{DepletionAdjustment}\right)}{\eta_{irr}}$$

where:
- $ET_c = K_c \times ET_0$ (Crop Evapotranspiration)
- $P_{eff}$: Effective rainfall derived via USDA-SCS methodology
- $\text{DepletionAdjustment}$: Moisture replenishment when root zone depletion exceeds Readily Available Water ($RAW$)
- $\eta_{irr}$: Irrigation application efficiency (Drip 0.90, Sprinkler 0.75, Surface 0.60)

---

## Feature Dictionary

| Feature | Data Type | Units / Range | Description |
|---|---|---|---|
| `crop_type` | Categorical | 10 classes | Wheat, Rice, Maize, Cotton, Sugarcane, Tomato, Potato, Soybean, Barley, Onion |
| `growth_stage` | Categorical | 4 stages | Initial, Vegetative, Mid-season, Late |
| `soil_type` | Categorical | 6 classes | Sandy, Sandy Loam, Loamy, Clay Loam, Silty, Clay |
| `soil_moisture_pct` | Continuous | 4.0 – 50.0% | Volumetric moisture content in root zone |
| `soil_ph` | Continuous | 5.0 – 8.5 | Soil acidity / alkalinity indicator |
| `temperature_c` | Continuous | 10.0 – 44.0 °C | Mean daily air temperature at 2m height |
| `humidity_pct` | Continuous | 20.0 – 95.0% | Relative humidity |
| `wind_speed_kmh` | Continuous | 2.0 – 35.0 km/h | 2m wind velocity |
| `rainfall_mm` | Continuous | 0.0 – 75.0 mm | Expected or recent daily precipitation |
| `solar_radiation` | Continuous | 10.0 – 28.0 $MJ/m^2/d$ | Incident global solar radiation |
| `et0_mm` | Continuous | 1.18 – 13.28 mm/d | Reference evapotranspiration via FAO-56 Penman-Monteith |
| `irrigation_method` | Categorical | 3 systems | Drip (90%), Sprinkler (75%), Surface/Flood (60%) |
| `water_requirement_mm` | Continuous (Target) | 0.0 – 60.9 mm | Gross irrigation depth required |
