You have shared the complete GitHub repository page for Cropwater Compass – Smart Irrigation Management System Using Machine Learning.

Below is the complete project information organized into sections, suitable for your project documentation, presentation, and explanation.

# 🌱 CROPWATER COMPASS

Smart Irrigation Management System Using Machine Learning

GitHub Repository

[https://github.com/Ravi-M-2005/Cropwater-Compass](https://github.com/Ravi-M-2005/Cropwater-Compass?utm_source=chatgpt.com)

Live Application

[https://frontend-two-chi-90.vercel.app/](https://frontend-two-chi-90.vercel.app/?utm_source=chatgpt.com)

## 1. Project Overview

Cropwater Compass is a full-stack, machine-learning-based smart irrigation management system designed to calculate the amount of water required by different crops.

Instead of simply predicting whether irrigation is required or not, the system estimates the exact irrigation water requirement in:

- Litres (L)
- Cubic metres (m³)
- Millimetres (mm)

It combines machine learning models with FAO-56 CROPWAT agricultural calculations, weather information, and soil properties to support efficient irrigation management.

## 2. Problem Statement

Traditional irrigation methods often apply water based on fixed schedules without considering actual crop water requirements.

This can lead to:

- Excessive water usage.
- Water wastage.
- Uneven irrigation.
- Reduced crop productivity.
- Increased agricultural costs.

Cropwater Compass addresses these problems by estimating the required irrigation water based on crop, soil, weather, and field conditions.

## 3. Main Objectives

1. Predict the irrigation water requirement for different crops.
2. Reduce unnecessary water usage.
3. Integrate machine learning models for water prediction.
4. Retrieve soil information using SoilGrids.
5. Use weather information for irrigation calculations.
6. Provide explainable predictions.
7. Maintain prediction history and generate reports.

## 4. Technologies Used

| Layer            | Technologies            |
| ---------------- | ----------------------- |
| Frontend         | React, TypeScript, Vite |
| Styling          | Tailwind CSS            |
| Backend          | FastAPI, Python         |
| Database         | SQLite                  |
| Machine Learning | XGBoost, ANN, LSTM      |
| Deep Learning    | PyTorch                 |
| Explainability   | SHAP                    |
| Weather API      | Open-Meteo              |
| Soil Data        | ISRIC SoilGrids         |
| Charts           | Recharts                |
| Testing          | Pytest, TypeScript      |
| Deployment       | Vercel, Render          |
| Version Control  | Git, GitHub             |

## 5. Machine Learning Models

The system uses three main machine learning models and an ensemble approach.

1\. XGBoost Regressor

- Uses gradient-boosted decision trees.
- Handles structured agricultural data.
- Predicts irrigation water requirements.

2\. Artificial Neural Network (ANN)

- Uses interconnected neural network layers.
- Learns complex relationships between input features.
- Predicts continuous water requirements.

3\. Long Short-Term Memory (LSTM)

- Uses recurrent neural network architecture.
- Learns temporal patterns in soil moisture and water depletion.
- Predicts irrigation requirements using sequence information.

4\. Ensemble Model

- Combines predictions from multiple models.
- Provides a weighted consensus prediction.

## 6. Model Performance

The following values are reported in the repository README.

| Model   | Test R² | RMSE (mm) | MAE (mm) |
| ------- | ------- | --------- | -------- |
| LSTM    | 0.9909  | 1.1791    | 0.8034   |
| ANN     | 0.9759  | 1.9178    | 1.1586   |
| XGBoost | 0.9259  | 3.3608    | 2.1758   |

Best-performing model: LSTM, based on the reported held-out test R².

Note: These results are based on the project's generated/calibrated dataset. They should not be presented as proof of real-world farm validation.

## 7. Dataset Details

Main dataset: `datasets/cropwater_dataset.csv`

- Total records: 5,000.
- Input features: 13.
- Target: Water requirement in millimetres.

Input features include:

1. Crop type.
2. Growth stage.
3. Soil type.
4. Soil moisture.
5. Temperature.
6. Humidity.
7. Wind speed.
8. Rainfall.
9. Solar radiation.
10. Reference evapotranspiration (ET₀).
11. Crop coefficient (Kc).
12. Irrigation method.
13. Farm area.

The main dataset is synthetically generated using agronomic calculations and physical constraints. It is not a collection of 5,000 real farm observations.

## 8. SoilGrids Integration

The application integrates ISRIC SoilGrids 250m soil data.

It retrieves soil properties such as:

- Clay percentage.
- Sand percentage.
- Silt percentage.
- Soil pH.
- Soil organic carbon.
- Bulk density.
- Cation exchange capacity.
- Nitrogen.
- Soil water retention.

The system uses these properties to classify soil into USDA soil texture classes and estimate available water characteristics.

## 9. Weather Integration

The system uses the Open-Meteo API to retrieve weather information.

Weather parameters include:

- Temperature.
- Humidity.
- Wind speed.
- Rainfall.
- Solar radiation.

It also calculates reference evapotranspiration (ET₀) using the FAO-56 Penman-Monteith method.

## 10. FAO-56 CROPWAT Calculation

The project uses agricultural water requirement calculations.

Important parameters:

- ET₀: Reference evapotranspiration.
- Kc: Crop coefficient.
- ETc: Crop evapotranspiration.
- TAW: Total Available Water.
- RAW: Readily Available Water.
- NIR: Net Irrigation Requirement.
- GIR: Gross Irrigation Requirement.

Main equations:

\\[ ET_c=K_c\times ET_0 \\]

\\[ P\_{eff}=\max(0,(P\times0.8)-5) \\]

\\[ NIR=\max(0,ET_c-P\_{eff}+\Delta S) \\]

\\[ GIR=\frac{NIR}{\eta\_{irrigation}} \\]

The calculated water depth is converted into litres using:

\\[ Water(L)=Depth(mm)\times Area(m^2) \\]

## 11. Main Application Modules

[Irrigation Dashboard - Concept by Satyajit Mane on Dribbble](https://images.openai.com/static-rsc-4/lkPuaPlt50-tfj7FJ5Sf9qAUq2v2y0Sy6tCNftn-Fy1wghsrzhs_KNhmVCw1Y4bvDonbx-WnhQCaSFcSR_7Y6mWuhelbKrBghDbJIy9Ec9zCxPQC8gEHuQ7wv1UlqIK-ShPoPgO6geD416lmd0n2i0GNce0doVCb8orVro5wIco?purpose=inline)

1\. Dashboard

Displays total recommended water, estimated water conserved, crop demand, and recent predictions.

[CornSoyWater: Real-Time Aid for Corn and Soybean Irrigation Decisions | CropWatch | Nebraska](https://images.openai.com/static-rsc-4/CNNmPwKO1GBgbRwnW5mMnJlfn3FM6cxnjr3cavdJOyqcxRZpmgfxXtWNd1aW5n4bKb-uKNHLLCyA2hSX5i1qmbAUkCpSecyBAAhy9esjUJdcvj7MDoV28HYwrX6B4B4a3fjzQRviRfa59pP-M-TlR_Xc7u3ZoA9awMiCXr4Ky5w?purpose=inline)

2\. Irrigation Prediction

Accepts farm, crop, soil, and weather details to estimate water requirements.

[PyCaret inside Streamlit - Using Streamlit - Streamlit](https://images.openai.com/static-rsc-4/8bwPUTzHvHzmq_tEY_r-u9y30G68EhBJkyuDHTnKees4788A7_1Yxa4YUfYsbf63DIgicJZb5PRKeISuCtWUpxmOSwxWpT7p2emTXva_8Kxl2gAH8UkvQ-iapqmI-0SmpbRRKNvnwApGjRAy6c_DdjZpClv9fJRAFCkOAQNJgAI?purpose=inline)

3\. Model Comparison

Compares XGBoost, ANN, and LSTM performance using regression metrics.

[Lecture 12: Feature importances and model transparency — CPSC 330 Applied Machine Learning 2025S](https://images.openai.com/static-rsc-4/9UQYcM2qRY1M1IbBIKRRPDiBT8roiBzbo-SY-v4e7M4gPMWerBgg_ZS4jvKT3RxDyRxVuTg2rfh_aRrzEZALiqyGUsQa2HqPmA9y2QV0K_d3zVFKu1BhRLj54-w4a71tKn-9NRBSf1DCB1XLDG1KXEtXYnHeukdsEtk4tJXNLg0?purpose=inline)

4\. SHAP Explainability

Explains how soil and weather features influence predictions.

[Weather Dashboard Examples | Explore Custom PWS Layouts](https://images.openai.com/static-rsc-4/7rKUhVU746M3M0boGDZBGw5Kpd-pSZs4B3LtGztabouWCJtSwT99UaA8WvHTh6yLrmS_8SbhkCTb6c25fDI-XGoIuyKYC2f7CzY-dWzGpSb8iVPHv4JVhX1Zyq6RcArf08siVeypUbKF-i5k9-nLsFS6OW8EkkOJXLs8K9fh5sI?purpose=inline)

5\. Weather and ET₀

Displays live weather information and evapotranspiration calculations.

[Datasets - Docs - Faraday](https://images.openai.com/static-rsc-4/V5X6RDQZ4kdU8BRC16enRRkK729S5hznrZHnD-JvEairern1He54m_f_aARhKQd8_2MsFtpQ9-S7alDYZ5dtaaBT-i-JGA9k7sSn8Fdre5Sd0CfOBGfvIx9al1W9wclvlG7QfwY9kzDS-9W2SzS2R3R3mYhxQruHCZNsiGwoluo?purpose=inline)

6\. Dataset Management

Supports CSV uploads, batch prediction, and downloading results.

[Mutus Tech | AI-Powered Farm Intelligence for Sustainable Agriculture](https://images.openai.com/static-rsc-4/Whun3ujEMf4wvmGCy49AgltWq-ljbNJ04SMMzpB-Q89c3B0uDG2tbuMa4r1REF52hOSy2tpdfynj-rGtFmfL9w0S_M4gLcROTr6roW1nqyd5E_f44vc7lhaYjvjxX5gZTYzylRDCn4CUzBv283jqFBLwEZiVP72rPUcm640HPvU?purpose=inline)

7\. Prediction History

Stores previous predictions and supports searching and filtering.

[Water Efficiency Dashboard for Agriculture | Mokkup.ai](https://images.openai.com/static-rsc-4/oYRgOfLKjGiFQgdxU6pCqI7fN6qyLSyno_lBEWKrY7zkZSELuQIXtQWdhnILl2-rD5IWweSeMEEEaPbjT5Ar1RH2-Qcb5ZhL9HolnZNaVKsmSjsgtoVtBRlP5n8yE_5T2tbr06FuLY8SYxAaYcPVJpbwl65SR8sMjCY3rPOwoY8?purpose=inline)

8\. Reports

Generates printable reports containing prediction details and water-saving estimates.

## 12. Water Conservation

The application estimates water conservation by comparing recommended water demand with a conventional irrigation baseline.

The project uses the following estimation:

\\[ WaterSaved=TotalDemand\times0.25 \\]

This represents an estimated 25% saving, not a measured result from field experiments.

## 13. System Architecture

User Interface

React · TypeScript · Tailwind CSS

Backend API

FastAPI · Python · Pydantic

ML Models

XGBoost · ANN · LSTM

Agronomic Engine

FAO-56 · ET₀ · CROPWAT

External Data

Open-Meteo · SoilGrids

Database

SQLite

Irrigation Prediction Results

Litres · Cubic metres · Water depth · Reports

## 14. Testing and Verification

According to the repository README:

- Backend tests: 44 passed.
- Frontend TypeScript compilation: successful.
- Frontend production build: successful.
- Production backend API checks: previously reported successful.
- Frontend deployment: Vercel.
- Backend deployment: Render.

## 15. Deployment Links

| Component   | Platform |
| ----------- | -------- |
| Frontend    | Vercel   |
| Backend     | Render   |
| Source code | GitHub   |

- Frontend: [https://frontend-two-chi-90.vercel.app/](https://frontend-two-chi-90.vercel.app/?utm_source=chatgpt.com)
- Backend: [https://cropwater-compass.onrender.com](https://cropwater-compass.onrender.com?utm_source=chatgpt.com)
- GitHub: [https://github.com/Ravi-M-2005/Cropwater-Compass](https://github.com/Ravi-M-2005/Cropwater-Compass?utm_source=chatgpt.com)

## 16. Advantages

1. Helps estimate crop-specific irrigation requirements.
2. Supports multiple crops and soil types.
3. Uses machine learning for prediction.
4. Integrates real-time weather data.
5. Retrieves soil information from SoilGrids.
6. Provides explainable predictions.
7. Supports batch CSV processing.
8. Maintains prediction history.
9. Generates printable reports.
10. Helps reduce unnecessary water usage.

## 17. Limitations

1. The main training dataset is synthetically generated.
2. Predictions require real-world agricultural validation.
3. Live weather and soil data require internet access.
4. Render free-tier services may take time to start after inactivity.
5. Actual water savings depend on field conditions, irrigation equipment, and farmer practices.

## 18. Future Enhancements

1. Integrate IoT soil moisture sensors.
2. Connect ESP32 or Arduino devices.
3. Automate water pumps using relay modules.
4. Collect real farm datasets.
5. Improve model performance using field observations.
6. Develop a mobile application.
7. Add multilingual support for farmers.
8. Provide automatic irrigation scheduling.

## 19. Conclusion

Cropwater Compass is a smart irrigation management platform that combines machine learning, agricultural calculations, weather information, and soil data to estimate crop water requirements. It provides predictions in litres, cubic metres, and millimetres, helping users make better irrigation decisions and reduce unnecessary water usage.

The project demonstrates how machine learning and agricultural technology can be combined to support precision agriculture and sustainable water management.

Important: The above is a complete organized explanation based on the GitHub README you shared. It is not a replacement for a formal college project report, which may additionally require an abstract, literature survey, methodology, implementation details, screenshots, references, and bibliography.
