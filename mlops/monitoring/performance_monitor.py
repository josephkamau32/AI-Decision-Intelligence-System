import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
import json
import os

class PerformanceMonitor:
    def __init__(self, model_id: str, problem_type: str = 'classification'):
        self.model_id = model_id
        self.problem_type = problem_type
        self.performance_history = []
        self.baseline_metrics = {}
        self.alerts = []
        self.decay_threshold = 0.1  # 10% decay threshold

    def update_baseline(self, y_true: np.ndarray, y_pred: np.ndarray):
        """Set baseline performance metrics."""
        self.baseline_metrics = self._calculate_metrics(y_true, y_pred)

    def monitor_performance(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
        """Monitor current performance and check for decay."""
        current_metrics = self._calculate_metrics(y_true, y_pred)

        timestamp = pd.Timestamp.now()
        self.performance_history.append({
            "timestamp": timestamp,
            "metrics": current_metrics,
            "sample_size": len(y_true)
        })

        decay_alerts = self._check_performance_decay(current_metrics)

        return {
            "current_metrics": current_metrics,
            "baseline_metrics": self.baseline_metrics,
            "decay_alerts": decay_alerts
        }

    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate performance metrics based on problem type."""
        metrics = {}

        if self.problem_type in ['classification', 'binary_classification']:
            try:
                metrics['accuracy'] = accuracy_score(y_true, y_pred)
                metrics['precision'] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
                metrics['recall'] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
                metrics['f1'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)
            except Exception as e:
                metrics['error'] = str(e)

        elif self.problem_type == 'regression':
            try:
                metrics['mse'] = mean_squared_error(y_true, y_pred)
                metrics['rmse'] = np.sqrt(metrics['mse'])
                metrics['r2'] = r2_score(y_true, y_pred)
            except Exception as e:
                metrics['error'] = str(e)

        return metrics

    def _check_performance_decay(self, current_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Check if performance has decayed below threshold."""
        alerts = []

        if not self.baseline_metrics:
            return alerts

        for metric_name, current_value in current_metrics.items():
            if metric_name in self.baseline_metrics and metric_name != 'error':
                baseline_value = self.baseline_metrics[metric_name]

                # For metrics where higher is better (accuracy, f1, etc.)
                if metric_name in ['accuracy', 'precision', 'recall', 'f1', 'r2']:
                    decay = (baseline_value - current_value) / baseline_value
                    if decay > self.decay_threshold:
                        alerts.append({
                            "timestamp": pd.Timestamp.now(),
                            "metric": metric_name,
                            "baseline": baseline_value,
                            "current": current_value,
                            "decay_percentage": decay * 100,
                            "message": f"Performance decay detected in {metric_name}: {decay*100:.1f}% drop"
                        })
                # For metrics where lower is better (mse, rmse)
                elif metric_name in ['mse', 'rmse']:
                    increase = (current_value - baseline_value) / baseline_value
                    if increase > self.decay_threshold:
                        alerts.append({
                            "timestamp": pd.Timestamp.now(),
                            "metric": metric_name,
                            "baseline": baseline_value,
                            "current": current_value,
                            "increase_percentage": increase * 100,
                            "message": f"Performance decay detected in {metric_name}: {increase*100:.1f}% increase"
                        })

        self.alerts.extend(alerts)
        return alerts

    def get_performance_history(self) -> List[Dict[str, Any]]:
        """Get performance monitoring history."""
        return self.performance_history

    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get performance decay alerts."""
        return self.alerts[-20:]  # Last 20 alerts

    def save_state(self, path: str):
        """Save monitor state to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump({
                'model_id': self.model_id,
                'problem_type': self.problem_type,
                'performance_history': self.performance_history,
                'baseline_metrics': self.baseline_metrics,
                'alerts': self.alerts,
                'decay_threshold': self.decay_threshold
            }, f, default=str)

    def load_state(self, path: str):
        """Load monitor state from disk."""
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                self.performance_history = data.get('performance_history', [])
                self.baseline_metrics = data.get('baseline_metrics', {})
                self.alerts = data.get('alerts', [])
                self.decay_threshold = data.get('decay_threshold', 0.1)