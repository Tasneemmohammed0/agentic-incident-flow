from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Agentic Incident Flow"
    app_version: str = "1.0.0"
    debug: bool = False

    servicenow_username: str
    servicenow_password: str
    servicenow_instance_url: HttpUrl

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
