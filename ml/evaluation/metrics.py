"""
Model Evaluation and Benchmark Metrics Calculation
Computes R², RMSE, MAE, MSE, and inference latency across regression models.
"""
import time
import numpy as np
from typing import Dict, Any, List
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error


def calculate_regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str,
    training_time_sec: float = 0.0,
    model_obj: Any = None,
    X_sample: np.ndarray = None,
    best_features: List[str] = None,
    description: str = ""
) -> Dict[str, Any]:
    """
    Computes genuine regression metrics on the held-out test set.
    """
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)

    r2 = float(r2_score(y_t, y_p))
    mse = float(mean_squared_error(y_t, y_p))
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_t, y_p))

    # Benchmark inference latency (average ms across 100 single-item predictions)
    latency_ms = 1.0
    if model_obj is not None and X_sample is not None and len(X_sample) > 0:
        single_x = X_sample[:1]
        latencies = []
        for _ in range(50):
            t0 = time.perf_counter()
            _ = model_obj.predict(single_x)
            latencies.append((time.perf_counter() - t0) * 1000.0)
        latency_ms = float(np.median(latencies))

    return {
        "model_name": model_name,
        "r2_score": round(r2, 4),
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "mse": round(mse, 4),
        "training_time_sec": round(training_time_sec, 3),
        "inference_latency_ms": round(latency_ms, 2),
        "best_features": best_features or [],
        "description": description
    }
