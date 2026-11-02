"""
Artificial Neural Network (ANN) Regressor for Irrigation Water Requirement Prediction
Implemented using Scikit-Learn MLPRegressor.
"""
import time
import joblib
import numpy as np
from typing import Dict, Any, Optional
from sklearn.neural_network import MLPRegressor


class ANNIrrigationModel:
    """
    Multi-Layer Perceptron (MLP) Artificial Neural Network for modeling
    non-linear agricultural interactions.
    """
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self.params = params or {
            "hidden_layer_sizes": (128, 64, 32),
            "activation": "relu",
            "solver": "adam",
            "alpha": 0.0005,
            "learning_rate_init": 0.002,
            "max_iter": 350,
            "early_stopping": True,
            "validation_fraction": 0.1,
            "n_iter_no_change": 15,
            "random_state": 42
        }
        self.model = MLPRegressor(**self.params)
        self.training_time_sec: float = 0.0
        self.is_trained: bool = False

    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict[str, Any]:
        """Trains the ANN MLPRegressor."""
        t0 = time.time()
        self.model.fit(X_train, y_train)
        self.training_time_sec = round(time.time() - t0, 3)
        self.is_trained = True

        return {
            "model_name": "Artificial Neural Network (ANN)",
            "training_time_sec": self.training_time_sec,
            "n_layers": len(self.params["hidden_layer_sizes"]),
            "iterations_completed": self.model.n_iter_,
            "final_loss": round(float(self.model.loss_), 5)
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predicts water requirement depth in mm."""
        if not self.is_trained:
            raise RuntimeError("ANN model is not trained yet.")
        preds = self.model.predict(X)
        return np.maximum(0.0, preds)

    def save(self, filepath: str):
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> "ANNIrrigationModel":
        return joblib.load(filepath)
