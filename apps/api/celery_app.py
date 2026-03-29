"""
Celery application — async task queue backed by Redis (Upstash free tier).
Used by: ocr-module (background OCR), agent-module (AI agent tasks).
"""
from celery import Celery
from core.config import get_settings

settings = get_settings()

celery = Celery(
    "ai_dd",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks from all modules
celery.autodiscover_tasks([
    "modules.ocr",
    "modules.agent",
])
