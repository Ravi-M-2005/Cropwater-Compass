"""
Data Preprocessing Pipeline for Cropwater Compass
Handles missing-value imputation, categorical encoding, and feature scaling
with strict prevention of data leakage.
"""
import joblib
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

CATEGORICAL_FEATURES = ["crop_type", "growth_stage", "soil_type", "irrigation_method"]
NUMERICAL_FEATURES = [
    "soil_moisture_pct", "soil_ph", "temperature_c", "humidity_pct",
    "wind_speed_kmh", "rainfall_mm", "solar_radiation", "et0_mm"
]
TARGET_COLUMN = "water_requirement_mm"


class DataPreprocessor(BaseEstimator, TransformerMixin):
    """
    Scikit-learn compatible preprocessor for agricultural tabular features.
    Guarantees no data leakage by fitting transformers solely on the training split.
    """
    def __init__(self):
        self.categorical_cols = CATEGORICAL_FEATURES
        self.numerical_cols = NUMERICAL_FEATURES
        self.target_col = TARGET_COLUMN
        self.pipeline: Optional[ColumnTransformer] = None
        self.feature_names_: List[str] = []
        self.is_fitted: bool = False

    def _build_pipeline(self) -> ColumnTransformer:
        num_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ])

        cat_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ])

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", num_pipeline, self.numerical_cols),
                ("cat", cat_pipeline, self.categorical_cols)
            ],
            remainder="drop"
        )
        return preprocessor

    def fit(self, X: pd.DataFrame, y=None):
        """Fit preprocessor only on the training feature set."""
        X_df = X.copy()
        # Ensure required columns exist
        for col in self.numerical_cols:
            if col not in X_df.columns:
                X_df[col] = 0.0
        for col in self.categorical_cols:
            if col not in X_df.columns:
                X_df[col] = "Unknown"

        self.pipeline = self._build_pipeline()
        self.pipeline.fit(X_df)

        # Extract generated feature names
        cat_encoder = self.pipeline.named_transformers_["cat"].named_steps["onehot"]
        encoded_cat_names = list(cat_encoder.get_feature_names_out(self.categorical_cols))
        self.feature_names_ = self.numerical_cols + encoded_cat_names
        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transforms features using the pre-fitted encoders and scalers."""
        if not self.is_fitted or self.pipeline is None:
            raise RuntimeError("Preprocessor has not been fitted yet. Call fit() before transform().")

        X_df = X.copy()
        for col in self.numerical_cols:
            if col not in X_df.columns:
                X_df[col] = 0.0
        for col in self.categorical_cols:
            if col not in X_df.columns:
                X_df[col] = "Unknown"

        return self.pipeline.transform(X_df)

    def fit_transform(self, X: pd.DataFrame, y=None) -> np.ndarray:
        return self.fit(X, y).transform(X)

    def get_feature_names(self) -> List[str]:
        return self.feature_names_

    def save(self, filepath: str):
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> "DataPreprocessor":
        return joblib.load(filepath)


def prepare_dataset(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, DataPreprocessor]:
    """
    Splits data into train and test sets BEFORE applying any transformations.
    Fits the preprocessor strictly on the training partition.
    """
    from sklearn.model_selection import train_test_split

    X = df.drop(columns=[TARGET_COLUMN], errors="ignore")
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    preprocessor = DataPreprocessor()
    preprocessor.fit(X_train)

    return X_train, X_test, y_train, y_test, preprocessor
