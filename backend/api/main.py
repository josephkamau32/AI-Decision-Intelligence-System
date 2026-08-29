import logging
import secrets
import string
import random
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

# Configure logging early
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ML-dependent imports with optional loading
try:
    from .models import router as models_router
    from .visualizations import router as visualizations_router
    ML_AVAILABLE = True
    logger.info("ML modules loaded successfully")
except ImportError as e:
    logger.warning(f"ML modules not available: {e}. ML endpoints will be disabled.")
    models_router = None
    visualizations_router = None
    ML_AVAILABLE = False

from .copilot import router as copilot_router
from .users import router as users_router
from .insights import router as insights_router
from ..utils.config import settings
from ..monitoring.prometheus_metrics import setup_prometheus_metrics
from ..utils.error_handlers import (
    DeciseraException,
    handle_decisera_exception,
    handle_http_exception,
    handle_generic_exception
)


def generate_secure_demo_password(length: int = 16) -> str:
    """
    Generate a secure random password that GUARANTEES meeting all validation requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character from [!@#$%^&*(),.?":{}|<>]
    
    This ensures registration will never fail due to weak password validation.
    """
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special_chars = "!@#$%^&*()"  # From the allowed set in validators.py
    
    # Start with ONE of each required character type to guarantee compliance
    password_chars = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special_chars)
    ]
    
    # Fill remaining length with random choices from all valid character classes
    all_chars = uppercase + lowercase + digits + special_chars
    for _ in range(length - 4):
        password_chars.append(secrets.choice(all_chars))
    
    # Shuffle to avoid predictable patterns (e.g., always Aa0!)
    random.shuffle(password_chars)
    
    return ''.join(password_chars)


# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Debug mode: {settings.debug_mode}")
    logger.info(f"API version: {settings.version}")
    
    # Run production validation checks
    try:
        from ..utils.production_checks import run_startup_validation
        is_valid, validator = run_startup_validation()
        if not is_valid:
            logger.warning("Production validation found issues. Please check the logs.")
        else:
            logger.info("✓ Production validation passed")
    except Exception as e:
        logger.warning(f"Could not run production validation: {e}")
    
    # Create default demo user if enabled
    if settings.allow_default_admin:
        # LOUD WARNING: This should never be enabled in production or shared environments
        warning_banner = """
╔════════════════════════════════════════════════════════════════╗
║  ⚠️  WARNING: DEFAULT ADMIN ACCOUNT ENABLED ⚠️                  ║
║                                                                ║
║  A default admin account will be created automatically.        ║
║  This setting should ONLY be used in local development.        ║
║                                                                ║
║  NEVER enable this in:                                         ║
║  - Shared environments                                         ║
║  - Staging or production servers                               ║
║  - Code repositories or CI/CD pipelines                         ║
║                                                                ║
║  To disable, set: ALLOW_DEFAULT_ADMIN=false                   ║
╚════════════════════════════════════════════════════════════════╝
        """
        logger.warning(warning_banner)
        
        try:
            from ..utils.auth import users_db, register_user
            if len(list(users_db.keys())) == 0:
                # Generate a secure random password that GUARANTEES validation compliance
                random_password = generate_secure_demo_password()
                logger.info("Creating default demo user...")
                register_user(
                    username="demo",
                    email="demo@decisera.com",
                    password=random_password,
                    role="admin"
                )
                # Log the credentials clearly and ONLY ONCE so the developer can capture them
                logger.warning("=" * 70)
                logger.warning("DEFAULT DEMO ACCOUNT CREDENTIALS (will not be shown again)")
                logger.warning(f"  Username: demo")
                logger.warning(f"  Email:    demo@decisera.com")
                logger.warning(f"  Password: {random_password}")
                logger.warning("=" * 70)
            else:
                logger.info("Users database already populated; skipping default admin creation.")
        except Exception as e:
            logger.error(f"Could not create default admin user: {e}", exc_info=True)
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="High-performance API for Decisera - AI Decision Intelligence Platform with MLOps capabilities",
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
# Register custom error handlers
app.add_exception_handler(DeciseraException, handle_decisera_exception)
app.add_exception_handler(HTTPException, handle_http_exception)
app.add_exception_handler(Exception, handle_generic_exception)

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


# Conditionally include ML-dependent routers
if ML_AVAILABLE and models_router:
    app.include_router(
        models_router,
        prefix=f"{settings.api_v1_prefix}/models",
        tags=["models"]
    )
    logger.info("✓ Models router enabled")
else:
    logger.info("Models router disabled (ML dependencies not available)")

if ML_AVAILABLE and visualizations_router:
    app.include_router(
        visualizations_router,
        prefix=f"{settings.api_v1_prefix}/visualizations",
        tags=["visualizations"]
    )
    logger.info("✓ Visualizations router enabled")
else:
    logger.info("Visualizations router disabled (ML dependencies not available)")


app.include_router(
    copilot_router,
    prefix=f"{settings.api_v1_prefix}/copilot",
    tags=["copilot"]
)

app.include_router(
    users_router,
    tags=["authentication"]
)

app.include_router(
    insights_router,
    prefix=f"{settings.api_v1_prefix}/insights",
    tags=["insights"]
)

# Setup Prometheus metrics
setup_prometheus_metrics(app)

# Health check with details
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.version,
        "timestamp": time.time()
    }