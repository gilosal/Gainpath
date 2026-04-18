import logging
import os

from pydantic_settings import BaseSettings
from pydantic import field_validator

logger = logging.getLogger(__name__)

_INSECURE_DEFAULTS = {
    "app_password": "changeme",
    "secret_key": "changeme-secret-key-32chars-minimum",
}


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://paceforge:paceforge@localhost:5432/paceforge"

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @field_validator("secret_key", mode="after")
    @classmethod
    def warn_insecure_secret_key(cls, v: str) -> str:
        if v == _INSECURE_DEFAULTS["secret_key"]:
            logger.warning(
                "secret_key is set to the insecure default. "
                "Set SECRET_KEY in your environment or .env file."
            )
        return v

    # Auth
    secret_key: str = "changeme-secret-key-32chars-minimum"
    app_password: str = "changeme"

    @field_validator("app_password", mode="after")
    @classmethod
    def reject_insecure_password(cls, v: str) -> str:
        if v == _INSECURE_DEFAULTS["app_password"]:
            env = os.getenv("APP_ENV", "development")
            if env != "development":
                raise ValueError(
                    "app_password must be changed from the default in non-development "
                    "environments. Set APP_PASSWORD in your environment or .env file."
                )
            logger.warning(
                "app_password is set to the insecure default 'changeme'. "
                "Set APP_PASSWORD in your environment or .env file before deploying."
            )
        return v

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
