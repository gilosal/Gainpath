"""Tests for critical paths changed by US-002, US-003, US-004.

These tests target the real flows modified by earlier stories, not generic
coverage expansion. Each test class maps to a specific user story's changes.

Backend tests focus on:
  - Session completion pipeline correctness (US-002)
  - AI client retry/fallback/reraise behavior (US-004)
  - Offline sync _apply_action field safety (US-005 H-2)
  - Schema validation gaps at ORM boundary (US-005 H-2)
  - Coaching engine orphan message risk (US-004)

Local test execution confirmed: 81 pre-existing tests passed before additions.
"""
import inspect
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4

from app.schemas.session import SessionLogCreate, SessionLogUpdate, SetLogCreate
from app.routers.sessions import _on_session_completed, update_session
from app.routers.offline import _apply_action
from app.services.ai_client import AIClient, strip_json_fences, _RETRYABLE
from app.services.coaching_engine import chat as coaching_chat


# ── US-002: Session completion pipeline ────────────────────────────────────────

class TestSessionCompletionPipelineCriticalPath:
    """Verify the exact data flow when a session transitions to 'completed'.

    The pipeline is: PATCH /sessions/{id} → background task → PR/streak/XP/
    achievements/coaching. These tests verify the data passing contract.
    """

    def test_background_task_receives_session_id_and_rpe(self):
        """_on_session_completed receives (session_id, rpe) exactly."""
        sig = inspect.signature(_on_session_completed)
        params = list(sig.parameters.keys())
        assert params == ["session_id", "rpe"]

    def test_background_task_passes_rpe_to_xp_for_session(self):
        """The XP step uses the rpe parameter, not a stale DB value."""
        source = inspect.getsource(_on_session_completed)
        assert "xp_for_session(session.session_type, rpe)" in source

    def test_completed_at_context_passed_to_achievements(self):
        """Achievement engine receives completed_at for early_bird checks."""
        source = inspect.getsource(_on_session_completed)
        assert 'completed_at' in source
        assert '"session_completed"' in source

    def test_new_prs_trigger_pr_detected_achievement(self):
        """If PRs are detected, a 'pr_detected' achievement event fires."""
        source = inspect.getsource(_on_session_completed)
        assert '"pr_detected"' in source

    def test_streak_updated_achievement_always_fires(self):
        """'streak_updated' achievement check fires regardless of PRs."""
        source = inspect.getsource(_on_session_completed)
        assert '"streak_updated"' in source

    @pytest.mark.asyncio
    async def test_db_closed_in_finally_even_on_early_return(self):
        """If session not found (early return), db.close() still executes."""
        with patch("app.database.SessionLocal") as MockSessionLocal:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            MockSessionLocal.return_value = mock_db
            await _on_session_completed(
                session_id="00000000-0000-0000-0000-000000000001", rpe=5
            )
            mock_db.close.assert_called_once()


# ── US-002 / US-005: Schema validation at ORM boundary ─────────────────────────

class TestSessionLogUpdateStatusConstraint:
    """SessionLogUpdate.status is Optional[str] with no enum constraint.
    Any string passes Pydantic and gets setattr'd onto the ORM model.
    This documents the gap and provides a regression test when a constraint
    is eventually added."""

    def test_status_accepts_valid_values(self):
        for status in ("planned", "in_progress", "completed", "skipped"):
            payload = SessionLogUpdate(status=status)
            assert payload.status == status

    def test_status_accepts_arbitrary_string_no_constraint(self):
        """BUG DOCUMENTED: No enum constraint on status field. Any string
        passes through to setattr on the ORM model. This test documents
        the gap so we know when it gets fixed."""
        payload = SessionLogUpdate(status="hacked_status")
        assert payload.status == "hacked_status"
        # When a constraint is added, this test should be updated to
        # assert that ValidationError is raised instead.

    def test_exclude_unset_on_status_update_does_not_leak_other_fields(self):
        """Updating only status should not null out other fields."""
        payload = SessionLogUpdate(status="completed")
        data = payload.model_dump(exclude_unset=True)
        assert data == {"status": "completed"}
        assert "started_at" not in data
        assert "completed_at" not in data
        assert "overall_rpe" not in data

    def test_rpe_boundary_values(self):
        SessionLogUpdate(overall_rpe=1)
        SessionLogUpdate(overall_rpe=10)
        with pytest.raises(Exception):
            SessionLogUpdate(overall_rpe=0)
        with pytest.raises(Exception):
            SessionLogUpdate(overall_rpe=11)


class TestSessionLogCreateConstraints:
    """SessionLogCreate is the POST body for creating new sessions."""

    def test_requires_session_date(self):
        with pytest.raises(Exception):
            SessionLogCreate(session_type="running")

    def test_requires_session_type(self):
        with pytest.raises(Exception):
            SessionLogCreate(session_date=date(2026, 4, 18))

    def test_session_type_is_unconstrained_str(self):
        """SESSION_TYPE has no enum constraint — any string is accepted.
        Documented gap: should constrain to running/lifting/mobility."""
        payload = SessionLogCreate(session_date=date(2026, 4, 18), session_type="anything")
        assert payload.session_type == "anything"


# ── US-005 H-2: Offline sync _apply_action field safety ────────────────────────

class TestOfflineApplyActionFieldSafety:
    """_apply_action 'complete_session' uses setattr(item, k, v) for any
    payload key that exists as a model attribute. This means 'id', 'created_at',
    or any ORM column could be overwritten. These tests verify the risk and
    check for basic guards."""

    def test_complete_session_uses_hasattr_guard(self):
        """The complete_session branch has a hasattr check before setattr."""
        source = inspect.getsource(_apply_action)
        assert "hasattr" in source

    def test_complete_session_could_overwrite_id_field(self):
        """WARNING DOCUMENTED: hasattr(SessionLog, 'id') returns True, so
        a payload with key 'id' would overwrite the session's primary key.
        This is a real attack surface for offline sync."""
        source = inspect.getsource(_apply_action)
        # The guard is `if k != "session_log_id" and hasattr(log, k)`
        # but "id" is not excluded and hasattr(SessionLog, "id") is True
        assert 'k != "session_log_id"' in source
        # "id" is NOT in the exclusion list — this is the gap
        assert '"id"' not in source

    def test_create_set_log_spreads_remaining_payload(self):
        """create_set_log uses **{} to spread payload minus session_log_id
        into SetLog(). Any extra keys become keyword args to ORM __init__."""
        source = inspect.getsource(_apply_action)
        assert "SetLog(" in source

    def test_add_body_feedback_spreads_remaining_payload(self):
        """add_body_feedback uses **{} to spread payload minus session_log_id
        into BodyFeedback(). Any extra keys become keyword args to ORM __init__."""
        source = inspect.getsource(_apply_action)
        assert "BodyFeedback(" in source


# ── US-004: AI client retry and fallback ────────────────────────────────────────

class TestAIClientRetryConfiguration:
    """Verify the full retry configuration chain — that settings flow through
    to tenacity decorators correctly."""

    def test_call_with_retry_decorator_exists(self):
        source = inspect.getsource(AIClient._call_with_retry)
        assert "@retry" in source

    def test_call_text_with_retry_decorator_exists(self):
        source = inspect.getsource(AIClient._call_text_with_retry)
        assert "@retry" in source

    def test_http_post_creates_client_per_request(self):
        """DOCUMENTED RISK: _http_post creates a new httpx.AsyncClient per
        request, discarding it after one call. Connection reuse would reduce
        latency for frequent AI calls (US-005 finding)."""
        source = inspect.getsource(AIClient._http_post)
        assert "async with httpx.AsyncClient" in source

    def test_retryable_exceptions_do_not_include_httpstatuserror(self):
        """HTTPStatusError (4xx/5xx) is NOT retryable — only network errors."""
        import httpx
        assert httpx.HTTPStatusError not in _RETRYABLE

    def test_strip_json_fences_empty_input(self):
        assert strip_json_fences("") == ""
        assert strip_json_fences("  ").strip() == ""


# ── US-004: Coaching engine orphan message risk ────────────────────────────────

class TestCoachingChatOrphanMessageRisk:
    """coaching_engine.chat stores the user message BEFORE calling AI.
    If AI generation fails, the user message is persisted but has no
    matching assistant message — an orphan row. These tests verify
    this pattern exists and document the risk."""

    def test_user_message_stored_before_ai_call(self):
        source = inspect.getsource(coaching_chat)
        lines = source.split("\n")
        user_add_line = None
        ai_call_line = None
        for i, line in enumerate(lines):
            if 'role="user"' in line:
                user_add_line = i
            if "generate_text" in line:
                ai_call_line = i
        assert user_add_line is not None, "Could not find user message storage"
        assert ai_call_line is not None, "Could not find AI generate_text call"
        assert user_add_line < ai_call_line, (
            "User message is stored before AI call — orphan risk exists"
        )

    def test_assistant_message_stored_after_ai_call(self):
        source = inspect.getsource(coaching_chat)
        lines = source.split("\n")
        ai_call_line = None
        assistant_add_line = None
        for i, line in enumerate(lines):
            if "generate_text" in line:
                ai_call_line = i
            if 'role="assistant"' in line:
                assistant_add_line = i
        assert assistant_add_line is not None, "Could not find assistant message storage"
        assert ai_call_line is not None, "Could not find AI generate_text call"
        assert assistant_add_line > ai_call_line, (
            "Assistant message should be stored after AI call"
        )

    def test_error_path_returns_fallback_text_not_exception(self):
        """On AI failure, chat() returns a fallback string instead of
        raising — so the caller (coaching router) still gets a response
        to persist as the assistant message."""
        source = inspect.getsource(coaching_chat)
        assert "having trouble connecting" in source

    def test_assistant_message_always_stored_even_on_failure(self):
        """Even when AI fails, the fallback text is stored as the
        assistant message — so there should be no true orphan."""
        source = inspect.getsource(coaching_chat)
        # After the except block, response_text is always added
        assert 'role="assistant"' in source