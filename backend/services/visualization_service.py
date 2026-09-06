from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from ..visualizations import (
    CorrelationHeatmap,
    FeatureImportancePlot,
    TrendAnalysisChart,
    ForecastPlot,
    InteractiveFilters,
)
from ..ml.data_ingestion import DataIngestion
from .dataset_service import dataset_service
import logging

logger = logging.getLogger(__name__)


class VisualizationService:
    def __init__(self):
        pass

    def get_correlation_heatmap(
        self, dataset_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        try:
            df = dataset_service.load_dataset_file(dataset_id, user_id=user_id)
        except Exception as e:
            logger.warning(f"Could not load dataset {dataset_id} for correlation: {e}")
            return None

        # Select numeric columns
        numeric_df = df.select_dtypes(include=[float, int, np.number])
        if numeric_df.empty or len(numeric_df.columns) < 2:
            return None

        corr = numeric_df.corr().fillna(0)
        heatmap = CorrelationHeatmap(numeric_df)
        plot_data = heatmap.generate_plot()

        # Return both matrix/columns expected by VisualInsights.tsx AND Plotly plot dict
        return {
            "matrix": corr.values.tolist(),
            "columns": corr.columns.tolist(),
            "labels": corr.columns.tolist(),
            "plot": plot_data,
        }

    def get_feature_importance(
        self, model_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        from .model_service import model_service

        model_info = model_service.get_model(model_id, user_id=user_id)
        if not model_info:
            return None

        estimator = model_info.get("model")
        feature_names = model_info.get("feature_names", [])

        if estimator is None:
            return None

        if hasattr(estimator, "feature_importances_"):
            importances = estimator.feature_importances_
        elif hasattr(estimator, "coef_"):
            importances = np.abs(estimator.coef_)
            if importances.ndim > 1:
                importances = importances.mean(axis=0)
        else:
            importances = np.ones(len(feature_names)) / max(1, len(feature_names))

        sorted_pairs = sorted(
            zip(feature_names, [float(x) for x in importances]),
            key=lambda x: x[1],
            reverse=True,
        )

        feature_dict = dict(sorted_pairs)
        feature_list = [
            {"name": p[0], "feature": p[0], "importance": p[1], "value": p[1]}
            for p in sorted_pairs
        ]

        plot_data = FeatureImportancePlot(estimator, feature_names).generate_plot()

        return {
            "feature_importance": feature_dict,
            "features": feature_list,
            "top_features": [p[0] for p in sorted_pairs],
            "importance_values": [p[1] for p in sorted_pairs],
            "plot": plot_data,
        }

    def get_trend_analysis(
        self, dataset_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        try:
            df = dataset_service.load_dataset_file(dataset_id, user_id=user_id)
        except Exception as e:
            logger.warning(
                f"Could not load dataset {dataset_id} for trend analysis: {e}"
            )
            return None

        num_cols = df.select_dtypes(include=[float, int, np.number]).columns.tolist()
        if not num_cols:
            return None

        # Check for date / time column
        date_col = None
        for col in df.columns:
            if (
                pd.api.types.is_datetime64_any_dtype(df[col])
                or "date" in str(col).lower()
                or "time" in str(col).lower()
            ):
                date_col = col
                break

        # Fallback: if no date column, use row index sequence as time step
        if date_col is not None:
            x_series = df[date_col].astype(str)
            target = (
                num_cols[0]
                if num_cols[0] != date_col
                else (num_cols[1] if len(num_cols) > 1 else num_cols[0])
            )
        else:
            date_col = "Row"
            x_series = pd.Series([f"#{i+1}" for i in range(len(df))])
            target = num_cols[0]

        # Generate traces for frontend VisualInsights.tsx
        traces = []
        for col in num_cols[:4]:
            traces.append(
                {
                    "name": str(col),
                    "x": list(x_series),
                    "y": [float(v) if pd.notna(v) else 0.0 for v in df[col]],
                    "values": [float(v) if pd.notna(v) else 0.0 for v in df[col]],
                }
            )

        # Plotly chart
        try:
            chart = TrendAnalysisChart(
                df, date_col if date_col in df.columns else target, target
            )
            plot_data = chart.generate_plot()
        except Exception:
            plot_data = {}

        return {
            "trends": traces,
            "values": traces[0]["y"] if traces else [],
            "plot": plot_data,
        }

    def get_forecast_plot(
        self, model_id: str, dataset_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        from .model_service import model_service

        model_info = model_service.get_model(model_id, user_id=user_id)
        if not model_info:
            return None
        model = model_info.get("model")
        try:
            df = dataset_service.load_dataset_file(dataset_id, user_id=user_id)
        except Exception:
            return None

        date_col = None
        for col in df.columns:
            if (
                pd.api.types.is_datetime64_any_dtype(df[col])
                or "date" in str(col).lower()
                or "time" in str(col).lower()
            ):
                date_col = col
                break
        num_cols = df.select_dtypes(include=[float, int, np.number]).columns
        target = num_cols[0] if not num_cols.empty else None

        if not date_col or not target:
            return None
        plot = ForecastPlot(df, model, date_col, target)
        return plot.generate_plot()

    def get_interactive_filters(
        self, dataset_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        try:
            df = dataset_service.load_dataset_file(dataset_id, user_id=user_id)
        except Exception:
            return None
        filters = InteractiveFilters(df)
        return filters.generate_filters()

    def get_shap_global_plot(
        self, model_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        return self.get_feature_importance(model_id, user_id=user_id)

    def get_shap_local_plot(
        self, model_id: str, input_data: Dict[str, Any], user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        return self.get_feature_importance(model_id, user_id=user_id)


visualization_service = VisualizationService()
