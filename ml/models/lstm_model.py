"""
LSTM Sequence Regressor for Irrigation Water Requirement Prediction
Implemented with PyTorch for capturing sequential weather and soil dynamics.
"""
import time
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader


class PyTorchLSTMNet(nn.Module):
    """Deep 2-layer LSTM Network with fully connected regression head."""
    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2, dropout: float = 0.1):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc1 = nn.Linear(hidden_dim, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, input_dim)
        lstm_out, _ = self.lstm(x)
        last_step = lstm_out[:, -1, :]
        out = self.relu(self.fc1(last_step))
        out = self.fc2(out)
        return out


class LSTMIrrigationModel:
    """
    Wrapper for training, evaluating and serializing the PyTorch LSTM model.
    """
    def __init__(
        self,
        hidden_dim: int = 64,
        num_layers: int = 2,
        learning_rate: float = 0.003,
        epochs: int = 40,
        batch_size: int = 64,
        seq_len: int = 1
    ):
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.seq_len = seq_len
        self.model: Optional[PyTorchLSTMNet] = None
        self.input_dim: Optional[int] = None
        self.training_time_sec: float = 0.0
        self.is_trained: bool = False

    def _prepare_sequence_tensor(self, X: np.ndarray) -> torch.Tensor:
        """Reshapes tabular input into 3D sequential shape (batch, seq_len, features)."""
        X_arr = np.asarray(X, dtype=np.float32)
        if len(X_arr.shape) == 2:
            # (N, D) -> (N, 1, D)
            X_arr = np.expand_dims(X_arr, axis=1)
        return torch.tensor(X_arr, dtype=torch.float32)

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Trains the LSTM network using Adam optimizer and MSE loss."""
        t0 = time.time()
        self.input_dim = X_train.shape[1] if len(X_train.shape) == 2 else X_train.shape[2]

        self.model = PyTorchLSTMNet(
            input_dim=self.input_dim,
            hidden_dim=self.hidden_dim,
            num_layers=self.num_layers
        )

        train_x_tensor = self._prepare_sequence_tensor(X_train)
        train_y_tensor = torch.tensor(np.asarray(y_train, dtype=np.float32).reshape(-1, 1), dtype=torch.float32)

        dataset = TensorDataset(train_x_tensor, train_y_tensor)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate, weight_decay=1e-5)
        criterion = nn.MSELoss()

        self.model.train()
        best_loss = float("inf")

        for epoch in range(self.epochs):
            total_loss = 0.0
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                outputs = self.model(batch_x)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item() * batch_x.size(0)

            epoch_loss = total_loss / len(dataset)
            if epoch_loss < best_loss:
                best_loss = epoch_loss

        self.training_time_sec = round(time.time() - t0, 3)
        self.is_trained = True

        return {
            "model_name": "LSTM Regressor",
            "training_time_sec": self.training_time_sec,
            "epochs_trained": self.epochs,
            "final_mse_loss": round(float(best_loss), 4),
            "hidden_dim": self.hidden_dim,
            "num_layers": self.num_layers
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Inference with the trained LSTM."""
        if not self.is_trained or self.model is None:
            raise RuntimeError("LSTM model is not trained yet.")

        self.model.eval()
        x_tensor = self._prepare_sequence_tensor(X)
        with torch.no_grad():
            outputs = self.model(x_tensor)
            preds = outputs.squeeze().cpu().numpy()

        if preds.ndim == 0:
            preds = np.array([preds])
        return np.maximum(0.0, preds)

    def save(self, filepath: str):
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> "LSTMIrrigationModel":
        return joblib.load(filepath)
