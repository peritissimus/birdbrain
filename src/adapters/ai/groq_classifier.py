"""Groq-based implementation of TweetClassifier."""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from src.core.entities import Tweet
from src.core.interfaces import TweetClassifier
from src.core.value_objects import ClassificationResult
from src.infrastructure.ai.groq_client import GroqClient, GroqConfig

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """You are a tweet classification assistant. Analyze the following tweet and provide:

1. **Topics**: 2-5 relevant topic tags (lowercase, hyphenated). Examples: machine-learning, python, web-dev, startup-advice, crypto, ai-tools, career-tips, productivity, design, javascript, data-science
2. **Summary**: A concise 1-2 sentence summary of the tweet's main point or value.

Tweet from @{author_handle}:
---
{text}
---

Respond in JSON format:
{{
  "topics": ["topic-1", "topic-2", "topic-3"],
  "summary": "Brief summary of the tweet content and why it might be valuable."
}}"""


class GroqTweetClassifier(TweetClassifier):
    """Groq-based implementation of TweetClassifier."""

    def __init__(self, config: GroqConfig):
        self.config = config
        self._client: Optional[GroqClient] = None

    async def __aenter__(self):
        self._client = GroqClient(self.config)
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.__aexit__(*args)
            self._client = None

    def is_available(self) -> bool:
        return bool(self.config.api_key)

    async def classify(self, tweet: Tweet) -> ClassificationResult:
        """Classify a single tweet."""
        if not self._client:
            raise RuntimeError("Classifier not initialized. Use async context manager.")

        if not tweet.text or not tweet.text.strip():
            return ClassificationResult(
                topics=["media-only"],
                summary="Tweet contains media without text content.",
                confidence=0.5,
                model_used=self.config.model,
                classified_at=datetime.utcnow(),
            )

        prompt = CLASSIFICATION_PROMPT.format(
            author_handle=tweet.author_handle or "unknown",
            text=tweet.text[:2000],
        )

        response = await self._client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"},
        )

        content = response["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        return ClassificationResult(
            topics=parsed.get("topics", [])[:5],
            summary=parsed.get("summary", "")[:500],
            confidence=0.9,
            model_used=self.config.model,
            classified_at=datetime.utcnow(),
        )

    async def classify_batch(
        self,
        tweets: List[Tweet],
        max_concurrent: int = 5,
    ) -> List[Tuple[Tweet, Optional[ClassificationResult], Optional[Exception]]]:
        """Classify multiple tweets with concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def classify_with_limit(
            tweet: Tweet,
        ) -> Tuple[Tweet, Optional[ClassificationResult], Optional[Exception]]:
            async with semaphore:
                try:
                    result = await self.classify(tweet)
                    return (tweet, result, None)
                except Exception as e:
                    logger.warning(f"Classification failed for {tweet.rest_id}: {e}")
                    return (tweet, None, e)

        tasks = [classify_with_limit(t) for t in tweets]
        return await asyncio.gather(*tasks)
