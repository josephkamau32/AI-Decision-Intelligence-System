import pandas as pd
import plotly.graph_objects as go
import json
from typing import Dict, Any
import numpy as np

class ForecastPlot:
    def __init__(self, df: pd.DataFrame, model, date_col: str, target_col: str, periods: int = 10):
        self.df = df
        self.model = model
        self.date_col = date_col
        self.target_col = target_col
        self.periods = periods

    def generate_plot(self) -> Dict[str, Any]:
        df_sorted = self.df.sort_values(self.date_col)
        fig = go.Figure()
        # Historical data
        fig.add_trace(go.Scatter(
            x=df_sorted[self.date_col],
            y=df_sorted[self.target_col],
            mode='lines+markers',
            name='Historical'
        ))
        # Forecast
        if hasattr(self.model, 'predict'):  # sklearn-like
            # For simplicity, assume model can predict future
            # This is tricky, need to prepare future X
            # For demo, just extend with mock
            last_date = df_sorted[self.date_col].max()
            future_dates = pd.date_range(start=last_date, periods=self.periods+1, freq='D')[1:]
            # Mock predictions
            predictions = np.random.randn(self.periods) * df_sorted[self.target_col].std() + df_sorted[self.target_col].mean()
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=predictions,
                mode='lines+markers',
                name='Forecast',
                line=dict(dash='dash')
            ))
        elif hasattr(self.model, 'make_future_dataframe'):  # Prophet
            future = self.model.make_future_dataframe(periods=self.periods)
            forecast = self.model.predict(future)
            fig.add_trace(go.Scatter(
                x=forecast['ds'],
                y=forecast['yhat'],
                mode='lines',
                name='Forecast',
                line=dict(dash='dash')
            ))
            fig.add_trace(go.Scatter(
                x=forecast['ds'],
                y=forecast['yhat_lower'],
                fill=None,
                mode='lines',
                line_color='lightblue',
                name='Lower Bound'
            ))
            fig.add_trace(go.Scatter(
                x=forecast['ds'],
                y=forecast['yhat_upper'],
                fill='tonexty',
                mode='lines',
                line_color='lightblue',
                name='Upper Bound'
            ))
        fig.update_layout(
            title='Forecast Plot',
            xaxis_title=self.date_col,
            yaxis_title=self.target_col
        )
        return json.loads(fig.to_json())

    def get_static_image(self) -> bytes:
        # Similar to above, but simplified
        df_sorted = self.df.sort_values(self.date_col)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_sorted[self.date_col],
            y=df_sorted[self.target_col],
            mode='lines+markers',
            name='Historical'
        ))
        # Mock forecast
        last_date = df_sorted[self.date_col].max()
        future_dates = pd.date_range(start=last_date, periods=self.periods+1, freq='D')[1:]
        predictions = np.random.randn(self.periods) * df_sorted[self.target_col].std() + df_sorted[self.target_col].mean()
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=predictions,
            mode='lines+markers',
            name='Forecast'
        ))
        fig.update_layout(title='Forecast Plot')
        return fig.to_image(format='png')