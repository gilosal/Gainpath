"""Tests for the session completion pipeline and offline sync (US-002, US-005, US-006).

Covers the critical path where a session transitions to "completed" status,
schema validation constraints, and offline sync action boundary checks.
"""
import inspect
import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from app.schemas.session import (
    SessionLogUpdate, BodyFeedbackCreate, SetLogCreate,
    SessionStatus, SessionType, SetType, Feeling,
    VALID_STATUS_TRANSITIONS, validate_status_transition,
)


class TestSessionLogUpdateSchema:
    """SessionLogUpdate is the PATCH payload — the primary user-facing
    mutation endpoint. Validates that the schema enforces constraints."""

    def test_status_only_update(self):
        payload = SessionLogUpdate(status=SessionStatus.completed)
        data = payload.model_dump(exclude_unset=True)
        assert data["status"] == SessionStatus.completed
        assert "started_at" not in data
        assert "notes" not in data

    def test_rpe_validation_range(self):
        with pytest.raises(Exception):
            SessionLogUpdate(overall_rpe=0)
        with pytest.raises(Exception):
            SessionLogUpdate(overall_rpe=11)
        payload = SessionLogUpdate(overall_rpe=5)
        assert payload.overall_rpe == 5

    def test_completed_at_is_optional(self):
        """The backend auto-sets completed_at when status transitions
        to 'completed' (US-002 fix)."""
        payload = SessionLogUpdate(status=SessionStatus.completed)
        assert payload.completed_at is None

    def test_severity_validation_range(self):
        with pytest.raises(Exception):
            BodyFeedbackCreate(body_area="knees", feeling=Feeling.tight, severity=0)
        with pytest.raises(Exception):
            BodyFeedbackCreate(body_area="knees", feeling=Feeling.tight, severity=6)
        fb = BodyFeedbackCreate(body_area="knees", feeling=Feeling.tight, severity=3)
        assert fb.severity == 3

    def test_set_log_rpe_validation_range(self):
        with pytest.raises(Exception):
            SetLogCreate(exercise_name="squat", rpe=0)
        with pytest.raises(Exception):
            SetLogCreate(exercise_name="squat", rpe=11)
        s = SetLogCreate(exercise_name="squat", rpe=8)
        assert s.rpe == 8

    def test_status_field_allows_expected_values(self):
        for status in SessionStatus:
            payload = SessionLogUpdate(status=status)
            assert payload.status == status

    def test_status_field_rejects_invalid_value(self):
        with pytest.raises(Exception):
            SessionLogUpdate(status="not_a_status")

    def test_session_type_uses_enum(self):
        for st in SessionType:
            from app.schemas.session import SessionLogCreate
            obj = SessionLogCreate(session_date="2025-01-01", session_type=st)
            assert obj.session_type == st

    def test_session_type_rejects_invalid_value(self):
        with pytest.raises(Exception):
            from app.schemas.session import SessionLogCreate
            SessionLogCreate(session_date="2025-01-01", session_type="swimming")

    def test_feeling_uses_enum(self):
        for f in Feeling:
            fb = BodyFeedbackCreate(body_area="knees", feeling=f)
            assert fb.feeling == f

    def test_feeling_rejects_invalid_value(self):
        with pytest.raises(Exception):
            BodyFeedbackCreate(body_area="knees", feeling="amazing")

    def test_set_type_uses_enum(self):
        for st in SetType:
            s = SetLogCreate(exercise_name="squat", set_type=st)
            assert s.set_type == st

    def test_notes_field_accepts_text(self):
        payload = SessionLogUpdate(notes="Felt strong today")
        assert payload.notes == "Felt strong today"

    def test_actual_distance_is_float(self):
        payload = SessionLogUpdate(actual_distance=5.2)
        assert payload.actual_distance == 5.2

    def test_actual_duration_is_int_seconds(self):
        payload = SessionLogUpdate(actual_duration=1800)
        assert payload.actual_duration == 1800


class TestStatusTransitionValidator:
    """Validate that status transition guards prevent invalid transitions
    (US-101)."""

    def test_valid_transition_planned_to_in_progress(self):
        validate_status_transition("planned", SessionStatus.in_progress)

    def test_valid_transition_planned_to_skipped(self):
        validate_status_transition("planned", SessionStatus.skipped)

    def test_valid_transition_in_progress_to_completed(self):
        validate_status_transition("in_progress", SessionStatus.completed)

    def test_valid_transition_in_progress_to_skipped(self):
        validate_status_transition("in_progress", SessionStatus.skipped)

    def test_invalid_transition_completed_to_planned(self):
        with pytest.raises(ValueError, match="Invalid status transition"):
            validate_status_transition("completed", SessionStatus.planned)

    def test_invalid_transition_completed_to_in_progress(self):
        with pytest.raises(ValueError, match="Invalid status transition"):
            validate_status_transition("completed", SessionStatus.in_progress)

    def test_invalid_transition_skipped_to_completed(self):
        with pytest.raises(ValueError, match="Invalid status transition"):
            validate_status_transition("skipped", SessionStatus.completed)

    def test_valid_transition_skipped_to_planned(self):
        validate_status_transition("skipped", SessionStatus.planned)

    def test_unknown_current_status_allows_any_transition(self):
        validate_status_transition("unknown_status", SessionStatus.completed)


class TestSessionCompletionContract:
    """Verify the _on_session_completed contract — specifically that it's
    async, accepts the right params, and each step is isolated (US-002)."""

    def test_on_session_completed_is_async(self):
        from app.routers.sessions import _on_session_completed
        assert inspect.iscoroutinefunction(_on_session_completed)

    def test_on_session_completed_signature(self):
        from app.routers.sessions import _on_session_completed
        sig = inspect.signature(_on_session_completed)
        params = list(sig.parameters.keys())
        assert "session_id" in params
        assert "rpe" in params

    def test_patch_endpoint_triggers_background_task(self):
        """Verify update_session adds BG task on completed transition."""
        import inspect
        from app.routers.sessions import update_session
        source = inspect.getsource(update_session)
        assert "background_tasks.add_task" in source
        assert "_on_session_completed" in source

    def test_completed_at_auto_set_in_source(self):
        """Verify the code that auto-sets completed_at (US-002 fix)."""
        import inspect
        from app.routers.sessions import update_session
        source = inspect.getsource(update_session)
        assert "completed_at" in source
        assert "datetime.utcnow()" in source


class TestOfflineSyncApplyAction:
    """Offline sync's _apply_action is a known risk (US-005 H-2).
    These tests verify the action-type allowlist and required field checks."""

    def test_unknown_action_raises(self):
        from app.routers.offline import _apply_action
        item = MagicMock()
        item.action_type = "delete_everything"
        item.payload = {"session_log_id": str(uuid4())}
        db = MagicMock()
        with pytest.raises(ValueError, match="Unknown action type"):
            _apply_action(item, db)

    def test_create_set_log_requires_session_id(self):
        from app.routers.offline import _apply_action
        item = MagicMock()
        item.action_type = "create_set_log"
        item.payload = {}
        db = MagicMock()
        with pytest.raises(ValueError, match="session_log_id required"):
            _apply_action(item, db)

    def test_valid_action_types_are_recognized(self):
        """The three known action types should not raise 'Unknown action type'."""
        from app.routers.offline import _apply_action
        known_actions = ["create_set_log", "complete_session", "add_body_feedback"]
        for action in known_actions:
            item = MagicMock()
            item.action_type = action
            item.payload = {"session_log_id": str(uuid4())}
            db = MagicMock()
            try:
                _apply_action(item, db)
            except ValueError as e:
                assert "Unknown action type" not in str(e)

    def test_apply_action_spreads_payload_into_orm(self):
        """Verify that _apply_action spreads arbitrary payload keys into
        ORM models for 'complete_session' — a known risk surface.
        This is a static analysis test confirming the risk exists."""
        import inspect
        from app.routers.offline import _apply_action
        source = inspect.getsource(_apply_action)
        assert "setattr" in source

    def test_complete_session_excludes_id_from_setattr(self):
        """US-101: The 'id' field must be excluded from the
        complete_session setattr loop."""
        import inspect
        from app.routers.offline import _apply_action
        source = inspect.getsource(_apply_action)
        assert '"id"' in source or "'id'" in source


class TestSetattrExcludesId:
    """US-101: Verify that the 'id' field is excluded from all setattr()
    update loops in the session and profile routers."""

    def test_update_session_excludes_id(self):
        import inspect
        from app.routers.sessions import update_session
        source = inspect.getsource(update_session)
        assert 'pop("id"' in source or "pop('id'" in source

    def test_update_set_excludes_id(self):
        import inspect
        from app.routers.sessions import update_set
        source = inspect.getsource(update_set)
        assert 'pop("id"' in source or "pop('id'" in source

    def test_update_profile_excludes_id(self):
        import inspect
        from app.routers.profile import update_profile
        source = inspect.getsource(update_profile)
        assert 'pop("id"' in source or "pop('id'" in source


class TestChatEndpointSchema:
    """Verify the ChatRequest schema constrains input."""

    def test_chat_request_requires_message(self):
        from app.routers.coaching import ChatRequest
        with pytest.raises(Exception):
            ChatRequest()

    def test_chat_request_accepts_valid_message(self):
        from app.routers.coaching import ChatRequest
        req = ChatRequest(message="How should I warm up today?")
        assert req.message == "How should I warm up today?"


class TestProxyHeaderStripping:
    """Verify that the frontend proxy strips WWW-Authenticate (US-001)."""

    def test_proxy_strips_www_authenticate(self):
        import pathlib
        proxy_src = (
            pathlib.Path(__file__).resolve().parents[2]
            / "frontend"
            / "app"
            / "api"
            / "proxy"
            / "[...path]"
            / "route.ts"
        )
        if proxy_src.exists():
            content = proxy_src.read_text()
            assert "www-authenticate" in content.lower()