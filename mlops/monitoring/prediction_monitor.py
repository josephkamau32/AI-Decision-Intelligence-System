import numpy as np
import pandas as pd
from typing import Dict, Any, List
from collections import defaultdict
import json
import os

class PredictionDistributionMonitor:
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.prediction_history = []
        self.distribution_stats = defaultdict(list)
        self.alerts = []

    def track_prediction(self, prediction: Any, input_data: Dict[str, Any]):
        """Track a prediction and update distribution stats."""
        timestamp = pd.Timestamp.now()

        # Store prediction
        self.prediction_history.append({
            "timestamp": timestamp,
            "prediction": prediction,
            "input_data": input_data
        })

        # Update distribution stats
        if isinstance(prediction, (int, float)):
            self.distribution_stats['predictions'].append(float(prediction))
        elif isinstance(prediction, (list, np.ndarray)):
            self.distribution_stats['predictions'].extend([float(p) for p in prediction])
        else:
            # For categorical predictions, track frequency
            pred_str = str(prediction)
            if 'categorical' not in self.distribution_stats:
                self.distribution_stats['categorical'] = defaultdict(int)
            self.distribution_stats['categorical'][pred_str] += 1

        # Check for anomalies
        self._check_distribution_anomalies()

    def get_distribution_stats(self) -> Dict[str, Any]:
        """Get current distribution statistics."""
        stats = {}

        if 'predictions' in self.distribution_stats and self.distribution_stats['predictions']:
            preds = np.array(self.distribution_stats['predictions'])
            stats['numerical'] = {
                'mean': float(np.mean(preds)),
                'std': float(np.std(preds)),
                'min': float(np.min(preds)),
                'max': float(np.max(preds)),
                'count': len(preds)
            }

        if 'categorical' in self.distribution_stats:
            total = sum(self.distribution_stats['categorical'].values())
            stats['categorical'] = {
                'frequencies': dict(self.distribution_stats['categorical']),
                'total_predictions': total
            }

        return stats

    def _check_distribution_anomalies(self):
        """Check for anomalies in prediction distribution."""
        if len(self.prediction_history) < 10:  # Need minimum data
            return

        recent_preds = [p['prediction'] for p in self.prediction_history[-10:]]

        if all(isinstance(p, (int, float)) for p in recent_preds):
            recent_mean = np.mean(recent_preds)
            overall_mean = np.mean(self.distribution_stats['predictions'][:-10] or [recent_mean])

            if abs(recent_mean - overall_mean) > 2 * np.std(self.distribution_stats['predictions'] or [0]):
                self.alerts.append({
                    "timestamp": pd.Timestamp.now(),
                    "type": "distribution_shift",
                    "message": f"Prediction distribution shifted. Recent mean: {recent_mean:.3f}, Overall mean: {overall_mean:.3f}"
                })

    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        return self.alerts[-10:]  # Last 10 alerts

    def save_history(self, path: str):
        """Save prediction history to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump({
                'model_id': self.model_id,
                'prediction_history': self.prediction_history,
                'distribution_stats': dict(self.distribution_stats),
                'alerts': self.alerts
            }, f, default=str)

    def load_history(self, path: str):
        """Load prediction history from disk."""
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                self.prediction_history = data.get('prediction_history', [])
                self.distribution_stats = defaultdict(list, data.get('distribution_stats', {}))
                self.alerts = data.get('alerts', [])