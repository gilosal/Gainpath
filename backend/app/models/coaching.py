import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSON
from ..database import Base


class CoachingMessage(Base):
    __tablename__ = "coaching_message"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # daily_motivation | post_workout | weekly_summary | nudge | streak_risk
    message_type = Column(String(30), nullable=False)
    content = Column(Text, nullable=False)
    # Source data used for generation (streak count, session stats, etc.)
    metadata_json = Column(JSON)
    displayed = Column(Boolean, default=False, nullable=False)
    dismissed = Column(Boolean, default=False, nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_message"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # user | assistant
    role = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    # Fitness context included in the prompt (recent sessions, PRs, plan)
    context_json = Column(JSON)
