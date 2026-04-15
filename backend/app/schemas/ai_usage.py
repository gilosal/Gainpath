from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class AIUsageLogRead(BaseModel):
    id: UUID
    created_at: datetime
    model: str
    feature: str
    plan_type: Optional[str] = None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    duration_ms: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    request_id: Optional[str] = None
    model_config = {"from_attributes": True}


class AIUsageSummary(BaseModel):
    total_requests: int
    successful_requests: int
    total_tokens: int
    total_cost_usd: float
    # Broken down by model slug
    by_model: dict[str, dict]
    # Broken down by feature
    by_feature: dict[str, dict]
