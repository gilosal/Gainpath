from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.session import SessionLog, SetLog, BodyFeedback
from ..models.plan import PlannedSession
from ..schemas.session import (
    SessionLogCreate, SessionLogUpdate, SessionLogRead,
    SetLogCreate, SetLogRead,
    BodyFeedbackCreate, BodyFeedbackRead,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


async def _on_session_completed(session_id: UUID, rpe: Optional[int]) -> None:
    """Background task chain triggered when a session is marked completed.

    Each step is isolated so a failure in one does not block the others.
    Uses its own DB session since the request session is closed by the time
    this background task runs.
    """
    import logging
    from ..database import SessionLocal
    from ..services.pr_detector import detect_prs_for_session
    from ..services.streak_engine import update_streak
    from ..services.achievement_engine import check_achievements, grant_xp, xp_for_session
    from ..services.coaching_engine import generate_post_workout_feedback

    log = logging.getLogger(__name__)
    db = SessionLocal()
    try:
        session = db.query(SessionLog).filter(SessionLog.id == session_id).first()
        if not session:
            return

        new_prs: list = []

        # 1. Detect personal records
        try:
            new_prs = detect_prs_for_session(db, session_id)
        except Exception:
            log.exception("PR detection failed for session %s", session_id)

        # 2. Update streak
        try:
            update_streak(db)
        except Exception:
            log.exception("Streak update failed for session %s", session_id)

        # 3. Grant XP
        xp = 0
        try:
            xp = xp_for_session(session.session_type, rpe)
            grant_xp(db, xp, "workout_complete", session_id, f"{session.session_type} session")
        except Exception:
            log.exception("XP grant failed for session %s", session_id)

        # 4. Check achievements
        try:
            context = {"completed_at": session.completed_at or datetime.utcnow()}
            check_achievements(db, "session_completed", context)
            if new_prs:
                check_achievements(db, "pr_detected", {})
            check_achievements(db, "streak_updated", {})
        except Exception:
            log.exception("Achievement check failed for session %s", session_id)

        # 5. Generate post-workout coaching message
        try:
            await generate_post_workout_feedback(db, session_id, xp)
        except Exception:
            log.exception("Post-workout coaching failed for session %s", session_id)
    finally:
        db.close()


# ── Session logs ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[SessionLogRead])
def list_sessions(
    session_date: Optional[date] = Query(None),
    session_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(SessionLog)
    if session_date:
        q = q.filter(SessionLog.session_date == session_date)
    if session_type:
        q = q.filter(SessionLog.session_type == session_type)
    return q.order_by(SessionLog.session_date.desc()).limit(limit).all()


@router.get("/today", response_model=list[SessionLogRead])
def get_today_sessions(db: Session = Depends(get_db)):
    today = date.today()
    # Return existing logs or create stubs from planned sessions
    logs = db.query(SessionLog).filter(SessionLog.session_date == today).all()
    if not logs:
        planned = (
            db.query(PlannedSession)
            .filter(PlannedSession.session_date == today)
            .all()
        )
        for ps in planned:
            if ps.session_type != "rest":
                log = SessionLog(
                    planned_session_id=ps.id,
                    session_date=today,
                    session_type=ps.session_type,
                    status="planned",
                )
                db.add(log)
        if planned:
            db.commit()
            logs = db.query(SessionLog).filter(SessionLog.session_date == today).all()
    return logs


@router.post("", response_model=SessionLogRead, status_code=201)
def create_session(payload: SessionLogCreate, db: Session = Depends(get_db)):
    log = SessionLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/{session_id}", response_model=SessionLogRead)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    log = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not log:
        raise HTTPException(404, "Session not found")
    return log


@router.patch("/{session_id}", response_model=SessionLogRead)
async def update_session(
    session_id: UUID,
    payload: SessionLogUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    log = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not log:
        raise HTTPException(404, "Session not found")

    was_completed = log.status == "completed"
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(log, field, value)

    if not was_completed and log.status == "completed":
        if log.completed_at is None:
            log.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(log)

    if not was_completed and log.status == "completed":
        background_tasks.add_task(_on_session_completed, session_id, log.overall_rpe)

    return log


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: UUID, db: Session = Depends(get_db)):
    log = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not log:
        raise HTTPException(404, "Session not found")
    db.delete(log)
    db.commit()


# ── Set logs ──────────────────────────────────────────────────────────────────

@router.post("/{session_id}/sets", response_model=SetLogRead, status_code=201)
def add_set(session_id: UUID, payload: SetLogCreate, db: Session = Depends(get_db)):
    log = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not log:
        raise HTTPException(404, "Session not found")
    set_log = SetLog(session_log_id=session_id, **payload.model_dump())
    db.add(set_log)
    # Update lifting tonnage aggregate
    if payload.weight and payload.reps:
        log.total_tonnage = (log.total_tonnage or 0.0) + (payload.weight * payload.reps)
    db.commit()
    db.refresh(set_log)
    return set_log


@router.patch("/{session_id}/sets/{set_id}", response_model=SetLogRead)
def update_set(session_id: UUID, set_id: UUID, payload: SetLogCreate, db: Session = Depends(get_db)):
    set_log = db.query(SetLog).filter(
        SetLog.id == set_id, SetLog.session_log_id == session_id
    ).first()
    if not set_log:
        raise HTTPException(404, "Set not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(set_log, field, value)
    db.commit()
    db.refresh(set_log)
    return set_log


@router.delete("/{session_id}/sets/{set_id}", status_code=204)
def delete_set(session_id: UUID, set_id: UUID, db: Session = Depends(get_db)):
    set_log = db.query(SetLog).filter(
        SetLog.id == set_id, SetLog.session_log_id == session_id
    ).first()
    if not set_log:
        raise HTTPException(404, "Set not found")
    db.delete(set_log)
    db.commit()


# ── Body feedback ─────────────────────────────────────────────────────────────

@router.post("/{session_id}/feedback", response_model=BodyFeedbackRead, status_code=201)
def add_body_feedback(session_id: UUID, payload: BodyFeedbackCreate, db: Session = Depends(get_db)):
    log = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not log:
        raise HTTPException(404, "Session not found")
    fb = BodyFeedback(session_log_id=session_id, **payload.model_dump())
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


@router.get("/{session_id}/feedback", response_model=list[BodyFeedbackRead])
def list_body_feedback(session_id: UUID, db: Session = Depends(get_db)):
    return db.query(BodyFeedback).filter(BodyFeedback.session_log_id == session_id).all()
