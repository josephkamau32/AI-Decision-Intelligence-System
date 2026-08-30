from fastapi import APIRouter
from datetime import datetime
from ..schemas.health import HealthResponse
from ..utils.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    logger.info("Health check endpoint called")
    return HealthResponse(
        status="healthy",
        version=settings.version,
        timestamp=datetime.utcnow().isoformat(),
    )
