"""
Tests for Model Evaluation, 5-Fold Cross-Validation, Residual Analysis,
and Independent Dataset Evaluation (Reviewer Feedback Parts B, C, D).
"""
import pytest
import numpy as np
from ml.evaluation.metrics import calculate_mape, calculate_residual_analysis
from backend.app.services.ml_service import get_models_benchmark_metrics
from backend.app.schemas.schemas import ModelsComparisonResponse


def test_mape_calculation_zero_protection():
    """Verifies calculate_mape avoids division by zero on zero-irrigation/heavy-rainfall instances."""
    y_true = np.array([0.0, 0.2, 5.0, 10.0])
    y_pred = np.array([0.1, 0.3, 4.5, 9.0])

    mape = calculate_mape(y_true, y_pred, min_threshold=0.5)
    assert mape > 0
    assert not np.isnan(mape)
    assert not np.isinf(mape)
    # 5.0 vs 4.5 -> 10%; 10.0 vs 9.0 -> 10% -> Mean MAPE = 10%
    assert abs(mape - 10.0) < 0.1


def test_residual_analysis_structure():
    """Verifies calculate_residual_analysis generates bias, quantiles, and histogram bins."""
    y_true = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
    y_pred = np.array([1.9, 4.2, 5.8, 8.1, 9.7])

    analysis = calculate_residual_analysis(y_true, y_pred, num_bins=5)
    assert "mean_residual" in analysis
    assert "std_residual" in analysis
    assert "quantiles" in analysis
    assert "p10" in analysis["quantiles"]
    assert "p50" in analysis["quantiles"]
    assert "p90" in analysis["quantiles"]
    assert "error_distribution" in analysis
    assert len(analysis["error_distribution"]) == 5
    assert "actual_vs_predicted" in analysis


def test_models_benchmark_metrics_contains_cv_and_residuals():
    """Verifies that get_models_benchmark_metrics serves 5-fold CV, residuals, justifications, and external validation."""
    data = get_models_benchmark_metrics()
    parsed = ModelsComparisonResponse(**data)

    assert len(parsed.models) == 3
    for model in parsed.models:
        assert model.r2_score > 0
        assert model.rmse > 0
        assert model.mae > 0
        assert model.mape is not None
        assert model.cross_validation is not None
        assert model.cross_validation.k_folds == 5
        assert model.cross_validation.r2_mean > 0.90
        assert model.residual_analysis is not None
        assert model.residual_analysis.residual_std > 0
        assert len(model.residual_analysis.distribution_bins) > 0
        assert len(model.strengths) > 0
        assert len(model.limitations) > 0
        assert model.suitability_reason != ""

    assert parsed.external_dataset_validation is not None
    assert parsed.external_dataset_validation.total_records == 600
    assert "XGBoost Regressor" in parsed.external_dataset_validation.metrics_by_model
    assert "Artificial Neural Network (ANN)" in parsed.external_dataset_validation.metrics_by_model
    assert "LSTM Regressor" in parsed.external_dataset_validation.metrics_by_model


def test_api_models_comparison_endpoint():
    """Tests get_model_comparison returns comprehensive comparison response."""
    from backend.app.routes.prediction import get_model_comparison
    json_data = get_model_comparison()
    assert "models" in json_data
    assert "model_justifications" in json_data
    assert "external_dataset_validation" in json_data
    assert len(json_data["models"]) == 3
