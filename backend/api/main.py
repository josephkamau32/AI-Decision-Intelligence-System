import sys
sys.path.insert(0, '.')
sys.path.insert(0, '..')

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time

from .health import router as health_router
from .datasets import router as datasets_router
from .models import router as models_router
from .visualizations import router as visualizations_router
from .copilot import router as copilot_router
from ..utils.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Debug mode: {settings.debug_mode}")
    logger.info(f"API version: {settings.version}")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="High-performance API for AI Decision Intelligence System with MLOps capabilities",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.4f}s"
    )
    
    return response

# CORS middleware with proper configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins if not settings.debug_mode else ["*"],
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
    expose_headers=["X-Process-Time"]
)

# Gzip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path)
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Don't leak error details in production
    error_message = str(exc) if settings.debug_mode else "Internal server error"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": 500,
                "message": error_message,
                "path": str(request.url.path)
            }
        }
    )

# Root endpoint with API information
@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.version,
        "status": "running",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "health": f"{settings.api_v1_prefix}/health",
            "datasets": f"{settings.api_v1_prefix}/datasets",
            "models": f"{settings.api_v1_prefix}/models",
            "visualizations": f"{settings.api_v1_prefix}/visualizations"
        }
    }

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
    visualizations_router,
    prefix=f"{settings.api_v1_prefix}/visualizations",
    tags=["visualizations"]
)

app.include_router(
    copilot_router,
    prefix=f"{settings.api_v1_prefix}/copilot",
    tags=["copilot"]
)

# Health check with details
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.version,
        "timestamp": time.time()
    }