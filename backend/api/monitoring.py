from fastapi import APIRouter, HTTPException
from ..schemas.monitoring import MonitoringMetricsResponse, AlertsResponse
from ..monitoring.monitoring_service import monitoring_service

router = APIRouter()

@router.get("/metrics/{model_id}", response_model=MonitoringMetricsResponse)
async def get_monitoring_metrics(model_id: str):
    """Get monitoring metrics for a model."""
    try:
        metrics = monitoring_service.get_monitoring_metrics(model_id)
        return MonitoringMetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring metrics: {str(e)}")

@router.get("/alerts/{model_id}", response_model=AlertsResponse)
async def get_model_alerts(model_id: str):
    """Get alerts for a model."""
    try:
        alerts = monitoring_service.get_all_alerts(model_id)
        return AlertsResponse(**alerts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.post("/initialize/{model_id}")
async def initialize_model_monitoring(model_id: str, reference_data: dict, problem_type: str = "classification"):
    """Initialize monitoring for a model."""
    try:
        import pandas as pd
        ref_df = pd.DataFrame(reference_data)
        monitoring_service.initialize_model_monitoring(model_id, ref_df, problem_type)
        return {"message": f"Monitoring initialized for model {model_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize monitoring: {str(e)}")

@router.post("/performance/{model_id}/baseline")
async def update_performance_baseline(model_id: str, y_true: list, y_pred: list):
    """Update performance baseline for a model."""
    try:
        import numpy as np
        y_true_arr = np.array(y_true)
        y_pred_arr = np.array(y_pred)
        monitoring_service.update_performance_baseline(model_id, y_true_arr, y_pred_arr)
        return {"message": f"Performance baseline updated for model {model_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update baseline: {str(e)}")

@router.post("/performance/{model_id}/monitor")
async def monitor_performance(model_id: str, y_true: list, y_pred: list):
    """Monitor current performance."""
    try:
        import numpy as np
        y_true_arr = np.array(y_true)
        y_pred_arr = np.array(y_pred)
        result = monitoring_service.monitor_performance(model_id, y_true_arr, y_pred_arr)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to monitor performance: {str(e)}")