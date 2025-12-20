from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import pandas as pd
import logging

# Make ML imports optional to allow auth to work without ML dependencies
try:
    from ..ml.automl import AutoML
    from ..ml.inference import ModelInference
    from ..ml.explainability import ModelExplainer
    from ..services.model_service import model_service
    ML_AVAILABLE = True
except ImportError as e:
    ML_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"ML modules not available: {e}. ML endpoints will not function.")
    model_service = None

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
class TrainModelRequest(BaseModel):
    dataset_id: str
    target_column: str
    task_type: str = 'auto'  # 'classification', 'regression', or 'auto'
    test_size: float = 0.2
    experiment_name: str = "AutoML"

class TrainModelResponse(BaseModel):
    task_id: str
    status: str
    message: str

class PredictRequest(BaseModel):
    model_id: str
    data: Dict[str, Any]  # Single instance as dict

class BatchPredictRequest(BaseModel):
    model_id: str
    data: List[Dict[str, Any]]  # List of instances

class PredictResponse(BaseModel):
    predictions: List[Dict[str, Any]]

class ModelMetricsResponse(BaseModel):
    model_id: str
    best_model: str
    metrics: Dict[str, Any]
    all_models: Dict[str, Dict[str, float]]

class ExplainRequest(BaseModel):
    model_id: str
    instance: Dict[str, Any]

class ExplainResponse(BaseModel):
    explanation: Dict[str, Any]

# Endpoints

@router.post("/train", response_model=TrainModelResponse)
async def train_model(request: TrainModelRequest, background_tasks: BackgroundTasks):
    """
    Train a model using AutoML
    
    This endpoint starts a background training task
    """
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="ML features are currently unavailable. Please check server configuration."
        )
    
    try:
        logger.info(f"Received training request for dataset {request.dataset_id}")
        
        # Get dataset from service
        dataset_df = model_service.get_dataset(request.dataset_id)
        
        if request.target_column not in dataset_df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Target column '{request.target_column}' not found in dataset"
            )
        
        # Create task ID
        task_id = f"train_{request.dataset_id}_{request.target_column}"
        
        # Add background task
        background_tasks.add_task(
            model_service.train_model_async,
            task_id=task_id,
            dataset_df=dataset_df,
            target_column=request.target_column,
            task_type=request.task_type,
            test_size=request.test_size,
            experiment_name=request.experiment_name
        )
        
        return TrainModelResponse(
            task_id=task_id,
            status="started",
            message=f"Training initiated for dataset {request.dataset_id}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get status of a training task"""
    try:
        status = model_service.get_task_status(task_id)
        if status is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_id}/metrics", response_model=ModelMetricsResponse)
async def get_model_metrics(model_id: str):
    """Get detailed metrics for a trained model"""
    try:
        metrics = model_service.get_model_metrics(model_id)
        if metrics is None:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        return ModelMetricsResponse(**metrics)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict", response_model=PredictResponse)
async def predict_single(request: PredictRequest):
    """Make a single prediction"""
    try:
        logger.info(f"Prediction request for model {request.model_id}")
        
        # Load model and make prediction
        result = model_service.predict(request.model_id, request.data)
        
        return PredictResponse(predictions=[result])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/predict/batch", response_model=PredictResponse)
async def predict_batch(request: BatchPredictRequest):
    """Make batch predictions"""
    try:
        logger.info(f"Batch prediction request for model {request.model_id}, {len(request.data)} samples")
        
        results = model_service.predict_batch(request.model_id, request.data)
        
        return PredictResponse(predictions=results)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_id}/explain/global")
async def get_global_explanations(model_id: str, top_n: int = Query(10, ge=1, le=50)):
    """Get global feature importance"""
    try:
        logger.info(f"Global explanation request for model {model_id}")
        
        explanation = model_service.get_global_explanation(model_id, top_n=top_n)
        
        return explanation
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Global explanation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{model_id}/explain/local", response_model=ExplainResponse)
async def explain_prediction(model_id: str, request: ExplainRequest):
    """Explain a single prediction"""
    try:
        logger.info(f"Local explanation request for model {model_id}")
        
        explanation = model_service.explain_instance(model_id, request.instance)
        
        return ExplainResponse(explanation=explanation)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Local explanation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_id}/explain/plots")
async def get_explanation_plots(model_id: str, plot_type: str = Query("summary", regex="^(summary|importance)$")):
    """
    Get SHAP visualization plots
    
    plot_type: 'summary' or 'importance'
    """
    try:
        logger.info(f"Plot request for model {model_id}, type: {plot_type}")
        
        plot_data = model_service.get_explanation_plot(model_id, plot_type)
        
        return {"plot": plot_data, "type": plot_type}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plot generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_models():
    """List all trained models"""
    try:
        models = model_service.list_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{model_id}")
async def delete_model(model_id: str):
    """Delete a model"""
    try:
        model_service.delete_model(model_id)
        return {"message": f"Model {model_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete model: {e}")
        raise HTTPException(status_code=500, detail=str(e))