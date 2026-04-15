from __future__ import annotations
from datetime import datetime, date
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel


# ── Exercise Library ──────────────────────────────────────────────────────────

class ExerciseLibraryCreate(BaseModel):
    name: str
    category: str
    subcategory: Optional[str] = None
    muscle_groups: list[str] = []
    movement_pattern: Optional[str] = None
    difficulty: str = "beginner"
    equipment_needed: list[str] = []
    description: Optional[str] = None
    cues: list[str] = []
    modifications: dict[str, str] = {}
    is_yoga_pose: bool = False
    hold_type: Optional[str] = None
    default_hold_duration: Optional[int] = None


class ExerciseLibraryRead(ExerciseLibraryCreate):
    id: UUID
    model_config = {"from_attributes": True}


# ── Planned Session ───────────────────────────────────────────────────────────

class PlannedSessionRead(BaseModel):
    id: UUID
    plan_week_id: UUID
    day_of_week: str
    session_date: date
    session_type: str
    session_subtype: Optional[str] = None
    title: str
    description: Optional[str] = None
    estimated_duration: Optional[int] = None
    exercises: list[Any] = []
    is_stacked: bool
    order_in_stack: int
    model_config = {"from_attributes": True}


# ── Plan Week ─────────────────────────────────────────────────────────────────

class PlanWeekRead(BaseModel):
    id: UUID
    plan_id: UUID
    week_number: int
    week_start_date: date
    theme: Optional[str] = None
    focus: Optional[str] = None
    total_volume_target: Optional[float] = None
    sessions: list[PlannedSessionRead] = []
    model_config = {"from_attributes": True}


# ── Training Plan ─────────────────────────────────────────────────────────────

class TrainingPlanCreate(BaseModel):
    plan_type: str  # running | lifting | mobility | unified


class TrainingPlanRead(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    plan_type: str
    goal: Optional[str] = None
    start_date: date
    end_date: date
    status: str
    weeks_total: int
    weeks: list[PlanWeekRead] = []
    model_config = {"from_attributes": True}


class TrainingPlanSummary(BaseModel):
    """Lightweight list item — no nested weeks/sessions."""
    id: UUID
    plan_type: str
    goal: Optional[str] = None
    start_date: date
    end_date: date
    status: str
    weeks_total: int
    model_config = {"from_attributes": True}
