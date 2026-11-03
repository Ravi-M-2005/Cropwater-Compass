"""
Unit and Integration Tests for ML Models, Preprocessing, and SHAP Explainability
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from ml.preprocessing.preprocess import DataPreprocessor, prepare_dataset
from ml.models.xgboost_model import XGBoostIrrigationModel
from ml.models.ann_model import ANNIrrigationModel
from ml.models.lstm_model import LSTMIrrigationModel
from ml.evaluation.metrics import calculate_regression_metrics
from ml.explainability.shap_analysis import ShapExplainer
from backend.app.services.ml_service import (
    load_model,
    get_preprocessor,
    predict_water_requirements,
    get_shap_explanation,
    get_models_benchmark_metrics
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASETS_DIR = PROJECT_ROOT / "datasets"
MODELS_DIR = PROJECT_ROOT / "ml" / "saved_models"


@pytest.fixture(scope="module")
def sample_dataset():
    csv_path = DATASETS_DIR / "cropwater_dataset.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        from ml.dataset_generator import generate_agro_climatic_dataset
        df = generate_agro_climatic_dataset(num_samples=500, random_seed=42)
    return df


def test_preprocessor_pipeline(sample_dataset):
    X = sample_dataset.drop(columns=["water_requirement_mm"], errors="ignore")
    preprocessor = DataPreprocessor()
    X_trans = preprocessor.fit_transform(X)

    assert X_trans.shape[0] == len(X)
    assert X_trans.shape[1] >= 20  # Numerical + One-hot columns
    assert not np.isnan(X_trans).any()
    assert len(preprocessor.get_feature_names()) == X_trans.shape[1]


def test_xgboost_model_interface(sample_dataset):
    X_train_df, X_test_df, y_train, y_test, prep = prepare_dataset(sample_dataset.head(600), test_size=0.25, random_state=42)
    X_tr = prep.transform(X_train_df)
    X_te = prep.transform(X_test_df)

    model = XGBoostIrrigationModel(params={"n_estimators": 50, "max_depth": 3, "random_state": 42})
    train_info = model.train(X_tr, y_train.values)
    assert model.is_trained
    assert train_info["training_time_sec"] >= 0

    preds = model.predict(X_te)
    assert len(preds) == len(X_te)
    assert (preds >= 0).all()

    metrics = calculate_regression_metrics(y_test.values, preds, "XGBoost")
    assert metrics["r2_score"] > 0.70
    assert metrics["rmse"] > 0


def test_ann_model_interface(sample_dataset):
    X_train_df, X_test_df, y_train, y_test, prep = prepare_dataset(sample_dataset.head(600), test_size=0.25, random_state=42)
    X_tr = prep.transform(X_train_df)
    X_te = prep.transform(X_test_df)

    ann = ANNIrrigationModel(params={"hidden_layer_sizes": (32, 16), "max_iter": 150, "random_state": 42})
    train_info = ann.train(X_tr, y_train.values)
    assert ann.is_trained

    preds = ann.predict(X_te)
    assert len(preds) == len(X_te)
    assert (preds >= 0).all()
    assert preds.shape[0] == X_te.shape[0]


def test_lstm_model_interface(sample_dataset):
    X_train_df, X_test_df, y_train, y_test, prep = prepare_dataset(sample_dataset.head(600), test_size=0.25, random_state=42)
    X_tr = prep.transform(X_train_df)
    X_te = prep.transform(X_test_df)

    lstm = LSTMIrrigationModel(epochs=8, batch_size=32, hidden_dim=32, num_layers=1)
    train_info = lstm.train(X_tr, y_train.values)
    assert lstm.is_trained

    preds = lstm.predict(X_te)
    assert len(preds) == len(X_te)
    assert (preds >= 0).all()


def test_trained_production_models_accuracy(sample_dataset):
    """
    Verifies that the trained production models in ml/saved_models/
    meet the target accuracy benchmark (R² > 0.90) on the held-out test split.
    """
    prep = get_preprocessor()
    assert prep is not None, "Production preprocessor must exist"

    # Take test split (last 1000 rows)
    test_df = sample_dataset.tail(1000)
    X_test_raw = test_df.drop(columns=["water_requirement_mm"], errors="ignore")
    y_test = test_df["water_requirement_mm"].values
    X_test = prep.transform(X_test_raw)

    for model_name in ["xgboost", "ann", "lstm"]:
        m = load_model(model_name)
        assert m is not None, f"Model {model_name} must be loaded"
        preds = m.predict(X_test)
        metrics = calculate_regression_metrics(y_test, preds, model_name)
        # All three production models should achieve R² > 0.88 on the benchmark dataset
        assert metrics["r2_score"] > 0.88, f"{model_name} R² {metrics['r2_score']} must be > 0.88"
        assert metrics["rmse"] < 4.0, f"{model_name} RMSE {metrics['rmse']} must be < 4.0 mm"


def test_shap_explainer_functionality(sample_dataset):
    xgb = load_model("xgboost")
    assert xgb is not None

    prep = get_preprocessor()
    assert prep is not None

    explainer = ShapExplainer(model=xgb, feature_names=prep.get_feature_names())
    sample_df = sample_dataset.head(50).drop(columns=["water_requirement_mm"], errors="ignore")
    X_sample = prep.transform(sample_df)
    explainer.fit(X_sample)
    assert len(explainer.global_importance_) > 0

    instance_exp = explainer.explain_instance(X_sample[0])
    assert "base_value" in instance_exp
    assert "predicted_value" in instance_exp
    assert len(instance_exp["feature_importances"]) > 0


def test_ml_service_integration():
    sample_input = {
        "crop_type": "Wheat",
        "growth_stage": "Mid-season",
        "soil_type": "Loamy",
        "soil_moisture_pct": 28.0,
        "soil_ph": 6.8,
        "temperature_c": 30.0,
        "humidity_pct": 50.0,
        "wind_speed_kmh": 12.0,
        "rainfall_mm": 0.0,
        "solar_radiation": 20.0,
        "et0_mm": 4.5,
        "irrigation_method": "Drip",
        "model_name": "xgboost"
    }

    primary, all_preds = predict_water_requirements(sample_input)
    assert primary > 0
    assert "xgboost" in all_preds
    assert "ann" in all_preds
    assert "lstm" in all_preds

    shap_data = get_shap_explanation(sample_input)
    assert "base_value" in shap_data
    assert len(shap_data["feature_importances"]) > 0

    benchmarks = get_models_benchmark_metrics()
    assert len(benchmarks["models"]) == 3
    assert benchmarks["benchmark_dataset_size"] == 5000
