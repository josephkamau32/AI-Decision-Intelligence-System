import pandas as pd
import plotly.graph_objects as go
import json
from typing import Dict, Any, List
import numpy as np


class FeatureImportancePlot:
    def __init__(self, model, feature_names: List[str]):
        self.model = model
        self.feature_names = feature_names

    def _get_importance(self) -> pd.Series:
        if hasattr(self.model, "feature_importances_"):
            importance = self.model.feature_importances_
        elif hasattr(self.model, "coef_"):
            importance = np.abs(self.model.coef_)
            if importance.ndim > 1:
                importance = importance.mean(axis=0)  # for multi-output
        else:
            # Fallback, assume equal importance
            importance = np.ones(len(self.feature_names)) / len(self.feature_names)
        return pd.Series(importance, index=self.feature_names).sort_values(
            ascending=False
        )

    def generate_plot(self) -> Dict[str, Any]:
        importance = self._get_importance()
        fig = go.Figure(
            data=[go.Bar(x=importance.values, y=importance.index, orientation="h")]
        )
        fig.update_layout(
            title="Feature Importance", xaxis_title="Importance", yaxis_title="Features"
        )
        return json.loads(fig.to_json())

    def get_static_image(self) -> bytes:
        importance = self._get_importance()
        fig = go.Figure(
            data=[go.Bar(x=importance.values, y=importance.index, orientation="h")]
        )
        fig.update_layout(title="Feature Importance")
        return fig.to_image(format="png")
