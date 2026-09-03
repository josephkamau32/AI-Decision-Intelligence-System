import pandas as pd
import numpy as np
from sklearn.model_selection import (
    train_test_split,
    cross_val_score,
    StratifiedKFold,
    KFold,
)
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
)
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier, XGBRegressor
import joblib
import mlflow
import mlflow.sklearn
import mlflow.pytorch
from typing import Dict, Any, List, Tuple, Optional
import logging
from datetime import datetime
import os

from ..ml.data_preprocessing import DataCleaner, FeatureEngineer
from ..ml.time_series import (
    ProphetForecaster,
    LSTMForecaster,
    detect_time_series,
    calculate_forecast_metrics,
)

logger = logging.getLogger(__name__)


class AutoML:
    """
    Automated Machine Learning engine that trains and compares multiple models
    """

    def __init__(
        self, task_type: str = "auto", test_size: float = 0.2, random_state: int = 42
    ):
        """
        Initialize AutoML engine

        Args:
            task_type: 'classification', 'regression', 'time_series', or 'auto' (auto-detect)
            test_size: Proportion of dataset to use for testing
            random_state: Random seed for reproducibility
        """
        self.task_type = task_type
        self.test_size = test_size
        self.random_state = random_state
        self.best_model = None
        self.best_model_name = None
        self.best_score = None
        self.models = {}
        self.results = {}
        self.date_column = None  # For time-series tasks

        logger.info(
            f"Initialized AutoML with task_type={task_type}, test_size={test_size}"
        )

    def detect_task_type(self, X: pd.DataFrame, y: pd.Series) -> str:
        """Automatically detect if task is classification, regression, or time-series"""
        # Detect date column if present (for datetime feature engineering)
        date_col = None
        for col in X.columns:
            if (
                pd.api.types.is_datetime64_any_dtype(X[col])
                or "date" in str(col).lower()
                or "time" in str(col).lower()
            ):
                date_col = col
                break
        if date_col is not None:
            self.date_column = date_col

        if self.task_type != "auto":
            return self.task_type

        # Target is non-numeric string/category/bool -> classification
        if not pd.api.types.is_numeric_dtype(y):
            logger.info("Auto-detected task type: classification (non-numeric target)")
            return "classification"

        # If numeric, check unique count
        n_unique = y.nunique(dropna=True)
        n_total = len(y.dropna())

        # Binary or small discrete classes (<= 20 unique values or < 5% unique) -> classification
        if n_unique <= 20 or (n_total > 0 and (n_unique / n_total) < 0.05):
            logger.info(f"Auto-detected task type: classification ({n_unique} unique classes)")
            return "classification"

        # Continuous numeric target -> regression
        logger.info("Auto-detected task type: regression (continuous numeric target)")
        return "regression"

    def get_classification_models(self) -> Dict[str, Any]:
        """Return dictionary of classification models to train"""
        return {
            "LogisticRegression": LogisticRegression(
                random_state=self.random_state, max_iter=1000
            ),
            "RandomForest": RandomForestClassifier(
                n_estimators=100, random_state=self.random_state
            ),
            "XGBoost": XGBClassifier(
                random_state=self.random_state,
                use_label_encoder=False,
                eval_metric="logloss",
            ),
            "GradientBoosting": GradientBoostingClassifier(
                random_state=self.random_state
            ),
        }

    def get_regression_models(self) -> Dict[str, Any]:
        """Return dictionary of regression models to train"""
        return {
            "LinearRegression": LinearRegression(),
            "Ridge": Ridge(random_state=self.random_state),
            "Lasso": Lasso(random_state=self.random_state),
            "RandomForest": RandomForestRegressor(
                n_estimators=100, random_state=self.random_state
            ),
            "XGBoost": XGBRegressor(random_state=self.random_state),
            "GradientBoosting": GradientBoostingRegressor(
                random_state=self.random_state
            ),
        }

    def get_timeseries_models(self, epochs: int = 10) -> Dict[str, Any]:
        """Return dictionary of time-series forecasting models to train"""
        models = {}
        try:
            models["Prophet"] = ProphetForecaster()
        except Exception as e:
            logger.warning(f"Prophet unavailable: {e}")

        try:
            models["LSTM"] = LSTMForecaster(
                seq_length=10, hidden_size=64, epochs=epochs, batch_size=32
            )
        except Exception as e:
            logger.warning(f"LSTM unavailable: {e}")

        return models

    def evaluate_classification(self, y_true, y_pred, y_prob=None) -> Dict[str, float]:
        """Calculate classification metrics"""
        metrics = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(
                precision_score(y_true, y_pred, average="weighted", zero_division=0)
            ),
            "recall": float(
                recall_score(y_true, y_pred, average="weighted", zero_division=0)
            ),
            "f1_score": float(
                f1_score(y_true, y_pred, average="weighted", zero_division=0)
            ),
        }

        # Add ROC-AUC for binary classification
        if len(np.unique(y_true)) == 2 and y_prob is not None:
            try:
                metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob[:, 1]))
            except (ValueError, IndexError, TypeError) as exc:
                logger.debug("ROC-AUC score computation skipped: %s", exc)

        return metrics

    def evaluate_regression(self, y_true, y_pred) -> Dict[str, float]:
        """Calculate regression metrics"""
        return {
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "r2_score": float(r2_score(y_true, y_pred)),
            "mse": float(mean_squared_error(y_true, y_pred)),
        }

    def train_and_evaluate(
        self,
        X_train,
        X_test,
        y_train,
        y_test,
        model_name: str,
        model: Any,
        use_cv: bool = True,
    ) -> Dict[str, Any]:
        """
        Train a single model and evaluate it

        Returns:
            Dictionary containing model, metrics, and cross-validation scores
        """
        logger.info(f"Training {model_name}...")

        # Train model
        model.fit(X_train, y_train)

        # Make predictions
        y_pred = model.predict(X_test)

        # Calculate metrics
        if self.task_type == "classification":
            y_prob = (
                model.predict_proba(X_test) if hasattr(model, "predict_proba") else None
            )
            metrics = self.evaluate_classification(y_test, y_pred, y_prob)
            primary_metric = "accuracy"
        else:
            metrics = self.evaluate_regression(y_test, y_pred)
            primary_metric = "r2_score"

        # Cross-validation
        cv_scores = None
        if use_cv:
            try:
                if self.task_type == "classification":
                    cv = StratifiedKFold(
                        n_splits=5, shuffle=True, random_state=self.random_state
                    )
                    scoring = "accuracy"
                else:
                    cv = KFold(n_splits=5, shuffle=True, random_state=self.random_state)
                    scoring = "r2"

                cv_scores = cross_val_score(
                    model, X_train, y_train, cv=cv, scoring=scoring
                )
                metrics["cv_mean"] = float(cv_scores.mean())
                metrics["cv_std"] = float(cv_scores.std())
                logger.info(
                    f"{model_name} CV Score: {metrics['cv_mean']:.4f} (+/- {metrics['cv_std']:.4f})"
                )
            except Exception as e:
                logger.warning(f"Cross-validation failed for {model_name}: {e}")

        logger.info(f"{model_name} {primary_metric}: {metrics[primary_metric]:.4f}")

        return {
            "model": model,
            "metrics": metrics,
            "primary_score": metrics[primary_metric],
        }

    def preprocess_fit(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Production-grade AutoML preprocessing:
        - Drops rows where target y is NaN
        - Auto-detects task type
        - Encodes target for classification with LabelEncoder
        - Drops all-NaN columns, constants, and high-cardinality ID columns
        - Extracts year, month, day, dayofweek from datetimes
        - Imputes numerical NaNs with column median
        - Imputes & encodes categorical columns
        - Casts everything to float for universal model compatibility
        """
        # 1. Clean target
        valid_mask = y.notna()
        X = X.loc[valid_mask].copy()
        y = y.loc[valid_mask].copy()

        # 2. Detect task type
        self.task_type = self.detect_task_type(X, y)

        # 3. Process target
        if self.task_type == "classification":
            self.target_encoder = LabelEncoder()
            y_clean = pd.Series(self.target_encoder.fit_transform(y.astype(str)), index=y.index, name=y.name)
            self.classes_ = list(self.target_encoder.classes_)
        else:
            y_numeric = pd.to_numeric(y, errors="coerce")
            valid_y = y_numeric.notna()
            if valid_y.sum() == 0:
                self.task_type = "classification"
                self.target_encoder = LabelEncoder()
                y_clean = pd.Series(self.target_encoder.fit_transform(y.astype(str)), index=y.index, name=y.name)
                self.classes_ = list(self.target_encoder.classes_)
            else:
                X = X.loc[valid_y].copy()
                y_clean = y_numeric.loc[valid_y].copy()
                self.target_encoder = None
                self.classes_ = None

        # 4. Filter X columns
        self.dropped_cols = []
        clean_cols = []
        n_rows = len(X)

        for col in X.columns:
            # Check all-NaN
            if X[col].isna().all():
                self.dropped_cols.append(col)
                continue
            # Check single constant value
            if X[col].nunique(dropna=True) <= 1:
                self.dropped_cols.append(col)
                continue
            # Check high-cardinality ID
            col_str = str(col).lower()
            if (col_str.endswith("_id") or col_str == "id") and X[col].nunique() > n_rows * 0.5:
                self.dropped_cols.append(col)
                continue
            clean_cols.append(col)

        X = X[clean_cols].copy()

        # 5. Extract datetime features
        self.datetime_cols = []
        for col in list(X.columns):
            if pd.api.types.is_datetime64_any_dtype(X[col]) or "date" in str(col).lower() or "time" in str(col).lower():
                try:
                    dt_series = pd.to_datetime(X[col], errors="coerce")
                    if dt_series.notna().sum() > 0.5 * n_rows:
                        median_year = dt_series.dt.year.median()
                        X[f"{col}_year"] = dt_series.dt.year.fillna(median_year if pd.notna(median_year) else 2024)
                        X[f"{col}_month"] = dt_series.dt.month.fillna(1)
                        X[f"{col}_day"] = dt_series.dt.day.fillna(1)
                        X[f"{col}_dayofweek"] = dt_series.dt.dayofweek.fillna(0)
                        self.datetime_cols.append(col)
                except Exception:
                    pass

        if self.datetime_cols:
            X = X.drop(columns=self.datetime_cols, errors="ignore")

        # 6. Process numerical columns
        self.numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        self.num_medians = {}
        for col in self.numeric_cols:
            median_val = X[col].median()
            if pd.isna(median_val):
                median_val = 0.0
            self.num_medians[col] = float(median_val)
            X[col] = X[col].fillna(median_val)

        # 7. Process categorical columns
        self.categorical_cols = [c for c in X.columns if c not in self.numeric_cols]
        self.cat_modes = {}
        self.cat_encoders = {}
        for col in self.categorical_cols:
            mode_val = X[col].mode()
            fill_val = str(mode_val[0]) if not mode_val.empty else "missing"
            self.cat_modes[col] = fill_val
            filled_series = X[col].fillna(fill_val).astype(str)
            le = LabelEncoder()
            X[col] = le.fit_transform(filled_series)
            self.cat_encoders[col] = le

        # Ensure all columns are numeric float
        X = X.astype(float)
        self.feature_names = X.columns.tolist()
        self.X_train_processed = X

        return X, y_clean

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform new data using fitted preprocessing parameters"""
        X = X.copy()
        if hasattr(self, "dropped_cols") and self.dropped_cols:
            X = X.drop(columns=[c for c in self.dropped_cols if c in X.columns], errors="ignore")

        if hasattr(self, "datetime_cols") and self.datetime_cols:
            for col in self.datetime_cols:
                if col in X.columns:
                    try:
                        dt_series = pd.to_datetime(X[col], errors="coerce")
                        X[f"{col}_year"] = dt_series.dt.year.fillna(2024)
                        X[f"{col}_month"] = dt_series.dt.month.fillna(1)
                        X[f"{col}_day"] = dt_series.dt.day.fillna(1)
                        X[f"{col}_dayofweek"] = dt_series.dt.dayofweek.fillna(0)
                    except Exception:
                        pass
            X = X.drop(columns=[c for c in self.datetime_cols if c in X.columns], errors="ignore")

        if hasattr(self, "num_medians"):
            for col, med in self.num_medians.items():
                if col in X.columns:
                    X[col] = pd.to_numeric(X[col], errors="coerce").fillna(med)
                else:
                    X[col] = med

        if hasattr(self, "cat_encoders"):
            for col, le in self.cat_encoders.items():
                fill_val = self.cat_modes.get(col, "missing")
                if col in X.columns:
                    filled = X[col].fillna(fill_val).astype(str)
                    classes_set = set(le.classes_)
                    fallback = le.classes_[0] if len(le.classes_) > 0 else fill_val
                    filled_mapped = filled.apply(lambda x: x if x in classes_set else fallback)
                    X[col] = le.transform(filled_mapped)
                else:
                    X[col] = 0

        if hasattr(self, "feature_names"):
            for col in self.feature_names:
                if col not in X.columns:
                    X[col] = 0.0
            X = X[self.feature_names]

        return X.astype(float)

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        dataset_id: str = None,
        experiment_name: str = "AutoML",
        use_cv: bool = True,
        log_artifacts: bool = True,
    ) -> Dict[str, Any]:
        """
        Train multiple models and select the best one
        """
        # Handle time-series separately
        if self.task_type == "time_series":
            return self._fit_timeseries(
                X, y, dataset_id, experiment_name, log_artifacts=log_artifacts
            )

        # Preprocess features and target
        X_clean, y_clean = self.preprocess_fit(X, y)
        X = X_clean
        y = y_clean

        # Stratify safely
        can_stratify = False
        if self.task_type == "classification":
            counts = pd.Series(y).value_counts()
            can_stratify = len(counts) > 1 and counts.min() >= 2

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y if can_stratify else None,
        )

        logger.info(f"Training set: {X_train.shape}, Test set: {X_test.shape}")

        # Get models based on task type
        if self.task_type == "classification":
            models = self.get_classification_models()
        else:
            models = self.get_regression_models()

        # Set up MLflow
        try:
            mlflow.set_experiment(experiment_name)
        except Exception as e:
            logger.warning(f"Could not set MLflow experiment: {e}")

        # Train all models
        results = {}
        try:
            with mlflow.start_run(
                run_name=f"AutoML_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ):
                # Log parameters
                mlflow.log_param("task_type", self.task_type)
                mlflow.log_param("test_size", self.test_size)
                mlflow.log_param("n_features", X.shape[1])
                mlflow.log_param("n_samples", X.shape[0])
                if dataset_id:
                    mlflow.log_param("dataset_id", dataset_id)

                # Train each model
                for model_name, model in models.items():
                    try:
                        with mlflow.start_run(
                            run_name=model_name, nested=True
                        ) as child_run:
                            result = self.train_and_evaluate(
                                X_train,
                                X_test,
                                y_train,
                                y_test,
                                model_name,
                                model,
                                use_cv=use_cv,
                            )
                            result["run_id"] = child_run.info.run_id
                            results[model_name] = result

                            # Log to MLflow
                            mlflow.log_params(
                                {f"{model_name}_param": str(model.get_params())}
                            )
                            mlflow.log_metrics(result["metrics"])
                            if log_artifacts:
                                try:
                                    mlflow.sklearn.log_model(result["model"], model_name)
                                except Exception as e:
                                    logger.warning(
                                        f"Failed to log model artifact for {model_name}: {e}"
                                    )

                    except Exception as e:
                        logger.error(f"Failed to train {model_name}: {e}")
                        continue
        except Exception as e:
            logger.warning(f"MLflow run context error: {e}. Falling back to direct training.")
            for model_name, model in models.items():
                try:
                    result = self.train_and_evaluate(
                        X_train,
                        X_test,
                        y_train,
                        y_test,
                        model_name,
                        model,
                        use_cv=use_cv,
                    )
                    results[model_name] = result
                except Exception as model_err:
                    logger.error(f"Failed to train {model_name} in fallback: {model_err}")
                    continue

        # Robust fallback if no advanced models succeeded
        if not results:
            logger.warning("No models succeeded in standard evaluation. Training robust fallback model...")
            if self.task_type == "classification":
                fallback_model = RandomForestClassifier(n_estimators=50, random_state=self.random_state)
            else:
                fallback_model = RandomForestRegressor(n_estimators=50, random_state=self.random_state)
            fallback_model.fit(X_train, y_train)
            y_pred = fallback_model.predict(X_test)
            if self.task_type == "classification":
                fallback_metrics = self.evaluate_classification(y_test, y_pred)
                score = fallback_metrics["accuracy"]
            else:
                fallback_metrics = self.evaluate_regression(y_test, y_pred)
                score = fallback_metrics["r2_score"]
            results["RandomForest"] = {
                "model": fallback_model,
                "metrics": fallback_metrics,
                "primary_score": score,
            }

        # Select best model
        self.best_model_name = max(
            results, key=lambda x: results[x]["primary_score"]
        )
        self.best_model = results[self.best_model_name]["model"]
        self.best_score = results[self.best_model_name]["primary_score"]

        logger.info(
            f"Best model: {self.best_model_name} with score: {self.best_score:.4f}"
        )

        self.results = results
        self.models = {name: res["model"] for name, res in results.items()}

        return {
            "best_model": self.best_model_name,
            "best_score": self.best_score,
            "all_results": {name: res["metrics"] for name, res in results.items()},
            "task_type": self.task_type,
        }

    def save_model(self, filepath: str):
        """Save the best model to disk"""
        if self.best_model is None:
            raise ValueError("No model has been trained yet")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self.best_model, filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str):
        """Load a model from disk"""
        self.best_model = joblib.load(filepath)
        logger.info(f"Model loaded from {filepath}")
        return self.best_model

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions using the best model"""
        if self.best_model is None:
            raise ValueError("No model has been trained yet")

        X_trans = self.transform(X)
        preds = self.best_model.predict(X_trans)
        if getattr(self, "target_encoder", None) is not None:
            try:
                preds = self.target_encoder.inverse_transform(preds.astype(int))
            except Exception:
                pass
        return preds

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities (classification only)"""
        if self.best_model is None:
            raise ValueError("No model has been trained yet")

        X_trans = self.transform(X)
        if hasattr(self.best_model, "predict_proba"):
            return self.best_model.predict_proba(X_trans)
        else:
            raise ValueError(f"{self.best_model_name} does not support predict_proba")

    def _fit_timeseries(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        dataset_id: Optional[str] = None,
        experiment_name: str = "AutoML_TimeSeries",
        log_artifacts: bool = True,
    ) -> Dict[str, Any]:
        """
        Train time-series forecasting models

        Args:
            X: Feature dataset (must include date column)
            y: Target variable (time-series values)
            dataset_id: Optional dataset identifier
            experiment_name: MLflow experiment name
            log_artifacts: Whether to log model artifacts to MLflow (default: True)

        Returns:
            Dictionary with best model info and all results
        """
        if not hasattr(self, "date_column") or self.date_column is None:
            for col in X.columns:
                if (
                    pd.api.types.is_datetime64_any_dtype(X[col])
                    or "date" in str(col).lower()
                    or "time" in str(col).lower()
                ):
                    self.date_column = col
                    break
            if self.date_column is None:
                for col in X.columns:
                    try:
                        pd.to_datetime(X[col])
                        self.date_column = col
                        break
                    except Exception:
                        pass

        if self.date_column is None:
            raise ValueError("No date column detected for time-series task")

        logger.info(f"Training time-series models with {len(X)} samples using date_column={self.date_column}")

        # Prepare data for time-series
        df = X.copy()
        df["target"] = y

        # Split data temporally (last test_size% for testing)
        split_idx = int(len(df) * (1 - self.test_size))
        df_train = df.iloc[:split_idx]
        df_test = df.iloc[split_idx:]

        # Get time-series models
        models = self.get_timeseries_models()

        # Set up MLflow
        mlflow.set_experiment(experiment_name)

        results = {}
        with mlflow.start_run(
            run_name=f"AutoML_TS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ):
            # Log parameters
            mlflow.log_param("task_type", "time_series")
            mlflow.log_param("test_size", self.test_size)
            mlflow.log_param("n_samples", len(df))
            mlflow.log_param("date_column", self.date_column)
            if dataset_id:
                mlflow.log_param("dataset_id", dataset_id)

            # Train each model
            for model_name, model in models.items():
                try:
                    with mlflow.start_run(
                        run_name=model_name, nested=True
                    ) as child_run:
                        logger.info(f"Training {model_name}...")

                        # Train model
                        if model_name == "Prophet":
                            model.fit(df_train, self.date_column, "target")
                            # Predict on test set
                            forecast = model.predict(periods=len(df_test))
                            y_pred = forecast["yhat"].tail(len(df_test)).values
                        else:  # LSTM
                            model.fit(df_train, self.date_column, "target")
                            # Get last sequence from training data
                            last_seq = df_train["target"].tail(model.seq_length).values
                            y_pred = model.predict(last_seq, periods=len(df_test))

                        # Calculate metrics
                        y_true = df_test["target"].values
                        metrics = calculate_forecast_metrics(y_true, y_pred)

                        # Store results
                        results[model_name] = {
                            "model": model,
                            "metrics": metrics,
                            "primary_score": -metrics[
                                "mape"
                            ],  # Negative MAPE (lower is better, so negate for max)
                            "run_id": child_run.info.run_id,
                        }

                        # Log to MLflow
                        mlflow.log_metrics(metrics)

                        # Save model
                        if log_artifacts:
                            try:
                                if model_name == "Prophet":
                                    mlflow.sklearn.log_model(model.model, model_name)
                                else:
                                    import tempfile

                                    with tempfile.TemporaryDirectory() as tmp_dir:
                                        tmp_file = os.path.join(
                                            tmp_dir, f"{model_name}_model.pt"
                                        )
                                        model.save_model(tmp_file)
                                        mlflow.log_artifact(tmp_file)
                            except Exception as e:
                                logger.warning(
                                    f"Failed to log time-series artifact for {model_name}: {e}"
                                )

                        logger.info(
                            f"{model_name} MAPE: {metrics['mape']:.2f}%, RMSE: {metrics['rmse']:.4f}"
                        )

                except Exception as e:
                    logger.error(f"Failed to train {model_name}: {e}")
                    continue

            # Select best model (lowest MAPE)
            if results:
                self.best_model_name = max(
                    results, key=lambda x: results[x]["primary_score"]
                )
                self.best_model = results[self.best_model_name]["model"]
                self.best_score = results[self.best_model_name]["metrics"]["mape"]
                best_run_id = results[self.best_model_name].get("run_id")

                logger.info(
                    f"Best model: {self.best_model_name} with MAPE: {self.best_score:.2f}%"
                )

                # Log best model
                mlflow.log_metric("best_mape", self.best_score)
                mlflow.log_param("best_model", self.best_model_name)

                if best_run_id and log_artifacts:
                    try:
                        model_uri = f"runs:/{best_run_id}/{self.best_model_name}"
                        mlflow.register_model(model_uri, f"best_{self.task_type}_model")
                    except Exception as e:
                        logger.warning(
                            f"Could not register model in MLflow model registry: {e}"
                        )

        self.results = results
        self.models = {name: res["model"] for name, res in results.items()}

        return {
            "best_model": self.best_model_name,
            "best_score": self.best_score,
            "all_results": {name: res["metrics"] for name, res in results.items()},
            "task_type": "time_series",
        }
