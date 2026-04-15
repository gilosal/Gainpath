"""
Running plan prompt + Pydantic response model.

The AI receives the athlete's profile and returns a fully structured
multi-week training plan in strict JSON that maps to RunningPlanResponse.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ── Response models ───────────────────────────────────────────────────────────

class RunSession(BaseModel):
    day_of_week: str            # "monday" … "sunday"
    session_type: str           # easy_run | tempo | intervals | long_run | recovery_run | rest
    title: str
    description: str
    distance_km: Optional[float] = None
    duration_minutes: Optional[int] = None
    pace_target: Optional[str] = None    # e.g. "5:30–5:45/km"
    effort_zone: Optional[str] = None    # zone1 … zone5 or easy/moderate/hard/max
    intervals: Optional[list[dict]] = None  # [{reps, distance_m, target_pace, rest_seconds}]
    notes: str = ""


class RunWeek(BaseModel):
    week_number: int
    theme: str                  # e.g. "Base Building", "Speed Focus", "Taper"
    total_distance_km: float
    sessions: list[RunSession]


class RunningPlanResponse(BaseModel):
    goal_race: str
    goal_date: str              # ISO date string
    total_weeks: int
    target_finish_time: Optional[str] = None
    plan_rationale: str = Field(..., description="2–3 sentence explanation of the overall approach")
    weeks: list[RunWeek]


# ── Prompt builder ────────────────────────────────────────────────────────────

RUNNING_SYSTEM_PROMPT = """\
You are an expert running coach who designs evidence-based training plans.
You MUST respond with a single JSON object — no markdown, no commentary, no code fences.
The JSON must exactly match the schema below.

SCHEMA:
{
  "goal_race": string,            // "5k" | "10k" | "half_marathon" | "marathon"
  "goal_date": string,            // ISO 8601 date "YYYY-MM-DD"
  "total_weeks": integer,
  "target_finish_time": string | null,
  "plan_rationale": string,       // 2–3 sentences
  "weeks": [
    {
      "week_number": integer,
      "theme": string,
      "total_distance_km": number,
      "sessions": [
        {
          "day_of_week": string,  // "monday" through "sunday"
          "session_type": string, // easy_run | tempo | intervals | long_run | recovery_run | rest
          "title": string,
          "description": string,
          "distance_km": number | null,
          "duration_minutes": integer | null,
          "pace_target": string | null,   // e.g. "5:30–5:45/km"
          "effort_zone": string | null,   // easy | moderate | threshold | hard | max
          "intervals": [                  // only for interval sessions
            {"reps": int, "distance_m": int, "target_pace": string, "rest_seconds": int}
          ] | null,
          "notes": string
        }
      ]
    }
  ]
}

Training principles to follow:
- 80/20 rule: ~80% of weekly volume at easy/zone2 effort, 20% quality work
- Progressive overload: increase weekly volume ≤10% week-over-week
- Recovery weeks every 3–4 weeks at 60–70% of peak volume
- Taper in final 2–3 weeks before goal race
- Never schedule quality sessions (tempo/intervals) on consecutive days
"""


def build_running_prompt(profile: dict, weeks_requested: int = 12) -> str:
    return f"""\
Generate a {weeks_requested}-week running training plan for the following athlete.
Return ONLY the JSON object as specified — no other text.

ATHLETE PROFILE:
- Goal race: {profile.get('running_goal_race', '10k')}
- Goal date: {profile.get('running_goal_date', 'in 12 weeks')}
- Fitness level: {profile.get('running_fitness_level', 'intermediate')}
- Current weekly mileage: {profile.get('running_weekly_mileage', 30)} km/week
- Recent race time: {profile.get('running_recent_race_time', 'none')}
- Available days: {', '.join(profile.get('available_days', ['monday','wednesday','thursday','saturday','sunday']))}
- Time constraints: {profile.get('session_time_constraints', {})}
- Distance units: {profile.get('units_distance', 'km')}

Build exactly {weeks_requested} weeks. Every week must have 5–6 entries covering all available days
(use "rest" type for rest/cross-training days). Include warm-up/cool-down guidance in the
description field for quality sessions.
"""
