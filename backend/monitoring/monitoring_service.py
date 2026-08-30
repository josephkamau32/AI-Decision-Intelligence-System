import mlops.monitoring.drift_detector as drift_detector_module
import mlops.monitoring.prediction_monitor as prediction_monitor_module
import mlops.monitoring.performance_monitor as performance_monitor_module
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import os
import json
import logging

logger = logging.getLogger(__name__)


class MonitoringService:
    def __init__(self):
        self.drift_detectors = {}  # model_id -> DataDriftDetector
        self.prediction_monitors = {}  # model_id -> PredictionDistributionMonitor
        self.performance_monitors = {}  # model_id -> PerformanceMonitor
        self.monitoring_dir = "monitoring_data"

    def initialize_model_monitoring(
        self,
        model_id: str,
        reference_data: pd.DataFrame,
        problem_type: str = "classification",
    ):
        """Initialize monitoring for a new model."""
        # Data drift detector
        self.drift_detectors[model_id] = drift_detector_module.DataDriftDetector(
            reference_data, model_id
        )

        # Prediction distribution monitor
        self.prediction_monitors[model_id] = (
            prediction_monitor_module.PredictionDistributionMonitor(model_id)
        )

        # Performance monitor
        self.performance_monitors[model_id] = (
            performance_monitor_module.PerformanceMonitor(model_id, problem_type)
        )

        # Load existing state if available
        self._load_monitoring_state(model_id)

    def monitor_inference(
        self, model_id: str, input_data: Dict[str, Any], prediction: Any
    ) -> Dict[str, Any]:
        """Monitor an inference call."""
        results = {}

        # Track prediction distribution
        if model_id in self.prediction_monitors:
            self.prediction_monitors[model_id].track_prediction(prediction, input_data)
            results["prediction_stats"] = self.prediction_monitors[
                model_id
            ].get_distribution_stats()

        # Check for data drift
        if model_id in self.drift_detectors:
            input_df = pd.DataFrame([input_data])
            drift_result = self.drift_detectors[model_id].detect_drift(input_df)
            results["drift_detection"] = drift_result

        return results

    def update_performance_baseline(
        self, model_id: str, y_true: np.ndarray, y_pred: np.ndarray
    ):
        """Update performance baseline for a model."""
        if model_id in self.performance_monitors:
            self.performance_monitors[model_id].update_baseline(y_true, y_pred)

    def monitor_performance(
        self, model_id: str, y_true: np.ndarray, y_pred: np.ndarray
    ) -> Dict[str, Any]:
        """Monitor model performance."""
        if model_id not in self.performance_monitors:
            return {"error": "Performance monitor not initialized"}

        return self.performance_monitors[model_id].monitor_performance(y_true, y_pred)

    def get_monitoring_metrics(self, model_id: str) -> Dict[str, Any]:
        """Get all monitoring metrics for a model."""
        metrics = {}

        if model_id in self.drift_detectors:
            metrics["drift_history"] = self.drift_detectors[
                model_id
            ].get_drift_history()

        if model_id in self.prediction_monitors:
            metrics["prediction_distribution"] = self.prediction_monitors[
                model_id
            ].get_distribution_stats()
            metrics["prediction_alerts"] = self.prediction_monitors[
                model_id
            ].get_alerts()

        if model_id in self.performance_monitors:
            metrics["performance_history"] = self.performance_monitors[
                model_id
            ].get_performance_history()
            metrics["performance_alerts"] = self.performance_monitors[
                model_id
            ].get_alerts()

        return metrics

    def get_all_alerts(self, model_id: str) -> Dict[str, Any]:
        """Get all alerts for a model."""
        alerts = {}

        if model_id in self.prediction_monitors:
            alerts["prediction_distribution"] = self.prediction_monitors[
                model_id
            ].get_alerts()

        if model_id in self.performance_monitors:
            alerts["performance_decay"] = self.performance_monitors[
                model_id
            ].get_alerts()

        return alerts

    def _load_monitoring_state(self, model_id: str):
        """Load monitoring state from disk."""
        try:
            if model_id in self.prediction_monitors:
                path = os.path.join(self.monitoring_dir, f"{model_id}_prediction.json")
                self.prediction_monitors[model_id].load_history(path)

            if model_id in self.performance_monitors:
                path = os.path.join(self.monitoring_dir, f"{model_id}_performance.json")
                self.performance_monitors[model_id].load_state(path)

        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.error("Failed to load monitoring state for %s: %s", model_id, e)

    def save_monitoring_state(self, model_id: str):
        """Save monitoring state to disk."""
        try:
            os.makedirs(self.monitoring_dir, exist_ok=True)

            if model_id in self.prediction_monitors:
                path = os.path.join(self.monitoring_dir, f"{model_id}_prediction.json")
                self.prediction_monitors[model_id].save_history(path)

            if model_id in self.performance_monitors:
                path = os.path.join(self.monitoring_dir, f"{model_id}_performance.json")
                self.performance_monitors[model_id].save_state(path)

            if model_id in self.drift_detectors:
                path = os.path.join(self.monitoring_dir, f"{model_id}_drift")
                self.drift_detectors[model_id].save_detector(path)

        except (OSError, TypeError, ValueError) as e:
            logger.error("Failed to save monitoring state for %s: %s", model_id, e)


monitoring_service = MonitoringService()
