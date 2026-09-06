"""
Enhanced Model Service with AutoML, Inference, and Explainability integration
Backed by persistent SQL storage (PostgreSQL / SQLite).
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
from ..utils.storage import models_storage

logger = logging.getLogger(__name__)


class ModelService:
    """Service for managing model training, inference, and explanations with SQL persistence"""

    def __init__(self, storage=None):
        self.storage = storage or models_storage
        self.models = {}  # In-memory fast cache
        self.tasks = {}  # In-memory task status tracking
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)

    def get_dataset(
        self, dataset_id: str, user_id: Optional[str] = None
    ) -> pd.DataFrame:
        """Load dataset from service"""
        # Try cache first
        cached = cache_get(f"dataset:{dataset_id}")
        if cached is not None:
            return pd.DataFrame(cached)

        # Load from dataset service
        df = dataset_service.load_dataset_file(dataset_id, user_id=user_id)
        if df is None or df.empty:
            raise ValueError(f"Dataset {dataset_id} not found or empty")

        # Cache it in Redis/in-memory cache
        try:
            cache_set(f"dataset:{dataset_id}", df.to_dict("records"), ttl=3600)
        except Exception:
            pass

        return df

    def train_model_async(
        self,
        task_id: str,
        dataset_df: pd.DataFrame,
        target_column: str,
        dataset_id: str = "",
        user_id: Optional[str] = None,
        task_type: str = "auto",
        test_size: float = 0.2,
        experiment_name: str = "AutoML",
    ):
        """
        Train model asynchronously (to be called as background task)
        """
        try:
            logger.info(f"Starting async training for task {task_id} by user {user_id}")

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

            # Train models with log_artifacts=False for ultra-fast training without MLflow hang
            results = automl.fit(
                X,
                y,
                dataset_id=dataset_id,
                experiment_name=experiment_name,
                log_artifacts=False,
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

            # Serialize model bundle to compressed bytes
            model_id = task_id
            feature_names = getattr(automl, "feature_names", list(X.columns))
            best_score = float(results.get("best_score", 0.0) or 0.0)
            actual_task_type = results.get("task_type", "classification")

            model_bundle = {
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

            # Serialize bundle with joblib into bytes
            artifact_bytes = automl.serialize_bundle()

            # Persist directly into PostgreSQL / SQLite database
            metrics_dict = results["all_results"].get(results["best_model"], {})
            self.storage.save_model(
                model_id=model_id,
                dataset_id=dataset_id,
                target_column=target_column,
                task_type=actual_task_type,
                best_model_name=results["best_model"],
                best_score=best_score,
                feature_names=feature_names,
                metrics=metrics_dict,
                all_results=results["all_results"],
                model_artifact=artifact_bytes,
                user_id=user_id,
                bundle=model_bundle,
            )

            # Store in fast memory cache
            self.models[model_id] = model_bundle

            # Also cache to local disk for zero-latency local fallback
            try:
                disk_path = self.model_dir / f"{model_id}.joblib"
                with open(disk_path, "wb") as f:
                    f.write(artifact_bytes)
            except Exception as disk_err:
                logger.warning(f"Could not write model to local disk: {disk_err}")

            # Update task status
            self.tasks[task_id] = {
                "status": "completed",
                "message": f"Training completed. Best model: {results['best_model']}",
                "progress": 100,
                "model_id": model_id,
                "results": results,
            }

            logger.info(f"Training completed successfully for task {task_id}")

        except Exception as e:
            logger.error(f"Training failed for task {task_id}: {e}", exc_info=True)
            self.tasks[task_id] = {
                "status": "failed",
                "message": f"Training failed: {str(e)}",
                "progress": 0,
                "error": str(e),
            }

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a training task"""
        return self.tasks.get(task_id)

    def get_model(
        self, model_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get full model bundle (from memory cache or deserialized from SQL)."""
        if model_id in self.models:
            bundle = self.models[model_id]
            return bundle

        # Fetch from SQL storage
        bundle = self.storage.get_model_bundle(model_id, user_id=user_id)
        if bundle:
            # Recreate explainer if needed on demand
            if bundle.get("explainer") is None and bundle.get("model") is not None:
                try:
                    from ..ml.explainability import ModelExplainer

                    X_sample = bundle.get("X_sample")
                    if X_sample is not None:
                        bundle["explainer"] = ModelExplainer(
                            bundle["model"], X_train=X_sample
                        )
                except Exception as expl_err:
                    logger.debug(f"Could not reinitialize explainer: {expl_err}")

            self.models[model_id] = bundle
            return bundle

        return None

    def get_model_metrics(
        self, model_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get detailed metrics for a trained model"""
        model_meta = self.storage.get_model(model_id, user_id=user_id)
        if not model_meta:
            return None

        return {
            "model_id": model_id,
            "best_model": model_meta["best_model"],
            "metrics": model_meta["metrics"],
            "all_models": model_meta.get("all_results", {}),
        }

    def predict(
        self, model_id: str, data: Dict[str, Any], user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make a single prediction"""
        model_info = self.get_model(model_id, user_id=user_id)
        if not model_info:
            raise ValueError(f"Model {model_id} not found")

        automl = model_info.get("automl")
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
        self,
        model_id: str,
        data_list: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Make batch predictions"""
        model_info = self.get_model(model_id, user_id=user_id)
        if not model_info:
            raise ValueError(f"Model {model_id} not found")

        automl = model_info.get("automl")
        df = pd.DataFrame(data_list)

        if automl is not None:
            predictions = automl.predict(df)
            try:
                probabilities = automl.predict_proba(df)
                confidences = [float(np.max(p)) for p in probabilities]
                probs = probabilities.tolist()
            except Exception:
                confidences = [None] * len(predictions)
                probs = [None] * len(predictions)
        else:
            model = model_info["model"]
            cols = [c for c in model_info["feature_names"] if c in df.columns]
            df_sub = df[cols] if cols else df
            predictions = model.predict(df_sub)
            confidences = [None] * len(predictions)
            probs = [None] * len(predictions)

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

    def get_global_explanation(
        self, model_id: str, top_n: int = 10, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get global feature importance"""
        model_info = self.get_model(model_id, user_id=user_id)
        if not model_info:
            raise ValueError(f"Model {model_id} not found")

        explainer = model_info.get("explainer")
        X_sample = model_info.get("X_sample")

        if explainer is None or X_sample is None:
            # Fallback to feature importance from model itself
            model = model_info["model"]
            feature_names = model_info["feature_names"]
            if hasattr(model, "feature_importances_"):
                imp = model.feature_importances_
            elif hasattr(model, "coef_"):
                imp = np.abs(model.coef_)
                if imp.ndim > 1:
                    imp = imp.mean(axis=0)
            else:
                imp = np.ones(len(feature_names)) / max(1, len(feature_names))

            sorted_pairs = sorted(
                zip(feature_names, [float(x) for x in imp]),
                key=lambda x: x[1],
                reverse=True,
            )[:top_n]
            return {
                "feature_importance": dict(sorted_pairs),
                "top_features": [p[0] for p in sorted_pairs],
                "importance_values": [p[1] for p in sorted_pairs],
                "features": [{"name": p[0], "importance": p[1]} for p in sorted_pairs],
            }

        importance = explainer.get_global_importance(X_sample, top_n=top_n)
        return importance

    def explain_instance(
        self,
        model_id: str,
        instance: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Explain a single prediction"""
        model_info = self.get_model(model_id, user_id=user_id)
        if not model_info:
            raise ValueError(f"Model {model_id} not found")

        explainer = model_info.get("explainer")
        if not explainer:
            raise ValueError(f"Explainer not available for model {model_id}")

        df = pd.DataFrame([instance])
        df = df[model_info["feature_names"]]
        return explainer.explain_instance(df)

    def get_explanation_plot(
        self,
        model_id: str,
        plot_type: str = "summary",
        user_id: Optional[str] = None,
    ) -> str:
        """Generate SHAP visualization plot"""
        model_info = self.get_model(model_id, user_id=user_id)
        if not model_info:
            raise ValueError(f"Model {model_id} not found")

        explainer = model_info.get("explainer")
        X_sample = model_info.get("X_sample")

        if not explainer or X_sample is None:
            raise ValueError(f"Explainer not available for model {model_id}")

        if plot_type == "summary":
            return explainer.generate_summary_plot(X_sample)
        elif plot_type == "importance":
            return explainer.generate_feature_importance_plot(X_sample)
        else:
            raise ValueError(f"Unknown plot type: {plot_type}")

    def list_models(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all trained models with complete summary metadata from SQL storage"""
        return self.storage.list_models(user_id=user_id)

    def delete_model(self, model_id: str, user_id: Optional[str] = None):
        """Delete a model from memory and SQL database"""
        # Delete from memory
        self.models.pop(model_id, None)

        # Delete from SQL database
        self.storage.delete_model(model_id, user_id=user_id)

        # Delete from disk
        model_path = self.model_dir / f"{model_id}.joblib"
        if model_path.exists():
            try:
                model_path.unlink()
            except OSError:
                pass

        # Clear cache
        cache_delete(f"model:{model_id}")
        logger.info(f"Model {model_id} deleted")


# Singleton instance
model_service = ModelService()
