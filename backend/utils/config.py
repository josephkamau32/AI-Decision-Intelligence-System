from pydantic import Field, AliasChoices, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Union
import json
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    app_name: str = "Decisera API"
    debug_mode: bool = Field(
        default=False,
        validation_alias=AliasChoices("DEBUG_MODE", "DEBUG", "debug_mode", "debug"),
        description="Enable debug mode (stack traces, open CORS for local testing)",
    )
    version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: Optional[str] = None

    # Security & JWT
    jwt_secret_key: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    allowed_origins: Union[List[str], str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://decisera.vercel.app",
        ],
        validation_alias=AliasChoices(
            "ALLOWED_ORIGINS", "allowed_origins", "CORS_ORIGINS", "cors_origins"
        ),
        description="Allowed origins for CORS requests",
    )

    @field_validator("allowed_origins")
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(o).strip() for o in parsed if str(o).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # File upload
    upload_dir: str = "uploads"
    max_upload_size: int = 100 * 1024 * 1024  # 100MB

    # MLflow
    mlflow_tracking_uri: str = "file:./mlops/experiments"
    mlflow_experiment_name: str = "Decisera"

    # OpenAI
    openai_api_key: str = ""

    # Google Gemini
    google_api_key: str = ""

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

    # Default Admin User (for development only)
    allow_default_admin: bool = (
        False  # Gate default admin creation behind explicit flag
    )

    # CORS
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]


settings = Settings()
