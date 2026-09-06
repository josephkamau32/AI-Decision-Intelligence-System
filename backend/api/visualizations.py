from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from ..services.visualization_service import visualization_service
from ..utils.auth import get_current_user

router = APIRouter()


@router.get("/correlation/{dataset_id}")
async def get_correlation_heatmap(
    dataset_id: str,
    current_user: dict = Depends(get_current_user),
):
    data = visualization_service.get_correlation_heatmap(
        dataset_id, user_id=current_user["id"]
    )
    if not data:
        raise HTTPException(
            status_code=404, detail="Dataset not found or no numeric data"
        )
    return data


@router.get("/feature_importance/{model_id}")
async def get_feature_importance_plot(
    model_id: str,
    current_user: dict = Depends(get_current_user),
):
    data = visualization_service.get_feature_importance(
        model_id, user_id=current_user["id"]
    )
    if not data:
        raise HTTPException(status_code=404, detail="Model not found")
    return data


@router.get("/trend/{dataset_id}")
async def get_trend_analysis_chart(
    dataset_id: str,
    current_user: dict = Depends(get_current_user),
):
    data = visualization_service.get_trend_analysis(
        dataset_id, user_id=current_user["id"]
    )
    if not data:
        raise HTTPException(
            status_code=404, detail="Dataset not found or not time series"
        )
    return data


@router.get("/forecast/{model_id}/{dataset_id}")
async def get_forecast_plot(
    model_id: str,
    dataset_id: str,
    current_user: dict = Depends(get_current_user),
):
    plot = visualization_service.get_forecast_plot(
        model_id, dataset_id, user_id=current_user["id"]
    )
    if not plot:
        raise HTTPException(
            status_code=404, detail="Model or dataset not found or not time series"
        )
    return {"plot": plot}


@router.get("/filters/{dataset_id}")
async def get_interactive_filters(
    dataset_id: str,
    current_user: dict = Depends(get_current_user),
):
    filters = visualization_service.get_interactive_filters(
        dataset_id, user_id=current_user["id"]
    )
    if not filters:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"filters": filters}


@router.get("/shap_global/{model_id}")
async def get_shap_global_plot(
    model_id: str,
    current_user: dict = Depends(get_current_user),
):
    data = visualization_service.get_shap_global_plot(
        model_id, user_id=current_user["id"]
    )
    if not data:
        raise HTTPException(status_code=404, detail="Model not found or no explainer")
    return data


@router.post("/shap_local/{model_id}")
async def get_shap_local_plot(
    model_id: str,
    input_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
):
    data = visualization_service.get_shap_local_plot(
        model_id, input_data, user_id=current_user["id"]
    )
    if not data:
        raise HTTPException(
            status_code=404, detail="Model not found or explanation failed"
        )
    return data
