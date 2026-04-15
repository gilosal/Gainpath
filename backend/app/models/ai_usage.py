import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class AIUsageLog(Base):
    __tablename__ = "ai_usage_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    model = Column(String(100), nullable=False)
    # plan_generation | recalculation | scheduling | other
    feature = Column(String(50), nullable=False)
    # running | lifting | mobility | unified | None
    plan_type = Column(String(20))

    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    duration_ms = Column(Integer)

    success = Column(Boolean, default=True)
    error_message = Column(Text)
    # OpenRouter request ID from response body
    request_id = Column(String(100))
