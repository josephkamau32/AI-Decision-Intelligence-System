from fastapi import APIRouter, HTTPException
from ..schemas.model import TrainRequest, TrainResponse, InferenceRequest, InferenceResponse, BatchInferenceRequest, BatchInferenceResponse
from ..services.model_service import model_service

router = APIRouter()

@router.post("/train", response_model=TrainResponse)
async def initiate_training(request: TrainRequest):
    """Initiate model training."""
    try:
        response = model_service.initiate_training(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training initiation failed: {str(e)}")

@router.get("/train/{training_id}", response_model=TrainResponse)
async def get_training_status(training_id: str):
    """Get training status."""
    try:
        response = model_service.get_training_status(training_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get training status: {str(e)}")

@router.post("/inference", response_model=InferenceResponse)
async def perform_inference(request: InferenceRequest):
    """Perform inference with a trained model."""
    try:
        response = model_service.perform_inference(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")

@router.post("/batch-inference", response_model=BatchInferenceResponse)
async def perform_batch_inference(request: BatchInferenceRequest):
    """Perform batch inference with a trained model."""
    try:
        response = model_service.perform_batch_inference(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch inference failed: {str(e)}")