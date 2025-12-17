"""
Enhanced copilot tools for dataset and model integration
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import logging

from ..services.dataset_service import dataset_service
from ..services.model_service import model_service
from ..ml.data_ingestion import DataProfiler

logger = logging.getLogger(__name__)

class CopilotTools:
    """Tools that AI Copilot can use to interact with the system"""
    
    def __init__(self):
        logger.info("Initialized CopilotTools")
    
    def get_dataset_schema(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get schema and column information for a dataset
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            Dictionary with schema information
        """
        try:
            df = model_service.get_dataset(dataset_id)
            
            schema = {
                'dataset_id': dataset_id,
                'columns': [],
                'row_count': len(df),
                'column_count': len(df.columns)
            }
            
            for col in df.columns:
                schema['columns'].append({
                    'name': col,
                    'dtype': str(df[col].dtype),
                    'unique_values': int(df[col].nunique()),
                    'null_count': int(df[col].isna().sum())
                })
            
            return schema
        except Exception as e:
            logger.error(f"Failed to get dataset schema: {e}")
            return {'error': str(e)}
    
    def get_dataset_statistics(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get statistical summary of a dataset
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            Dictionary with statistics
        """
        try:
            df = model_service.get_dataset(dataset_id)
            
            # Profile the dataset
            profiler = DataProfiler(df)
            profile = profiler.generate_profile()
            
            return {
                'dataset_id': dataset_id,
                'profile': profile,
                'quality_issues': profiler.get_data_quality_issues()
            }
        except Exception as e:
            logger.error(f"Failed to get dataset statistics: {e}")
            return {'error': str(e)}
    
    def get_model_performance(self, model_id: str) -> Dict[str, Any]:
        """
        Get performance metrics for a trained model
        
        Args:
            model_id: ID of the model
            
        Returns:
            Dictionary with performance info
        """
        try:
            metrics = model_service.get_model_metrics(model_id)
            
            if metrics is None:
                return {'error': f'Model {model_id} not found'}
            
            return metrics
        except Exception as e:
            logger.error(f"Failed to get model performance: {e}")
            return {'error': str(e)}
    
    def get_feature_importance(self, model_id: str, top_n: int = 10) -> Dict[str, Any]:
        """
        Get top features for a model
        
        Args:
            model_id: ID of the model
            top_n: Number of top features
            
        Returns:
            Dictionary with feature importance
        """
        try:
            importance = model_service.get_global_explanation(model_id, top_n=top_n)
            return importance
        except Exception as e:
            logger.error(f"Failed to get feature importance: {e}")
            return {'error': str(e)}
    
    def query_data(self, dataset_id: str, query: str, limit: int = 100) -> Dict[str, Any]:
        """
        Query dataset with pandas-like operations
        
        Args:
            dataset_id: ID of the dataset
            query: Query string (pandas query syntax)
            limit: Maximum rows to return
            
        Returns:
            Dictionary with query results
        """
        try:
            df = model_service.get_dataset(dataset_id)
            
            # Execute query
            result_df = df.query(query).head(limit)
            
            return {
                'dataset_id': dataset_id,
                'query': query,
                'row_count': len(result_df),
                'data': result_df.to_dict('records')
            }
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {'error': str(e)}
    
    def get_predictions(self, model_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a prediction with a model
        
        Args:
            model_id: ID of the model
            data: Input data as dictionary
            
        Returns:
            Dictionary with prediction
        """
        try:
            prediction = model_service.predict(model_id, data)
            return prediction
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {'error': str(e)}
    
    def list_available_datasets(self) -> List[Dict[str, Any]]:
        """
        List all available datasets
        
        Returns:
            List of dataset info
        """
        try:
            datasets = []
            # Mock implementation - would query dataset service
            return datasets
        except Exception as e:
            logger.error(f"Failed to list datasets: {e}")
            return []
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all trained models
        
        Returns:
            List of model info
        """
        try:
            models = model_service.list_models()
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def get_all_tools_description(self) -> List[Dict[str, str]]:
        """
        Get descriptions of all available tools (for LLM function calling)
        
        Returns:
            List of tool descriptions
        """
        return [
            {
                'name': 'get_dataset_schema',
                'description': 'Get column names, types, and basic info about a dataset',
                'parameters': {
                    'dataset_id': 'ID of the dataset to describe'
                }
            },
            {
                'name': 'get_dataset_statistics',
                'description': 'Get statistical summary, missing values, outliers for a dataset',
                'parameters': {
                    'dataset_id': 'ID of the dataset to analyze'
                }
            },
            {
                'name': 'get_model_performance',
                'description': 'Get accuracy, precision, recall, and other metrics for a trained model',
                'parameters': {
                    'model_id': 'ID of the model'
                }
            },
            {
                'name': 'get_feature_importance',
                'description': 'Get the most important features used by a model',
                'parameters': {
                    'model_id': 'ID of the model',
                    'top_n': 'Number of top features to return (default: 10)'
                }
            },
            {
                'name': 'query_data',
                'description': 'Query dataset using pandas syntax to filter or analyze data',
                'parameters': {
                    'dataset_id': 'ID of the dataset',
                    'query': 'Pandas query string (e.g., "age > 30 and salary < 50000")',
                    'limit': 'Maximum rows to return'
                }
            },
            {
                'name': 'get_predictions',
                'description': 'Make a prediction using a trained model',
                'parameters': {
                    'model_id': 'ID of the model',
                    'data': 'Input data as dictionary with feature names and values'
                }
            },
            {
                'name': 'list_available_datasets',
                'description': 'List all datasets in the system',
                'parameters': {}
            },
            {
                'name': 'list_available_models',
                'description': 'List all trained models',
                'parameters': {}
            }
        ]

# Singleton instance
copilot_tools = CopilotTools()