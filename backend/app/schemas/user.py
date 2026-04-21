from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class WeightUnit(str, Enum):
    kg = "kg"
    lb = "lb"


class DistanceUnit(str, Enum):
    km = "km"
    mi = "mi"


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None

    # Running
    running_goal_race: Optional[Literal["5k", "10k", "half_marathon", "marathon", "ultra"]] = None
    running_goal_date: Optional[datetime] = None
    running_fitness_level: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    running_weekly_mileage: Optional[float] = Field(None, ge=0)
    running_recent_race_time: Optional[str] = None

    # Weight training
    training_days_per_week: Optional[int] = Field(None, ge=1, le=7)
    available_equipment: Optional[Literal["home_gym", "full_gym", "bodyweight"]] = None
    weight_training_goal: Optional[Literal["hypertrophy", "strength", "general_fitness", "complement_running"]] = None
    training_preferred_days: Optional[list[str]] = None

    # Mobility
    mobility_goal: Optional[Literal["general_flexibility", "injury_prevention", "recovery", "targeted"]] = None
    mobility_target_areas: Optional[list[str]] = None
    mobility_experience: Optional[Literal["beginner", "intermediate", "experienced"]] = None
    mobility_session_length: Optional[int] = Field(None, ge=5, le=120)

    # Schedule
    available_days: Optional[list[str]] = None
    session_time_constraints: Optional[dict[str, int]] = None
    no_morning_days: Optional[list[str]] = None

    # Preferences
    units_weight: Optional[WeightUnit] = None
    units_distance: Optional[DistanceUnit] = None
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
