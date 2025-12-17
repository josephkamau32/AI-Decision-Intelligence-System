from .celery_app import celery_app
from .pipelines.ai_pipeline import AIPipeline
from .services.dataset_service import dataset_service
from .services.model_service import model_service
import mlflow
from mlops.registry.setup import register_model
import shap
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def train_model_task(self, dataset_id: str, model_type: str, parameters: dict = None):
    """Async task for model training."""
    try:
        self.update_state(state='PROGRESS', meta={'message': 'Starting training'})

        dataset = next((d for d in dataset_service.datasets if d.id == dataset_id), None)
        if not dataset:
            raise ValueError("Dataset not found")

        pipeline = AIPipeline()
        result = pipeline.run_pipeline(dataset.file_path)
        processed_data = result['processed_data']
        profile = result['profile']
        automl_result = result['automl_result']
        trained_model = automl_result['trained_model']
        features = list(processed_data.drop(columns=[profile['target_variable']]).columns)

        # Create explainer
        explainer = None
        background = None
        if profile['problem_type'] != 'time_series':
            if hasattr(trained_model, 'feature_importances_'):  # tree
                explainer = shap.TreeExplainer(trained_model)
            elif hasattr(trained_model, 'coef_'):  # linear
                background = processed_data[features].values[:min(100, len(processed_data))]
                explainer = shap.LinearExplainer(trained_model, background)
            else:
                background = processed_data[features].values[:min(100, len(processed_data))]
                explainer = shap.KernelExplainer(trained_model.predict, background)

        model_data = {
            'model': trained_model,
            'explainer': explainer,
            'features': features,
            'target': profile['target_variable'],
            'problem_type': profile['problem_type'],
            'background': background
        }

        run_id = automl_result.get('run_id')
        model_name = None
        if run_id:
            model_name = f"{automl_result['best_model']}_{self.request.id}"
            register_model(run_id, model_name, "model")

        return {
            'status': 'completed',
            'model_data': model_data,
            'model_name': model_name,
            'message': f"Training completed with best model {automl_result['best_model']}"
        }

    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        raise

@celery_app.task(bind=True)
def perform_inference_task(self, model_id: str, input_data: dict):
    """Async task for inference."""
    try:
        if model_id not in model_service.models:
            raise ValueError("Model not found")

        model_info = model_service.models[model_id]
        model = model_info['model']
        features = model_info['features']

        # Prepare input
        input_df = pd.DataFrame([input_data])
        input_df = input_df[features]  # Ensure correct feature order

        prediction = model.predict(input_df)

        return {
            'prediction': prediction.tolist() if hasattr(prediction, 'tolist') else prediction,
            'confidence': 0.95  # Mock confidence
        }

    except Exception as e:
        logger.error(f"Inference failed: {str(e)}")
        raise

@celery_app.task(bind=True)
def batch_inference_task(self, model_id: str, input_data_list: list):
    """Async task for batch inference."""
    try:
        if model_id not in model_service.models:
            raise ValueError("Model not found")

        model_info = model_service.models[model_id]
        model = model_info['model']
        features = model_info['features']

        # Prepare input
        input_df = pd.DataFrame(input_data_list)
        input_df = input_df[features]

        predictions = model.predict(input_df)

        return {
            'predictions': predictions.tolist() if hasattr(predictions, 'tolist') else predictions,
            'confidence': 0.95
        }

    except Exception as e:
        logger.error(f"Batch inference failed: {str(e)}")
        raise