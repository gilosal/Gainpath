from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.session import SessionLog, SetLog
from ..models.plan import PlannedSession

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Key stats for the mobile dashboard hero cards."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday

    # This week's sessions
    week_sessions = (
        db.query(SessionLog)
        .filter(SessionLog.session_date >= week_start, SessionLog.session_date <= today)
        .all()
    )

    running_this_week = sum(
        s.actual_distance or 0
        for s in week_sessions
        if s.session_type == "running" and s.status == "completed"
    )
    lifting_this_week = sum(
        s.total_tonnage or 0
        for s in week_sessions
        if s.session_type == "lifting" and s.status == "completed"
    )
    mobility_minutes_this_week = sum(
        (s.actual_duration or 0) / 60
        for s in week_sessions
        if s.session_type == "mobility" and s.status == "completed"
    )
    sessions_completed = sum(1 for s in week_sessions if s.status == "completed")
    sessions_planned = (
        db.query(PlannedSession)
        .filter(
            PlannedSession.session_date >= week_start,
            PlannedSession.session_date <= week_start + timedelta(days=6),
            PlannedSession.session_type != "rest",
        )
        .count()
    )

    # Today's planned sessions
    today_planned = (
        db.query(PlannedSession)
        .filter(PlannedSession.session_date == today, PlannedSession.session_type != "rest")
        .all()
    )

    return {
        "today": str(today),
        "week_start": str(week_start),
        "running_km_this_week": round(running_this_week, 2),
        "lifting_tonnage_this_week": round(lifting_this_week, 1),
        "mobility_minutes_this_week": round(mobility_minutes_this_week, 0),
        "sessions_completed_this_week": sessions_completed,
        "sessions_planned_this_week": sessions_planned,
        "today_sessions_count": len(today_planned),
    }


@router.get("/trends/running")
def running_trends(weeks: int = Query(12, ge=1, le=52), db: Session = Depends(get_db)):
    """Weekly running mileage trend."""
    cutoff = date.today() - timedelta(weeks=weeks)
    sessions = (
        db.query(SessionLog)
        .filter(
            SessionLog.session_type == "running",
            SessionLog.status == "completed",
            SessionLog.session_date >= cutoff,
        )
        .all()
    )
    # Group by ISO week
    by_week: dict[str, float] = {}
    for s in sessions:
        week_key = s.session_date.strftime("%Y-W%W")
        by_week[week_key] = by_week.get(week_key, 0.0) + (s.actual_distance or 0)

    return [{"week": k, "km": round(v, 2)} for k, v in sorted(by_week.items())]


@router.get("/trends/lifting")
def lifting_trends(weeks: int = Query(12, ge=1, le=52), db: Session = Depends(get_db)):
    """Weekly lifting tonnage trend."""
    cutoff = date.today() - timedelta(weeks=weeks)
    sessions = (
        db.query(SessionLog)
        .filter(
            SessionLog.session_type == "lifting",
            SessionLog.status == "completed",
            SessionLog.session_date >= cutoff,
        )
        .all()
    )
    by_week: dict[str, float] = {}
    for s in sessions:
        week_key = s.session_date.strftime("%Y-W%W")
        by_week[week_key] = by_week.get(week_key, 0.0) + (s.total_tonnage or 0)

    return [{"week": k, "tonnage": round(v, 1)} for k, v in sorted(by_week.items())]


@router.get("/trends/mobility")
def mobility_trends(weeks: int = Query(12, ge=1, le=52), db: Session = Depends(get_db)):
    """Weekly mobility session count and minutes."""
    cutoff = date.today() - timedelta(weeks=weeks)
    sessions = (
        db.query(SessionLog)
        .filter(
            SessionLog.session_type == "mobility",
            SessionLog.status == "completed",
            SessionLog.session_date >= cutoff,
        )
        .all()
    )
    by_week: dict[str, dict] = {}
    for s in sessions:
        week_key = s.session_date.strftime("%Y-W%W")
        if week_key not in by_week:
            by_week[week_key] = {"count": 0, "minutes": 0.0}
        by_week[week_key]["count"] += 1
        by_week[week_key]["minutes"] += (s.actual_duration or 0) / 60

    return [
        {"week": k, "sessions": v["count"], "minutes": round(v["minutes"], 0)}
        for k, v in sorted(by_week.items())
    ]


@router.get("/trends/exercise/{exercise_name}")
def exercise_progression(exercise_name: str, db: Session = Depends(get_db)):
    """Best set per session for a given exercise (for strength progression chart)."""
    sets = (
        db.query(SetLog)
        .filter(
            SetLog.exercise_name.ilike(f"%{exercise_name}%"),
            SetLog.weight.isnot(None),
            SetLog.reps.isnot(None),
        )
        .order_by(SetLog.completed_at)
        .all()
    )
    # Estimated 1RM via Epley formula: weight * (1 + reps/30)
    results = []
    for s in sets:
        if s.weight and s.reps:
            e1rm = round(s.weight * (1 + s.reps / 30), 1)
            results.append({
                "date": str(s.completed_at.date()),
                "weight": s.weight,
                "reps": s.reps,
                "estimated_1rm": e1rm,
                "rpe": s.rpe,
            })
    return results


@router.get("/calendar")
def get_calendar_week(
    start_date: date = Query(...),
    db: Session = Depends(get_db),
):
    """Returns planned sessions + logs for a 7-day window starting at start_date."""
    end_date = start_date + timedelta(days=6)
    planned = (
        db.query(PlannedSession)
        .filter(
            PlannedSession.session_date >= start_date,
            PlannedSession.session_date <= end_date,
        )
        .order_by(PlannedSession.session_date, PlannedSession.order_in_stack)
        .all()
    )
    logs = (
        db.query(SessionLog)
        .filter(
            SessionLog.session_date >= start_date,
            SessionLog.session_date <= end_date,
        )
        .all()
    )
    log_by_date: dict[str, list] = {}
    for log in logs:
        key = str(log.session_date)
        log_by_date.setdefault(key, []).append({
            "id": str(log.id),
            "session_type": log.session_type,
            "status": log.status,
            "overall_rpe": log.overall_rpe,
        })

    days = []
    for i in range(7):
        d = start_date + timedelta(days=i)
        day_planned = [p for p in planned if p.session_date == d]
        days.append({
            "date": str(d),
            "day_of_week": d.strftime("%A").lower(),
            "planned_sessions": [
                {
                    "id": str(p.id),
                    "session_type": p.session_type,
                    "session_subtype": p.session_subtype,
                    "title": p.title,
                    "estimated_duration": p.estimated_duration,
                    "is_stacked": p.is_stacked,
                }
                for p in day_planned
            ],
            "logged_sessions": log_by_date.get(str(d), []),
        })
    return {"start_date": str(start_date), "end_date": str(end_date), "days": days}
