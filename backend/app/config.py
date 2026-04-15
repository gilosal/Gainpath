from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://paceforge:paceforge@localhost:5432/paceforge"

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    # Auth
    secret_key: str = "changeme-secret-key-32chars-minimum"
    app_password: str = "changeme"

    # OpenRouter / AI
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ai_model: str = "anthropic/claude-sonnet-4-5"
    ai_fallback_model: str = "openai/gpt-4o-mini"
    ai_max_retries: int = 3
    ai_timeout: float = 90.0

    # App
    app_name: str = "PaceForge"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
