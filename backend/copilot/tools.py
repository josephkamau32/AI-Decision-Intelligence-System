from langchain.tools import BaseTool
from typing import Any, Dict, List
import pandas as pd
import shap
from ..ml.data_ingestion import DataIngestion, DataProfiler
from ..services.dataset_service import dataset_service
from ..services.model_service import model_service
from .rag import rag_system

class DatasetInfoTool(BaseTool):
    name = "dataset_info"
    description = "Get information about a dataset including schema, statistics, and profiling."

    def _run(self, dataset_id: str) -> str:
        dataset = next((d for d in dataset_service.datasets if d.id == dataset_id), None)
        if not dataset:
            return "Dataset not found."

        df = DataIngestion.load_data(dataset.file_path)
        profiler = DataProfiler(df)
        profile = profiler.profile()

        info = f"""
Dataset: {dataset.name}
Description: {dataset.description}
Shape: {profile['shape']}
Columns: {', '.join(profile['columns'])}
Data Types: {profile['data_types']}
Missing Values: {profile['missing_values']}
Target Variable: {profile['target_variable']}
Problem Type: {profile['problem_type']}
"""
        return info

class FeatureImportanceTool(BaseTool):
    name = "feature_importance"
    description = "Get feature importance for a trained model."

    def _run(self, model_id: str) -> str:
        model = model_service.models.get(model_id)
        if not model:
            return "Model not found."

        if hasattr(model, 'feature_importances_'):
            # Get features from latest dataset (simplified)
            dataset = dataset_service.datasets[-1] if dataset_service.datasets else None
            if dataset:
                df = DataIngestion.load_data(dataset.file_path)
                features = list(df.columns[:-1])
                importance = dict(zip(features, model.feature_importances_))
                sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
                return "\n".join([f"{feat}: {imp:.4f}" for feat, imp in sorted_imp])
        return "Feature importance not available for this model type."

class SHAPExplanationTool(BaseTool):
    name = "shap_explanation"
    description = "Get SHAP explanations for model predictions."

    def _run(self, model_id: str, dataset_id: str = None) -> str:
        model = model_service.models.get(model_id)
        if not model:
            return "Model not found."

        dataset = next((d for d in dataset_service.datasets if d.id == dataset_id), None) if dataset_id else dataset_service.datasets[-1]
        if not dataset:
            return "Dataset not found."

        df = DataIngestion.load_data(dataset.file_path)
        X = df.drop(columns=[df.columns[-1]]).values  # Assume last column is target

        try:
            explainer = shap.TreeExplainer(model) if hasattr(model, 'feature_importances_') else shap.LinearExplainer(model, X)
            shap_values = explainer.shap_values(X[:10])  # Explain first 10 samples

            # Simplified summary
            mean_abs_shap = abs(shap_values).mean(axis=0) if len(shap_values.shape) == 2 else abs(shap_values[1]).mean(axis=0)
            features = list(df.columns[:-1])
            importance = dict(zip(features, mean_abs_shap))
            sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)

            return "SHAP Feature Importance:\n" + "\n".join([f"{feat}: {imp:.4f}" for feat, imp in sorted_imp])
        except Exception as e:
            return f"SHAP explanation failed: {str(e)}"

class PredictionTool(BaseTool):
    name = "predict"
    description = "Make predictions using a trained model."

    def _run(self, model_id: str, input_data: Dict[str, Any]) -> str:
        model = model_service.models.get(model_id)
        if not model:
            return "Model not found."

        try:
            # Convert input_data to array
            # Assume input_data keys match feature names
            dataset = dataset_service.datasets[-1] if dataset_service.datasets else None
            if dataset:
                df = DataIngestion.load_data(dataset.file_path)
                features = list(df.columns[:-1])
                X = [[input_data.get(feat, 0) for feat in features]]
                prediction = model.predict(X)[0]
                return f"Prediction: {prediction}"
        except Exception as e:
            return f"Prediction failed: {str(e)}"

class RAGQueryTool(BaseTool):
    name = "rag_query"
    description = "Query the RAG system for relevant dataset and model information."

    def _run(self, query: str) -> str:
        return rag_system.get_context(query)

# List of tools
tools = [
    DatasetInfoTool(),
    FeatureImportanceTool(),
    SHAPExplanationTool(),
    PredictionTool(),
    RAGQueryTool()
]