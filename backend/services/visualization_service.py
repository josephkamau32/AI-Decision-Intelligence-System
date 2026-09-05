from typing import Dict, Any, Optional
import pandas as pd
from ..visualizations import (
    CorrelationHeatmap,
    FeatureImportancePlot,
    TrendAnalysisChart,
    ForecastPlot,
    InteractiveFilters,
)
from ..ml.data_ingestion import DataIngestion
from .dataset_service import dataset_service


class VisualizationService:
    def __init__(self):
        pass

    def get_correlation_heatmap(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        dataset = next(
            (d for d in dataset_service.datasets if d.id == dataset_id), None
        )
        if not dataset:
            return None
        df = DataIngestion.load_data(dataset.file_path)
        # Select numeric columns
        numeric_df = df.select_dtypes(include=[float, int])
        if numeric_df.empty:
            return None
        heatmap = CorrelationHeatmap(numeric_df)
        return heatmap.generate_plot()

    def get_feature_importance(self, model_id: str) -> Optional[Dict[str, Any]]:
        from .model_service import model_service

        model = model_service.models.get(model_id)
        if not model:
            return None
        # Need feature names, assume from dataset, but for simplicity, mock
        # In real, store feature names with model
        feature_names = [f"feature_{i}" for i in range(10)]  # mock
        plot = FeatureImportancePlot(model, feature_names)
        return plot.generate_plot()

    def get_trend_analysis(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        dataset = next(
            (d for d in dataset_service.datasets if d.id == dataset_id), None
        )
        if not dataset:
            return None
        try:
            df = DataIngestion.load_data(dataset.file_path)
            profile = getattr(dataset, "profile", {}) or {}
            target = profile.get("target_variable")
            if not target or target not in df.columns:
                num_cols = df.select_dtypes(include=[float, int]).columns
                target = num_cols[0] if not num_cols.empty else None

            # Find date col
            date_col = None
            for col in df.columns:
                if (
                    pd.api.types.is_datetime64_any_dtype(df[col])
                    or "date" in str(col).lower()
                    or "time" in str(col).lower()
                ):
                    date_col = col
                    break
            if not date_col or not target:
                return None
            chart = TrendAnalysisChart(df, date_col, target)
            return chart.generate_plot()
        except Exception as e:
            return None

    def get_forecast_plot(
        self, model_id: str, dataset_id: str
    ) -> Optional[Dict[str, Any]]:
        from .model_service import model_service

        model = model_service.models.get(model_id)
        dataset = next(
            (d for d in dataset_service.datasets if d.id == dataset_id), None
        )
        if not model or not dataset:
            return None
        try:
            df = DataIngestion.load_data(dataset.file_path)
            profile = getattr(dataset, "profile", {}) or {}
            target = profile.get("target_variable")
            if not target or target not in df.columns:
                num_cols = df.select_dtypes(include=[float, int]).columns
                target = num_cols[0] if not num_cols.empty else None
            date_col = None
            for col in df.columns:
                if (
                    pd.api.types.is_datetime64_any_dtype(df[col])
                    or "date" in str(col).lower()
                ):
                    date_col = col
                    break
            if not date_col or not target:
                return None
            plot = ForecastPlot(df, model, date_col, target)
            return plot.generate_plot()
        except Exception as e:
            return None

    def get_interactive_filters(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        dataset = next(
            (d for d in dataset_service.datasets if d.id == dataset_id), None
        )
        if not dataset:
            return None
        df = DataIngestion.load_data(dataset.file_path)
        filters = InteractiveFilters(df)
        return filters.generate_filters()


visualization_service = VisualizationService()
