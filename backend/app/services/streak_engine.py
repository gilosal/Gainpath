"""
streak_engine.py — Workout streak tracking.

A streak counts consecutive training days (days where at least one session
was completed). Missing a scheduled rest day never breaks a streak. A streak
freeze can be used once per 7 days to skip a missed training day.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, date, timedelta

from sqlalchemy.orm import Session

from ..models.gamification import StreakSnapshot
from ..models.session import SessionLog
from ..models.user import UserProfile

logger = logging.getLogger(__name__)


def _get_or_create_snapshot(db: Session) -> StreakSnapshot:
    snap = db.query(StreakSnapshot).first()
    if not snap:
        snap = StreakSnapshot(id=uuid.uuid4(), current_streak=0, longest_streak=0)
        db.add(snap)
        db.commit()
        db.refresh(snap)
    return snap


def _get_available_days(db: Session) -> set[str]:
    """Return the user's configured available training days as lowercase weekday names."""
    profile = db.query(UserProfile).first()
    if not profile or not profile.available_days:
        # Default: all days are training days
        return {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
    return {d.lower() for d in profile.available_days}


def _is_training_day(d: date, available_days: set[str]) -> bool:
    day_name = d.strftime("%A").lower()
    return day_name in available_days


def update_streak(db: Session) -> StreakSnapshot:
    """
    Recompute the current streak from session_log history.
    Called in a background task after every session completion.
    """
    snap = _get_or_create_snapshot(db)
    available_days = _get_available_days(db)
    today = date.today()

    # Collect all dates that have at least one completed session
    completed_dates: set[date] = {
        row.session_date
        for row in db.query(SessionLog.session_date)
        .filter(SessionLog.status == "completed")
        .distinct()
        .all()
    }

    if not completed_dates:
        snap.current_streak = 0
        snap.streak_start_date = None
        snap.last_workout_date = None
        snap.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(snap)
        return snap

    last_workout = max(completed_dates)
    snap.last_workout_date = last_workout

    # Walk backwards from today to compute current streak
    streak = 0
    cursor = today

    # Allow today or yesterday as the most recent workout
    if last_workout < today - timedelta(days=1):
        # More than one day ago — streak may be broken
        # Check if the gap days were training days
        gap_day = today - timedelta(days=1)
        gap_broken = False
        while gap_day > last_workout:
            if _is_training_day(gap_day, available_days) and gap_day not in completed_dates:
                # Missed a training day — streak is broken
                gap_broken = True
                break
            gap_day -= timedelta(days=1)
        if gap_broken:
            snap.current_streak = 0
            snap.streak_start_date = None
            snap.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(snap)
            return snap

    # Count streak walking backwards from last_workout
    cursor = last_workout
    streak = 0
    streak_start = cursor

    while cursor >= today - timedelta(days=365):  # cap at 1 year lookback
        if cursor in completed_dates:
            streak += 1
            streak_start = cursor
            cursor -= timedelta(days=1)
        elif not _is_training_day(cursor, available_days):
            # Rest day — skip without breaking streak
            cursor -= timedelta(days=1)
        elif snap.streak_frozen and snap.freeze_used_at == cursor:
            # Frozen day — skip without breaking
            cursor -= timedelta(days=1)
        else:
            # Missed training day — streak ends here
            break

    snap.current_streak = streak
    snap.streak_start_date = streak_start if streak > 0 else None
    if streak > snap.longest_streak:
        snap.longest_streak = streak
    snap.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(snap)
    return snap


def check_streak_risk(db: Session) -> bool:
    """
    Returns True if today has a planned session that is not yet completed
    and it is past 18:00 (streak risk window).
    """
    now = datetime.utcnow()
    if now.hour < 18:
        return False

    today = date.today()
    completed_today = (
        db.query(SessionLog)
        .filter(SessionLog.session_date == today, SessionLog.status == "completed")
        .count()
    )
    if completed_today > 0:
        return False

    planned_today = (
        db.query(SessionLog)
        .filter(SessionLog.session_date == today, SessionLog.status == "planned")
        .count()
    )
    return planned_today > 0


def use_streak_freeze(db: Session) -> tuple[bool, str]:
    """
    Attempt to use a streak freeze for the most recently missed training day.
    Returns (success, message).
    One freeze allowed per 7 days.
    """
    snap = _get_or_create_snapshot(db)
    today = date.today()

    # Check cooldown
    if snap.freeze_used_at and (today - snap.freeze_used_at).days < 7:
        days_left = 7 - (today - snap.freeze_used_at).days
        return False, f"Streak freeze available again in {days_left} day(s)."

    snap.streak_frozen = True
    snap.freeze_used_at = today
    snap.updated_at = datetime.utcnow()
    db.commit()

    # Recompute streak with freeze applied
    update_streak(db)
    return True, "Streak freeze applied! Your streak is safe."


def get_streak(db: Session) -> StreakSnapshot:
    return _get_or_create_snapshot(db)
