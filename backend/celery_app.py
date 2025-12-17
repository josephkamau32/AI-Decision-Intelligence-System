from celery import Celery
from .utils.config import settings

celery_app = Celery(
    "ai_decision_intelligence",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["backend.tasks"]
)

celery_app.conf.update(
    result_expires=3600,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)