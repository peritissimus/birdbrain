"""Low-level Groq API client using httpx for async HTTP."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class GroqConfig:
    api_key: str
    base_url: str = "https://api.groq.com/openai/v1"
    model: str = "llama-3.3-70b-versatile"
    timeout: float = 30.0
    max_retries: int = 3


class GroqClient:
    """Async HTTP client for Groq API with retry logic."""

    def __init__(self, config: GroqConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(self.config.timeout),
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 500,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Send chat completion request to Groq with retry logic."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = await self._client.post("/chat/completions", json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 429:
                    retry_after = float(
                        e.response.headers.get("retry-after", 2 ** (attempt + 1))
                    )
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                elif e.response.status_code >= 500:
                    delay = 2 ** (attempt + 1)
                    logger.warning(f"Server error {e.response.status_code}, retry in {delay}s")
                    await asyncio.sleep(delay)
                else:
                    raise
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    logger.warning("Timeout, retrying...")
                    await asyncio.sleep(1)
                else:
                    raise

        raise last_error or RuntimeError("Max retries exceeded")
