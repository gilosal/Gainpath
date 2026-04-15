import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from ..database import Base


class UserProfile(Base):
    __tablename__ = "user_profile"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    name = Column(String(100), default="Athlete", nullable=False)

    # ── Running ──────────────────────────────────────────────────────────────
    # goal_race: 5k | 10k | half_marathon | marathon | ultra
    running_goal_race = Column(String(50))
    running_goal_date = Column(DateTime)
    # fitness_level: beginner | intermediate | advanced
    running_fitness_level = Column(String(20))
    running_weekly_mileage = Column(Float)
    # "45:30" for a 10K, "1:52:00" for a half, etc.
    running_recent_race_time = Column(String(50))

    # ── Weight training ───────────────────────────────────────────────────────
    training_days_per_week = Column(Integer, default=3)
    # home_gym | full_gym | bodyweight
    available_equipment = Column(String(50), default="full_gym")
    # hypertrophy | strength | general_fitness | complement_running
    weight_training_goal = Column(String(50), default="general_fitness")
    # e.g. ["monday", "wednesday", "friday"]
    training_preferred_days = Column(JSON, default=list)

    # ── Mobility / yoga ───────────────────────────────────────────────────────
    # general_flexibility | injury_prevention | recovery | targeted
    mobility_goal = Column(String(50), default="general_flexibility")
    # e.g. ["hips", "shoulders", "hamstrings", "lower_back"]
    mobility_target_areas = Column(JSON, default=list)
    # beginner | intermediate | experienced
    mobility_experience = Column(String(20), default="beginner")
    # minutes: 10 | 20 | 30 | 45 | 60
    mobility_session_length = Column(Integer, default=20)

    # ── Schedule ──────────────────────────────────────────────────────────────
    # e.g. ["monday", "tuesday", "thursday", "saturday"]
    available_days = Column(JSON, default=list)
    # per-day time caps in minutes: {"wednesday": 20, "friday": 45}
    session_time_constraints = Column(JSON, default=dict)
    # days where morning sessions aren't possible
    no_morning_days = Column(JSON, default=list)

    # ── Preferences ───────────────────────────────────────────────────────────
    # kg | lb
    units_weight = Column(String(5), default="kg")
    # km | mi
    units_distance = Column(String(5), default="km")
    dark_mode = Column(Boolean, default=True)
    # override default AI model for this user
    preferred_ai_model = Column(String(100))
