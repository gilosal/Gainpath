import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class SessionLog(Base):
    __tablename__ = "session_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Nullable — allows logging an unplanned/ad-hoc session
    planned_session_id = Column(UUID(as_uuid=True), ForeignKey("planned_session.id", ondelete="SET NULL"), nullable=True)

    session_date = Column(Date, nullable=False)
    # running | lifting | mobility
    session_type = Column(String(20), nullable=False)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    # planned | in_progress | completed | skipped
    status = Column(String(20), default="planned", nullable=False)

    overall_rpe = Column(Integer)  # 1–10
    notes = Column(Text)

    # Running
    actual_distance = Column(Float)        # km or mi per user prefs
    actual_duration = Column(Integer)      # seconds
    actual_pace = Column(Float)            # min/km or min/mi

    # Lifting aggregate
    total_tonnage = Column(Float)          # kg·reps

    # Mobility
    completed_flow = Column(Boolean)

    planned_session = relationship("PlannedSession", back_populates="logs")
    sets = relationship("SetLog", back_populates="session", cascade="all, delete-orphan", order_by="SetLog.set_number")
    body_feedback = relationship("BodyFeedback", back_populates="session", cascade="all, delete-orphan")


class SetLog(Base):
    __tablename__ = "set_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_log_id = Column(UUID(as_uuid=True), ForeignKey("session_log.id", ondelete="CASCADE"), nullable=False)

    exercise_name = Column(String(200), nullable=False)
    exercise_library_id = Column(UUID(as_uuid=True), ForeignKey("exercise_library.id", ondelete="SET NULL"), nullable=True)

    set_number = Column(Integer, default=1)
    # working | warmup | dropset | failure
    set_type = Column(String(20), default="working")

    # Lifting
    weight = Column(Float)    # kg or lb
    reps = Column(Integer)
    rpe = Column(Integer)     # 1–10

    # Running (interval or track work)
    distance = Column(Float)  # km or mi
    duration = Column(Integer)  # seconds
    pace = Column(Float)      # min/km or min/mi

    # Mobility
    hold_duration = Column(Integer)  # seconds
    # left | right | bilateral
    body_side = Column(String(15))
    tightness_notes = Column(Text)

    completed_at = Column(DateTime, default=datetime.utcnow)
    is_offline = Column(Boolean, default=False)

    session = relationship("SessionLog", back_populates="sets")


class BodyFeedback(Base):
    __tablename__ = "body_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_log_id = Column(UUID(as_uuid=True), ForeignKey("session_log.id", ondelete="CASCADE"), nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # hips | shoulders | hamstrings | quads | calves | lower_back |
    # upper_back | knees | ankles | it_band | chest | etc.
    body_area = Column(String(50), nullable=False)
    # good | tight | sore | pain
    feeling = Column(String(20), nullable=False)
    severity = Column(Integer)   # 1–5
    notes = Column(Text)

    session = relationship("SessionLog", back_populates="body_feedback")


class OfflineQueue(Base):
    __tablename__ = "offline_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # pending | syncing | synced | failed
    sync_status = Column(String(20), default="pending", nullable=False)
    # create_set_log | complete_session | add_body_feedback
    action_type = Column(String(50), nullable=False)
    # Full request payload as JSON
    payload = Column(JSON, nullable=False)

    session_log_id = Column(UUID(as_uuid=True), ForeignKey("session_log.id", ondelete="SET NULL"), nullable=True)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    synced_at = Column(DateTime)
