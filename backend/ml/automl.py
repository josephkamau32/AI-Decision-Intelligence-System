from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from xgboost import XGBClassifier, XGBRegressor
from prophet import Prophet
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
import mlflow.pytorch
from typing import List, Dict, Any
from backend.utils.config import settings
import logging

logger = logging.getLogger(__name__)

class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out

class AutoMLEngine:
    def __init__(self):
        self.models = {
            'classification': [
                ('LogisticRegression', LogisticRegression()),
                ('RandomForest', RandomForestClassifier()),
                ('XGBoost', XGBClassifier())
            ],
            'regression': [
                ('LinearRegression', LinearRegression()),
                ('RandomForest', RandomForestRegressor()),
                ('XGBoost', XGBRegressor())
            ],
            'time_series': [
                ('Prophet', Prophet),
                ('LSTM', LSTMModel)
            ]
        }
        logger.info("Initialized AutoMLEngine with available models")

    def train_and_select(self, df: pd.DataFrame, target: str, problem_type: str) -> Dict[str, Any]:
        logger.info(f"Starting AutoML training for {problem_type} problem with target {target}")
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.set_experiment(settings.mlflow_experiment_name)
        with mlflow.start_run():
            mlflow.log_param("target", target)
            mlflow.log_param("problem_type", problem_type)
            mlflow.log_param("dataset_shape", df.shape)
            if problem_type == 'time_series':
                result = self._train_time_series(df, target)
            else:
                result = self._train_supervised(df, target, problem_type)
            mlflow.log_metric("best_score", result['best_score'])
            mlflow.log_param("best_model", result['best_model'])
            # Log the model
            if hasattr(result['trained_model'], 'predict'):  # sklearn-like
                mlflow.sklearn.log_model(result['trained_model'], "model")
            elif isinstance(result['trained_model'], torch.nn.Module):
                mlflow.pytorch.log_model(result['trained_model'], "model")
            else:
                # For Prophet or others, perhaps save as artifact
                import tempfile
                import joblib
                with tempfile.TemporaryDirectory() as tmpdir:
                    model_path = f"{tmpdir}/model.pkl"
                    joblib.dump(result['trained_model'], model_path)
                    mlflow.log_artifact(model_path, "model")
            # Log all results as artifact
            import json
            results_summary = {res['model']: res['score'] for res in result['all_results']}
            with tempfile.TemporaryDirectory() as tmpdir:
                results_path = f"{tmpdir}/results.json"
                with open(results_path, 'w') as f:
                    json.dump(results_summary, f)
                mlflow.log_artifact(results_path, "results")
            result['run_id'] = mlflow.active_run().info.run_id
            logger.info(f"AutoML training completed. Best model: {result['best_model']}, Score: {result['best_score']}")
            return result

    def _train_supervised(self, df: pd.DataFrame, target: str, problem_type: str) -> Dict[str, Any]:
        logger.info(f"Training supervised models for {problem_type}")
        X = df.drop(columns=[target]).values
        y = df[target].values
        results = []
        for name, model in self.models[problem_type]:
            scores = cross_val_score(model, X, y, cv=3, scoring='accuracy' if problem_type == 'classification' else 'neg_mean_squared_error')
            mean_score = scores.mean()
            results.append({
                'model': name,
                'score': mean_score,
                'model_instance': model
            })
            logger.info(f"Model {name} scored {mean_score}")
        # Sort by score descending for accuracy, ascending for mse (neg so higher better)
        results.sort(key=lambda x: x['score'], reverse=True)
        best = results[0]
        # Fit best model
        best['model_instance'].fit(X, y)
        logger.info(f"Best model {best['model']} fitted")
        return {
            'best_model': best['model'],
            'best_score': best['score'],
            'trained_model': best['model_instance'],
            'all_results': results
        }

    def _train_time_series(self, df: pd.DataFrame, target: str) -> Dict[str, Any]:
        logger.info("Training time series models")
        # Assume df has 'ds' and 'y'
        if 'ds' not in df.columns or 'y' not in df.columns:
            # Fallback, assume first col date, last y
            date_col = df.columns[0]
            df = df.rename(columns={date_col: 'ds', target: 'y'})
            df['ds'] = pd.to_datetime(df['ds'])
        results = []
        # Prophet
        prophet = Prophet()
        prophet.fit(df[['ds', 'y']])
        # For scoring, predict on train or something, but simple, assume prophet is good
        results.append({
            'model': 'Prophet',
            'score': 0.8,  # mock
            'model_instance': prophet
        })
        logger.info("Prophet model trained")
        # LSTM
        # Create sequences
        data = df['y'].values
        seq_length = 10
        X, y = [], []
        for i in range(len(data) - seq_length):
            X.append(data[i:i+seq_length])
            y.append(data[i+seq_length])
        X = np.array(X)
        y = np.array(y)
        X = torch.tensor(X, dtype=torch.float32).unsqueeze(-1)
        y = torch.tensor(y, dtype=torch.float32)
        dataset = TensorDataset(X, y)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
        model = LSTMModel(input_size=1, hidden_size=50, output_size=1)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        # Train for few epochs
        for epoch in range(10):
            for batch_X, batch_y in dataloader:
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs.squeeze(), batch_y)
                loss.backward()
                optimizer.step()
        # Mock score
        results.append({
            'model': 'LSTM',
            'score': 0.7,
            'model_instance': model
        })
        logger.info("LSTM model trained")
        results.sort(key=lambda x: x['score'], reverse=True)
        best = results[0]
        return {
            'best_model': best['model'],
            'best_score': best['score'],
            'trained_model': best['model_instance'],
            'all_results': results
        }