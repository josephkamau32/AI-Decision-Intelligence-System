"""
Time-Series Forecasting Models
Implements Prophet and LSTM models for time-series analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import logging
from datetime import datetime, timedelta
import joblib
import mlflow
import mlflow.sklearn
import mlflow.pytorch

# Prophet
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics

# PyTorch for LSTM
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)


class TimeSeriesDataset(Dataset):
    """PyTorch Dataset for time-series data"""
    
    def __init__(self, data: np.ndarray, seq_length: int = 10):
        self.data = torch.FloatTensor(data)
        self.seq_length = seq_length
        
    def __len__(self):
        return len(self.data) - self.seq_length
    
    def __getitem__(self, idx):
        x = self.data[idx:idx + self.seq_length]
        y = self.data[idx + self.seq_length]
        return x, y


class LSTMModel(nn.Module):
    """LSTM Neural Network for Time-Series Forecasting"""
    
    def __init__(self, input_size: int = 1, hidden_size: int = 64, 
                 num_layers: int = 2, dropout: float = 0.2):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        lstm_out, _ = self.lstm(x)
        # Take the last output
        last_output = lstm_out[:, -1, :]
        predictions = self.fc(last_output)
        return predictions


class ProphetForecaster:
    """
    Prophet-based time-series forecasting model
    Handles univariate time-series with automatic seasonality detection
    """
    
    def __init__(self, 
                 seasonality_mode: str = 'additive',
                 changepoint_prior_scale: float = 0.05,
                 yearly_seasonality: bool = 'auto',
                 weekly_seasonality: bool = 'auto',
                 daily_seasonality: bool = 'auto'):
        """
        Initialize Prophet model
        
        Args:
            seasonality_mode: 'additive' or 'multiplicative'
            changepoint_prior_scale: Flexibility of trend (higher = more flexible)
            yearly_seasonality: Include yearly seasonality
            weekly_seasonality: Include weekly seasonality
            daily_seasonality: Include daily seasonality
        """
        self.model = Prophet(
            seasonality_mode=seasonality_mode,
            changepoint_prior_scale=changepoint_prior_scale,
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality
        )
        self.is_fitted = False
        self.metrics = {}
        
    def fit(self, df: pd.DataFrame, date_col: str, target_col: str):
        """
        Train Prophet model
        
        Args:
            df: DataFrame with time-series data
            date_col: Name of date column
            target_col: Name of target column
        """
        # Prophet requires 'ds' and 'y' columns
        train_data = pd.DataFrame({
            'ds': pd.to_datetime(df[date_col]),
            'y': df[target_col]
        })
        
        logger.info(f"Training Prophet model on {len(train_data)} data points")
        self.model.fit(train_data)
        self.is_fitted = True
        
        # Calculate metrics using cross-validation
        logger.info("Running cross-validation...")
        cv_results = cross_validation(
            self.model,
            initial='365 days',
            period='180 days',
            horizon='90 days'
        )
        
        self.metrics = performance_metrics(cv_results)
        logger.info(f"Prophet metrics: {self.metrics[['mape', 'rmse']].mean().to_dict()}")
        
        return self
        
    def predict(self, periods: int = 30, freq: str = 'D') -> pd.DataFrame:
        """
        Generate forecasts
        
        Args:
            periods: Number of periods to forecast
            freq: Frequency ('D' for daily, 'W' for weekly, etc.)
            
        Returns:
            DataFrame with predictions
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before predicting")
            
        future = self.model.make_future_dataframe(periods=periods, freq=freq)
        forecast = self.model.predict(future)
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    
    def get_components(self) -> Dict[str, Any]:
        """Get seasonality components"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")
        
        return {
            'trend': self.model.params.get('trend'),
            'seasonality': self.model.seasonalities
        }


class LSTMForecaster:
    """
    LSTM-based time-series forecasting model
    Handles univariate time-series with neural networks
    """
    
    def __init__(self,
                 seq_length: int = 10,
                 hidden_size: int = 64,
                 num_layers: int = 2,
                 dropout: float = 0.2,
                 learning_rate: float = 0.001,
                 epochs: int = 100,
                 batch_size: int = 32):
        """
        Initialize LSTM model
        
        Args:
            seq_length: Number of time steps to look back
            hidden_size: Number of LSTM hidden units
            num_layers: Number of LSTM layers
            dropout: Dropout rate
            learning_rate: Learning rate for optimizer
            epochs: Number of training epochs
            batch_size: Batch size for training
        """
        self.seq_length = seq_length
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        
        self.model = None
        self.scaler = MinMaxScaler()
        self.is_fitted = False
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    def fit(self, df: pd.DataFrame, date_col: str, target_col: str):
        """
        Train LSTM model
        
        Args:
            df: DataFrame with time-series data
            date_col: Name of date column
            target_col: Name of target column
        """
        # Sort by date
        df = df.sort_values(date_col)
        data = df[target_col].values.reshape(-1, 1)
        
        # Normalize data
        scaled_data = self.scaler.fit_transform(data)
        
        # Create dataset
        dataset = TimeSeriesDataset(scaled_data, self.seq_length)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        # Initialize model
        self.model = LSTMModel(
            input_size=1,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout
        ).to(self.device)
        
        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Training loop
        logger.info(f"Training LSTM model for {self.epochs} epochs...")
        self.model.train()
        
        for epoch in range(self.epochs):
            total_loss = 0
            for batch_x, batch_y in dataloader:
                batch_x = batch_x.unsqueeze(-1).to(self.device)
                batch_y = batch_y.to(self.device)
                
                # Forward pass
                outputs = self.model(batch_x)
                loss = criterion(outputs.squeeze(), batch_y.squeeze())
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            if (epoch + 1) % 10 == 0:
                avg_loss = total_loss / len(dataloader)
                logger.info(f"Epoch [{epoch+1}/{self.epochs}], Loss: {avg_loss:.4f}")
        
        self.is_fitted = True
        logger.info("LSTM training completed")
        
        return self
    
    def predict(self, last_sequence: np.ndarray, periods: int = 30) -> np.ndarray:
        """
        Generate forecasts
        
        Args:
            last_sequence: Last seq_length values from training data
            periods: Number of periods to forecast
            
        Returns:
            Array of predictions
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before predicting")
        
        self.model.eval()
        predictions = []
        
        # Normalize last sequence
        current_seq = self.scaler.transform(last_sequence.reshape(-1, 1))
        current_seq = torch.FloatTensor(current_seq).unsqueeze(0).unsqueeze(-1).to(self.device)
        
        with torch.no_grad():
            for _ in range(periods):
                # Predict next value
                pred = self.model(current_seq)
                predictions.append(pred.cpu().numpy()[0, 0])
                
                # Update sequence for next prediction
                current_seq = torch.cat([current_seq[:, 1:, :], pred.unsqueeze(1).unsqueeze(-1)], dim=1)
        
        # Denormalize predictions
        predictions = np.array(predictions).reshape(-1, 1)
        predictions = self.scaler.inverse_transform(predictions)
        
        return predictions.flatten()
    
    def save_model(self, filepath: str):
        """Save LSTM model to disk"""
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted model")
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'scaler': self.scaler,
            'config': {
                'seq_length': self.seq_length,
                'hidden_size': self.hidden_size,
                'num_layers': self.num_layers,
                'dropout': self.dropout
            }
        }, filepath)
        logger.info(f"LSTM model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load LSTM model from disk"""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.seq_length = checkpoint['config']['seq_length']
        self.hidden_size = checkpoint['config']['hidden_size']
        self.num_layers = checkpoint['config']['num_layers']
        self.dropout = checkpoint['config']['dropout']
        
        self.model = LSTMModel(
            input_size=1,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout
        ).to(self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.scaler = checkpoint['scaler']
        self.is_fitted = True
        
        logger.info(f"LSTM model loaded from {filepath}")


def detect_time_series(df: pd.DataFrame) -> Optional[str]:
    """
    Detect if dataset contains time-series data
    
    Returns:
        Name of date column if found, else None
    """
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
        
        # Try parsing as datetime
        try:
            pd.to_datetime(df[col])
            return col
        except:
            continue
    
    return None


def calculate_forecast_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate forecasting metrics
    
    Returns:
        Dictionary with MAE, RMSE, MAPE
    """
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100
    
    return {
        'mae': float(mae),
        'rmse': float(rmse),
        'mape': float(mape)
    }
