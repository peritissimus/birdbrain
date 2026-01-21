"""Celery tasks for background processing."""

import asyncio
import logging

from src.infrastructure.celery_app import celery_app
from src.infrastructure.config import get_settings
from src.infrastructure.database import SessionLocal
from src.infrastructure.ai.groq_client import GroqConfig
from src.adapters.db.repository import SqlAlchemyRepository
from src.adapters.ai.groq_classifier import GroqTweetClassifier
from src.use_cases.classify_tweets import classify_pending_tweets

logger = logging.getLogger(__name__)


async def _run_classification(batch_size: int) -> dict:
    """Async classification runner."""
    settings = get_settings()

    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY not configured, skipping classification")
        return {"skipped": True, "reason": "no_api_key"}

    config = GroqConfig(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        base_url=settings.groq_base_url,
        timeout=settings.groq_timeout,
    )

    db = SessionLocal()
    try:
        repo = SqlAlchemyRepository(db)
        classifier = GroqTweetClassifier(config)

        async with classifier:
            result = await classify_pending_tweets(repo, classifier, batch_size)
            logger.info(f"Classification complete: {result}")
            return result
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def classify_tweets_task(self, batch_size: int = 20):
    """
    Celery task for tweet classification.

    Uses asyncio.run() to execute the async classification in a sync context.
    Retries up to 3 times on failure with 60s delay.
    """
    try:
        logger.info(f"Starting classification task (batch_size={batch_size})")
        result = asyncio.run(_run_classification(batch_size))
        return result
    except Exception as exc:
        logger.error(f"Classification task failed: {exc}")
        raise self.retry(exc=exc)
