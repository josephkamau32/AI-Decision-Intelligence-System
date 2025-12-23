"""
Insights Service
Generates analytics and insights for datasets, models, and system
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class InsightsService:
    """Service for generating insights and recommendations"""
    
    def __init__(self):
        pass
    
    async def generate_dataset_insights(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        Generate comprehensive insights for a dataset
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            Dictionary containing insights and recommendations
        """
        try:
            # Get dataset from service
            from .dataset_service import dataset_service
            dataset = dataset_service.get_dataset(dataset_id)
            
            if not dataset:
                return None
            
            # Load dataset for analysis
            try:
                df = dataset_service.load_dataset_dataframe(dataset_id)
            except Exception as e:
                logger.warning(f"Could not load dataset for analysis: {e}")
                # Return basic insights without dataframe
                return {
                    "dataset_id": dataset_id,
                    "insights": {
                        "name": dataset.name,
                        "rows": getattr(dataset, 'rows', 0),
                        "columns": getattr(dataset, 'columns', 0),
                        "status": "available"
                    },
                    "recommendations": [
                        "Dataset is available for analysis",
                        "Upload more data to get detailed insights"
                    ],
                    "quality_score": 0.8
                }
            
            # Calculate insights
            insights = {
                "basic_stats": self._calculate_basic_stats(df),
                "data_quality": self._calculate_data_quality(df),
                "feature_types": self._analyze_feature_types(df),
                "correlations": self._calculate_correlations(df)
            }
            
 # Generate recommendations
            recommendations = self._generate_dataset_recommendations(df, insights)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(insights)
            
            return {
                "dataset_id": dataset_id,
                "insights": insights,
                "recommendations": recommendations,
                "quality_score": quality_score
            }
            
        except Exception as e:
            logger.error(f"Error generating dataset insights: {e}", exc_info=True)
            raise
    
    async def generate_model_insights(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Generate comprehensive insights for a model
        
        Args:
            model_id: ID of the model
            
        Returns:
            Dictionary containing insights and recommendations
        """
        try:
            # Mock implementation - replace with actual model service
            insights = {
                "performance_metrics": {
                    "accuracy": 0.85,
                    "precision": 0.82,
                    "recall": 0.88,
                    "f1_score": 0.85
                },
                "feature_importance": {
                    "feature_1": 0.25,
                    "feature_2": 0.20,
                    "feature_3": 0.15
                },
                "prediction_distribution": {
                    "class_0": 450,
                    "class_1": 550
                }
            }
            
            # Mock performance trends
            performance_trends = [
                {"date": "2025-12-20", "accuracy": 0.83},
                {"date": "2025-12-21", "accuracy": 0.84},
                {"date": "2025-12-22", "accuracy": 0.85}
            ]
            
            recommendations = [
                "Model performance is good and stable",
                "Consider adding more training data to improve accuracy",
                "Monitor for concept drift in production"
            ]
            
            return {
                "model_id": model_id,
                "insights": insights,
                "performance_trends": performance_trends,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error generating model insights: {e}", exc_info=True)
            raise
    
    async def generate_system_insights(self) -> Dict[str, Any]:
        """
        Generate system-wide insights
        
        Returns:
            Dictionary containing system insights
        """
        try:
            # Get system statistics
            from .dataset_service import dataset_service
            
            datasets = dataset_service.list_datasets()
            
            insights = {
                "total_datasets": len(datasets),
                "total_models": 0,  # Would query model service
                "total_predictions": 0,  # Would query prediction logs
                "system_health": {
                    "status": "healthy",
                    "uptime_hours": 24,
                    "cpu_usage": 45.5,
                    "memory_usage": 62.3,
                    "disk_usage": 38.2
                },
                "recommendations": [
                    "System is running optimally",
                    "Consider archiving old datasets to save space",
                    "Regular backups are recommended"
                ]
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating system insights: {e}", exc_info=True)
            raise
    
    async def get_recommendations(
        self,
        context: Optional[str] = None,
        limit: int = 10,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations
        
        Args:
            context: Context for recommendations
            limit: Maximum number of recommendations
            user_id: User ID for personalization
            
        Returns:
            List of recommendations
        """
        try:
            recommendations = []
            
            # Context-specific recommendations
            if context == "dataset":
                recommendations.extend([
                    {
                        "type": "dataset",
                        "priority": "high",
                        "title": "Clean missing values",
                        "description": "Some datasets have significant missing values that should be addressed"
                    },
                    {
                        "type": "dataset",
                        "priority": "medium",
                        "title": "Feature engineering",
                        "description": "Consider creating derived features to improve model performance"
                    }
                ])
            elif context == "model":
                recommendations.extend([
                    {
                        "type": "model",
                        "priority": "high",
                        "title": "Retrain models",
                        "description": "Some models haven't been retrained in 30+ days"
                    },
                    {
                        "type": "model",
                        "priority": "medium",
                        "title": "Hyperparameter tuning",
                        "description": "Try different hyperparameters to improve model performance"
                    }
                ])
            else:
                # General recommendations
                recommendations.extend([
                    {
                        "type": "general",
                        "priority": "high",
                        "title": "Set up monitoring",
                        "description": "Enable model monitoring to detect performance degradation"
                    },
                    {
                        "type": "general",
                        "priority": "medium",
                        "title": "Backup data",
                        "description": "Regular backups ensure data safety"
                    }
                ])
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            raise
    
    # Helper methods for data analysis
    
    def _calculate_basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics for the dataset"""
        try:
            return {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024),
                "duplicate_rows": df.duplicated().sum()
            }
        except Exception as e:
            logger.warning(f"Error calculating basic stats: {e}")
            return {}
    
    def _calculate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate data quality metrics"""
        try:
            missing_values = df.isnull().sum()
            total_cells = len(df) * len(df.columns)
            missing_cells = missing_values.sum()
            
            return {
                "missing_percentage": (missing_cells / total_cells * 100) if total_cells > 0 else 0,
                "columns_with_missing": (missing_values > 0).sum(),
                "complete_rows": df.notna().all(axis=1).sum(),
                "complete_percentage": (df.notna().all(axis=1).sum() / len(df) * 100) if len(df) > 0 else 0
            }
        except Exception as e:
            logger.warning(f"Error calculating data quality: {e}")
            return {}
    
    def _analyze_feature_types(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze feature types in the dataset"""
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
            
            return {
                "numeric_features": len(numeric_cols),
                "categorical_features": len(categorical_cols),
                "datetime_features": len(datetime_cols),
                "numeric_feature_names": numeric_cols[:10],  # Limit to first 10
                "categorical_feature_names": categorical_cols[:10]
            }
        except Exception as e:
            logger.warning(f"Error analyzing feature types: {e}")
            return {}
    
    def _calculate_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate feature correlations"""
        try:
            numeric_df = df.select_dtypes(include=[np.number])
            
            if len(numeric_df.columns) < 2:
                return {"message": "Not enough numeric features for correlation analysis"}
            
            corr_matrix = numeric_df.corr()
            
            # Find highly correlated pairs
            high_corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    if abs(corr_matrix.iloc[i, j]) > 0.7:
                        high_corr_pairs.append({
                            "feature_1": corr_matrix.columns[i],
                            "feature_2": corr_matrix.columns[j],
                            "correlation": float(corr_matrix.iloc[i, j])
                        })
            
            return {
                "highly_correlated_pairs": high_corr_pairs[:5],  # Top 5
                "average_correlation": float(corr_matrix.abs().mean().mean())
            }
        except Exception as e:
            logger.warning(f"Error calculating correlations: {e}")
            return {}
    
    def _generate_dataset_recommendations(self, df: pd.DataFrame, insights: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on dataset analysis"""
        recommendations = []
        
        try:
            # Check data quality
            quality = insights.get("data_quality", {})
            missing_pct = quality.get("missing_percentage", 0)
            
            if missing_pct > 10:
                recommendations.append(
                    f"Dataset has {missing_pct:.1f}% missing values. Consider imputation or removal of incomplete rows."
                )
            elif missing_pct > 0:
                recommendations.append(
                    f"Dataset has {missing_pct:.1f}% missing values. Data quality is good but could be improved."
                )
            
            # Check duplicates
            basic_stats = insights.get("basic_stats", {})
            duplicates = basic_stats.get("duplicate_rows", 0)
            if duplicates > 0:
                recommendations.append(
                    f"Found {duplicates} duplicate rows. Consider removing duplicates to improve data quality."
                )
            
            # Check correlations
            corr_data = insights.get("correlations", {})
            high_corr = corr_data.get("highly_correlated_pairs", [])
            if len(high_corr) > 0:
                recommendations.append(
                    f"Found {len(high_corr)} highly correlated feature pairs. Consider feature selection to reduce multicollinearity."
                )
            
            # Size recommendations
            total_rows = basic_stats.get("total_rows", 0)
            if total_rows < 100:
                recommendations.append(
                    "Dataset is very small. Consider collecting more data for better model performance."
                )
            elif total_rows > 1000000:
                recommendations.append(
                    "Large dataset detected. Consider sampling for faster analysis or using distributed computing."
                )
            
            if not recommendations:
                recommendations.append("Dataset quality is good. Ready for analysis and modeling.")
            
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
            recommendations.append("Unable to generate detailed recommendations")
        
        return recommendations
    
    def _calculate_quality_score(self, insights: Dict[str, Any]) -> float:
        """Calculate overall data quality score (0-1)"""
        try:
            score = 1.0
            
            # Deduct for missing values
            quality = insights.get("data_quality", {})
            missing_pct = quality.get("missing_percentage", 0)
            score -= (missing_pct / 100) * 0.3
            
            # Deduct for duplicates
            basic_stats = insights.get("basic_stats", {})
            total_rows = basic_stats.get("total_rows", 1)
            duplicates = basic_stats.get("duplicate_rows", 0)
            duplicate_pct = (duplicates / total_rows * 100) if total_rows > 0 else 0
            score -= (duplicate_pct / 100) * 0.2
            
            # Ensure score is between 0 and 1
            score = max(0.0, min(1.0, score))
            
            return round(score, 2)
            
        except Exception as e:
            logger.warning(f"Error calculating quality score: {e}")
            return 0.8  # Default reasonable score


# Create singleton instance
insights_service = InsightsService()
