import pandas as pd
import plotly.graph_objects as go
import json
from typing import Dict, Any


class TrendAnalysisChart:
    def __init__(self, df: pd.DataFrame, date_col: str, target_col: str):
        self.df = df
        self.date_col = date_col
        self.target_col = target_col

    def generate_plot(self) -> Dict[str, Any]:
        # Assume df has date_col and target_col
        df_sorted = self.df.sort_values(self.date_col)
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df_sorted[self.date_col],
                y=df_sorted[self.target_col],
                mode="lines+markers",
                name=self.target_col,
            )
        )
        fig.update_layout(
            title=f"Trend Analysis: {self.target_col} over {self.date_col}",
            xaxis_title=self.date_col,
            yaxis_title=self.target_col,
        )
        return json.loads(fig.to_json())

    def get_static_image(self) -> bytes:
        df_sorted = self.df.sort_values(self.date_col)
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df_sorted[self.date_col],
                y=df_sorted[self.target_col],
                mode="lines+markers",
            )
        )
        fig.update_layout(title=f"Trend Analysis: {self.target_col}")
        return fig.to_image(format="png")
