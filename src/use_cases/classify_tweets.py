"""Use case for classifying tweets."""

import logging
from typing import Dict, Any

from src.core.interfaces import BookmarkRepository, TweetClassifier

logger = logging.getLogger(__name__)


async def classify_pending_tweets(
    repo: BookmarkRepository,
    classifier: TweetClassifier,
    batch_size: int = 20,
) -> Dict[str, Any]:
    """
    Process pending tweets for classification.

    Returns:
        Stats dict with success/failure counts
    """
    if not classifier.is_available():
        logger.warning("Classifier not available - skipping classification")
        return {"skipped": True, "reason": "classifier_unavailable"}

    tweets = repo.get_unclassified_tweets(limit=batch_size)
    if not tweets:
        return {"processed": 0, "success": 0, "failed": 0}

    results = await classifier.classify_batch(tweets, max_concurrent=5)

    success_count = 0
    fail_count = 0

    for tweet, result, error in results:
        if result:
            repo.update_tweet_classification(tweet.rest_id, result)
            success_count += 1
            logger.info(f"Classified tweet {tweet.rest_id}: {result.topics}")
        else:
            repo.mark_classification_failed(
                tweet.rest_id,
                error_type=type(error).__name__ if error else "unknown",
                retry_count=tweet.classification_retry_count + 1,
            )
            fail_count += 1
            logger.warning(f"Failed to classify tweet {tweet.rest_id}: {error}")

    return {
        "processed": len(tweets),
        "success": success_count,
        "failed": fail_count,
    }
