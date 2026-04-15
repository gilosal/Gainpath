"""
coaching_engine.py — AI-generated coaching messages.

All generation runs as background tasks after session events or on a daily schedule.
Messages are stored in coaching_message and served to the frontend on demand.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, date, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.coaching import CoachingMessage, ChatMessage
from ..models.gamification import StreakSnapshot, PersonalRecord, WeeklyChallenge
from ..models.session import SessionLog
from ..models.user import UserProfile
from ..services.ai_client import ai_client
from ..prompts.coaching import (
    COACHING_SYSTEM_PROMPT,
    DailyMotivationResponse,
    PostWorkoutResponse,
    WeeklySummaryResponse,
    WeeklyChallengeResponse,
    build_daily_motivation_prompt,
    build_post_workout_prompt,
    build_weekly_summary_prompt,
    build_weekly_challenge_prompt,
    build_nudge_prompt,
    build_chat_system_prompt,
)

logger = logging.getLogger(__name__)


def _get_profile(db: Session) -> Optional[UserProfile]:
    return db.query(UserProfile).first()


def _get_streak(db: Session) -> int:
    snap = db.query(StreakSnapshot).first()
    return snap.current_streak if snap else 0


def _recent_sessions_summary(db: Session, days: int = 7) -> str:
    cutoff = date.today() - timedelta(days=days)
    sessions = (
        db.query(SessionLog)
        .filter(SessionLog.session_date >= cutoff, SessionLog.status == "completed")
        .order_by(SessionLog.session_date.desc())
        .limit(10)
        .all()
    )
    if not sessions:
        return "No sessions in the past week."
    parts = []
    for s in sessions:
        desc = s.session_type
        if s.actual_distance:
            desc += f" {s.actual_distance:.1f}km"
        if s.total_tonnage:
            desc += f" {s.total_tonnage:.0f}kg"
        parts.append(f"{s.session_date}: {desc}")
    return ", ".join(parts)


def _store_message(
    db: Session,
    message_type: str,
    content: str,
    metadata: Optional[dict] = None,
) -> CoachingMessage:
    msg = CoachingMessage(
        id=uuid.uuid4(),
        message_type=message_type,
        content=content,
        metadata_json=metadata,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


# ── Daily motivation ──────────────────────────────────────────────────────────

async def generate_daily_motivation(db: Session) -> Optional[CoachingMessage]:
    profile = _get_profile(db)
    if not profile:
        return None

    today = date.today()
    streak = _get_streak(db)
    sessions_this_week = (
        db.query(SessionLog)
        .filter(
            SessionLog.session_date >= today - timedelta(days=today.weekday()),
            SessionLog.status == "completed",
        )
        .count()
    )
    planned_today = [
        s.session_type
        for s in db.query(SessionLog)
        .filter(SessionLog.session_date == today, SessionLog.status == "planned")
        .all()
    ]

    user_prompt = build_daily_motivation_prompt(
        name=profile.name,
        current_streak=streak,
        sessions_this_week=sessions_this_week,
        planned_today=planned_today,
        fitness_goal=profile.fitness_goal,
    )

    try:
        result = await ai_client.generate(
            system_prompt=COACHING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=DailyMotivationResponse,
            feature="coaching",
            db=db,
        )
        content = f"{result.emoji} {result.message}"
        return _store_message(db, "daily_motivation", content, {"streak": streak, "date": str(today)})
    except Exception as exc:
        logger.warning("Failed to generate daily motivation: %s", exc)
        return None


# ── Post-workout feedback ─────────────────────────────────────────────────────

async def generate_post_workout_feedback(
    db: Session, session_log_id: uuid.UUID, xp_earned: int = 0
) -> Optional[CoachingMessage]:
    session = db.query(SessionLog).filter(SessionLog.id == session_log_id).first()
    if not session:
        return None

    profile = _get_profile(db)
    name = profile.name if profile else "Athlete"
    streak = _get_streak(db)

    new_prs = [
        f"{pr.exercise_name} ({pr.record_type})"
        for pr in db.query(PersonalRecord)
        .filter(
            PersonalRecord.session_log_id == session_log_id,
            PersonalRecord.celebrated == False,
        )
        .all()
    ]

    duration_minutes = None
    if session.actual_duration:
        duration_minutes = session.actual_duration // 60

    user_prompt = build_post_workout_prompt(
        name=name,
        session_type=session.session_type,
        duration_minutes=duration_minutes,
        rpe=session.overall_rpe,
        new_prs=new_prs,
        streak=streak,
        xp_earned=xp_earned,
    )

    try:
        result = await ai_client.generate(
            system_prompt=COACHING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=PostWorkoutResponse,
            feature="coaching",
            db=db,
        )
        content = f"**{result.headline}** {result.body} {result.next_suggestion}"
        return _store_message(
            db,
            "post_workout",
            content,
            {"session_id": str(session_log_id), "prs": new_prs},
        )
    except Exception as exc:
        logger.warning("Failed to generate post-workout feedback: %s", exc)
        return None


# ── Weekly summary ────────────────────────────────────────────────────────────

async def generate_weekly_summary(db: Session) -> Optional[CoachingMessage]:
    profile = _get_profile(db)
    if not profile:
        return None

    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    completed = (
        db.query(SessionLog)
        .filter(SessionLog.session_date >= week_start, SessionLog.status == "completed")
        .all()
    )
    planned_count = (
        db.query(SessionLog)
        .filter(SessionLog.session_date >= week_start, SessionLog.status.in_(["planned", "completed", "skipped"]))
        .count()
    )

    running_km = sum(s.actual_distance or 0 for s in completed if s.session_type == "running")
    lifting_tonnage = sum(s.total_tonnage or 0 for s in completed if s.session_type == "lifting")
    mobility_minutes = sum((s.actual_duration or 0) // 60 for s in completed if s.session_type == "mobility")

    streak = _get_streak(db)
    new_prs = [
        pr.exercise_name
        for pr in db.query(PersonalRecord)
        .filter(PersonalRecord.created_at >= datetime.combine(week_start, datetime.min.time()))
        .all()
    ]

    user_prompt = build_weekly_summary_prompt(
        name=profile.name,
        sessions_completed=len(completed),
        sessions_planned=planned_count,
        running_km=running_km,
        lifting_tonnage=lifting_tonnage,
        mobility_minutes=mobility_minutes,
        streak=streak,
        new_achievements=[],
        new_prs=new_prs,
    )

    try:
        result = await ai_client.generate(
            system_prompt=COACHING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=WeeklySummaryResponse,
            feature="coaching",
            db=db,
        )
        content_parts = [f"**{result.headline}**", ""]
        content_parts.extend(f"• {h}" for h in result.highlights)
        content_parts.append("")
        content_parts.append(result.encouragement)
        content_parts.append(f"**Next week focus:** {result.focus_next_week}")
        content = "\n".join(content_parts)
        return _store_message(db, "weekly_summary", content, {"week_start": str(week_start)})
    except Exception as exc:
        logger.warning("Failed to generate weekly summary: %s", exc)
        return None


# ── Nudge ─────────────────────────────────────────────────────────────────────

async def generate_nudge(db: Session) -> Optional[CoachingMessage]:
    profile = _get_profile(db)
    if not profile:
        return None

    today = date.today()
    streak = _get_streak(db)
    planned_today = (
        db.query(SessionLog)
        .filter(SessionLog.session_date == today, SessionLog.status == "planned")
        .first()
    )
    if not planned_today:
        return None

    from datetime import datetime
    hour = datetime.now().hour
    time_of_day = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"

    user_prompt = build_nudge_prompt(
        name=profile.name,
        session_type=planned_today.session_type,
        streak=streak,
        time_of_day=time_of_day,
    )

    try:
        result = await ai_client.generate(
            system_prompt=COACHING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=DailyMotivationResponse,
            feature="coaching",
            db=db,
        )
        content = f"{result.emoji} {result.message}"
        return _store_message(db, "nudge", content, {"date": str(today), "streak": streak})
    except Exception as exc:
        logger.warning("Failed to generate nudge: %s", exc)
        return None


# ── Weekly challenge ──────────────────────────────────────────────────────────

async def generate_weekly_challenge(db: Session) -> Optional[WeeklyChallenge]:
    profile = _get_profile(db)
    if not profile:
        return None

    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # Compute averages from past 4 weeks
    four_weeks_ago = week_start - timedelta(weeks=4)
    recent = (
        db.query(SessionLog)
        .filter(SessionLog.session_date >= four_weeks_ago, SessionLog.status == "completed")
        .all()
    )
    sessions_per_week = len(recent) / 4.0
    running_km_avg = sum(s.actual_distance or 0 for s in recent if s.session_type == "running") / 4.0
    lifting_sessions_avg = sum(1 for s in recent if s.session_type == "lifting") / 4.0
    streak = _get_streak(db)

    user_prompt = build_weekly_challenge_prompt(
        name=profile.name,
        sessions_per_week=sessions_per_week,
        running_km_avg=running_km_avg,
        lifting_sessions_avg=lifting_sessions_avg,
        current_streak=streak,
        fitness_goal=profile.fitness_goal,
    )

    try:
        result = await ai_client.generate(
            system_prompt=COACHING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=WeeklyChallengeResponse,
            feature="coaching",
            db=db,
        )
        challenge = WeeklyChallenge(
            id=uuid.uuid4(),
            week_start_date=week_start,
            challenge_type=result.challenge_type,
            title=result.title,
            description=result.description,
            target_value=result.target_value,
            current_value=0.0,
            status="active",
            xp_reward=200,
            generated_by_ai=True,
        )
        db.add(challenge)
        db.commit()
        db.refresh(challenge)
        return challenge
    except Exception as exc:
        logger.warning("Failed to generate weekly challenge: %s", exc)
        return None


# ── Conversational chat ───────────────────────────────────────────────────────

async def chat(db: Session, user_message: str) -> str:
    profile = _get_profile(db)
    name = profile.name if profile else "Athlete"
    streak = _get_streak(db)
    sessions_completed = db.query(SessionLog).filter(SessionLog.status == "completed").count()
    recent_summary = _recent_sessions_summary(db)

    recent_prs = [
        pr.exercise_name
        for pr in db.query(PersonalRecord)
        .order_by(PersonalRecord.created_at.desc())
        .limit(5)
        .all()
    ]

    system_prompt = build_chat_system_prompt(
        name=name,
        current_streak=streak,
        sessions_completed=sessions_completed,
        fitness_goal=profile.fitness_goal if profile else None,
        recent_sessions_summary=recent_summary,
        recent_prs=recent_prs,
    )

    # Include recent chat history for context (last 20 messages)
    history = (
        db.query(ChatMessage)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
        .all()
    )
    history.reverse()
    history_text = "\n".join(f"{m.role.upper()}: {m.content}" for m in history)
    full_user_prompt = f"{history_text}\nUSER: {user_message}" if history_text else user_message

    # Store user message
    db.add(ChatMessage(id=uuid.uuid4(), role="user", content=user_message))
    db.commit()

    try:
        response_text = await ai_client.generate_text(
            system_prompt=system_prompt,
            user_prompt=full_user_prompt,
            feature="coaching_chat",
            db=db,
        )
    except Exception as exc:
        logger.warning("Chat generation failed: %s", exc)
        response_text = "I'm having trouble connecting right now. Try again in a moment!"

    # Store assistant response
    db.add(ChatMessage(id=uuid.uuid4(), role="assistant", content=response_text))
    db.commit()

    return response_text
