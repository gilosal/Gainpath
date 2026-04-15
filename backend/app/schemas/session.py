from __future__ import annotations
from datetime import datetime, date
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field


# ── Set Log ───────────────────────────────────────────────────────────────────

class SetLogCreate(BaseModel):
    exercise_name: str
    exercise_library_id: Optional[UUID] = None
    set_number: int = 1
    set_type: str = "working"
    # Lifting
    weight: Optional[float] = None
    reps: Optional[int] = None
    rpe: Optional[int] = Field(None, ge=1, le=10)
    # Running
    distance: Optional[float] = None
    duration: Optional[int] = None
    pace: Optional[float] = None
    # Mobility
    hold_duration: Optional[int] = None
    body_side: Optional[str] = None
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
    feeling: str  # good | tight | sore | pain
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
    session_type: str


class SessionLogUpdate(BaseModel):
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: Optional[str] = None
    overall_rpe: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None
    # Running
    actual_distance: Optional[float] = None
    actual_duration: Optional[int] = None
    actual_pace: Optional[float] = None
    # Lifting
    total_tonnage: Optional[float] = None
    # Mobility
    completed_flow: Optional[bool] = None


class SessionLogRead(BaseModel):
    id: UUID
    planned_session_id: Optional[UUID] = None
    session_date: date
    session_type: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str
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
