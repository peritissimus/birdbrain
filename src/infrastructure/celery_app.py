"""Celery application configuration."""

from celery import Celery
from src.infrastructure.config import get_settings

settings = get_settings()

celery_app = Celery(
    "birdbrain",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=["src.infrastructure.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
