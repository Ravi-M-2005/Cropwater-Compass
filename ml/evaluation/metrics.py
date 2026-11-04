"""
Model Evaluation and Benchmark Metrics Calculation
Computes R², RMSE, MAE, MSE, MAPE, residual distribution, and cross-validation metrics.
Strictly regression metrics for continuous water requirement depth (mm).
"""
import time
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error


def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray, min_threshold: float = 0.5) -> float:
    """
    Computes Mean Absolute Percentage Error (MAPE) on significant irrigation events (> min_threshold mm).
    Avoids mathematically invalid division by zero on zero-irrigation heavy rainfall observations.
    """
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)
    mask = y_t >= min_threshold
    if np.sum(mask) == 0:
        return 0.0
    return float(np.mean(np.abs((y_t[mask] - y_p[mask]) / y_t[mask])) * 100.0)


def calculate_residual_analysis(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    num_bins: int = 10,
    sample_size: int = 100
) -> Dict[str, Any]:
    """
    Computes detailed residual analysis (errors = actual - predicted)
    including mean bias, standard deviation, error distribution histogram, and paired scatter data.
    """
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)
    residuals = y_t - y_p

    mean_res = float(np.mean(residuals))
    std_res = float(np.std(residuals))
    median_res = float(np.median(residuals))

    # Error distribution histogram
    hist, bin_edges = np.histogram(residuals, bins=num_bins)
    distribution = []
    for i in range(len(hist)):
        distribution.append({
            "bin_start": round(float(bin_edges[i]), 2),
            "bin_end": round(float(bin_edges[i + 1]), 2),
            "label": f"{bin_edges[i]:.1f} to {bin_edges[i + 1]:.1f}",
            "count": int(hist[i])
        })

    # Sample actual vs predicted pairs for scatter visualization
    indices = np.linspace(0, len(y_t) - 1, min(sample_size, len(y_t)), dtype=int)
    actual_vs_predicted = [
        {
            "actual": round(float(y_t[i]), 2),
            "predicted": round(float(y_p[i]), 2),
            "residual": round(float(residuals[i]), 2)
        }
        for i in indices
    ]

    return {
        "mean_residual": round(mean_res, 4),
        "std_residual": round(std_res, 4),
        "median_residual": round(median_res, 4),
        "quantiles": {
            "p10": round(float(np.percentile(residuals, 10)), 3),
            "p25": round(float(np.percentile(residuals, 25)), 3),
            "p50": round(median_res, 3),
            "p75": round(float(np.percentile(residuals, 75)), 3),
            "p90": round(float(np.percentile(residuals, 90)), 3),
        },
        "error_distribution": distribution,
        "actual_vs_predicted": actual_vs_predicted
    }


def calculate_regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str,
    training_time_sec: float = 0.0,
    model_obj: Any = None,
    X_sample: np.ndarray = None,
    best_features: List[str] = None,
    description: str = "",
    cv_scores: Optional[Dict[str, Any]] = None,
    external_validation: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes genuine regression metrics on held-out test data.
    """
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)

    r2 = float(r2_score(y_t, y_p))
    mse = float(mean_squared_error(y_t, y_p))
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_t, y_p))
    mape = calculate_mape(y_t, y_p, min_threshold=0.5)

    # Benchmark single-instance latency in ms
    latency_ms = 1.0
    if model_obj is not None and X_sample is not None and len(X_sample) > 0:
        single_x = X_sample[:1]
        latencies = []
        for _ in range(30):
            t0 = time.perf_counter()
            _ = model_obj.predict(single_x)
            latencies.append((time.perf_counter() - t0) * 1000.0)
        latency_ms = float(np.median(latencies))

    # Error and residual analysis
    residuals_info = calculate_residual_analysis(y_t, y_p)

    return {
        "model_name": model_name,
        "r2_score": round(r2, 4),
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "mse": round(mse, 4),
        "mape_pct": round(mape, 2),
        "training_time_sec": round(training_time_sec, 3),
        "inference_latency_ms": round(latency_ms, 2),
        "best_features": best_features or [],
        "description": description,
        "cross_validation": cv_scores or {},
        "residual_analysis": residuals_info,
        "external_validation": external_validation or {}
    }
