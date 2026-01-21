import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///birdbrain.db"
    server_port: int = 8787
    server_host: str = "127.0.0.1"
    auth_dir: str = os.path.join(os.getcwd(), "auth_storage")

    # Redis/Celery Configuration
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None

    # Groq AI Configuration
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_timeout: float = 30.0
    groq_max_concurrent: int = 5

    # Classification behavior
    classification_enabled: bool = True
    classification_batch_size: int = 20
    classification_max_retries: int = 3

    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url

    def get_auth_path(self, username: str) -> str:
        os.makedirs(self.auth_dir, exist_ok=True)
        return os.path.join(self.auth_dir, f"{username}_state.json")


@lru_cache
def get_settings() -> Settings:
    """Returns cached settings instance."""
    return Settings()
