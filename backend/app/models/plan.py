import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class TrainingPlan(Base):
    __tablename__ = "training_plan"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # running | lifting | mobility | unified
    plan_type = Column(String(20), nullable=False)
    goal = Column(String(200))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    # active | completed | archived
    status = Column(String(20), default="active", nullable=False)
    weeks_total = Column(Integer, nullable=False)
    # Full AI-generated JSON kept for reference / recalculation
    raw_plan_json = Column(JSON)

    weeks = relationship("PlanWeek", back_populates="plan", cascade="all, delete-orphan", order_by="PlanWeek.week_number")


class PlanWeek(Base):
    __tablename__ = "plan_week"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("training_plan.id", ondelete="CASCADE"), nullable=False)
    week_number = Column(Integer, nullable=False)
    week_start_date = Column(Date, nullable=False)
    # e.g. "Base Building", "Speed Work", "Taper"
    theme = Column(String(100))
    focus = Column(String(200))
    # target mileage (running) or tonnage (lifting) or minutes (mobility)
    total_volume_target = Column(Float)

    plan = relationship("TrainingPlan", back_populates="weeks")
    sessions = relationship("PlannedSession", back_populates="week", cascade="all, delete-orphan", order_by="PlannedSession.session_date")


class PlannedSession(Base):
    __tablename__ = "planned_session"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_week_id = Column(UUID(as_uuid=True), ForeignKey("plan_week.id", ondelete="CASCADE"), nullable=False)

    # monday | tuesday | ... | sunday
    day_of_week = Column(String(10), nullable=False)
    session_date = Column(Date, nullable=False)

    # running | lifting | mobility | rest
    session_type = Column(String(20), nullable=False)
    # easy_run | tempo | intervals | long_run | recovery_run |
    # push | pull | legs | upper | lower | full_body |
    # active_recovery | pre_run_dynamic | post_run_static | dedicated_flexibility | foam_rolling
    session_subtype = Column(String(50))

    title = Column(String(200), nullable=False)
    description = Column(Text)
    estimated_duration = Column(Integer)  # minutes

    # Structured workout data — shape depends on session_type:
    # running: [{type, distance, pace_target, effort, notes}]
    # lifting: [{exercise, sets, reps, rpe, rest_seconds, notes}]
    # mobility: [{name, hold_duration, reps, target_area, side, modifications}]
    exercises = Column(JSON, default=list)

    # True when this session is bundled with another (e.g. run + post-run stretch)
    is_stacked = Column(Boolean, default=False)
    order_in_stack = Column(Integer, default=0)

    week = relationship("PlanWeek", back_populates="sessions")
    logs = relationship("SessionLog", back_populates="planned_session")


class ExerciseLibrary(Base):
    __tablename__ = "exercise_library"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)

    # strength | cardio | mobility | flexibility | balance
    category = Column(String(50), nullable=False)
    subcategory = Column(String(50))

    # e.g. ["quads", "hamstrings", "glutes"]
    muscle_groups = Column(JSON, default=list)
    # push | pull | hinge | squat | carry | rotation | core | locomotion | hold
    movement_pattern = Column(String(50))
    # beginner | intermediate | advanced
    difficulty = Column(String(20), default="beginner")
    # e.g. ["barbell", "bench"] or ["mat"] or []
    equipment_needed = Column(JSON, default=list)

    description = Column(Text)
    # Coaching cues as a list of short strings
    cues = Column(JSON, default=list)
    # {"beginner": "use a strap", "advanced": "add a tempo"}
    modifications = Column(JSON, default=dict)

    # Yoga / mobility specifics
    is_yoga_pose = Column(Boolean, default=False)
    # static | dynamic | flow
    hold_type = Column(String(20))
    default_hold_duration = Column(Integer)  # seconds
