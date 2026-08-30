"""
Insights API Endpoints
Provides analytics and insights for datasets and models
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..utils.auth import get_current_user
from ..services.insights_service import insights_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class DatasetInsightsResponse(BaseModel):
    dataset_id: str
    insights: Dict[str, Any]
    recommendations: List[str]
    quality_score: float


class ModelInsightsResponse(BaseModel):
    model_id: str
    insights: Dict[str, Any]
    performance_trends: List[Dict[str, Any]]
    recommendations: List[str]


class SystemInsightsResponse(BaseModel):
    total_datasets: int
    total_models: int
    total_predictions: int
    system_health: Dict[str, Any]
    recommendations: List[str]


@router.get("/datasets/{dataset_id}", response_model=DatasetInsightsResponse)
async def get_dataset_insights(
    dataset_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive insights for a specific dataset

    Includes:
    - Data quality metrics
    - Statistical summary
    - Missing value analysis
    - Feature correlations
    - Recommendations for improvement
    """
    logger.info(f"Getting insights for dataset: {dataset_id}")

    try:
        insights = await insights_service.generate_dataset_insights(dataset_id)

        if not insights:
            raise HTTPException(
                status_code=404, detail=f"Dataset not found: {dataset_id}"
            )

        logger.info(f"Generated insights for dataset: {dataset_id}")
        return insights

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate dataset insights: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate insights: {str(e)}"
        )


@router.get("/models/{model_id}", response_model=ModelInsightsResponse)
async def get_model_insights(
    model_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive insights for a trained model

    Includes:
    - Performance metrics over time
    - Feature importance
    - Prediction distribution
    - Model drift detection
    - Recommendations for optimization
    """
    logger.info(f"Getting insights for model: {model_id}")

    try:
        insights = await insights_service.generate_model_insights(model_id)

        if not insights:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

        logger.info(f"Generated insights for model: {model_id}")
        return insights
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate model insights: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate insights: {str(e)}"
        )


@router.get("/system", response_model=SystemInsightsResponse)
async def get_system_insights(current_user: dict = Depends(get_current_user)):
    """
    Get system-wide insights and analytics

    Includes:
    - Overall system statistics
    - Resource usage
    - Performance trends
    - System health status
    - Recommendations for optimization
    """
    logger.info("Getting system insights")

    try:
        insights = await insights_service.generate_system_insights()
        logger.info("Generated system insights")
        return insights

    except Exception as e:
        logger.error(f"Failed to generate system insights: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate insights: {str(e)}"
        )


@router.get("/recommendations")
async def get_recommendations(
    context: Optional[str] = Query(
        None, description="Context for recommendations (dataset, model, system)"
    ),
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get personalized recommendations based on context

    Args:
        context: Type of recommendations (dataset, model, system)
        limit: Maximum number of recommendations to return
    """
    logger.info(f"Getting recommendations - context: {context}, limit: {limit}")

    try:
        recommendations = await insights_service.get_recommendations(
            context=context, limit=limit, user_id=current_user["id"]
        )

        return {"recommendations": recommendations, "count": len(recommendations)}

    except Exception as e:
        logger.error(f"Failed to generate recommendations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate recommendations: {str(e)}"
        )
