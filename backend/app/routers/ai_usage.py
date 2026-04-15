from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.ai_usage import AIUsageLog
from ..schemas.ai_usage import AIUsageLogRead, AIUsageSummary

router = APIRouter(prefix="/ai-usage", tags=["ai-usage"])


@router.get("", response_model=list[AIUsageLogRead])
def list_usage_logs(
    limit: int = Query(100, le=500),
    feature: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(AIUsageLog)
    if feature:
        q = q.filter(AIUsageLog.feature == feature)
    return q.order_by(AIUsageLog.created_at.desc()).limit(limit).all()


@router.get("/summary", response_model=AIUsageSummary)
def get_usage_summary(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    cutoff = date.today() - timedelta(days=days)
    logs = (
        db.query(AIUsageLog)
        .filter(AIUsageLog.created_at >= cutoff)
        .all()
    )

    total_cost = sum(l.cost_usd for l in logs)
    total_tokens = sum(l.total_tokens for l in logs)
    successful = sum(1 for l in logs if l.success)

    by_model: dict[str, dict] = {}
    for l in logs:
        if l.model not in by_model:
            by_model[l.model] = {"requests": 0, "tokens": 0, "cost_usd": 0.0}
        by_model[l.model]["requests"] += 1
        by_model[l.model]["tokens"] += l.total_tokens
        by_model[l.model]["cost_usd"] = round(by_model[l.model]["cost_usd"] + l.cost_usd, 6)

    by_feature: dict[str, dict] = {}
    for l in logs:
        if l.feature not in by_feature:
            by_feature[l.feature] = {"requests": 0, "tokens": 0, "cost_usd": 0.0}
        by_feature[l.feature]["requests"] += 1
        by_feature[l.feature]["tokens"] += l.total_tokens
        by_feature[l.feature]["cost_usd"] = round(by_feature[l.feature]["cost_usd"] + l.cost_usd, 6)

    return AIUsageSummary(
        total_requests=len(logs),
        successful_requests=successful,
        total_tokens=total_tokens,
        total_cost_usd=round(total_cost, 6),
        by_model=by_model,
        by_feature=by_feature,
    )
