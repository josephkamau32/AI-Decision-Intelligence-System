import uuid
from typing import Dict, Any
from ..schemas.model import TrainRequest, TrainResponse, InferenceRequest, InferenceResponse, BatchInferenceRequest, BatchInferenceResponse
from ..pipelines.ai_pipeline import AIPipeline
from ..services.dataset_service import dataset_service
from ..tasks import train_model_task
from ..monitoring.monitoring_service import monitoring_service
import mlflow
from backend.utils.config import settings
from mlops.registry.setup import register_model
import shap
import numpy as np
import pandas as pd

class ModelService:
    def __init__(self):
        self.trainings = {}  # In-memory storage for demo
        self.models = {}  # Store model info: {'model': model, 'explainer': explainer, 'features': features, 'target': target, 'problem_type': problem_type}

    def initiate_training(self, request: TrainRequest) -> TrainResponse:
        training_id = str(uuid.uuid4())
        dataset = next((d for d in dataset_service.datasets if d.id == request.dataset_id), None)
        if not dataset:
            return TrainResponse(training_id=training_id, status="failed", message="Dataset not found")

        # Start async training task
        task = train_model_task.delay(request.dataset_id, request.model_type, request.parameters)
        self.trainings[training_id] = {'task_id': task.id, 'status': 'pending'}

        return TrainResponse(
            training_id=training_id,
            status="started",
            message="Training initiated asynchronously"
        )

    def get_training_status(self, training_id: str) -> TrainResponse:
        if training_id not in self.trainings:
            return TrainResponse(training_id=training_id, status="not_found", message="Training not found")

        training_info = self.trainings[training_id]
        task_id = training_info['task_id']
        task_result = train_model_task.AsyncResult(task_id)

        if task_result.state == 'PENDING':
            status = "pending"
            message = "Training is pending"
        elif task_result.state == 'PROGRESS':
            status = "running"
            message = task_result.info.get('message', 'Training in progress')
        elif task_result.state == 'SUCCESS':
            # Store the model
            result = task_result.result
            self.models[training_id] = result['model_data']
            status = result['status']
            message = result['message']
            # Update training status
            self.trainings[training_id]['status'] = status
        else:  # FAILURE
            status = "failed"
            message = str(task_result.info)
            self.trainings[training_id]['status'] = status

        return TrainResponse(
            training_id=training_id,
            status=status,
            message=message
        )

    def perform_inference(self, request: InferenceRequest) -> InferenceResponse:
        """Perform inference with a trained model."""
        if request.model_id not in self.models:
            raise ValueError("Model not found")

        model_info = self.models[request.model_id]
        model = model_info['model']
        features = model_info['features']

        # Prepare input
        input_df = pd.DataFrame([request.input_data])
        input_df = input_df[features]

        prediction = model.predict(input_df)
        pred_value = prediction.tolist()[0] if hasattr(prediction, 'tolist') else prediction[0]

        result = {
            "prediction": pred_value,
            "details": request.input_data
        }

        # Monitor inference
        monitoring_service.monitor_inference(request.model_id, request.input_data, pred_value)

        return InferenceResponse(
            result=result,
            confidence=0.95
        )

    def perform_batch_inference(self, request: BatchInferenceRequest) -> BatchInferenceResponse:
        """Perform batch inference with a trained model."""
        if request.model_id not in self.models:
            raise ValueError("Model not found")

        model_info = self.models[request.model_id]
        model = model_info['model']
        features = model_info['features']

        # Prepare input
        input_df = pd.DataFrame(request.input_data_list)
        input_df = input_df[features]

        predictions = model.predict(input_df)

        results = []
        for i, pred in enumerate(predictions):
            results.append({
                "prediction": pred.tolist() if hasattr(pred, 'tolist') else pred,
                "details": request.input_data_list[i]
            })

        return BatchInferenceResponse(
            results=results,
            confidence=0.95
        )

model_service = ModelService()
