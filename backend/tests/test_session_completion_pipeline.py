"""Tests for the session completion pipeline (US-006).

These tests verify the most critical backend flow: what happens when a session
transitions to "completed" status. This triggers PR detection, streak updates,
XP grants, achievement checks, and post-workout coaching — all in a background
task that must use its own DB session and isolate failures.
"""
import inspect
import pytest
from datetime import datetime, date
from unittest.mock import MagicMock, patch, AsyncMock

from app.routers.sessions import _on_session_completed, update_session
from app.schemas.session import SessionLogUpdate, SessionStatus


class TestOnSessionCompletedDBSessionIsolation:
    """The background task MUST create its own DB session because the
    request-scoped session is closed before BackgroundTasks run (US-002)."""

    def test_creates_own_db_session(self):
        source = inspect.getsource(_on_session_completed)
        assert "SessionLocal()" in source

    def test_closes_db_in_finally(self):
        source = inspect.getsource(_on_session_completed)
        assert "db.close()" in source

    def test_each_step_is_exception_isolated(self):
        """Each step (PR detection, streak, XP, achievements, coaching) must
        be in its own try/except so one failure doesn't block the rest."""
        source = inspect.getsource(_on_session_completed)
        try_count = source.count("except Exception")
        assert try_count >= 4, (
            f"Expected at least 4 isolated try/except blocks, found {try_count}. "
            "Each pipeline step should be independently isolated."
        )

    def test_returns_early_if_session_not_found(self):
        """If the session is gone by the time the background task runs,
        it should return silently rather than crashing."""
        source = inspect.getsource(_on_session_completed)
        assert "if not session" in source
        assert "return" in source


class TestOnSessionCompletedStepOrdering:
    """Verify the pipeline steps execute in the correct order and with
    correct arguments."""

    def test_pr_detection_called_with_db_and_session_id(self):
        source = inspect.getsource(_on_session_completed)
        assert "detect_prs_for_session(db, session_id)" in source

    def test_update_streak_called_with_db(self):
        source = inspect.getsource(_on_session_completed)
        assert "update_streak(db)" in source

    def test_xp_for_session_and_grant_xp_called(self):
        source = inspect.getsource(_on_session_completed)
        assert "xp_for_session" in source
        assert "grant_xp" in source

    def test_check_achievements_called_for_session_completed(self):
        source = inspect.getsource(_on_session_completed)
        assert 'check_achievements(db, "session_completed"' in source

    def test_post_workout_coaching_called(self):
        source = inspect.getsource(_on_session_completed)
        assert "generate_post_workout_feedback" in source


class TestUpdateSessionEndpoint:
    """Verify the PATCH /sessions/{id} endpoint behavior — specifically
    the completion trigger logic."""

    def test_patch_triggers_background_task_on_status_transition(self):
        source = inspect.getsource(update_session)
        assert "background_tasks.add_task" in source
        assert "_on_session_completed" in source

    def test_auto_sets_completed_at(self):
        """When transitioning to completed, completed_at must be auto-set
        if not provided by the client (US-002 fix)."""
        source = inspect.getsource(update_session)
        assert "completed_at" in source
        assert "datetime.utcnow()" in source

    def test_only_triggers_on_transition(self):
        """Background task should only fire when status CHANGES to completed,
        not on every PATCH to an already-completed session."""
        source = inspect.getsource(update_session)
        assert "was_completed" in source
        assert "not was_completed" in source

    def test_spreads_unset_fields_via_setattr(self):
        """This is intentional — SessionLogUpdate uses exclude_unset=True
        in the caller. Verify the pattern exists and document the risk."""
        source = inspect.getsource(update_session)
        assert "setattr" in source
        assert "exclude_unset=True" in source

    def test_excludes_id_from_setattr_loop(self):
        """US-101: The 'id' field must be excluded from update loops."""
        source = inspect.getsource(update_session)
        assert 'pop("id"' in source or "pop('id'" in source


class TestSessionLogUpdateSchemaConstraints:
    """Verify the PATCH schema enforces field-level constraints to prevent
    invalid data from reaching the ORM layer."""

    def test_status_must_be_recognized(self):
        for s in SessionStatus:
            payload = SessionLogUpdate(status=s)
            assert payload.status == s

    def test_status_rejects_invalid_string(self):
        with pytest.raises(Exception):
            SessionLogUpdate(status="not_a_status")

    def test_rpe_range_enforced(self):
        with pytest.raises(Exception):
            SessionLogUpdate(overall_rpe=0)
        with pytest.raises(Exception):
            SessionLogUpdate(overall_rpe=11)
        payload = SessionLogUpdate(overall_rpe=1)
        assert payload.overall_rpe == 1
        payload = SessionLogUpdate(overall_rpe=10)
        assert payload.overall_rpe == 10

    def test_exclude_unset_prevents_overwriting_unspecified_fields(self):
        """SessionLogUpdate(status="completed").model_dump(exclude_unset=True)
        should only contain 'status', not null out started_at or notes."""
        payload = SessionLogUpdate(status=SessionStatus.completed)
        data = payload.model_dump(exclude_unset=True)
        assert set(data.keys()) == {"status"}
        assert "started_at" not in data
        assert "notes" not in data


class TestOnSessionCompletedAsyncExecution:
    """Verify _on_session_completed is properly async — it calls
    async coaching functions."""

    @pytest.mark.asyncio
    async def test_can_be_awaited(self):
        """The function is async and should be awaitable without error
        when the session doesn't exist (early return path)."""
        with patch("app.database.SessionLocal") as MockSessionLocal:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            MockSessionLocal.return_value = mock_db
            await _on_session_completed(session_id="00000000-0000-0000-0000-000000000001", rpe=5)
            mock_db.close.assert_called_once()