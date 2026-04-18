"""Tests for backend config validation (US-001, US-006).

Covers the Pydantic validators that reject insecure defaults in production
and warn in development mode. Uses monkeypatch to isolate each test from
environment variable pollution.
"""
import os
import pytest
from pydantic import ValidationError

from app.config import Settings, _INSECURE_DEFAULTS


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove all Settings env vars between tests so they don't bleed."""
    for key in list(os.environ):
        if key.upper() in {
            "APP_ENV", "APP_PASSWORD", "SECRET_KEY",
            "DATABASE_URL", "OPENROUTER_API_KEY", "OPENROUTER_BASE_URL",
            "AI_MODEL", "AI_FALLBACK_MODEL", "AI_MAX_RETRIES", "AI_TIMEOUT",
            "APP_NAME", "CORS_ORIGINS",
        }:
            monkeypatch.delenv(key, raising=False)


class TestSettingsValidation:
    """Config startup validation — the gate that prevents deploying with
    default credentials in production environments."""

    def test_development_allows_default_password(self):
        """In development mode, the default password is allowed (with warning)."""
        s = Settings(APP_ENV="development", APP_PASSWORD=_INSECURE_DEFAULTS["app_password"])
        assert s.app_password == _INSECURE_DEFAULTS["app_password"]

    def test_production_rejects_default_password(self):
        """In non-development environments, the default password must be changed."""
        with pytest.raises(ValidationError, match="app_password"):
            Settings(APP_ENV="production", APP_PASSWORD=_INSECURE_DEFAULTS["app_password"])

    def test_staging_rejects_default_password(self):
        with pytest.raises(ValidationError, match="app_password"):
            Settings(APP_ENV="staging", APP_PASSWORD=_INSECURE_DEFAULTS["app_password"])

    def test_production_accepts_custom_password(self):
        s = Settings(APP_ENV="production", APP_PASSWORD="my-secure-password-2024")
        assert s.app_password == "my-secure-password-2024"

    def test_postgres_url_normalization(self):
        """postgres:// URLs are normalized to postgresql:// at the Pydantic level."""
        s = Settings(
            APP_ENV="development",
            APP_PASSWORD="test",
            DATABASE_URL="postgres://user:pass@localhost:5432/db",
        )
        assert s.database_url.startswith("postgresql://")

    def test_database_url_passthrough(self):
        url = "postgresql://user:pass@localhost:5432/db"
        s = Settings(APP_ENV="development", APP_PASSWORD="test", DATABASE_URL=url)
        assert s.database_url == url

    def test_secret_key_default_triggers_warning(self, caplog):
        """The insecure default secret_key logs a warning but does not raise."""
        with caplog.at_level("WARNING"):
            s = Settings(
                APP_ENV="development",
                APP_PASSWORD="test",
                SECRET_KEY=_INSECURE_DEFAULTS["secret_key"],
            )
        assert s.secret_key == _INSECURE_DEFAULTS["secret_key"]
        assert any("secret_key" in r.getMessage() and "insecure" in r.getMessage() for r in caplog.records)

    def test_ai_max_retries_configurable(self):
        s = Settings(APP_ENV="development", APP_PASSWORD="test")
        assert s.ai_max_retries == 3

    def test_ai_timeout_configurable(self):
        s = Settings(APP_ENV="development", APP_PASSWORD="test")
        assert s.ai_timeout == 90.0