from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "AI Decision Intelligence System API"
    debug: bool = False
    version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: Optional[str] = None

    # JWT
    secret_key: str = "your-secret-key-here"  # Change in production
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

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

    class Config:
        env_file = ".env"

settings = Settings()