from __future__ import annotations

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.gamification import (
    StreakSnapshot, Achievement, UserAchievement, XPLedger,
    WeeklyChallenge, PersonalRecord,
)
from ..models.user import UserProfile
from ..services.streak_engine import get_streak, use_streak_freeze

router = APIRouter(prefix="/gamification", tags=["gamification"])


# ── Pydantic response schemas ─────────────────────────────────────────────────

class StreakRead(BaseModel):
    current_streak: int
    longest_streak: int
    streak_start_date: Optional[str]
    last_workout_date: Optional[str]
    streak_frozen: bool
    freeze_available: bool  # True if no freeze used in last 7 days

    model_config = {"from_attributes": True}


class AchievementRead(BaseModel):
    id: str
    slug: str
    name: str
    description: str
    icon_name: str
    category: str
    threshold: int
    xp_reward: int
    earned: bool
    earned_at: Optional[str] = None

    model_config = {"from_attributes": True}


class XPStateRead(BaseModel):
    total_xp: int
    level: int
    xp_to_next_level: int
    recent_entries: list[dict]

    model_config = {"from_attributes": True}


class ChallengeRead(BaseModel):
    id: str
    week_start_date: str
    challenge_type: str
    title: str
    description: str
    target_value: float
    current_value: float
    status: str
    xp_reward: int
    progress_pct: float

    model_config = {"from_attributes": True}


class PRRead(BaseModel):
    id: str
    created_at: str
    exercise_name: str
    record_type: str
    value: float
    previous_value: Optional[float]
    celebrated: bool

    model_config = {"from_attributes": True}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _level_xp_required(level: int) -> int:
    """XP required to reach level N: 100 * (level-1)^2"""
    return 100 * (level - 1) ** 2


def _xp_to_next_level(total_xp: int, level: int) -> int:
    next_threshold = _level_xp_required(level + 1)
    return max(0, next_threshold - total_xp)


def _freeze_available(snap: StreakSnapshot) -> bool:
    if not snap.freeze_used_at:
        return True
    from datetime import date
    return (date.today() - snap.freeze_used_at).days >= 7


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/streak", response_model=StreakRead)
def streak(db: Session = Depends(get_db)):
    snap = get_streak(db)
    return StreakRead(
        current_streak=snap.current_streak,
        longest_streak=snap.longest_streak,
        streak_start_date=str(snap.streak_start_date) if snap.streak_start_date else None,
        last_workout_date=str(snap.last_workout_date) if snap.last_workout_date else None,
        streak_frozen=snap.streak_frozen,
        freeze_available=_freeze_available(snap),
    )


@router.post("/streak/freeze")
def freeze_streak(db: Session = Depends(get_db)):
    success, message = use_streak_freeze(db)
    if not success:
        raise HTTPException(400, message)
    return {"message": message}


@router.get("/achievements", response_model=list[AchievementRead])
def achievements(db: Session = Depends(get_db)):
    all_ach = db.query(Achievement).all()
    earned_map = {
        ua.achievement_id: ua.earned_at
        for ua in db.query(UserAchievement).all()
    }
    result = []
    for ach in all_ach:
        result.append(AchievementRead(
            id=str(ach.id),
            slug=ach.slug,
            name=ach.name,
            description=ach.description,
            icon_name=ach.icon_name,
            category=ach.category,
            threshold=ach.threshold,
            xp_reward=ach.xp_reward,
            earned=ach.id in earned_map,
            earned_at=str(earned_map[ach.id]) if ach.id in earned_map else None,
        ))
    # Sort: earned first, then by category
    result.sort(key=lambda a: (not a.earned, a.category))
    return result


@router.get("/xp", response_model=XPStateRead)
def xp_state(db: Session = Depends(get_db)):
    profile = db.query(UserProfile).first()
    total_xp = profile.total_xp if profile else 0
    level = profile.level if profile else 1

    recent = (
        db.query(XPLedger)
        .order_by(XPLedger.created_at.desc())
        .limit(10)
        .all()
    )
    return XPStateRead(
        total_xp=total_xp,
        level=level,
        xp_to_next_level=_xp_to_next_level(total_xp, level),
        recent_entries=[
            {"amount": e.amount, "source": e.source, "note": e.note, "created_at": str(e.created_at)}
            for e in recent
        ],
    )


@router.get("/challenges", response_model=list[ChallengeRead])
def challenges(db: Session = Depends(get_db)):
    rows = (
        db.query(WeeklyChallenge)
        .order_by(WeeklyChallenge.week_start_date.desc())
        .limit(8)
        .all()
    )
    result = []
    for c in rows:
        pct = min(100.0, (c.current_value / c.target_value * 100) if c.target_value > 0 else 0)
        result.append(ChallengeRead(
            id=str(c.id),
            week_start_date=str(c.week_start_date),
            challenge_type=c.challenge_type,
            title=c.title,
            description=c.description,
            target_value=c.target_value,
            current_value=c.current_value,
            status=c.status,
            xp_reward=c.xp_reward,
            progress_pct=round(pct, 1),
        ))
    return result


@router.get("/prs", response_model=list[PRRead])
def personal_records(
    exercise: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(PersonalRecord).order_by(PersonalRecord.created_at.desc())
    if exercise:
        q = q.filter(PersonalRecord.exercise_name.ilike(f"%{exercise}%"))
    rows = q.limit(100).all()
    return [
        PRRead(
            id=str(r.id),
            created_at=str(r.created_at),
            exercise_name=r.exercise_name,
            record_type=r.record_type,
            value=r.value,
            previous_value=r.previous_value,
            celebrated=r.celebrated,
        )
        for r in rows
    ]


@router.get("/prs/uncelebrated", response_model=list[PRRead])
def uncelebrated_prs(db: Session = Depends(get_db)):
    rows = (
        db.query(PersonalRecord)
        .filter(PersonalRecord.celebrated == False)
        .order_by(PersonalRecord.created_at.desc())
        .all()
    )
    return [
        PRRead(
            id=str(r.id),
            created_at=str(r.created_at),
            exercise_name=r.exercise_name,
            record_type=r.record_type,
            value=r.value,
            previous_value=r.previous_value,
            celebrated=r.celebrated,
        )
        for r in rows
    ]


@router.patch("/prs/{pr_id}/celebrate")
def celebrate_pr(pr_id: UUID, db: Session = Depends(get_db)):
    pr = db.query(PersonalRecord).filter(PersonalRecord.id == pr_id).first()
    if not pr:
        raise HTTPException(404, "Personal record not found")
    pr.celebrated = True
    db.commit()
    return {"ok": True}
