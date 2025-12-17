"""
Celery tasks for async processing integrated with new AutoML engine
"""
from celery_app import celery_app
from ml.automl import AutoML
from ml.data_preprocessing import DataCleaner, FeatureEngineer
from ml.explainability import ModelExplainer
from services.dataset_service import dataset_service
from services.model_service import model_service
import pandas as pd
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='tasks.train_model')
def train_model_task(
    self,
    task_id: str,
    dataset_id: str,
    target_column: str,
    task_type: str = 'auto',
    test_size: float = 0.2,
    experiment_name: str = "AutoML"
):
    """
    Async Celery task for model training using AutoML engine
    
    Args:
        task_id: Unique task identifier
        dataset_id: ID of the dataset to train on
        target_column: Name of the target variable
        task_type: 'classification', 'regression', or 'auto'
        test_size: Proportion for test set
        experiment_name: MLflow experiment name
    """
    try:
        logger.info(f"[Task {task_id}] Starting AutoML training for dataset {dataset_id}")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'message': 'Loading dataset...'}
        )
        
        # Load dataset
        dataset_df = model_service.get_dataset(dataset_id)
        
        if target_column not in dataset_df.columns:
            raise ValueError(f"Target column '{target_column}' not found in dataset")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 20, 'message': 'Preprocessing data...'}
        )
        
        # Data preprocessing
        cleaner = DataCleaner(dataset_df)
        cleaned_df = cleaner.handle_missing_values(strategy='mean')
        
        # Separate features and target
        X = cleaned_df.drop(columns=[target_column])
        y = cleaned_df[target_column]
        
        # Feature engineering
        engineer = FeatureEngineer(X)
        X_encoded = engineer.encode_categorical(method='label')
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 30, 'message': 'Training models...'}
        )
        
        # Initialize and train AutoML
        automl = AutoML(task_type=task_type, test_size=test_size)
        results = automl.fit(X_encoded, y, dataset_id=dataset_id, experiment_name=experiment_name)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 80, 'message': 'Generating explanations...'}
        )
        
        # Create explainer
        explainer = ModelExplainer(automl.best_model, X_encoded.sample(min(100, len(X_encoded))))
        
        # Save model
        model_id = task_id
        model_path = Path("models") / f"{model_id}.joblib"
        model_path.parent.mkdir(exist_ok=True)
        automl.save_model(str(model_path))
        
        # Store in model service
        model_service.models[model_id] = {
            'automl': automl,
            'model': automl.best_model,
            'explainer': explainer,
            'X_sample': X_encoded.sample(min(100, len(X_encoded))),
            'feature_names': X_encoded.columns.tolist(),
            'target_column': target_column,
            'task_type': results['task_type'],
            'best_model_name': results['best_model'],
            'best_score': results['best_score'],
            'all_results': results['all_results']
        }
        
        # Update task status in model service
        model_service.tasks[task_id] = {
            'status': 'completed',
            'message': f"Training completed. Best model: {results['best_model']}",
            'progress': 100,
            'model_id': model_id,
            'results': results
        }
        
        logger.info(f"[Task {task_id}] Training completed successfully")
        
        return {
            'status': 'completed',
            'task_id': task_id,
            'model_id': model_id,
            'best_model': results['best_model'],
            'best_score': results['best_score'],
            'message': f"Training completed with {results['best_model']} (score: {results['best_score']:.4f})"
        }
        
    except Exception as e:
        logger.error(f"[Task {task_id}] Training failed: {e}")
        
        # Update task status
        if task_id in model_service.tasks:
            model_service.tasks[task_id] = {
                'status': 'failed',
                'message': f"Training failed: {str(e)}",
                'progress': 0,
                'error': str(e)
            }
        
        raise

@celery_app.task(bind=True, name='tasks.batch_predict')
def batch_predict_task(self, model_id: str, data_list: list):
    """
    Async task for batch predictions
    
    Args:
        model_id: ID of the trained model
        data_list: List of dictionaries with input data
    """
    try:
        logger.info(f"Batch prediction task for model {model_id}, {len(data_list)} samples")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 20, 'message': 'Loading model...'}
        )
        
        # Make predictions using model service
        results = model_service.predict_batch(model_id, data_list)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 100, 'message': 'Predictions completed'}
        )
        
        logger.info(f"Batch predictions completed for model {model_id}")
        
        return {
            'status': 'completed',
            'predictions': results,
            'count': len(results)
        }
        
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise

@celery_app.task(bind=True, name='tasks.profile_dataset')
def profile_dataset_task(self, dataset_id: str):
    """
    Async task for dataset profiling and quality analysis
    
    Args:
        dataset_id: ID of the dataset to profile
    """
    try:
        logger.info(f"Profiling dataset {dataset_id}")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'message': 'Loading dataset...'}
        )
        
        # Load dataset
        dataset_df = model_service.get_dataset(dataset_id)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 30, 'message': 'Analyzing data...'}
        )
        
        # Generate profile
        profile = {
            'rows': len(dataset_df),
            'columns': len(dataset_df.columns),
            'memory_usage': dataset_df.memory_usage(deep=True).sum() / 1024**2,  # MB
            'columns_info': [],
            'missing_values': {},
            'duplicates': int(dataset_df.duplicated().sum()),
            'data_types': {}
        }
        
        # Analyze each column
        for col in dataset_df.columns:
            col_data = dataset_df[col]
            col_info = {
                'name': col,
                'dtype': str(col_data.dtype),
                'unique_values': int(col_data.nunique()),
                'missing_count': int(col_data.isna().sum()),
                'missing_percent': float(col_data.isna().sum() / len(col_data) * 100)
            }
            
            # Add statistics for numeric columns
            if pd.api.types.is_numeric_dtype(col_data):
                col_info.update({
                    'mean': float(col_data.mean()) if not col_data.isna().all() else None,
                    'std': float(col_data.std()) if not col_data.isna().all() else None,
                    'min': float(col_data.min()) if not col_data.isna().all() else None,
                    'max': float(col_data.max()) if not col_data.isna().all() else None,
                    'median': float(col_data.median()) if not col_data.isna().all() else None
                })
            
            profile['columns_info'].append(col_info)
            
            if col_info['missing_count'] > 0:
                profile['missing_values'][col] = col_info['missing_count']
            
            profile['data_types'][col] = str(col_data.dtype)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 100, 'message': 'Profiling completed'}
        )
        
        logger.info(f"Dataset profile completed for {dataset_id}")
        
        return {
            'status': 'completed',
            'profile': profile
        }
        
    except Exception as e:
        logger.error(f"Dataset profiling failed: {e}")
        raise

@celery_app.task(bind=True, name='tasks.generate_explanations')
def generate_explanations_task(self, model_id: str, num_samples: int = 100):
    """
    Async task for generating SHAP explanations
    
    Args:
        model_id: ID of the trained model
        num_samples: Number of samples to use for explanation
    """
    try:
        logger.info(f"Generating explanations for model {model_id}")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 20, 'message': 'Loading model...'}
        )
        
        # Get global explanations
        importance = model_service.get_global_explanation(model_id, top_n=20)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 70, 'message': 'Generating plots...'}
        )
        
        # Generate plots
        summary_plot = model_service.get_explanation_plot(model_id, plot_type='summary')
        importance_plot = model_service.get_explanation_plot(model_id, plot_type='importance')
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 100, 'message': 'Explanations generated'}
        )
        
        logger.info(f"Explanations generated for model {model_id}")
        
        return {
            'status': 'completed',
            'importance': importance,
            'plots': {
                'summary': summary_plot,
                'importance': importance_plot
            }
        }
        
    except Exception as e:
        logger.error(f"Explanation generation failed: {e}")
        raise