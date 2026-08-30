"""
Prometheus Metrics Instrumentation
Exposes custom metrics for ML operations monitoring
"""

from prometheus_client import Counter, Histogram, Gauge, Summary, Info
from prometheus_client import make_asgi_app
from fastapi import FastAPI
import time
from typing import Callable
from functools import wraps

# HTTP Metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

# ML Training Metrics
ml_training_duration_seconds = Histogram(
    "ml_training_duration_seconds",
    "Model training duration in seconds",
    ["model_type", "task_type"],
)

ml_training_total = Counter(
    "ml_training_total",
    "Total number of model training jobs",
    ["model_type", "task_type", "status"],
)

ml_model_accuracy = Gauge(
    "ml_model_accuracy", "Model accuracy score", ["model_id", "model_type"]
)

# Inference Metrics
ml_inference_duration_seconds = Histogram(
    "ml_inference_duration_seconds", "Model inference duration in seconds", ["model_id"]
)

ml_inference_total = Counter(
    "ml_inference_total", "Total number of predictions", ["model_id", "type"]
)

# Data Processing Metrics
data_processing_duration_seconds = Histogram(
    "data_processing_duration_seconds",
    "Data processing duration in seconds",
    ["operation"],
)

dataset_size_bytes = Gauge(
    "dataset_size_bytes", "Size of uploaded dataset in bytes", ["dataset_id"]
)

dataset_rows = Gauge("dataset_rows", "Number of rows in dataset", ["dataset_id"])

# Drift Detection Metrics
drift_detected_total = Counter(
    "drift_detected_total",
    "Total number of drift detections",
    ["model_id", "drift_type"],
)

drift_score = Gauge("drift_score", "Data drift score", ["model_id"])

# System Metrics
active_models = Gauge("active_models", "Number of active models")

active_users = Gauge("active_users", "Number of active users")

celery_tasks_active = Gauge(
    "celery_tasks_active", "Number of active Celery tasks", ["task_type"]
)

# Application Info
app_info = Info("app_info", "Application information")


def track_request_metrics(
    method: str, endpoint: str, status_code: int, duration: float
):
    """
    Track HTTP request metrics

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Endpoint path
        status_code: Response status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(
        method=method, endpoint=endpoint, status=status_code
    ).inc()

    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
        duration
    )


def track_training_metrics(
    model_type: str,
    task_type: str,
    duration: float,
    status: str,
    accuracy: float = None,
    model_id: str = None,
):
    """
    Track model training metrics

    Args:
        model_type: Type of model (e.g., 'xgboost', 'random_forest')
        task_type: Task type ('classification', 'regression', 'time_series')
        duration: Training duration in seconds
        status: Training status ('success', 'failed')
        accuracy: Model accuracy score (optional)
        model_id: Model ID (optional)
    """
    ml_training_duration_seconds.labels(
        model_type=model_type, task_type=task_type
    ).observe(duration)

    ml_training_total.labels(
        model_type=model_type, task_type=task_type, status=status
    ).inc()

    if accuracy is not None and model_id is not None:
        ml_model_accuracy.labels(model_id=model_id, model_type=model_type).set(accuracy)


def track_inference_metrics(
    model_id: str, duration: float, inference_type: str = "single"
):
    """
    Track inference metrics

    Args:
        model_id: Model ID
        duration: Inference duration in seconds
        inference_type: 'single' or 'batch'
    """
    ml_inference_duration_seconds.labels(model_id=model_id).observe(duration)

    ml_inference_total.labels(model_id=model_id, type=inference_type).inc()


def track_drift_metrics(
    model_id: str, drift_detected: bool, drift_type: str = "data", score: float = 0.0
):
    """
    Track drift detection metrics

    Args:
        model_id: Model ID
        drift_detected: Whether drift was detected
        drift_type: Type of drift ('data', 'concept', 'prediction')
        score: Drift score
    """
    if drift_detected:
        drift_detected_total.labels(model_id=model_id, drift_type=drift_type).inc()

    drift_score.labels(model_id=model_id).set(score)


def setup_prometheus_metrics(app: FastAPI):
    """
    Set up Prometheus metrics endpoint

    Args:
        app: FastAPI application instance
    """
    # Create metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # Set application info
    app_info.info({"version": "1.0.0", "name": "AI Decision Intelligence Platform"})

    # Middleware to track HTTP requests
    @app.middleware("http")
    async def prometheus_middleware(request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        track_request_metrics(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration=duration,
        )

        return response

    return app
