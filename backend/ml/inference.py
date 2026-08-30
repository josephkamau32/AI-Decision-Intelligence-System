"""
Inference module for making predictions with trained models
"""

import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from typing import Dict, Any, List, Union
import logging
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelInference:
    """Handle model loading and predictions"""

    def __init__(
        self, model_path: str = None, model_name: str = None, mlflow_uri: str = None
    ):
        """
        Initialize inference engine

        Args:
            model_path: Direct path to saved model file
            model_name: MLflow registered model name
            mlflow_uri: MLflow model URI
        """
        self.model = None
        self.model_info = {}

        if model_path:
            self.load_from_file(model_path)
        elif model_name:
            self.load_from_mlflow_registry(model_name)
        elif mlflow_uri:
            self.load_from_mlflow_uri(mlflow_uri)

    def load_from_file(self, filepath: str):
        """Load model from joblib file"""
        try:
            self.model = joblib.load(filepath)
            self.model_info = {"source": "file", "path": filepath}
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load model from {filepath}: {e}")
            raise

    def load_from_mlflow_registry(self, model_name: str, stage: str = "Production"):
        """Load model from MLflow model registry"""
        try:
            model_uri = f"models:/{model_name}/{stage}"
            self.model = mlflow.sklearn.load_model(model_uri)
            self.model_info = {
                "source": "mlflow_registry",
                "model_name": model_name,
                "stage": stage,
                "uri": model_uri,
            }
            logger.info(
                f"Model {model_name} loaded from MLflow registry (stage: {stage})"
            )
        except Exception as e:
            logger.error(f"Failed to load model from MLflow registry: {e}")
            raise

    def load_from_mlflow_uri(self, model_uri: str):
        """Load model from MLflow URI"""
        try:
            self.model = mlflow.sklearn.load_model(model_uri)
            self.model_info = {"source": "mlflow_uri", "uri": model_uri}
            logger.info(f"Model loaded from URI: {model_uri}")
        except Exception as e:
            logger.error(f"Failed to load model from URI: {e}")
            raise

    def predict(self, X: Union[pd.DataFrame, np.ndarray, List, Dict]) -> np.ndarray:
        """
        Make predictions

        Args:
            X: Input features (DataFrame, array, list, or dict)

        Returns:
            Predictions array
        """
        if self.model is None:
            raise ValueError("No model loaded")

        # Convert input to DataFrame if needed
        if isinstance(X, dict):
            X = pd.DataFrame([X])
        elif isinstance(X, list):
            X = pd.DataFrame(X)
        elif isinstance(X, np.ndarray):
            X = pd.DataFrame(X)

        try:
            predictions = self.model.predict(X)
            logger.info(f"Made {len(predictions)} predictions")
            return predictions
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise

    def predict_proba(
        self, X: Union[pd.DataFrame, np.ndarray, List, Dict]
    ) -> np.ndarray:
        """
        Get prediction probabilities (classification only)

        Args:
            X: Input features

        Returns:
            Probability array
        """
        if self.model is None:
            raise ValueError("No model loaded")

        if not hasattr(self.model, "predict_proba"):
            raise ValueError("Model does not support probability predictions")

        # Convert input
        if isinstance(X, dict):
            X = pd.DataFrame([X])
        elif isinstance(X, list):
            X = pd.DataFrame(X)
        elif isinstance(X, np.ndarray):
            X = pd.DataFrame(X)

        try:
            probabilities = self.model.predict_proba(X)
            logger.info(f"Generated probabilities for {len(probabilities)} predictions")
            return probabilities
        except Exception as e:
            logger.error(f"Probability prediction failed: {e}")
            raise

    def predict_with_confidence(self, X: Union[pd.DataFrame, Dict]) -> List[Dict]:
        """
        Make predictions with confidence scores

        Returns:
            List of dicts with prediction and confidence
        """
        predictions = self.predict(X)

        results = []

        # Try to get probabilities for confidence
        try:
            probabilities = self.predict_proba(X)
            for i, pred in enumerate(predictions):
                # Max probability as confidence
                confidence = float(np.max(probabilities[i]))
                results.append(
                    {
                        "prediction": (
                            float(pred)
                            if isinstance(pred, (np.integer, np.floating))
                            else pred
                        ),
                        "confidence": confidence,
                        "probabilities": (
                            probabilities[i].tolist()
                            if probabilities is not None
                            else None
                        ),
                    }
                )
        except (ValueError, AttributeError, IndexError, TypeError) as exc:
            logger.debug(
                "Probabilities unavailable for confidence calculation: %s", exc
            )
            # No probabilities available, return without confidence
            for pred in predictions:
                results.append(
                    {
                        "prediction": (
                            float(pred)
                            if isinstance(pred, (np.integer, np.floating))
                            else pred
                        ),
                        "confidence": None,
                        "probabilities": None,
                    }
                )

        return results

    def batch_predict(self, X: pd.DataFrame, batch_size: int = 1000) -> np.ndarray:
        """
        Make predictions in batches for large datasets

        Args:
            X: Input features
            batch_size: Number of samples per batch

        Returns:
            Predictions array
        """
        if self.model is None:
            raise ValueError("No model loaded")

        n_samples = len(X)
        predictions = []

        for i in range(0, n_samples, batch_size):
            batch = X.iloc[i : i + batch_size]
            batch_preds = self.model.predict(batch)
            predictions.extend(batch_preds)
            logger.info(
                f"Processed batch {i//batch_size + 1}/{(n_samples + batch_size - 1)//batch_size}"
            )

        return np.array(predictions)
