"""
Enhanced Model Service with AutoML,  Inference, and Explainability integration
"""

import uuid
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path
import joblib

from ..utils.cache import cache_get, cache_set, cache_delete
from ..services.dataset_service import dataset_service

logger = logging.getLogger(__name__)


class ModelService:
    """Service for managing model training, inference, and explanations"""

    def __init__(self):
        self.models = (
            {}
        )  # In-memory model cache: {model_id: {model, explainer, metadata}}
        self.tasks = {}  # Task status tracking
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)

    def get_dataset(self, dataset_id: str) -> pd.DataFrame:
        """Load dataset from service"""
        # Try cache first
        cached = cache_get(f"dataset:{dataset_id}")
        if cached is not None:
            return pd.DataFrame(cached)

        # Load from dataset service
        dataset = dataset_service.get_dataset_by_id(dataset_id)
        if dataset is None:
            raise ValueError(f"Dataset {dataset_id} not found")

        # Convert to DataFrame (assuming dataset has data attribute)
        if hasattr(dataset, "data"):
            df = pd.DataFrame(dataset.data)
        else:
            # Load from file
            df = dataset_service.load_dataset_file(dataset_id)

        # Cache it
        cache_set(f"dataset:{dataset_id}", df.to_dict("records"), ttl=3600)

        return df

    def train_model_async(
        self,
        task_id: str,
        dataset_df: pd.DataFrame,
        target_column: str,
        dataset_id: str = "",
        task_type: str = "auto",
        test_size: float = 0.2,
        experiment_name: str = "AutoML",
    ):
        """
        Train model asynchronously (to be called as background task)
        """
        try:
            logger.info(f"Starting async training for task {task_id}")

            # Update task status
            self.tasks[task_id] = {
                "status": "running",
                "message": "Model training in progress",
                "progress": 0,
            }

            # Prepare data: drop any rows where target is missing
            valid_mask = dataset_df[target_column].notna()
            clean_df = dataset_df.loc[valid_mask].copy()
            X = clean_df.drop(columns=[target_column])
            y = clean_df[target_column]

            # Lazy import AutoML and ModelExplainer to prevent high idle memory usage
            from ..ml.automl import AutoML
            from ..ml.explainability import ModelExplainer

            # Initialize AutoML
            automl = AutoML(task_type=task_type, test_size=test_size)

            # Update progress
            self.tasks[task_id]["progress"] = 20
            self.tasks[task_id]["message"] = "Training models..."

            # Train models
            results = automl.fit(
                X, y, dataset_id=dataset_id, experiment_name=experiment_name
            )

            # Update progress
            self.tasks[task_id]["progress"] = 80
            self.tasks[task_id]["message"] = "Generating explanations..."

            # Create explainer using clean processed data
            if (
                hasattr(automl, "X_train_processed")
                and not automl.X_train_processed.empty
            ):
                X_sample = automl.X_train_processed.sample(
                    min(100, len(automl.X_train_processed))
                )
            else:
                X_sample = X.sample(min(100, len(X)))

            try:
                explainer = ModelExplainer(automl.best_model, X_train=X_sample)
            except Exception as explainer_err:
                logger.warning(f"Could not initialize SHAP explainer: {explainer_err}")
                explainer = None

            # Save model
            model_id = task_id
            model_path = self.model_dir / f"{model_id}.joblib"
            automl.save_model(str(model_path))

            # Store in memory
            feature_names = getattr(automl, "feature_names", list(X.columns))
            best_score = float(results.get("best_score", 0.0) or 0.0)
            actual_task_type = results.get("task_type", "classification")

            self.models[model_id] = {
                "automl": automl,
                "model": automl.best_model,
                "explainer": explainer,
                "X_sample": X_sample,
                "feature_names": feature_names,
                "dataset_id": dataset_id,
                "target_column": target_column,
                "task_type": actual_task_type,
                "best_model_name": results["best_model"],
                "best_score": best_score,
                "all_results": results["all_results"],
                "created_at": datetime.utcnow().isoformat(),
            }

            # Update task status
            self.tasks[task_id] = {
                "status": "completed",
                "message": f"Training completed. Best model: {results['best_model']}",
                "progress": 100,
                "model_id": model_id,
                "results": results,
            }

            logger.info(f"Training completed for task {task_id}")

        except Exception as e:
            logger.error(f"Training failed for task {task_id}: {e}")
            self.tasks[task_id] = {
                "status": "failed",
                "message": f"Training failed: {str(e)}",
                "progress": 0,
                "error": str(e),
            }

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a training task"""
        return self.tasks.get(task_id)

    def get_model_metrics(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed metrics for a trained model"""
        if model_id not in self.models:
            return None

        model_info = self.models[model_id]

        return {
            "model_id": model_id,
            "best_model": model_info["best_model_name"],
            "metrics": {
                "best_score": model_info["best_score"],
                "task_type": model_info["task_type"],
            },
            "all_models": model_info["all_results"],
        }

    def predict(self, model_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a single prediction"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")

        model_info = self.models[model_id]
        automl = model_info.get("automl")

        # Convert to DataFrame
        df = pd.DataFrame([data])

        if automl is not None:
            prediction = automl.predict(df)[0]
            try:
                proba = automl.predict_proba(df)[0]
                confidence = float(np.max(proba))
                probabilities = proba.tolist()
            except Exception:
                confidence = None
                probabilities = None
        else:
            model = model_info["model"]
            cols = [c for c in model_info["feature_names"] if c in df.columns]
            df = df[cols] if cols else df
            prediction = model.predict(df)[0]
            confidence = None
            probabilities = None

        return {
            "prediction": (
                float(prediction)
                if isinstance(prediction, (np.integer, np.floating))
                else prediction
            ),
            "confidence": confidence,
            "probabilities": probabilities,
            "model": model_info["best_model_name"],
        }

    def predict_batch(
        self, model_id: str, data_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Make batch predictions"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")

        model_info = self.models[model_id]
        model = model_info["model"]

        # Convert to DataFrame
        df = pd.DataFrame(data_list)

        # Ensure feature order
        df = df[model_info["feature_names"]]

        # Make predictions
        predictions = model.predict(df)

        # Try to get confidences
        confidences = []
        probs = []
        try:
            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(df)
                confidences = [float(np.max(p)) for p in probabilities]
                probs = probabilities.tolist()
            else:
                confidences = [None] * len(predictions)
                probs = [None] * len(predictions)
        except (AttributeError, ValueError, IndexError, TypeError) as exc:
            logger.debug(
                "Could not compute batch prediction probabilities for model %s: %s",
                model_id,
                exc,
            )
            confidences = [None] * len(predictions)
            probs = [None] * len(predictions)

        # Format results
        results = []
        for i, pred in enumerate(predictions):
            results.append(
                {
                    "prediction": (
                        float(pred)
                        if isinstance(pred, (np.integer, np.floating))
                        else pred
                    ),
                    "confidence": confidences[i],
                    "probabilities": probs[i],
                    "model": model_info["best_model_name"],
                }
            )

        return results

    def get_global_explanation(self, model_id: str, top_n: int = 10) -> Dict[str, Any]:
        """Get global feature importance"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")

        model_info = self.models[model_id]
        explainer = model_info["explainer"]
        X_sample = model_info["X_sample"]

        # Get global importance
        importance = explainer.get_global_importance(X_sample, top_n=top_n)

        return importance

    def explain_instance(
        self, model_id: str, instance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Explain a single prediction"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")

        model_info = self.models[model_id]
        explainer = model_info["explainer"]

        # Convert to DataFrame
        df = pd.DataFrame([instance])
        df = df[model_info["feature_names"]]

        # Get explanation
        explanation = explainer.explain_instance(df)

        return explanation

    def get_explanation_plot(self, model_id: str, plot_type: str = "summary") -> str:
        """Generate SHAP visualization plot"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")

        model_info = self.models[model_id]
        explainer = model_info["explainer"]
        X_sample = model_info["X_sample"]

        if plot_type == "summary":
            plot_data = explainer.generate_summary_plot(X_sample)
        elif plot_type == "importance":
            plot_data = explainer.generate_feature_importance_plot(X_sample)
        else:
            raise ValueError(f"Unknown plot type: {plot_type}")

        return plot_data

    def list_models(self) -> List[Dict[str, Any]]:
        """List all trained models with complete summary metadata"""
        models_list = []
        for model_id, info in self.models.items():
            best_score = float(info.get("best_score", 0.0) or 0.0)
            task_type = info.get("task_type", "classification")
            models_list.append(
                {
                    "model_id": model_id,
                    "model_type": info.get("best_model_name", "AutoML"),
                    "best_model": info.get("best_model_name", "AutoML"),
                    "dataset_id": info.get("dataset_id", ""),
                    "target_column": info.get("target_column", ""),
                    "task_type": task_type,
                    "best_score": best_score,
                    "features": len(info.get("feature_names", [])),
                    "metrics": {
                        (
                            "accuracy" if task_type == "classification" else "r2_score"
                        ): best_score,
                        "best_score": best_score,
                    },
                    "created_at": info.get("created_at", datetime.utcnow().isoformat()),
                }
            )
        return models_list

    def delete_model(self, model_id: str):
        """Delete a model"""
        if model_id in self.models:
            # Delete from memory
            del self.models[model_id]

            # Delete from disk
            model_path = self.model_dir / f"{model_id}.joblib"
            if model_path.exists():
                model_path.unlink()

            # Clear cache
            cache_delete(f"model:{model_id}")

            logger.info(f"Model {model_id} deleted")


# Singleton instance
model_service = ModelService()
