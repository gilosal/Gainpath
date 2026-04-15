from __future__ import annotations

import asyncio
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.plan import TrainingPlan, PlanWeek, PlannedSession
from ..models.session import SessionLog, BodyFeedback
from ..models.user import UserProfile
from ..schemas.plan import TrainingPlanRead, TrainingPlanSummary
from ..services.ai_client import ai_client, AIGenerationError
from ..prompts.running import build_running_prompt, RunningPlanResponse, RUNNING_SYSTEM_PROMPT
from ..prompts.lifting import build_lifting_prompt, LiftingPlanResponse, LIFTING_SYSTEM_PROMPT
from ..prompts.mobility import build_mobility_prompt, MobilityPlanResponse, MOBILITY_SYSTEM_PROMPT
from ..prompts.scheduling import (
    build_recalculation_prompt,
    RECALCULATION_SYSTEM_PROMPT,
)

router = APIRouter(prefix="/plans", tags=["plans"])

_PLAN_WEEKS = {"running": 12, "lifting": 8, "mobility": 4, "unified": 8}


# ── helpers ───────────────────────────────────────────────────────────────────

def _profile_dict(profile: UserProfile) -> dict:
    return {c.name: getattr(profile, c.name) for c in profile.__table__.columns}


def _persist_running_plan(plan_resp: RunningPlanResponse, profile: UserProfile, db: Session) -> TrainingPlan:
    start = date.today()
    end = start + timedelta(weeks=plan_resp.total_weeks)
    plan = TrainingPlan(
        plan_type="running",
        goal=f"{plan_resp.goal_race} by {plan_resp.goal_date}",
        start_date=start,
        end_date=end,
        status="active",
        weeks_total=plan_resp.total_weeks,
        raw_plan_json=plan_resp.model_dump(),
    )
    db.add(plan)
    db.flush()
    for w in plan_resp.weeks:
        week_start = start + timedelta(weeks=w.week_number - 1)
        plan_week = PlanWeek(
            plan_id=plan.id,
            week_number=w.week_number,
            week_start_date=week_start,
            theme=w.theme,
            total_volume_target=w.total_distance_km,
        )
        db.add(plan_week)
        db.flush()
        for s in w.sessions:
            day_offset = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"].index(s.day_of_week)
            session_date = week_start + timedelta(days=day_offset)
            db.add(PlannedSession(
                plan_week_id=plan_week.id,
                day_of_week=s.day_of_week,
                session_date=session_date,
                session_type="running" if s.session_type != "rest" else "rest",
                session_subtype=s.session_type,
                title=s.title,
                description=s.description,
                estimated_duration=s.duration_minutes,
                exercises=[{
                    "distance_km": s.distance_km,
                    "pace_target": s.pace_target,
                    "effort_zone": s.effort_zone,
                    "intervals": s.intervals,
                    "notes": s.notes,
                }],
            ))
    db.commit()
    db.refresh(plan)
    return plan


def _persist_lifting_plan(plan_resp: LiftingPlanResponse, db: Session) -> TrainingPlan:
    start = date.today()
    end = start + timedelta(weeks=plan_resp.total_weeks)
    plan = TrainingPlan(
        plan_type="lifting",
        goal=plan_resp.goal,
        start_date=start,
        end_date=end,
        status="active",
        weeks_total=plan_resp.total_weeks,
        raw_plan_json=plan_resp.model_dump(),
    )
    db.add(plan)
    db.flush()
    for w in plan_resp.weeks:
        week_start = start + timedelta(weeks=w.week_number - 1)
        plan_week = PlanWeek(
            plan_id=plan.id,
            week_number=w.week_number,
            week_start_date=week_start,
            theme=w.theme,
        )
        db.add(plan_week)
        db.flush()
        for s in w.sessions:
            day_offset = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"].index(s.day_of_week)
            db.add(PlannedSession(
                plan_week_id=plan_week.id,
                day_of_week=s.day_of_week,
                session_date=week_start + timedelta(days=day_offset),
                session_type="lifting" if s.session_type != "rest" else "rest",
                session_subtype=s.session_type,
                title=s.title,
                description=s.description,
                estimated_duration=s.estimated_duration_minutes,
                exercises=[e.model_dump() for e in s.exercises],
            ))
    db.commit()
    db.refresh(plan)
    return plan


def _persist_mobility_plan(plan_resp: MobilityPlanResponse, db: Session) -> TrainingPlan:
    start = date.today()
    end = start + timedelta(weeks=plan_resp.total_weeks)
    plan = TrainingPlan(
        plan_type="mobility",
        goal=plan_resp.goal,
        start_date=start,
        end_date=end,
        status="active",
        weeks_total=plan_resp.total_weeks,
        raw_plan_json=plan_resp.model_dump(),
    )
    db.add(plan)
    db.flush()
    for w in plan_resp.weeks:
        week_start = start + timedelta(weeks=w.week_number - 1)
        plan_week = PlanWeek(
            plan_id=plan.id,
            week_number=w.week_number,
            week_start_date=week_start,
            theme=w.theme,
        )
        db.add(plan_week)
        db.flush()
        for s in w.sessions:
            day_offset = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"].index(s.day_of_week)
            db.add(PlannedSession(
                plan_week_id=plan_week.id,
                day_of_week=s.day_of_week,
                session_date=week_start + timedelta(days=day_offset),
                session_type="mobility" if s.session_subtype != "rest" else "rest",
                session_subtype=s.session_subtype,
                title=s.title,
                description=s.description,
                estimated_duration=s.estimated_duration_minutes,
                exercises=[m.model_dump() for m in s.sequence],
            ))
    db.commit()
    db.refresh(plan)
    return plan


# ── routes ────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[TrainingPlanSummary])
def list_plans(db: Session = Depends(get_db)):
    return db.query(TrainingPlan).order_by(TrainingPlan.created_at.desc()).all()


@router.get("/{plan_id}", response_model=TrainingPlanRead)
def get_plan(plan_id: UUID, db: Session = Depends(get_db)):
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "Plan not found")
    return plan


@router.post("/generate/running", response_model=TrainingPlanRead, status_code=201)
async def generate_running_plan(db: Session = Depends(get_db)):
    profile = db.query(UserProfile).first()
    if not profile:
        raise HTTPException(400, "Complete your profile before generating a plan")
    pdict = _profile_dict(profile)
    user_prompt = build_running_prompt(pdict, _PLAN_WEEKS["running"])
    try:
        resp = await ai_client.generate(
            system_prompt=RUNNING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=RunningPlanResponse,
            feature="plan_generation",
            plan_type="running",
            db=db,
            model_override=profile.preferred_ai_model,
        )
    except AIGenerationError as exc:
        raise HTTPException(502, f"AI generation failed: {exc}")
    return _persist_running_plan(resp, profile, db)


@router.post("/generate/lifting", response_model=TrainingPlanRead, status_code=201)
async def generate_lifting_plan(db: Session = Depends(get_db)):
    profile = db.query(UserProfile).first()
    if not profile:
        raise HTTPException(400, "Complete your profile before generating a plan")
    pdict = _profile_dict(profile)
    user_prompt = build_lifting_prompt(pdict, _PLAN_WEEKS["lifting"])
    try:
        resp = await ai_client.generate(
            system_prompt=LIFTING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=LiftingPlanResponse,
            feature="plan_generation",
            plan_type="lifting",
            db=db,
            model_override=profile.preferred_ai_model,
        )
    except AIGenerationError as exc:
        raise HTTPException(502, f"AI generation failed: {exc}")
    return _persist_lifting_plan(resp, db)


@router.post("/generate/mobility", response_model=TrainingPlanRead, status_code=201)
async def generate_mobility_plan(db: Session = Depends(get_db)):
    profile = db.query(UserProfile).first()
    if not profile:
        raise HTTPException(400, "Complete your profile before generating a plan")
    pdict = _profile_dict(profile)
    user_prompt = build_mobility_prompt(pdict, _PLAN_WEEKS["mobility"])
    try:
        resp = await ai_client.generate(
            system_prompt=MOBILITY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=MobilityPlanResponse,
            feature="plan_generation",
            plan_type="mobility",
            db=db,
            model_override=profile.preferred_ai_model,
        )
    except AIGenerationError as exc:
        raise HTTPException(502, f"AI generation failed: {exc}")
    return _persist_mobility_plan(resp, db)


@router.post("/{plan_id}/recalculate", response_model=TrainingPlanRead)
async def recalculate_plan(plan_id: UUID, db: Session = Depends(get_db)):
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "Plan not found")

    profile = db.query(UserProfile).first()

    # Gather recent logs (last 14 days)
    cutoff = date.today() - timedelta(days=14)
    recent_logs = (
        db.query(SessionLog)
        .filter(SessionLog.session_date >= cutoff, SessionLog.session_type == plan.plan_type)
        .order_by(SessionLog.session_date.desc())
        .limit(20)
        .all()
    )
    body_fb = (
        db.query(BodyFeedback)
        .join(SessionLog)
        .filter(SessionLog.session_date >= cutoff)
        .order_by(BodyFeedback.logged_at.desc())
        .limit(30)
        .all()
    )

    weeks_remaining = max(1, (plan.end_date - date.today()).days // 7)

    logs_dicts = [{c.name: getattr(l, c.name) for c in l.__table__.columns} for l in recent_logs]
    fb_dicts = [{c.name: getattr(f, c.name) for c in f.__table__.columns} for f in body_fb]

    # Select correct response model and system prompt
    model_map = {
        "running": (RunningPlanResponse, RUNNING_SYSTEM_PROMPT),
        "lifting": (LiftingPlanResponse, LIFTING_SYSTEM_PROMPT),
        "mobility": (MobilityPlanResponse, MOBILITY_SYSTEM_PROMPT),
    }
    if plan.plan_type not in model_map:
        raise HTTPException(400, f"Recalculation not supported for plan type: {plan.plan_type}")

    response_model, system_prompt = model_map[plan.plan_type]
    user_prompt = build_recalculation_prompt(
        plan_type=plan.plan_type,
        original_plan_summary=plan.raw_plan_json or {},
        recent_logs=logs_dicts,
        body_feedback=fb_dicts,
        weeks_remaining=weeks_remaining,
    )

    try:
        resp = await ai_client.generate(
            system_prompt=RECALCULATION_SYSTEM_PROMPT + "\n\n" + system_prompt,
            user_prompt=user_prompt,
            response_model=response_model,
            feature="recalculation",
            plan_type=plan.plan_type,
            db=db,
            model_override=profile.preferred_ai_model if profile else None,
        )
    except AIGenerationError as exc:
        raise HTTPException(502, f"AI recalculation failed: {exc}")

    # Archive old plan and persist new one
    plan.status = "archived"
    db.commit()

    if plan.plan_type == "running":
        return _persist_running_plan(resp, profile, db)
    elif plan.plan_type == "lifting":
        return _persist_lifting_plan(resp, db)
    else:
        return _persist_mobility_plan(resp, db)


@router.delete("/{plan_id}", status_code=204)
def delete_plan(plan_id: UUID, db: Session = Depends(get_db)):
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "Plan not found")
    db.delete(plan)
    db.commit()
