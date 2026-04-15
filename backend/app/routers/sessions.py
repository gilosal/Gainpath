from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
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
def update_session(session_id: UUID, payload: SessionLogUpdate, db: Session = Depends(get_db)):
    log = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not log:
        raise HTTPException(404, "Session not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(log, field, value)
    db.commit()
    db.refresh(log)
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
