"""
Configuration loaded from environment variables.
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Required
    anthropic_api_key: str = ""
    telegram_bot_token: str = ""

    # Optional
    tavily_api_key: str = ""
    log_level: str = "INFO"
    allowed_user_ids: str = ""  # comma-separated

    # Model configuration
    router_model: str = "claude-haiku-4-5-20251001"
    agent_model: str = "claude-sonnet-4-5-20250929"

    @property
    def allowed_users(self) -> set[int]:
        """Parse allowed user IDs into a set of integers."""
        if not self.allowed_user_ids:
            return set()
        return {int(uid.strip()) for uid in self.allowed_user_ids.split(",") if uid.strip()}

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
