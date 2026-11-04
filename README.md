# 🌱 Cropwater Compass
### Smart Irrigation Management System Using Machine Learning

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.15-EE4C2C.svg?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-Regressor-EB6A2D.svg?style=flat)](https://xgboost.readthedocs.io)
[![React](https://img.shields.io/badge/Frontend-React_18_TypeScript-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/Styles-Tailwind_CSS-38B2AC.svg?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Standard](https://img.shields.io/badge/Agronomy-FAO--56_CROPWAT-2E7D32.svg?style=flat)](https://www.fao.org/land-water/databases-and-software/cropwat/en/)
[![Tests](https://img.shields.io/badge/Tests-44_Passed-brightgreen.svg?style=flat)](tests/)
[![ISRIC SoilGrids](https://img.shields.io/badge/Soil_Data-ISRIC_SoilGrids_250m-2E7D32.svg?style=flat)](https://docs.isric.org/globaldata/soilgrids/)

**Cropwater Compass** is a full-stack, machine learning–powered precision agriculture platform that predicts the volumetric irrigation water requirements for crops in **Litres** (alongside $m^3$ and millimeter depth). Moving far beyond simple binary ("irrigation required: yes/no") triggers, Cropwater Compass combines standard **FAO-56 CROPWAT** agronomic physics with a multi-model ML suite (**XGBoost**, **Artificial Neural Networks**, **PyTorch LSTM**, and **Ensemble**) to eliminate water wastage, prevent crop water stress, and optimize irrigation schedules.

---

## 📸 Application Screenshots

### 1. Central Analytics Dashboard
Executive KPI cards displaying total recommended volume, estimated water conserved (~25%), crop-wise demand distribution, and recent field evaluations.
![Dashboard Overview](docs/images/dashboard_screenshot.png)

### 2. Volumetric Irrigation Prediction
Input farm dimensions, crop stage, soil class, and weather to receive the exact water requirement in **Litres**, $m^3$, and $mm$, coupled with pulse duration and urgency levels.
![Irrigation Prediction](docs/images/prediction_screenshot.png)

### 3. ML Multi-Model Benchmark Comparison
Head-to-head empirical comparison of XGBoost, ANN, and LSTM across $R^2$, RMSE, MAE, and inference latency on held-out test data.
![Model Comparison](docs/images/models_screenshot.png)

### 4. SHAP Explainability & Feature Attribution
Local feature contributions indicating which meteorological or soil moisture factors drove water demand up or down.
![SHAP Explainability](docs/images/explainability_screenshot.png)

### 5. Meteorological & FAO-56 Penman-Monteith $ET_0$
Live Open-Meteo weather feeds with automated solar radiation and Penman-Monteith reference evapotranspiration calculation.
![Weather & ET0](docs/images/weather_screenshot.png)

### 6. CSV Dataset Management & Batch Ingestion
Drag-and-drop CSV batch processor evaluating multiple field plots simultaneously with automated download of sample templates.
![Dataset Management](docs/images/dataset_screenshot.png)

### 7. Persistent Prediction Audit Trail
SQLite-backed prediction history with multi-parameter search, filtering by crop and model, and inspection modals.
![Prediction History](docs/images/history_screenshot.png)

### 8. Executive Reports & Printable Audit
Printable, high-fidelity operational reports complete with water stewardship recommendations and export-ready print CSS.
![Reports View](docs/images/reports_screenshot.png)

---

## 🌟 Key Capabilities

1. **Volumetric Output in Litres**: Translates millimeter depth directly into tangible volume ($1\text{ mm} \times 1\text{ m}^2 = 1\text{ Litre}$, or $10,000\text{ Litres}$ per millimeter per hectare).
2. **ISRIC SoilGrids 250m Integration**: Retrieves authentic global 250m soil layers via OGC WCS 2.0.1 (clay %, sand %, silt %, pH, SOC, bulk density, CEC, nitrogen, and volumetric water retention at 10, 33, and 1500 kPa). Classified into 12 standard USDA Soil Texture Triangle classes with local SQLite caching.
3. **Multi-Model Suite**:
   - **XGBoost Regressor**: Gradient-boosted decision trees for tabular agro-climatic interactions.
   - **Artificial Neural Network (ANN)**: 3-layer deep Multi-Layer Perceptron (128-64-32) capturing continuous non-linearities.
   - **LSTM Sequence Regressor**: 2-layer PyTorch LSTM modeling temporal depletion trajectories.
   - **Ensemble Regressor**: Weighted consensus combining tree-based, neural, and sequence predictors.
4. **Strict Error Validation & Error Diagnostics**: Pydantic v2 and client-side boundary validation preventing invalid predictions (negative rainfall, area $\le 0$, out-of-range soil moisture or pH).
5. **5-Fold Cross-Validation & Residual Diagnostics**: 5-Fold CV metrics ($R^2$, RMSE, MAE, MAPE mean $\pm$ std) and residual error distributions ($y - \hat{y}$) for all models.
6. **Simulated Out-of-Distribution Benchmark Validation**: Stress-tested against an out-of-distribution benchmark dataset (600 records across 10 crops and 10 Indian regions calibrated to ICAR agronomic ranges) to evaluate domain shift robustness.
7. **SHAP TreeExplainer**: Local waterfall charts showing positive and negative marginal feature impacts.
8. **FAO-56 CROPWAT Foundation**: Complete integration of crop coefficients ($K_c$), Total Available Water ($TAW$), Readily Available Water ($RAW$), and distribution efficiency adjustments (Drip 90%, Sprinkler 75%, Flood 60%).
9. **Automatic GPS & Real-Time Weather Integration**: Browser GPS location detection with real-time Open-Meteo meteorological integration and offline dataset fallback.
10. **Batch Ingestion**: Evaluate arbitrary agricultural CSV files with instant downloadable results.
11. **SQLite Audit Trail**: Persistent storage of every prediction with full parameter telemetry.
12. **Printable Executive Reports**: Standardized reporting designed for farm managers and agronomists.

---

## 📊 Machine Learning Model Evaluation & 5-Fold Cross-Validation

All models were evaluated using strictly regression metrics ($R^2$, RMSE, MAE, MAPE, 5-Fold Cross-Validation, and residual distribution) saved in `ml/saved_models/evaluation_metrics.json`:

| Model Architecture | 5-Fold CV $R^2$ (Mean ± Std) | Test $R^2$ Score | RMSE ($mm$) | MAE ($mm$) | MAPE (%) | Inference Latency |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **LSTM Regressor (PyTorch)** ⭐ | **0.9867 ± 0.0008** | **0.9909** | **1.1791** | **0.8034** | **14.28%** | 0.52 ms |
| **Artificial Neural Network (ANN)** | **0.9800 ± 0.0020** | **0.9759** | **1.9178** | **1.1586** | **23.95%** | 0.12 ms |
| **XGBoost Regressor** | **0.9342 ± 0.0037** | **0.9259** | **3.3608** | **2.1758** | **34.66%** | 0.45 ms |

> **Model Selection Justification**:
> - **XGBoost**: Handles tabular agro-climatic interactions without feature scaling; exact local/global explainability via TreeSHAP.
> - **ANN (MLP)**: Universal continuous function approximator; lowest inference latency ($0.12\text{ ms}$).
> - **LSTM**: Highest explained variance ($R^2 = 99.09\%$, CV $R^2 = 0.9867$); models temporal lag in root-zone soil drying cycles.

---

## 🔬 Dataset Details & Synthetic Benchmark Notice

- **Dataset File**: `datasets/cropwater_dataset.csv` (5,000 samples).
- **Features (13)**: `crop_type`, `growth_stage`, `soil_type`, `soil_moisture_pct`, `temperature_c`, `humidity_pct`, `wind_speed_kmh`, `rainfall_mm`, `solar_radiation`, `et0_mm`, `crop_kc`, `irrigation_method`, `area_hectares`.
- **Target**: `water_requirement_mm` (Gross Irrigation Requirement in mm) and volumetric conversion in `litres`.
- **Agronomic Ground Truth**: Calibrated using FAO-56 standard formulas:
  $$ET_c = K_c \times ET_0$$
  $$\text{Effective Rainfall } P_{eff} = \max(0, (P \times 0.8) - 5)$$
  $$NIR = \max(0, ET_c - P_{eff} + \Delta S)$$
  $$GIR = NIR / \eta_{irrigation}$$
- **Data Status**: The benchmark dataset is a **synthetically generated agro-climatic benchmark dataset** generated via `ml/dataset_generator.py` with physical constraints and realistic $\pm 5\%$ stochastic sensor noise. It provides a standardized, leak-free testbed for model comparison, rather than uncalibrated raw field telemetry.

---

## 💧 Water Savings Estimation Methodology

The application displays an **Estimated Water Conserved** metric on the dashboard and executive reports:
- **Baseline**: Conventional surface flood irrigation typically operates at 50–60% application efficiency and often over-irrigates by applying fixed water schedules regardless of current root-zone moisture deficits.
- **Smart Precision Irrigation**: By calculating exact crop evapotranspiration ($ET_c$) and compensating only for the readily available water deficit ($RAW$), precision delivery (especially drip/sprinkler) eliminates runoff and deep percolation losses.
- **Formula**:
  $$\text{Water Saved (Litres)} = \text{Total Evaluated Demand (Litres)} \times 0.25$$
- **Classification**: This figure is an **estimated ~25% conservation saving** against conventional unmetered surface flooding based on FAO-56 water efficiency benchmarks.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide Icons |
| **Backend API** | FastAPI, Uvicorn, Pydantic v2, Python 3.13 |
| **Machine Learning** | PyTorch (`torch-cpu`), XGBoost, Scikit-learn, SHAP, NumPy, Pandas |
| **Persistence** | SQLite3 (`backend/data/cropwater.db`), Joblib artifacts (`ml/saved_models/`) |
| **Testing** | Pytest, AnyIO, TypeScript Compiler (`tsc`) |

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.13 (or 3.11+)
- Node.js v18+ or v20+ with npm
- Git

### 1. Backend Setup & Startup
```powershell
# Open terminal in project root
cd C:\Users\Ravi\OneDrive\Desktop\Cropwater-Compass

# Activate existing Python 3.13 virtual environment
.\.venv\Scripts\Activate.ps1

# (Optional) Verify dependencies
pip install -r backend/requirements.txt

# Run backend unit & integration tests (27 tests)
python -m pytest -v

# Start FastAPI server on port 8000
python -m uvicorn backend.app.main:app --reload --port 8000
```
- API is running at: [http://localhost:8000](http://localhost:8000)
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 2. Frontend Setup & Startup
In a separate terminal:
```powershell
# Set Node.js path if using portable distribution
$env:PATH = "$env:LOCALAPPDATA\Programs\nodejs;$env:PATH"

# Navigate to frontend
cd frontend

# Install dependencies (if first time)
npm install

# Start Vite development server
npm run dev
```
- Frontend application is live at: [http://localhost:5173](http://localhost:5173)

---

## 🧪 Test Suite Verification

Run the automated test suite covering agronomic math, ML model interfaces, API schemas, and end-to-end user workflows:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```
**Results: 44 passed in 17.57s (100% pass rate).**

To verify the frontend TypeScript and production bundle:
```powershell
cd frontend
npm run build
```
**Results: 2,392 modules transformed, built with 0 errors.**

---

## 📖 Comprehensive Documentation
- [Agronomic Foundations & Mathematical Formulation](docs/project_description.md)
- [System Architecture & API Route Reference](docs/architecture.md)
- [Step-by-Step Setup & Deployment Guide](docs/setup_guide.md)
- [Dataset Documentation & Provenance](datasets/README.md)

---

## 📜 License
Developed for educational and precision agricultural management. All rights reserved.
