from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None

    # Running
    running_goal_race: Optional[str] = None
    running_goal_date: Optional[datetime] = None
    running_fitness_level: Optional[str] = None
    running_weekly_mileage: Optional[float] = None
    running_recent_race_time: Optional[str] = None

    # Weight training
    training_days_per_week: Optional[int] = Field(None, ge=1, le=7)
    available_equipment: Optional[str] = None
    weight_training_goal: Optional[str] = None
    training_preferred_days: Optional[list[str]] = None

    # Mobility
    mobility_goal: Optional[str] = None
    mobility_target_areas: Optional[list[str]] = None
    mobility_experience: Optional[str] = None
    mobility_session_length: Optional[int] = None

    # Schedule
    available_days: Optional[list[str]] = None
    session_time_constraints: Optional[dict[str, int]] = None
    no_morning_days: Optional[list[str]] = None

    # Preferences
    units_weight: Optional[str] = None
    units_distance: Optional[str] = None
    dark_mode: Optional[bool] = None
    preferred_ai_model: Optional[str] = None


class UserProfileRead(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    name: str

    running_goal_race: Optional[str] = None
    running_goal_date: Optional[datetime] = None
    running_fitness_level: Optional[str] = None
    running_weekly_mileage: Optional[float] = None
    running_recent_race_time: Optional[str] = None

    training_days_per_week: int
    available_equipment: str
    weight_training_goal: str
    training_preferred_days: list[str]

    mobility_goal: str
    mobility_target_areas: list[str]
    mobility_experience: str
    mobility_session_length: int

    available_days: list[str]
    session_time_constraints: dict[str, int]
    no_morning_days: list[str]

    units_weight: str
    units_distance: str
    dark_mode: bool
    preferred_ai_model: Optional[str] = None

    model_config = {"from_attributes": True}
