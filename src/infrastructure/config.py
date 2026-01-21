import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///birdbrain.db"
    server_port: int = 8000
    server_host: str = "127.0.0.1"
    auth_dir: str = os.path.join(os.getcwd(), "auth_storage")

    def get_auth_path(self, username: str) -> str:
        os.makedirs(self.auth_dir, exist_ok=True)
        return os.path.join(self.auth_dir, f"{username}_state.json")


@lru_cache
def get_settings() -> Settings:
    """Returns cached settings instance."""
    return Settings()
