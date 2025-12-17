from fastapi import APIRouter, HTTPException
from ..services.visualization_service import visualization_service

router = APIRouter()

@router.get("/correlation/{dataset_id}")
async def get_correlation_heatmap(dataset_id: str):
    plot = visualization_service.get_correlation_heatmap(dataset_id)
    if not plot:
        raise HTTPException(status_code=404, detail="Dataset not found or no numeric data")
    return {"plot": plot}

@router.get("/feature_importance/{model_id}")
async def get_feature_importance_plot(model_id: str):
    plot = visualization_service.get_feature_importance(model_id)
    if not plot:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"plot": plot}

@router.get("/trend/{dataset_id}")
async def get_trend_analysis_chart(dataset_id: str):
    plot = visualization_service.get_trend_analysis(dataset_id)
    if not plot:
        raise HTTPException(status_code=404, detail="Dataset not found or not time series")
    return {"plot": plot}

@router.get("/forecast/{model_id}/{dataset_id}")
async def get_forecast_plot(model_id: str, dataset_id: str):
    plot = visualization_service.get_forecast_plot(model_id, dataset_id)
    if not plot:
        raise HTTPException(status_code=404, detail="Model or dataset not found or not time series")
    return {"plot": plot}

@router.get("/filters/{dataset_id}")
async def get_interactive_filters(dataset_id: str):
    filters = visualization_service.get_interactive_filters(dataset_id)
    if not filters:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"filters": filters}

@router.get("/shap_global/{model_id}")
async def get_shap_global_plot(model_id: str):
    plot = visualization_service.get_shap_global_plot(model_id)
    if not plot:
        raise HTTPException(status_code=404, detail="Model not found or no explainer")
    return {"plot": plot}

@router.post("/shap_local/{model_id}")
async def get_shap_local_plot(model_id: str, input_data: Dict[str, Any]):
    plot = visualization_service.get_shap_local_plot(model_id, input_data)
    if not plot:
        raise HTTPException(status_code=404, detail="Model not found or explanation failed")
    return {"plot": plot}