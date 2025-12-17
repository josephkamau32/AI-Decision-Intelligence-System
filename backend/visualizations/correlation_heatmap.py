import pandas as pd
import plotly.graph_objects as go
import json
from typing import Dict, Any

class CorrelationHeatmap:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def generate_plot(self) -> Dict[str, Any]:
        # Compute correlation matrix
        corr = self.df.corr()
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.columns,
            colorscale='RdBu',
            zmin=-1,
            zmax=1,
            text=corr.round(2).values,
            texttemplate='%{text}',
            textfont={"size":10},
            hoverongaps=False
        ))
        fig.update_layout(
            title='Correlation Heatmap',
            xaxis_title='Features',
            yaxis_title='Features'
        )
        return json.loads(fig.to_json())

    def get_static_image(self) -> bytes:
        fig = go.Figure(data=go.Heatmap(
            z=self.df.corr().values,
            x=self.df.corr().columns,
            y=self.df.corr().columns,
            colorscale='RdBu',
            zmin=-1,
            zmax=1
        ))
        fig.update_layout(title='Correlation Heatmap')
        return fig.to_image(format='png')