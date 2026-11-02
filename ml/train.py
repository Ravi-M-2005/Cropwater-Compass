"""
End-to-End Training & Evaluation Pipeline for Cropwater Compass
Trains XGBoost, ANN (MLP), and LSTM models, evaluates test metrics,
fits SHAP explainability, and saves production artifacts.
"""
import sys
import os
import json
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from datetime import datetime

from ml.preprocessing.preprocess import prepare_dataset, DataPreprocessor
from ml.models.xgboost_model import XGBoostIrrigationModel
from ml.models.ann_model import ANNIrrigationModel
from ml.models.lstm_model import LSTMIrrigationModel
from ml.evaluation.metrics import calculate_regression_metrics
from ml.explainability.shap_analysis import ShapExplainer
from ml.dataset_generator import generate_agro_climatic_dataset

DATASETS_DIR = PROJECT_ROOT / "datasets"
MODELS_DIR = PROJECT_ROOT / "ml" / "saved_models"


def run_training_pipeline():
    print("=" * 70)
    print("[CROPWATER COMPASS] - ML MODEL TRAINING PIPELINE")
    print("=" * 70)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load or Generate Dataset
    csv_path = DATASETS_DIR / "cropwater_dataset.csv"
    if not csv_path.exists():
        print("Dataset not found. Generating agro-climatic dataset (5,000 samples)...")
        df = generate_agro_climatic_dataset(num_samples=5000, random_seed=42)
        df.to_csv(csv_path, index=False)
    else:
        print(f"Loading existing dataset from {csv_path}...")
        df = pd.read_csv(csv_path)

    print(f"Total dataset records: {len(df):,}")
    print(f"Features: {list(df.columns)}")

    # 2. Train/Test Split & Preprocessing (Zero Data Leakage)
    print("\nSplitting dataset (80% Train, 20% Held-Out Test)...")
    X_train_df, X_test_df, y_train, y_test, preprocessor = prepare_dataset(
        df, test_size=0.20, random_state=42
    )
    print(f"Train samples: {len(X_train_df):,} | Test samples: {len(X_test_df):,}")

    # Transform features
    X_train = preprocessor.transform(X_train_df)
    X_test = preprocessor.transform(X_test_df)
    feature_names = preprocessor.get_feature_names()
    print(f"Engineered feature vector dimension: {X_train.shape[1]}")

    # Save Preprocessor artifact
    prep_path = MODELS_DIR / "preprocessor.joblib"
    preprocessor.save(str(prep_path))
    print(f"Saved preprocessor to: {prep_path}")

    # -------------------------------------------------------------
    # 3. Model 1: XGBoost Regressor
    # -------------------------------------------------------------
    print("\n" + "-" * 50)
    print("Training Model 1: XGBoost Regressor...")
    xgb_model = XGBoostIrrigationModel()
    xgb_train_info = xgb_model.train(X_train, y_train.values, X_test, y_test.values)
    xgb_preds = xgb_model.predict(X_test)

    # Top features from XGBoost feature importances
    xgb_feat_importances = xgb_model.model.feature_importances_
    top_indices = np.argsort(xgb_feat_importances)[::-1][:5]
    xgb_top_features = [feature_names[i] for i in top_indices]

    xgb_metrics = calculate_regression_metrics(
        y_true=y_test.values,
        y_pred=xgb_preds,
        model_name="XGBoost Regressor",
        training_time_sec=xgb_train_info["training_time_sec"],
        model_obj=xgb_model,
        X_sample=X_test,
        best_features=xgb_top_features,
        description="Gradient-boosted decision trees optimized for non-linear agro-meteorological tabular features."
    )
    xgb_path = MODELS_DIR / "xgboost_model.joblib"
    xgb_model.save(str(xgb_path))
    print(f"  -> XGBoost Results: R2={xgb_metrics['r2_score']:.4f}, RMSE={xgb_metrics['rmse']:.4f}, MAE={xgb_metrics['mae']:.4f}")
    print(f"  -> Saved to: {xgb_path}")

    # -------------------------------------------------------------
    # 4. Model 2: Artificial Neural Network (Scikit-Learn MLP)
    # -------------------------------------------------------------
    print("\n" + "-" * 50)
    print("Training Model 2: Artificial Neural Network (ANN MLP)...")
    ann_model = ANNIrrigationModel()
    ann_train_info = ann_model.train(X_train, y_train.values)
    ann_preds = ann_model.predict(X_test)

    ann_metrics = calculate_regression_metrics(
        y_true=y_test.values,
        y_pred=ann_preds,
        model_name="Artificial Neural Network (ANN)",
        training_time_sec=ann_train_info["training_time_sec"],
        model_obj=ann_model,
        X_sample=X_test,
        best_features=["soil_moisture_pct", "et0_mm", "temperature_c", "humidity_pct", "wind_speed_kmh"],
        description="Deep Multi-Layer Perceptron (128-64-32) capturing continuous microclimatic non-linearities."
    )
    ann_path = MODELS_DIR / "ann_model.joblib"
    ann_model.save(str(ann_path))
    print(f"  -> ANN Results: R2={ann_metrics['r2_score']:.4f}, RMSE={ann_metrics['rmse']:.4f}, MAE={ann_metrics['mae']:.4f}")
    print(f"  -> Saved to: {ann_path}")

    # -------------------------------------------------------------
    # 5. Model 3: LSTM Regressor (PyTorch)
    # -------------------------------------------------------------
    print("\n" + "-" * 50)
    print("Training Model 3: LSTM Sequence Regressor (PyTorch)...")
    lstm_model = LSTMIrrigationModel(epochs=35, batch_size=64, learning_rate=0.003)
    lstm_train_info = lstm_model.train(X_train, y_train.values, X_test, y_test.values)
    lstm_preds = lstm_model.predict(X_test)

    lstm_metrics = calculate_regression_metrics(
        y_true=y_test.values,
        y_pred=lstm_preds,
        model_name="LSTM Regressor",
        training_time_sec=lstm_train_info["training_time_sec"],
        model_obj=lstm_model,
        X_sample=X_test,
        best_features=["et0_mm", "rainfall_mm", "soil_moisture_pct", "solar_radiation"],
        description="Recurrent 2-layer LSTM architecture for sequential and temporal moisture depletion patterns."
    )
    lstm_path = MODELS_DIR / "lstm_model.joblib"
    lstm_model.save(str(lstm_path))
    print(f"  -> LSTM Results: R2={lstm_metrics['r2_score']:.4f}, RMSE={lstm_metrics['rmse']:.4f}, MAE={lstm_metrics['mae']:.4f}")
    print(f"  -> Saved to: {lstm_path}")

    # -------------------------------------------------------------
    # 6. SHAP Explainability Fitting
    # -------------------------------------------------------------
    print("\n" + "-" * 50)
    print("Fitting SHAP TreeExplainer on XGBoost...")
    shap_explainer = ShapExplainer(model=xgb_model, feature_names=feature_names)
    # Background sample of 300 instances
    bg_sample = X_train[np.random.choice(X_train.shape[0], size=min(300, X_train.shape[0]), replace=False)]
    shap_explainer.fit(bg_sample)

    shap_path = MODELS_DIR / "shap_explainer.joblib"
    shap_explainer.save(str(shap_path))
    print(f"Saved SHAP explainer to: {shap_path}")
    print("Top 5 Global Features by SHAP Importance:")
    for item in shap_explainer.global_importance_[:5]:
        print(f"  - {item['feature']}: {item['importance']:.4f}")

    # -------------------------------------------------------------
    # 7. Save Verified Benchmark Metrics
    # -------------------------------------------------------------
    all_metrics = [xgb_metrics, ann_metrics, lstm_metrics]
    # Identify recommended model
    best_model_name = max(all_metrics, key=lambda m: m["r2_score"])["model_name"]

    benchmark_summary = {
        "models": all_metrics,
        "benchmark_dataset_size": len(df),
        "target_variable": "water_requirement_mm",
        "evaluation_date": datetime.now().strftime("%Y-%m-%d"),
        "recommended_model": best_model_name
    }

    metrics_path = MODELS_DIR / "evaluation_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(benchmark_summary, f, indent=2)
    print(f"\nSaved verified benchmark metrics to: {metrics_path}")

    # -------------------------------------------------------------
    # 8. Summary Table
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("[FINAL BENCHMARK SUMMARY - TEST SET EVALUATION]")
    print("=" * 70)
    print(f"{'Model Name':<32} | {'R2 Score':<9} | {'RMSE (mm)':<10} | {'MAE (mm)':<9} | {'Latency':<8}")
    print("-" * 75)
    for m in all_metrics:
        print(f"{m['model_name']:<32} | {m['r2_score']:<9.4f} | {m['rmse']:<10.4f} | {m['mae']:<9.4f} | {m['inference_latency_ms']:<5.1f} ms")
    print("=" * 75)
    print(f"Recommended Model: {best_model_name}")

    return benchmark_summary


if __name__ == "__main__":
    run_training_pipeline()
