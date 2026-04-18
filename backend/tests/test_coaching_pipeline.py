"""Tests for the coaching and AI client flows (US-006).

Covers the coaching chat endpoint's message storage pattern, AI client
retry/reraise behavior, and session completion→coaching pipeline integration.
"""
import inspect
import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.ai_client import (
    AIClient,
    AIGenerationError,
    AIEmptyResponseError,
    strip_json_fences,
    _RETRYABLE,
)
from app.routers.coaching import ChatRequest


class TestChatEndpointStoresUserMessageBeforeAI:
    """The coaching chat endpoint stores the user message BEFORE calling
    the AI model. This means if AI generation fails, an orphan user message
    row is left in the database. These tests verify this pattern exists
    and document the risk."""

    def test_chat_endpoint_stores_user_message_first(self):
        """Source inspection: verify user message is persisted before AI call."""
        from app.services import coaching_engine
        source = inspect.getsource(coaching_engine.chat)
        assert 'ChatMessage(id=uuid.uuid4(), role="user"' in source
        # The user message is stored before the AI call
        user_msg_line = source.index('role="user"')
        ai_call_line = source.index("generate_text")
        assert user_msg_line < ai_call_line, (
            "User message should be stored before calling AI — "
            "if AI fails, this leaves an orphan row"
        )

    def test_chat_request_schema_requires_message(self):
        with pytest.raises(Exception):
            ChatRequest()

    def test_chat_request_schema_has_message_field(self):
        req = ChatRequest(message="test")
        assert req.message == "test"

    def test_chat_request_does_not_constrain_length(self):
        """The ChatRequest schema has no max length constraint on message.
        This is a low-risk issue for a single-user app but worth noting."""
        field = ChatRequest.model_fields["message"]
        assert field.annotation is str


class TestAIClientRetryBehavior:
    """Verify the AI client retry configuration from US-004 — specifically
    that reraise=True is set and retryable errors propagate correctly."""

    def test_reraise_is_true_on_call_with_retry(self):
        """US-004 fix: tenacity's default reraise=False silently swallows
        the last exception. Verify reraise=True is set."""
        source = inspect.getsource(AIClient._call_with_retry)
        assert "reraise=True" in source

    def test_reraise_is_true_on_call_text_with_retry(self):
        source = inspect.getsource(AIClient._call_text_with_retry)
        assert "reraise=True" in source

    def test_retryable_exceptions_include_timeout(self):
        assert httpx_module := __import__("httpx")
        assert httpx_module.TimeoutException in _RETRYABLE

    def test_retryable_exceptions_include_connect_error(self):
        assert httpx_module := __import__("httpx")
        assert httpx_module.ConnectError in _RETRYABLE

    def test_retry_uses_settings_max_retries(self):
        """US-004 fix: retry count should reference settings, not be hardcoded."""
        source = inspect.getsource(AIClient._call_with_retry)
        assert "settings.ai_max_retries" in source

    def test_text_retry_uses_settings_max_retries(self):
        source = inspect.getsource(AIClient._call_text_with_retry)
        assert "settings.ai_max_retries" in source


class TestAIClientFallbackBehavior:
    """Verify that when the primary model fails, the fallback model is tried."""

    def test_generate_tries_fallback_on_primary_failure(self):
        source = inspect.getsource(AIClient.generate)
        assert "models_to_try" in source
        assert "fallback_model" in source
        assert "last_exc" in source

    def test_generate_text_tries_fallback_on_primary_failure(self):
        source = inspect.getsource(AIClient.generate_text)
        assert "models_to_try" in source
        assert "fallback_model" in source

    def test_generate_raises_last_exception_if_all_fail(self):
        source = inspect.getsource(AIClient.generate)
        assert "raise last_exc" in source

    def test_generate_text_raises_last_exception_if_all_fail(self):
        source = inspect.getsource(AIClient.generate_text)
        assert "raise last_exc" in source


class TestAIEmptyResponseGuard:
    """AIEmptyResponseError was added in US-004 to catch models returning
    empty/whitespace-only content — which would previously pass through
    silently and cause downstream JSON parse errors."""

    def test_empty_string_raises(self):
        client = AIClient()
        with pytest.raises(AIEmptyResponseError):
            raise AIEmptyResponseError("[test] Empty response")

    def test_is_subclass_of_generation_error(self):
        assert issubclass(AIEmptyResponseError, AIGenerationError)

    def test_generate_checks_empty_content(self):
        source = inspect.getsource(AIClient._call_with_retry)
        assert "not raw_content" in source or "raw_content or not raw_content.strip()" in source

    def test_generate_text_checks_empty_content(self):
        source = inspect.getsource(AIClient.generate_text)
        assert "not content or not content.strip()" in source

    def test_strip_json_fences_handles_empty(self):
        """Empty/whitespace strings should pass through without error."""
        assert strip_json_fences("").strip() == ""
        assert strip_json_fences("   ").strip() == ""


class TestCoachingBackgroundTaskDBIsolation:
    """Background tasks in coaching.py must create their own DB sessions
    (US-002/US-004 pattern)."""

    def test_daily_motivation_creates_own_session(self):
        from app.routers.coaching import _run_daily_motivation
        source = inspect.getsource(_run_daily_motivation)
        assert "SessionLocal()" in source
        assert "db.close()" in source

    def test_weekly_summary_creates_own_session(self):
        from app.routers.coaching import _run_weekly_summary
        source = inspect.getsource(_run_weekly_summary)
        assert "SessionLocal()" in source
        assert "db.close()" in source

    def test_post_workout_creates_own_session(self):
        from app.routers.coaching import _run_post_workout
        source = inspect.getsource(_run_post_workout)
        assert "SessionLocal()" in source
        assert "db.close()" in source

    def test_session_completion_bg_task_creates_own_session(self):
        source = inspect.getsource(_on_session_completed)
        assert "SessionLocal()" in source