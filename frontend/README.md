# Cropwater Compass – Frontend Dashboard

Modern, responsive Agricultural Decision Support System built with React, Vite, TypeScript, and Tailwind CSS.

---

## 🌟 Application Modules

1. **Dashboard (`DashboardView.tsx`)**:
   - Total recommended water in **Litres** and cubic meters ($m^3$).
   - Estimated water conserved via precision micro-irrigation (~25% vs unmetered surface flood).
   - Dynamic charts: Cumulative water demand by crop (BarChart), Water demand by soil class (Donut).
   - Recent field evaluations table with urgency flags.

2. **Irrigation Prediction (`PredictionView.tsx`)**:
   - Complete plot input form: Crop selection, Growth stage (Initial, Vegetative, Mid-season, Late), Farm area (Ha, Acres, m²), Soil type (6 classes), Soil moisture %, Soil pH, and Microclimate parameters.
   - Sensor auto-fill integration with live weather API.
   - High-impact result panel with headline **Water Requirement in Litres**, gross depth in mm, urgency badge, and application schedule (days interval, duration in hours, optimal time window).
   - Direct link to SHAP feature attribution.

3. **Weather & ET₀ (`WeatherView.tsx`)**:
   - Real-time air temperature, relative humidity, 2m wind velocity, precipitation, and incident solar radiation.
   - FAO-56 Penman-Monteith daily Reference Evapotranspiration ($ET_0$) gauge.
   - 7-day agricultural weather and $ET_0$ projection trend chart.
   - Regional selector for major agricultural production basins.

4. **Model Comparison (`ModelComparisonView.tsx`)**:
   - Side-by-side empirical metrics: XGBoost Regressor ($R^2=0.9595$), ANN ($R^2=0.9869$), and PyTorch LSTM ($R^2=0.9941$).
   - Comparative BarCharts for $R^2$ accuracy, RMSE error, and inference latency.

5. **Explainability (`ExplainabilityView.tsx`)**:
   - SHAP (SHapley Additive exPlanations) TreeExplainer waterfall chart.
   - Explicitly displays factors increasing water requirement (e.g. elevated temperature, arid wind, sandy soil) versus factors decreasing water requirement (e.g. soil moisture, rainfall, drip efficiency).

6. **Dataset & CSV (`DatasetView.tsx`)**:
   - File drag-and-drop / upload for agricultural CSV datasets.
   - Sample CSV template downloader.
   - Batch evaluation summary and plot previews.

7. **History & Audit (`HistoryView.tsx`)**:
   - Filterable, searchable audit trail of past evaluations backed by SQLite.
   - Modal viewer for detailed agronomic parameters.
   - Record deletion and history clearing.

8. **Executive Reports (`ReportsView.tsx`)**:
   - Comprehensive printable operational report with print-optimized CSS (`@media print`).
   - Actionable water stewardship recommendations.

---

## 🚀 Execution Instructions

### Development Mode:
```powershell
# From the frontend directory
npm run dev
```
The application will be running at [http://localhost:5173](http://localhost:5173) and proxying `/api` requests to the FastAPI backend at [http://localhost:8000](http://localhost:8000).

### Production Build:
```powershell
npm run build
```
Emits optimized static bundles to `frontend/dist/`.
