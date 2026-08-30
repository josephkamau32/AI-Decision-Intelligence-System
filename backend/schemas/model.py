from pydantic import BaseModel
from typing import Optional, Dict, Any


class TrainRequest(BaseModel):
    dataset_id: str
    model_type: str  # e.g., "linear", "neural_network"
    parameters: Optional[Dict[str, Any]] = None


class TrainResponse(BaseModel):
    training_id: str
    status: str  # "started", "running", etc.
    message: str


class InferenceRequest(BaseModel):
    model_id: str
    input_data: Dict[str, Any]


class InferenceResponse(BaseModel):
    result: Dict[str, Any]
    confidence: Optional[float] = None


class BatchInferenceRequest(BaseModel):
    model_id: str
    input_data_list: list[Dict[str, Any]]


class BatchInferenceResponse(BaseModel):
    results: list[Dict[str, Any]]
    confidence: Optional[float] = None
