"""
achievement_engine.py — Achievement seeding, evaluation, and XP tracking.

All XP flows through grant_xp(). Achievement evaluation is trigger-based:
call check_achievements() after session_completed, streak_updated, or pr_detected.
"""
from __future__ import annotations

import uuid
import math
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ..models.gamification import Achievement, UserAchievement, XPLedger, StreakSnapshot, PersonalRecord
from ..models.session import SessionLog
from ..models.user import UserProfile

logger = logging.getLogger(__name__)

# ── Achievement seed data ──────────────────────────────────────────────────────

ACHIEVEMENTS = [
    # Milestone: first workouts
    {"slug": "first_workout", "name": "First Step", "description": "Complete your first workout.", "icon_name": "Footprints", "category": "milestone", "threshold": 1, "xp_reward": 50},
    {"slug": "workouts_10", "name": "Getting Started", "description": "Complete 10 workouts.", "icon_name": "TrendingUp", "category": "milestone", "threshold": 10, "xp_reward": 200},
    {"slug": "workouts_50", "name": "Halfway Hundred", "description": "Complete 50 workouts.", "icon_name": "Award", "category": "milestone", "threshold": 50, "xp_reward": 500},
    {"slug": "workouts_100", "name": "Century Club", "description": "Complete 100 workouts.", "icon_name": "Trophy", "category": "milestone", "threshold": 100, "xp_reward": 1000},
    # Streak
    {"slug": "streak_3", "name": "Warming Up", "description": "Maintain a 3-day workout streak.", "icon_name": "Flame", "category": "streak", "threshold": 3, "xp_reward": 100},
    {"slug": "streak_7", "name": "Week Warrior", "description": "Maintain a 7-day workout streak.", "icon_name": "Flame", "category": "streak", "threshold": 7, "xp_reward": 250},
    {"slug": "streak_14", "name": "Fortnight Force", "description": "Maintain a 14-day workout streak.", "icon_name": "Zap", "category": "streak", "threshold": 14, "xp_reward": 500},
    {"slug": "streak_30", "name": "Monthly Machine", "description": "Maintain a 30-day workout streak.", "icon_name": "Star", "category": "streak", "threshold": 30, "xp_reward": 1000},
    # PRs
    {"slug": "first_pr", "name": "New PR!", "description": "Set your first personal record.", "icon_name": "Medal", "category": "milestone", "threshold": 1, "xp_reward": 150},
    {"slug": "prs_10", "name": "Record Breaker", "description": "Set 10 personal records.", "icon_name": "ChartLine", "category": "milestone", "threshold": 10, "xp_reward": 300},
    # Volume
    {"slug": "run_100km", "name": "100km Runner", "description": "Log 100km of running in total.", "icon_name": "MapPin", "category": "volume", "threshold": 100, "xp_reward": 500},
    {"slug": "tonnage_10k", "name": "10 Ton Club", "description": "Lift a cumulative 10,000kg.", "icon_name": "Dumbbell", "category": "volume", "threshold": 10000, "xp_reward": 300},
    # Consistency
    {"slug": "variety", "name": "Cross-Trainer", "description": "Complete all 3 session types (run, lift, mobility) in one week.", "icon_name": "Shuffle", "category": "consistency", "threshold": 1, "xp_reward": 200},
    {"slug": "early_bird", "name": "Early Bird", "description": "Complete a workout before 7am.", "icon_name": "Sunrise", "category": "consistency", "threshold": 1, "xp_reward": 100},
    {"slug": "challenge_complete", "name": "Challenge Accepted", "description": "Complete a weekly challenge.", "icon_name": "Target", "category": "consistency", "threshold": 1, "xp_reward": 150},
]


def seed_achievements(db: Session) -> None:
    """Idempotent: only inserts achievements that don't already exist by slug."""
    existing_slugs = {row.slug for row in db.query(Achievement.slug).all()}
    for data in ACHIEVEMENTS:
        if data["slug"] not in existing_slugs:
            ach = Achievement(id=uuid.uuid4(), **data)
            db.add(ach)
    db.commit()


# ── XP granting ───────────────────────────────────────────────────────────────

def grant_xp(
    db: Session,
    amount: int,
    source: str,
    reference_id: Optional[uuid.UUID] = None,
    note: Optional[str] = None,
) -> None:
    """Insert into xp_ledger, update total_xp and level on user_profile."""
    entry = XPLedger(
        id=uuid.uuid4(),
        amount=amount,
        source=source,
        reference_id=reference_id,
        note=note,
    )
    db.add(entry)

    profile = db.query(UserProfile).first()
    if profile:
        profile.total_xp = (profile.total_xp or 0) + amount
        profile.level = _compute_level(profile.total_xp)

    db.commit()


def _compute_level(total_xp: int) -> int:
    """Level = floor(sqrt(total_xp / 100)) + 1, minimum 1."""
    return max(1, int(math.floor(math.sqrt(max(0, total_xp) / 100))) + 1)


def xp_for_session(session_type: str, rpe: Optional[int]) -> int:
    """XP awarded per completed session, scaled by type and effort."""
    base = {"running": 40, "lifting": 40, "mobility": 25}.get(session_type, 30)
    if rpe and rpe >= 8:
        base += 10
    return base


# ── Achievement checking ───────────────────────────────────────────────────────

def check_achievements(
    db: Session,
    trigger_event: str,
    context: Optional[dict] = None,
) -> list[Achievement]:
    """
    Evaluate all unearned achievements against current state.
    Returns list of newly earned achievements.
    trigger_event: "session_completed" | "streak_updated" | "pr_detected" | "challenge_completed"
    """
    context = context or {}
    earned_ids = {row.achievement_id for row in db.query(UserAchievement.achievement_id).all()}
    all_achievements = db.query(Achievement).all()
    newly_earned: list[Achievement] = []

    for ach in all_achievements:
        if ach.id in earned_ids:
            continue
        if _evaluate_achievement(db, ach, trigger_event, context):
            _grant_achievement(db, ach, context)
            newly_earned.append(ach)

    return newly_earned


def _evaluate_achievement(
    db: Session,
    ach: Achievement,
    trigger_event: str,
    context: dict,
) -> bool:
    slug = ach.slug

    # ── Milestone: workout counts ──────────────────────────────────────────────
    if slug in ("first_workout", "workouts_10", "workouts_50", "workouts_100"):
        if trigger_event != "session_completed":
            return False
        count = db.query(SessionLog).filter(SessionLog.status == "completed").count()
        return count >= ach.threshold

    # ── Streak achievements ────────────────────────────────────────────────────
    if slug in ("streak_3", "streak_7", "streak_14", "streak_30"):
        if trigger_event not in ("session_completed", "streak_updated"):
            return False
        snap = db.query(StreakSnapshot).first()
        if not snap:
            return False
        return snap.current_streak >= ach.threshold

    # ── PR achievements ────────────────────────────────────────────────────────
    if slug == "first_pr":
        if trigger_event != "pr_detected":
            return False
        return True  # Any PR detected is enough

    if slug == "prs_10":
        if trigger_event != "pr_detected":
            return False
        count = db.query(PersonalRecord).count()
        return count >= 10

    # ── Volume achievements ────────────────────────────────────────────────────
    if slug == "run_100km":
        if trigger_event != "session_completed":
            return False
        from sqlalchemy import func
        total = db.query(func.sum(SessionLog.actual_distance)).filter(
            SessionLog.session_type == "running",
            SessionLog.status == "completed",
            SessionLog.actual_distance.isnot(None),
        ).scalar() or 0.0
        return total >= 100.0

    if slug == "tonnage_10k":
        if trigger_event != "session_completed":
            return False
        from sqlalchemy import func
        total = db.query(func.sum(SessionLog.total_tonnage)).filter(
            SessionLog.session_type == "lifting",
            SessionLog.status == "completed",
            SessionLog.total_tonnage.isnot(None),
        ).scalar() or 0.0
        return total >= 10000.0

    # ── Consistency achievements ───────────────────────────────────────────────
    if slug == "variety":
        if trigger_event != "session_completed":
            return False
        from datetime import date, timedelta
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        types_this_week = {
            row.session_type
            for row in db.query(SessionLog.session_type)
            .filter(
                SessionLog.session_date >= week_start,
                SessionLog.status == "completed",
            )
            .distinct()
            .all()
        }
        return {"running", "lifting", "mobility"}.issubset(types_this_week)

    if slug == "early_bird":
        if trigger_event != "session_completed":
            return False
        completed_at = context.get("completed_at")
        if completed_at and hasattr(completed_at, "hour"):
            return completed_at.hour < 7
        return False

    if slug == "challenge_complete":
        return trigger_event == "challenge_completed"

    return False


def _grant_achievement(db: Session, ach: Achievement, context: dict) -> None:
    ua = UserAchievement(
        id=uuid.uuid4(),
        achievement_id=ach.id,
        earned_at=datetime.utcnow(),
        context_json=context or None,
    )
    db.add(ua)
    db.flush()
    grant_xp(db, ach.xp_reward, "achievement", ach.id, f"Earned: {ach.name}")
