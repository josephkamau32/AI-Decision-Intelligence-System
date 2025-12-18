import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, KFold
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
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
from ..ml.time_series import ProphetForecaster, LSTMForecaster, detect_time_series, calculate_forecast_metrics

logger = logging.getLogger(__name__)

class AutoML:
    """
    Automated Machine Learning engine that trains and compares multiple models
    """
    
    def __init__(self, task_type: str = 'auto', test_size: float = 0.2, random_state: int = 42):
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
        
        logger.info(f"Initialized AutoML with task_type={task_type}, test_size={test_size}")
    
    def detect_task_type(self, X: pd.DataFrame, y: pd.Series) -> str:
        """Automatically detect if task is classification, regression, or time-series"""
        if self.task_type != 'auto':
            return self.task_type
        
        # Check for time-series data
        date_col = detect_time_series(X)
        if date_col is not None:
            self.date_column = date_col
            logger.info(f"Auto-detected task type: time_series (date column: {date_col})")
            return 'time_series'
        
        # Check if target is numeric with many unique values
        if y.dtype in ['int64', 'float64']:
            unique_ratio = len(y.unique()) / len(y)
            if unique_ratio > 0.05:  # More than 5% unique values suggests regression
                logger.info("Auto-detected task type: regression")
                return 'regression'
        
        logger.info("Auto-detected task type: classification")
        return 'classification'
    
    def get_classification_models(self) -> Dict[str, Any]:
        """Return dictionary of classification models to train"""
        return {
            'LogisticRegression': LogisticRegression(random_state=self.random_state, max_iter=1000),
            'RandomForest': RandomForestClassifier(n_estimators=100, random_state=self.random_state, n_jobs=-1),
            'XGBoost': XGBClassifier(random_state=self.random_state, n_jobs=-1, use_label_encoder=False, eval_metric='logloss'),
            'GradientBoosting': GradientBoostingClassifier(random_state=self.random_state)
        }
    
    def get_regression_models(self) -> Dict[str, Any]:
        """Return dictionary of regression models to train"""
        return {
            'LinearRegression': LinearRegression(),
            'Ridge': Ridge(random_state=self.random_state),
            'Lasso': Lasso(random_state=self.random_state),
            'RandomForest': RandomForestRegressor(n_estimators=100, random_state=self.random_state, n_jobs=-1),
            'XGBoost': XGBRegressor(random_state=self.random_state, n_jobs=-1),
            'GradientBoosting': GradientBoostingRegressor(random_state=self.random_state)
        }
    
    def get_timeseries_models(self) -> Dict[str, Any]:
        """Return dictionary of time-series forecasting models to train"""
        return {
            'Prophet': ProphetForecaster(),
            'LSTM': LSTMForecaster(
                seq_length=10,
                hidden_size=64,
                epochs=50,  # Reduced for faster training
                batch_size=32
            )
        }
    
    def evaluate_classification(self, y_true, y_pred, y_prob=None) -> Dict[str, float]:
        """Calculate classification metrics"""
        metrics = {
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'precision': float(precision_score(y_true, y_pred, average='weighted', zero_division=0)),
            'recall': float(recall_score(y_true, y_pred, average='weighted', zero_division=0)),
            'f1_score': float(f1_score(y_true, y_pred, average='weighted', zero_division=0))
        }
        
        # Add ROC-AUC for binary classification
        if len(np.unique(y_true)) == 2 and y_prob is not None:
            try:
                metrics['roc_auc'] = float(roc_auc_score(y_true, y_prob[:, 1]))
            except:
                pass
        
        return metrics
    
    def evaluate_regression(self, y_true, y_pred) -> Dict[str, float]:
        """Calculate regression metrics"""
        return {
            'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
            'mae': float(mean_absolute_error(y_true, y_pred)),
            'r2_score': float(r2_score(y_true, y_pred)),
            'mse': float(mean_squared_error(y_true, y_pred))
        }
    
    def train_and_evaluate(
        self, 
        X_train, 
        X_test, 
        y_train, 
        y_test, 
        model_name: str, 
        model: Any,
        use_cv: bool = True
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
        if self.task_type == 'classification':
            y_prob = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None
            metrics = self.evaluate_classification(y_test, y_pred, y_prob)
            primary_metric = 'accuracy'
        else:
            metrics = self.evaluate_regression(y_test, y_pred)
            primary_metric = 'r2_score'
        
        # Cross-validation
        cv_scores = None
        if use_cv:
            try:
                if self.task_type == 'classification':
                    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=self.random_state)
                    scoring = 'accuracy'
                else:
                    cv = KFold(n_splits=5, shuffle=True, random_state=self.random_state)
                    scoring = 'r2'
                
                cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring=scoring, n_jobs=-1)
                metrics['cv_mean'] = float(cv_scores.mean())
                metrics['cv_std'] = float(cv_scores.std())
                logger.info(f"{model_name} CV Score: {metrics['cv_mean']:.4f} (+/- {metrics['cv_std']:.4f})")
            except Exception as e:
                logger.warning(f"Cross-validation failed for {model_name}: {e}")
        
        logger.info(f"{model_name} {primary_metric}: {metrics[primary_metric]:.4f}")
        
        return {
            'model': model,
            'metrics': metrics,
            'primary_score': metrics[primary_metric]
        }
    
    def fit(
        self, 
        X: pd.DataFrame, 
        y: pd.Series,
        dataset_id: str = None,
        experiment_name: str = "AutoML"
    ) -> Dict[str, Any]:
        """
        Train multiple models and select the best one
        
        Args:
            X: Feature dataset
            y: Target variable
            dataset_id: Optional dataset identifier
            experiment_name: MLflow experiment name
            
        Returns:
            Dictionary with best model info and all results
        """
        # Detect task type
        self.task_type = self.detect_task_type(X, y)
        
        # Handle time-series separately
        if self.task_type == 'time_series':
            return self._fit_timeseries(X, y, dataset_id, experiment_name)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state,
            stratify=y if self.task_type == 'classification' else None
        )
        
        logger.info(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
        
        # Get models based on task type
        if self.task_type == 'classification':
            models = self.get_classification_models()
        else:
            models = self.get_regression_models()
        
        # Set up MLflow
        mlflow.set_experiment(experiment_name)
        
        # Train all models
        results = {}
        with mlflow.start_run(run_name=f"AutoML_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
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
                    with mlflow.start_run(run_name=model_name, nested=True):
                        result = self.train_and_evaluate(
                            X_train, X_test, y_train, y_test, model_name, model
                        )
                        results[model_name] = result
                        
                        # Log to MLflow
                        mlflow.log_params({f"{model_name}_param": str(model.get_params())})
                        mlflow.log_metrics(result['metrics'])
                        mlflow.sklearn.log_model(result['model'], model_name)
                        
                except Exception as e:
                    logger.error(f"Failed to train {model_name}: {e}")
                    continue
            
            # Select best model
            if results:
                self.best_model_name = max(results, key=lambda x: results[x]['primary_score'])
                self.best_model = results[self.best_model_name]['model']
                self.best_score = results[self.best_model_name]['primary_score']
                
                logger.info(f"Best model: {self.best_model_name} with score: {self.best_score:.4f}")
                
                # Log best model
                mlflow.log_metric("best_score", self.best_score)
                mlflow.log_param("best_model", self.best_model_name)
                
                # Register best model
                model_uri = f"runs:/{mlflow.active_run().info.run_id}/{self.best_model_name}"
                mlflow.register_model(model_uri, f"best_{self.task_type}_model")
        
        self.results = results
        self.models = {name: res['model'] for name, res in results.items()}
        
        return {
            'best_model': self.best_model_name,
            'best_score': self.best_score,
            'all_results': {name: res['metrics'] for name, res in results.items()},
            'task_type': self.task_type
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
        
        return self.best_model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities (classification only)"""
        if self.best_model is None:
            raise ValueError("No model has been trained yet")
        
        if not hasattr(self.best_model, 'predict_proba'):
            raise ValueError("Model does not support probability predictions")
        
        return self.best_model.predict_proba(X)
    
    def _fit_timeseries(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        dataset_id: Optional[str] = None,
        experiment_name: str = "AutoML_TimeSeries"
    ) -> Dict[str, Any]:
        """
        Train time-series forecasting models
        
        Args:
            X: Feature dataset (must include date column)
            y: Target variable (time-series values)
            dataset_id: Optional dataset identifier
            experiment_name: MLflow experiment name
            
        Returns:
            Dictionary with best model info and all results
        """
        if self.date_column is None:
            raise ValueError("No date column detected for time-series task")
        
        logger.info(f"Training time-series models with {len(X)} samples")
        
        # Prepare data for time-series
        df = X.copy()
        df['target'] = y
        
        # Split data temporally (last test_size% for testing)
        split_idx = int(len(df) * (1 - self.test_size))
        df_train = df.iloc[:split_idx]
        df_test = df.iloc[split_idx:]
        
        # Get time-series models
        models = self.get_timeseries_models()
        
        # Set up MLflow
        mlflow.set_experiment(experiment_name)
        
        results = {}
        with mlflow.start_run(run_name=f"AutoML_TS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
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
                    with mlflow.start_run(run_name=model_name, nested=True):
                        logger.info(f"Training {model_name}...")
                        
                        # Train model
                        if model_name == 'Prophet':
                            model.fit(df_train, self.date_column, 'target')
                            # Predict on test set
                            forecast = model.predict(periods=len(df_test))
                            y_pred = forecast['yhat'].tail(len(df_test)).values
                        else:  # LSTM
                            model.fit(df_train, self.date_column, 'target')
                            # Get last sequence from training data
                            last_seq = df_train['target'].tail(model.seq_length).values
                            y_pred = model.predict(last_seq, periods=len(df_test))
                        
                        # Calculate metrics
                        y_true = df_test['target'].values
                        metrics = calculate_forecast_metrics(y_true, y_pred)
                        
                        # Store results
                        results[model_name] = {
                            'model': model,
                            'metrics': metrics,
                            'primary_score': -metrics['mape']  # Negative MAPE (lower is better, so negate for max)
                        }
                        
                        # Log to MLflow
                        mlflow.log_metrics(metrics)
                        
                        # Save model
                        if model_name == 'Prophet':
                            mlflow.sklearn.log_model(model.model, model_name)
                        else:
                            model.save_model(f"{model_name}_model.pt")
                            mlflow.log_artifact(f"{model_name}_model.pt")
                        
                        logger.info(f"{model_name} MAPE: {metrics['mape']:.2f}%, RMSE: {metrics['rmse']:.4f}")
                        
                except Exception as e:
                    logger.error(f"Failed to train {model_name}: {e}")
                    continue
            
            # Select best model (lowest MAPE)
            if results:
                self.best_model_name = max(results, key=lambda x: results[x]['primary_score'])
                self.best_model = results[self.best_model_name]['model']
                self.best_score = results[self.best_model_name]['metrics']['mape']
                
                logger.info(f"Best model: {self.best_model_name} with MAPE: {self.best_score:.2f}%")
                
                # Log best model
                mlflow.log_metric("best_mape", self.best_score)
                mlflow.log_param("best_model", self.best_model_name)
        
        self.results = results
        self.models = {name: res['model'] for name, res in results.items()}
        
        return {
            'best_model': self.best_model_name,
            'best_score': self.best_score,
            'all_results': {name: res['metrics'] for name, res in results.items()},
            'task_type': 'time_series'
        }