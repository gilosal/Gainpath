import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from ..database import Base


class StreakSnapshot(Base):
    __tablename__ = "streak_snapshot"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    streak_start_date = Column(Date)
    last_workout_date = Column(Date)
    # Streak freeze: preserves streak when a training day is missed (once per 7 days)
    streak_frozen = Column(Boolean, default=False, nullable=False)
    freeze_used_at = Column(Date)


class Achievement(Base):
    __tablename__ = "achievement"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(String(300), nullable=False)
    icon_name = Column(String(50), nullable=False)
    # streak | volume | consistency | milestone
    category = Column(String(30), nullable=False)
    threshold = Column(Integer, default=1, nullable=False)
    xp_reward = Column(Integer, default=100, nullable=False)


class UserAchievement(Base):
    __tablename__ = "user_achievement"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey("achievement.id", ondelete="CASCADE"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # Additional context: {"exercise": "Bench Press", "weight": 100}
    context_json = Column(JSON)


class XPLedger(Base):
    __tablename__ = "xp_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    amount = Column(Integer, nullable=False)
    # workout_complete | streak_bonus | achievement | challenge
    source = Column(String(50), nullable=False)
    reference_id = Column(UUID(as_uuid=True))
    note = Column(String(200))


class WeeklyChallenge(Base):
    __tablename__ = "weekly_challenge"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    week_start_date = Column(Date, nullable=False)
    # consistency | volume | variety | streak
    challenge_type = Column(String(30), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, default=0.0, nullable=False)
    # active | completed | failed | expired
    status = Column(String(20), default="active", nullable=False)
    xp_reward = Column(Integer, default=200, nullable=False)
    generated_by_ai = Column(Boolean, default=True, nullable=False)


class PersonalRecord(Base):
    __tablename__ = "personal_record"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    exercise_name = Column(String(200), nullable=False)
    # weight_1rm | max_weight | max_reps | max_volume | fastest_pace | longest_distance
    record_type = Column(String(30), nullable=False)
    value = Column(Float, nullable=False)
    previous_value = Column(Float)
    set_log_id = Column(UUID(as_uuid=True), ForeignKey("set_log.id", ondelete="SET NULL"))
    session_log_id = Column(UUID(as_uuid=True), ForeignKey("session_log.id", ondelete="SET NULL"))
    celebrated = Column(Boolean, default=False, nullable=False)
