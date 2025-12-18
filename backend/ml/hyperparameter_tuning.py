"""
Advanced Hyperparameter Tuning with Optuna
Implements automated hyperparameter optimization for all models
"""
import optuna
from optuna.integration.mlflow import MLflowCallback
import mlflow
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge, Lasso
from xgboost import XGBClassifier, XGBRegressor
from lightgbm import LGBMClassifier, LGBMRegressor
from typing import Dict, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class OptunaHyperparameterTuner:
    """
    Optuna-based hyperparameter optimization
    Supports all models in the AutoML pipeline
    """
    
    def __init__(self, 
                 n_trials: int = 50,
                 timeout: Optional[int] = None,
                 n_jobs: int = -1,
                 sampler: str = 'TPE'):
        """
        Initialize hyperparameter tuner
        
        Args:
            n_trials: Number of optimization trials
            timeout: Time limit in seconds (None = no limit)
            n_jobs: Number of parallel jobs
            sampler: Sampling algorithm ('TPE', 'Random', 'Grid')
        """
        self.n_trials = n_trials
        self.timeout = timeout
        self.n_jobs = n_jobs
        
        # Select sampler
        if sampler == 'TPE':
            self.sampler = optuna.samplers.TPESampler()
        elif sampler == 'Random':
            self.sampler = optuna.samplers.RandomSampler()
        else:
            self.sampler = optuna.samplers.TPESampler()
        
        self.best_params = None
        self.best_value = None
        self.study = None
        
    def get_search_space(self, model_name: str, trial: optuna.Trial) -> Dict[str, Any]:
        """
        Define search space for each model
        
        Args:
            model_name: Name of the model
            trial: Optuna trial object
            
        Returns:
            Dictionary of hyperparameters
        """
        if model_name == 'random_forest_clf' or model_name == 'random_forest_reg':
            return {
                'n_estimators': trial.suggest_int('n_estimators', 50, 500),
                'max_depth': trial.suggest_int('max_depth', 3, 20),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None])
            }
        
        elif model_name == 'xgboost_clf' or model_name == 'xgboost_reg':
            return {
                'n_estimators': trial.suggest_int('n_estimators', 50, 500),
                'max_depth': trial.suggest_int('max_depth', 3, 15),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'gamma': trial.suggest_float('gamma', 0, 5),
                'reg_alpha': trial.suggest_float('reg_alpha', 0, 2),
                'reg_lambda': trial.suggest_float('reg_lambda', 0, 2)
            }
        
        elif model_name == 'lightgbm_clf' or model_name == 'lightgbm_reg':
            return {
                'n_estimators': trial.suggest_int('n_estimators', 50, 500),
                'max_depth': trial.suggest_int('max_depth', 3, 15),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'num_leaves': trial.suggest_int('num_leaves', 20, 150),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 0, 2),
                'reg_lambda': trial.suggest_float('reg_lambda', 0, 2)
            }
        
        elif model_name == 'gradient_boosting_clf' or model_name == 'gradient_boosting_reg':
            return {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10)
            }
        
        elif model_name == 'logistic_regression':
            return {
                'C': trial.suggest_float('C', 0.001, 10, log=True),
                'penalty': trial.suggest_categorical('penalty', ['l1', 'l2']),
                'solver': trial.suggest_categorical('solver', ['liblinear', 'saga'])
            }
        
        elif model_name == 'ridge':
            return {
                'alpha': trial.suggest_float('alpha', 0.001, 10, log=True)
            }
        
        elif model_name == 'lasso':
            return {
                'alpha': trial.suggest_float('alpha', 0.001, 10, log=True)
            }
        
        else:
            return {}
    
    def create_model(self, model_name: str, params: Dict[str, Any], task_type: str):
        """
        Create model with given parameters
        
        Args:
            model_name: Name of the model
            params: Hyperparameters
            task_type: 'classification' or 'regression'
            
        Returns:
            Model instance
        """
        if model_name == 'random_forest_clf':
            return RandomForestClassifier(**params, random_state=42)
        elif model_name == 'random_forest_reg':
            return RandomForestRegressor(**params, random_state=42)
        elif model_name == 'xgboost_clf':
            return XGBClassifier(**params, random_state=42, use_label_encoder=False, eval_metric='logloss')
        elif model_name == 'xgboost_reg':
            return XGBRegressor(**params, random_state=42)
        elif model_name == 'lightgbm_clf':
            return LGBMClassifier(**params, random_state=42, verbose=-1)
        elif model_name == 'lightgbm_reg':
            return LGBMRegressor(**params, random_state=42, verbose=-1)
        elif model_name == 'gradient_boosting_clf':
            return GradientBoostingClassifier(**params, random_state=42)
        elif model_name == 'gradient_boosting_reg':
            return GradientBoostingRegressor(**params, random_state=42)
        elif model_name == 'logistic_regression':
            return LogisticRegression(**params, random_state=42, max_iter=1000)
        elif model_name == 'ridge':
            return Ridge(**params, random_state=42)
        elif model_name == 'lasso':
            return Lasso(**params, random_state=42)
        else:
            raise ValueError(f"Unknown model: {model_name}")
    
    def objective(self, trial: optuna.Trial, 
                  X: pd.DataFrame, 
                  y: pd.Series, 
                  model_name: str,
                  task_type: str,
                  cv: int = 5,
                  scoring: str = 'accuracy') -> float:
        """
        Objective function for optimization
        
        Args:
            trial: Optuna trial
            X: Features
            y: Target
            model_name: Model to optimize
            task_type: 'classification' or 'regression'
            cv: Number of cross-validation folds
            scoring: Scoring metric
            
        Returns:
            Mean cross-validation score
        """
        # Get hyperparameters for this trial
        params = self.get_search_space(model_name, trial)
        
        # Create model with trial parameters
        model = self.create_model(model_name, params, task_type)
        
        # Cross-validation
        scores = cross_val_score(model, X, y, cv=cv, scoring=scoring, n_jobs=1)
        
        return scores.mean()
    
    def optimize(self,
                 X: pd.DataFrame,
                 y: pd.Series,
                 model_name: str,
                 task_type: str,
                 cv: int = 5,
                 scoring: str = 'accuracy',
                 study_name: Optional[str] = None,
                 mlflow_tracking: bool = True) -> Dict[str, Any]:
        """
        Run hyperparameter optimization
        
        Args:
            X: Features
            y: Target
            model_name: Model to optimize
            task_type: 'classification' or 'regression'
            cv: Number of CV folds
            scoring: Scoring metric
            study_name: Name for the optimization study
            mlflow_tracking: Whether to log to MLflow
            
        Returns:
            Dictionary with best parameters and score
        """
        logger.info(f"Starting hyperparameter optimization for {model_name}")
        logger.info(f"Trials: {self.n_trials}, CV: {cv}, Scoring: {scoring}")
        
        # Create study
        study_name = study_name or f"{model_name}_optimization"
        
        # MLflow callback
        callbacks = []
        if mlflow_tracking:
            mlflc = MLflowCallback(
                tracking_uri=mlflow.get_tracking_uri(),
                metric_name=scoring
            )
            callbacks.append(mlflc)
        
        self.study = optuna.create_study(
            study_name=study_name,
            direction='maximize',
            sampler=self.sampler,
            pruner=optuna.pruners.MedianPruner()
        )
        
        # Optimize
        self.study.optimize(
            lambda trial: self.objective(trial, X, y, model_name, task_type, cv, scoring),
            n_trials=self.n_trials,
            timeout=self.timeout,
            n_jobs=self.n_jobs,
            callbacks=callbacks,
            show_progress_bar=True
        )
        
        self.best_params = self.study.best_params
        self.best_value = self.study.best_value
        
        logger.info(f"Optimization complete!")
        logger.info(f"Best {scoring}: {self.best_value:.4f}")
        logger.info(f"Best parameters: {self.best_params}")
        
        return {
            'best_params': self.best_params,
            'best_score': self.best_value,
            'n_trials': len(self.study.trials),
            'best_trial': self.study.best_trial.number
        }
    
    def get_optimization_history(self) -> pd.DataFrame:
        """
        Get optimization history as DataFrame
        
        Returns:
            DataFrame with trial results
        """
        if self.study is None:
            return pd.DataFrame()
        
        return self.study.trials_dataframe()
    
    def plot_optimization_history(self, save_path: Optional[str] = None):
        """
        Plot optimization history
        
        Args:
            save_path: Path to save plot (optional)
        """
        if self.study is None:
            logger.warning("No study to plot")
            return
        
        try:
            import matplotlib.pyplot as plt
            
            fig = optuna.visualization.matplotlib.plot_optimization_history(self.study)
            
            if save_path:
                plt.savefig(save_path)
                logger.info(f"Optimization history saved to {save_path}")
            else:
                plt.show()
                
        except ImportError:
            logger.warning("Matplotlib not available for plotting")
    
    def plot_param_importances(self, save_path: Optional[str] = None):
        """
        Plot parameter importances
        
        Args:
            save_path: Path to save plot (optional)
        """
        if self.study is None:
            logger.warning("No study to plot")
            return
        
        try:
            import matplotlib.pyplot as plt
            
            fig = optuna.visualization.matplotlib.plot_param_importances(self.study)
            
            if save_path:
                plt.savefig(save_path)
                logger.info(f"Parameter importances saved to {save_path}")
            else:
                plt.show()
                
        except ImportError:
            logger.warning("Matplotlib not available for plotting")


def tune_model(X: pd.DataFrame,
               y: pd.Series,
               model_name: str,
               task_type: str,
               n_trials: int = 50,
               cv: int = 5,
               scoring: str = None) -> Dict[str, Any]:
    """
    Convenience function to tune a single model
    
    Args:
        X: Features
        y: Target
        model_name: Model to tune
        task_type: 'classification' or 'regression'
        n_trials: Number of optimization trials
        cv: Number of CV folds
        scoring: Scoring metric (auto-detected if None)
        
    Returns:
        Dictionary with best parameters and results
    """
    # Auto-detect scoring if not provided
    if scoring is None:
        scoring = 'accuracy' if task_type == 'classification' else 'r2'
    
    tuner = OptunaHyperparameterTuner(n_trials=n_trials)
    results = tuner.optimize(X, y, model_name, task_type, cv, scoring)
    
    return results
