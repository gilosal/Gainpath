"""
pr_detector.py — Personal record detection.

For lifting: uses the Epley formula to estimate 1RM from each working set,
then compares against the stored personal record for that exercise.

For running: detects fastest pace per distance bracket and longest distance.

Called in a background task after each session completion.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ..models.gamification import PersonalRecord
from ..models.session import SessionLog, SetLog

logger = logging.getLogger(__name__)


def _epley_1rm(weight: float, reps: int) -> float:
    """Epley formula: 1RM estimate from a multi-rep set."""
    if reps == 1:
        return weight
    return weight * (1 + reps / 30.0)


def _get_current_pr(db: Session, exercise_name: str, record_type: str) -> Optional[PersonalRecord]:
    return (
        db.query(PersonalRecord)
        .filter(
            PersonalRecord.exercise_name == exercise_name,
            PersonalRecord.record_type == record_type,
        )
        .order_by(PersonalRecord.value.desc())
        .first()
    )


def detect_prs_for_session(db: Session, session_log_id: uuid.UUID) -> list[PersonalRecord]:
    """
    Detect new personal records for all exercises in the given session.
    Returns a list of newly created PersonalRecord rows.
    """
    session = db.query(SessionLog).filter(SessionLog.id == session_log_id).first()
    if not session:
        return []

    new_prs: list[PersonalRecord] = []

    if session.session_type == "lifting":
        new_prs.extend(_detect_lifting_prs(db, session))
    elif session.session_type == "running":
        new_prs.extend(_detect_running_prs(db, session))

    if new_prs:
        db.commit()

    return new_prs


def _detect_lifting_prs(db: Session, session: SessionLog) -> list[PersonalRecord]:
    new_prs: list[PersonalRecord] = []

    # Group sets by exercise name
    sets_by_exercise: dict[str, list[SetLog]] = {}
    for s in session.sets:
        if s.set_type not in ("working", "failure"):
            continue
        if not s.weight or not s.reps:
            continue
        sets_by_exercise.setdefault(s.exercise_name, []).append(s)

    for exercise_name, sets in sets_by_exercise.items():
        # Best estimated 1RM from this session
        best_1rm = max(_epley_1rm(s.weight, s.reps) for s in sets)
        best_set = max(sets, key=lambda s: _epley_1rm(s.weight, s.reps))

        current_pr = _get_current_pr(db, exercise_name, "weight_1rm")
        if current_pr is None or best_1rm > current_pr.value:
            pr = PersonalRecord(
                id=uuid.uuid4(),
                exercise_name=exercise_name,
                record_type="weight_1rm",
                value=round(best_1rm, 2),
                previous_value=current_pr.value if current_pr else None,
                set_log_id=best_set.id,
                session_log_id=session.id,
                celebrated=False,
            )
            db.add(pr)
            new_prs.append(pr)
            logger.info("New PR: %s 1RM = %.1f (prev: %s)", exercise_name, best_1rm, current_pr.value if current_pr else "none")

    return new_prs


def _detect_running_prs(db: Session, session: SessionLog) -> list[PersonalRecord]:
    new_prs: list[PersonalRecord] = []

    # Longest distance PR
    if session.actual_distance:
        current_pr = _get_current_pr(db, "running", "longest_distance")
        if current_pr is None or session.actual_distance > current_pr.value:
            pr = PersonalRecord(
                id=uuid.uuid4(),
                exercise_name="running",
                record_type="longest_distance",
                value=session.actual_distance,
                previous_value=current_pr.value if current_pr else None,
                session_log_id=session.id,
                celebrated=False,
            )
            db.add(pr)
            new_prs.append(pr)

    # Fastest pace PR (lower is better — min/km)
    if session.actual_pace and session.actual_distance:
        # Only compare within similar distance brackets to avoid unfair comparison
        bracket = _distance_bracket(session.actual_distance)
        if bracket:
            current_pr = _get_current_pr(db, f"running_pace_{bracket}", "fastest_pace")
            # For pace, lower value is better, so we need special handling
            if current_pr is None or session.actual_pace < current_pr.value:
                pr = PersonalRecord(
                    id=uuid.uuid4(),
                    exercise_name=f"running_pace_{bracket}",
                    record_type="fastest_pace",
                    value=session.actual_pace,
                    previous_value=current_pr.value if current_pr else None,
                    session_log_id=session.id,
                    celebrated=False,
                )
                db.add(pr)
                new_prs.append(pr)

    return new_prs


def _distance_bracket(distance_km: float) -> Optional[str]:
    """Return a named distance bracket for pace comparison."""
    if distance_km < 1.5:
        return "1k"
    elif distance_km < 3.5:
        return "3k"
    elif distance_km < 7.0:
        return "5k"
    elif distance_km < 12.0:
        return "10k"
    elif distance_km < 16.0:
        return "half_marathon"
    elif distance_km < 35.0:
        return "marathon"
    else:
        return "ultra"
