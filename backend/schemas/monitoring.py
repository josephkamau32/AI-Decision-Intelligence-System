from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class DriftDetectionResult(BaseModel):
    drift_detected: bool
    p_value: Optional[float] = None
    threshold: Optional[float] = None
    feature_drift: Optional[List[float]] = None
    error: Optional[str] = None

class PredictionStats(BaseModel):
    numerical: Optional[Dict[str, float]] = None
    categorical: Optional[Dict[str, Any]] = None

class PerformanceMetrics(BaseModel):
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None
    mse: Optional[float] = None
    rmse: Optional[float] = None
    r2: Optional[float] = None
    error: Optional[str] = None

class Alert(BaseModel):
    timestamp: datetime
    type: str
    message: str
    metric: Optional[str] = None
    baseline: Optional[float] = None
    current: Optional[float] = None
    decay_percentage: Optional[float] = None
    increase_percentage: Optional[float] = None

class MonitoringMetricsResponse(BaseModel):
    drift_history: Optional[List[Dict[str, Any]]] = None
    prediction_distribution: Optional[PredictionStats] = None
    prediction_alerts: Optional[List[Alert]] = None
    performance_history: Optional[List[Dict[str, Any]]] = None
    performance_alerts: Optional[List[Alert]] = None

class AlertsResponse(BaseModel):
    prediction_distribution: Optional[List[Alert]] = None
    performance_decay: Optional[List[Alert]] = None

class InferenceMonitoringResult(BaseModel):
    prediction_stats: Optional[PredictionStats] = None
    drift_detection: Optional[DriftDetectionResult] = None