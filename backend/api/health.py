import os
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
    commit_sha = os.getenv(
        "RENDER_GIT_COMMIT",
        os.getenv("GIT_COMMIT", os.getenv("GITHUB_SHA", "dev")),
    )
    return HealthResponse(
        status="healthy",
        version=settings.version,
        timestamp=datetime.utcnow().isoformat(),
        commit=commit_sha,
        environment=getattr(settings, "environment", "production"),
    )
