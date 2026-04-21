from __future__ import annotations
from datetime import datetime, date
from enum import Enum
from typing import Literal, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    planned = "planned"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"


class SessionType(str, Enum):
    running = "running"
    lifting = "lifting"
    mobility = "mobility"


VALID_STATUS_TRANSITIONS: dict[SessionStatus, set[SessionStatus]] = {
    SessionStatus.planned: {SessionStatus.in_progress, SessionStatus.skipped},
    SessionStatus.in_progress: {SessionStatus.completed, SessionStatus.skipped},
    SessionStatus.completed: set(),
    SessionStatus.skipped: {SessionStatus.planned},
}


def validate_status_transition(current: str, new: SessionStatus) -> None:
    try:
        current_enum = SessionStatus(current)
    except ValueError:
        return
    allowed = VALID_STATUS_TRANSITIONS.get(current_enum, set())
    if new not in allowed:
        allowed_str = ", ".join(s.value for s in allowed) or "none"
        raise ValueError(
            f"Invalid status transition: {current_enum.value} -> {new.value}. "
            f"Allowed from '{current_enum.value}': [{allowed_str}]"
        )


class SetType(str, Enum):
    working = "working"
    warmup = "warmup"
    dropset = "dropset"
    failure = "failure"


class BodySide(str, Enum):
    left = "left"
    right = "right"
    bilateral = "bilateral"


class Feeling(str, Enum):
    good = "good"
    tight = "tight"
    sore = "sore"
    pain = "pain"


# ── Set Log ───────────────────────────────────────────────────────────────────

class SetLogCreate(BaseModel):
    exercise_name: str
    exercise_library_id: Optional[UUID] = None
    set_number: int = Field(1, ge=1)
    set_type: SetType = SetType.working
    # Lifting
    weight: Optional[float] = Field(None, ge=0)
    reps: Optional[int] = Field(None, ge=0)
    rpe: Optional[int] = Field(None, ge=1, le=10)
    # Running
    distance: Optional[float] = Field(None, ge=0)
    duration: Optional[int] = Field(None, ge=0)
    pace: Optional[float] = Field(None, ge=0)
    # Mobility
    hold_duration: Optional[int] = Field(None, ge=0)
    body_side: Optional[BodySide] = None
    tightness_notes: Optional[str] = None
    is_offline: bool = False


class SetLogRead(SetLogCreate):
    id: UUID
    session_log_id: UUID
    completed_at: datetime
    model_config = {"from_attributes": True}


# ── Body Feedback ─────────────────────────────────────────────────────────────

class BodyFeedbackCreate(BaseModel):
    body_area: str
    feeling: Feeling
    severity: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class BodyFeedbackRead(BodyFeedbackCreate):
    id: UUID
    session_log_id: UUID
    logged_at: datetime
    model_config = {"from_attributes": True}


# ── Session Log ───────────────────────────────────────────────────────────────

class SessionLogCreate(BaseModel):
    planned_session_id: Optional[UUID] = None
    session_date: date
    session_type: SessionType


class SessionLogUpdate(BaseModel):
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: Optional[SessionStatus] = None
    overall_rpe: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None
    # Running
    actual_distance: Optional[float] = Field(None, ge=0)
    actual_duration: Optional[int] = Field(None, ge=0)
    actual_pace: Optional[float] = Field(None, ge=0)
    # Lifting
    total_tonnage: Optional[float] = Field(None, ge=0)
    # Mobility
    completed_flow: Optional[bool] = None

    model_config = {"use_enum_values": True}


class SessionLogRead(BaseModel):
    id: UUID
    planned_session_id: Optional[UUID] = None
    session_date: date
    session_type: SessionType
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: SessionStatus
    overall_rpe: Optional[int] = None
    notes: Optional[str] = None
    actual_distance: Optional[float] = None
    actual_duration: Optional[int] = None
    actual_pace: Optional[float] = None
    total_tonnage: Optional[float] = None
    completed_flow: Optional[bool] = None
    sets: list[SetLogRead] = []
    body_feedback: list[BodyFeedbackRead] = []
    model_config = {"from_attributes": True}


# ── Offline Queue ─────────────────────────────────────────────────────────────

class OfflineQueueItemCreate(BaseModel):
    action_type: str
    payload: dict[str, Any]
    session_log_id: Optional[UUID] = None


class OfflineQueueItemRead(BaseModel):
    id: UUID
    created_at: datetime
    sync_status: str
    action_type: str
    payload: dict[str, Any]
    session_log_id: Optional[UUID] = None
    error_message: Optional[str] = None
    retry_count: int
    synced_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
