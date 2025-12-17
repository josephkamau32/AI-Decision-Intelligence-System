import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .health import router as health_router
from .datasets import router as datasets_router
from .models import router as models_router
from .copilot import router as copilot_router
from .visualizations import router as visualizations_router
from .monitoring import router as monitoring_router
from ..utils.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="API for AI Decision Intelligence System",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include routers
app.include_router(
    health_router,
    prefix=settings.api_v1_prefix,
    tags=["health"]
)
app.include_router(
    datasets_router,
    prefix=f"{settings.api_v1_prefix}/datasets",
    tags=["datasets"]
)
app.include_router(
    models_router,
    prefix=f"{settings.api_v1_prefix}/models",
    tags=["models"]
)
app.include_router(
    copilot_router,
    prefix=f"{settings.api_v1_prefix}/copilot",
    tags=["copilot"]
)
app.include_router(
    visualizations_router,
    prefix=f"{settings.api_v1_prefix}/visualizations",
    tags=["visualizations"]
)
app.include_router(
    monitoring_router,
    prefix=f"{settings.api_v1_prefix}/monitoring",
    tags=["monitoring"]
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting AI Decision Intelligence API")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down AI Decision Intelligence API")