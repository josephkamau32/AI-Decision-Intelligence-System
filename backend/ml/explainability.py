"""
Model explainability using SHAP (SHapley Additive exPlanations)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union
import logging
import io
import base64

logger = logging.getLogger(__name__)


class ModelExplainer:
    """Generate explanations for model predictions using SHAP"""

    def __init__(self, model, X_train: pd.DataFrame = None):
        """
        Initialize explainer

        Args:
            model: Trained sklearn model
            X_train: Training data for background distribution (optional but recommended)
        """
        self.model = model
        self.X_train = X_train
        self.explainer = None
        self._initialize_explainer()

    def _initialize_explainer(self):
        """Initialize appropriate SHAP explainer based on model type"""
        import shap

        try:
            # Try TreeExplainer first (for tree-based models)
            self.explainer = shap.TreeExplainer(self.model)
            self.explainer_type = "tree"
            logger.info("Initialized TreeExplainer")
        except (TypeError, ValueError, AttributeError) as exc:
            logger.debug(
                "TreeExplainer not applicable (%s), attempting LinearExplainer", exc
            )
            try:
                # Try LinearExplainer (for linear models)
                self.explainer = shap.LinearExplainer(self.model, self.X_train)
                self.explainer_type = "linear"
                logger.info("Initialized LinearExplainer")
            except (TypeError, ValueError, AttributeError) as exc:
                logger.debug(
                    "LinearExplainer not applicable (%s), falling back to KernelExplainer",
                    exc,
                )
                # Fall back to KernelExplainer (model-agnostic but slower)
                if self.X_train is not None:
                    # Sample for efficiency
                    background = shap.sample(self.X_train, min(100, len(self.X_train)))
                    self.explainer = shap.KernelExplainer(
                        self.model.predict, background
                    )
                    self.explainer_type = "kernel"
                    logger.info("Initialized KernelExplainer")
                else:
                    raise ValueError("Need training data (X_train) for KernelExplainer")

    def get_global_importance(self, X: pd.DataFrame, top_n: int = 10) -> Dict[str, Any]:
        """
        Get global feature importance

        Args:
            X: Dataset to explain
            top_n: Number of top features to return

        Returns:
            Dictionary with feature importance
        """
        logger.info(f"Calculating global feature importance for {len(X)} samples")

        # Calculate SHAP values
        shap_values = self.explainer.shap_values(X)

        # Handle multi-class case (take absolute mean across all classes)
        if isinstance(shap_values, list):
            # Multi-class classification
            shap_values_combined = np.abs(shap_values).mean(axis=0)
        else:
            shap_values_combined = shap_values

        # Calculate mean absolute SHAP values
        mean_shap = np.abs(shap_values_combined).mean(axis=0)

        # Create feature importance ranking
        feature_names = (
            X.columns.tolist()
            if isinstance(X, pd.DataFrame)
            else [f"feature_{i}" for i in range(X.shape[1])]
        )
        importance_dict = dict(zip(feature_names, mean_shap))

        # Sort by importance
        sorted_features = sorted(
            importance_dict.items(), key=lambda x: x[1], reverse=True
        )

        # Take top N
        top_features = sorted_features[:top_n]

        return {
            "feature_importance": [
                {"feature": feat, "importance": float(imp)}
                for feat, imp in top_features
            ],
            "all_features": [
                {"feature": feat, "importance": float(imp)}
                for feat, imp in sorted_features
            ],
        }

    def explain_instance(
        self,
        X: Union[pd.DataFrame, pd.Series, np.ndarray, Dict],
        feature_names: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Explain a single prediction

        Args:
            X: Single instance to explain
            feature_names: Optional list of feature names

        Returns:
            Dictionary with explanation
        """
        # Convert to DataFrame if needed
        if isinstance(X, dict):
            X = pd.DataFrame([X])
        elif isinstance(X, pd.Series):
            X = X.to_frame().T
        elif isinstance(X, np.ndarray):
            if X.ndim == 1:
                X = X.reshape(1, -1)
            if feature_names:
                X = pd.DataFrame(X, columns=feature_names)
            else:
                X = pd.DataFrame(X)

        # Calculate SHAP values for this instance
        shap_values = self.explainer.shap_values(X)

        # Handle multi-class
        if isinstance(shap_values, list):
            # For multi-class, return explanation for each class
            explanations = []
            for class_idx, class_shap in enumerate(shap_values):
                feature_contributions = []
                for i, col in enumerate(X.columns):
                    feature_contributions.append(
                        {
                            "feature": col,
                            "value": float(X.iloc[0, i]),
                            "contribution": float(class_shap[0, i]),
                        }
                    )

                # Sort by absolute contribution
                feature_contributions.sort(
                    key=lambda x: abs(x["contribution"]), reverse=True
                )

                explanations.append(
                    {"class": class_idx, "features": feature_contributions}
                )

            return {"type": "multi-class", "explanations": explanations}
        else:
            # Single output
            feature_contributions = []
            for i, col in enumerate(X.columns):
                feature_contributions.append(
                    {
                        "feature": col,
                        "value": float(X.iloc[0, i]),
                        "contribution": float(shap_values[0, i]),
                    }
                )

            # Sort by absolute contribution
            feature_contributions.sort(
                key=lambda x: abs(x["contribution"]), reverse=True
            )

            return {
                "type": "single-output",
                "features": feature_contributions,
                "base_value": (
                    float(self.explainer.expected_value)
                    if hasattr(self.explainer, "expected_value")
                    else None
                ),
            }

    def generate_summary_plot(self, X: pd.DataFrame, max_display: int = 20) -> str:
        """
        Generate SHAP summary plot and return as base64 string

        Returns:
            Base64 encoded plot image
        """
        logger.info("Generating SHAP summary plot")

        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import shap

        # Calculate SHAP values
        shap_values = self.explainer.shap_values(X)

        # Create figure
        plt.figure(figsize=(10, 8))
        shap.summary_plot(shap_values, X, max_display=max_display, show=False)

        # Save to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=100)
        buf.seek(0)
        plt.close()

        # Encode to base64
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")

        return f"data:image/png;base64,{img_base64}"

    def generate_feature_importance_plot(self, X: pd.DataFrame, top_n: int = 10) -> str:
        """
        Generate feature importance bar plot

        Returns:
            Base64 encoded plot image
        """
        logger.info("Generating feature importance plot")

        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # Get global importance
        importance_data = self.get_global_importance(X, top_n=top_n)

        # Extract data
        features = [item["feature"] for item in importance_data["feature_importance"]]
        importances = [
            item["importance"] for item in importance_data["feature_importance"]
        ]

        # Create plot
        plt.figure(figsize=(10, 6))
        plt.barh(features[::-1], importances[::-1])
        plt.xlabel("Mean |SHAP value|")
        plt.title(f"Top {top_n} Feature Importance")
        plt.tight_layout()

        # Save to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=100)
        buf.seek(0)
        plt.close()

        # Encode to base64
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")

        return f"data:image/png;base64,{img_base64}"
