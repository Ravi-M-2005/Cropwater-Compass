"""
SHAP Explainability Analyzer
Provides TreeExplainer and feature attribution for trained models.
"""
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
import shap


class ShapExplainer:
    """
    SHAP-based interpretability wrapper for tree-based irrigation regression.
    """
    def __init__(self, model: Any, feature_names: List[str]):
        self.model = model
        self.feature_names = feature_names
        self.explainer: Optional[shap.TreeExplainer] = None
        self.global_importance_: List[Dict[str, Any]] = []
        self.base_value_: float = 0.0

    def fit(self, X_sample: np.ndarray):
        """Initializes TreeExplainer using background training sample."""
        # Check if model has underlying xgb regressor
        underlying = getattr(self.model, "model", self.model)
        self.explainer = shap.TreeExplainer(underlying)

        shap_values = self.explainer(X_sample)
        self.base_value_ = float(np.mean(self.explainer.expected_value))

        # Compute global feature importance (mean |SHAP value|)
        raw_values = shap_values.values if hasattr(shap_values, "values") else np.array(shap_values)
        mean_abs = np.mean(np.abs(raw_values), axis=0)

        importance_list = []
        for name, imp in zip(self.feature_names, mean_abs):
            importance_list.append({
                "feature": name,
                "importance": round(float(imp), 4)
            })

        self.global_importance_ = sorted(importance_list, key=lambda x: x["importance"], reverse=True)
        return self

    def explain_instance(self, x_single: np.ndarray, top_k: int = 10) -> Dict[str, Any]:
        """
        Computes local SHAP waterfall feature attributions for a single instance.
        """
        if self.explainer is None:
            raise RuntimeError("ShapExplainer is not initialized. Call fit() first.")

        if len(x_single.shape) == 1:
            x_single = x_single.reshape(1, -1)

        shap_res = self.explainer(x_single)
        vals = shap_res.values[0] if hasattr(shap_res, "values") else np.array(shap_res)[0]
        base_val = float(shap_res.base_values[0]) if hasattr(shap_res, "base_values") else self.base_value_

        # Map to readable feature names
        features_output = []
        top_pos = []
        top_neg = []

        for name, sv in zip(self.feature_names, vals):
            direction = "increases_water" if sv >= 0 else "decreases_water"
            display_name = name.replace("num__", "").replace("cat__", "").replace("_", " ").title()
            item = {
                "feature": name,
                "display_name": display_name,
                "importance": round(abs(float(sv)), 4),
                "shap_value": round(float(sv), 4),
                "impact_direction": direction
            }
            features_output.append(item)
            if sv > 0.05:
                top_pos.append(display_name)
            elif sv < -0.05:
                top_neg.append(display_name)

        sorted_items = sorted(features_output, key=lambda x: x["importance"], reverse=True)
        predicted_val = round(base_val + float(np.sum(vals)), 2)

        return {
            "base_value": round(base_val, 2),
            "predicted_value": max(0.0, predicted_val),
            "feature_importances": sorted_items[:top_k],
            "top_positive_features": top_pos[:3],
            "top_negative_features": top_neg[:3],
            "explanation_summary": (
                f"Base expectation is {base_val:.2f} mm. "
                f"Top factors driving water demand up are {', '.join(top_pos[:2]) or 'ambient temperature'}, "
                f"while {', '.join(top_neg[:2]) or 'soil moisture'} offsets irrigation requirement."
            )
        }

    def save(self, filepath: str):
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> "ShapExplainer":
        return joblib.load(filepath)
