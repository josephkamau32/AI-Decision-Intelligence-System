from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import secrets

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    app_name: str = "AI Decision Intelligence System API"
    debug_mode: bool = False
    version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: Optional[str] = None

    # Security
    secret_key: str = secrets.token_urlsafe(32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # File upload
    upload_dir: str = "uploads"
    max_upload_size: int = 100 * 1024 * 1024  # 100MB

    # MLflow
    mlflow_tracking_uri: str = "file:./mlops/experiments"
    mlflow_experiment_name: str = "AI Decision Intelligence"

    # OpenAI
    openai_api_key: str = ""

    # Celery and Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

    # Caching
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutes

    # CORS
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

settings = Settings()