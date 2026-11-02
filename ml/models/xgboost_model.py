"""
XGBoost Regressor for Irrigation Water Requirement Prediction
"""
import time
import joblib
import numpy as np
from typing import Dict, Any, Optional
import xgboost as xgb


class XGBoostIrrigationModel:
    """
    Gradient Boosted Decision Tree Regressor for tabular agricultural features.
    """
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self.params = params or {
            "n_estimators": 250,
            "learning_rate": 0.05,
            "max_depth": 5,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "random_state": 42,
            "n_jobs": -1
        }
        self.model = xgb.XGBRegressor(**self.params)
        self.training_time_sec: float = 0.0
        self.is_trained: bool = False

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Trains the XGBoost regressor."""
        t0 = time.time()
        eval_set = [(X_val, y_val)] if X_val is not None and y_val is not None else None
        
        self.model.fit(
            X_train,
            y_train,
            eval_set=eval_set,
            verbose=False
        )
        self.training_time_sec = round(time.time() - t0, 3)
        self.is_trained = True

        return {
            "model_name": "XGBoost Regressor",
            "training_time_sec": self.training_time_sec,
            "n_estimators": self.params["n_estimators"],
            "max_depth": self.params["max_depth"]
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Runs predictions; non-negative water requirement depth in mm."""
        if not self.is_trained:
            raise RuntimeError("XGBoost model is not trained yet.")
        preds = self.model.predict(X)
        return np.maximum(0.0, preds)

    def save(self, filepath: str):
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> "XGBoostIrrigationModel":
        return joblib.load(filepath)
