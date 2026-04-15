"""
Weight training plan prompt + Pydantic response model.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ── Response models ───────────────────────────────────────────────────────────

class ExerciseBlock(BaseModel):
    exercise_name: str
    sets: int
    reps: str                   # "8–10" or "5" or "AMRAP"
    rpe: Optional[str] = None   # "7–8" or "8"
    rest_seconds: int = 90
    tempo: Optional[str] = None # "3-1-1-0" (eccentric-pause-concentric-pause)
    notes: str = ""
    superset_group: Optional[str] = None  # "A", "B" — exercises in same group are done back-to-back


class LiftingSession(BaseModel):
    day_of_week: str
    session_type: str           # push | pull | legs | upper | lower | full_body | rest
    title: str
    description: str
    estimated_duration_minutes: int
    warm_up: list[str] = []     # brief warm-up cues
    exercises: list[ExerciseBlock]
    cool_down: list[str] = []


class LiftingWeek(BaseModel):
    week_number: int
    theme: str                  # e.g. "Hypertrophy Focus", "Strength Block", "Deload"
    sessions: list[LiftingSession]
    weekly_notes: str = ""


class LiftingPlanResponse(BaseModel):
    program_name: str
    split_type: str             # push_pull_legs | upper_lower | full_body | bro_split
    goal: str
    total_weeks: int
    plan_rationale: str = Field(..., description="2–3 sentence explanation")
    weeks: list[LiftingWeek]


# ── Prompt builder ────────────────────────────────────────────────────────────

LIFTING_SYSTEM_PROMPT = """\
You are an expert strength and conditioning coach who designs evidence-based resistance training programs.
You MUST respond with a single JSON object — no markdown, no commentary, no code fences.
The JSON must exactly match the schema below.

SCHEMA:
{
  "program_name": string,
  "split_type": string,          // push_pull_legs | upper_lower | full_body | bro_split
  "goal": string,
  "total_weeks": integer,
  "plan_rationale": string,
  "weeks": [
    {
      "week_number": integer,
      "theme": string,           // e.g. "Hypertrophy Focus", "Strength Block", "Deload"
      "weekly_notes": string,
      "sessions": [
        {
          "day_of_week": string,
          "session_type": string, // push | pull | legs | upper | lower | full_body | rest
          "title": string,
          "description": string,
          "estimated_duration_minutes": integer,
          "warm_up": [string],
          "cool_down": [string],
          "exercises": [
            {
              "exercise_name": string,
              "sets": integer,
              "reps": string,         // "8–10" or "5" or "AMRAP"
              "rpe": string | null,   // "7–8"
              "rest_seconds": integer,
              "tempo": string | null, // "3-1-1-0"
              "notes": string,
              "superset_group": string | null  // "A", "B" for superset pairing
            }
          ]
        }
      ]
    }
  ]
}

Programming principles:
- Match split type to available training days (2d→full body, 3d→upper/lower or PPL start, 4d→upper/lower, 5–6d→PPL)
- Hypertrophy: 3–5 sets × 8–15 reps, RPE 7–9, ~60–90s rest for isolation, 90–120s compound
- Strength: 3–6 sets × 1–6 reps, RPE 8–9.5, 2–5 min rest
- Complement-to-running goal: prioritize upper body and posterior chain, avoid high-volume leg work before long runs
- Include a deload week every 4–5 weeks (volume -40%, intensity maintained)
- Compound movements first in each session, isolation work after
- Never programme two high-volume leg days back-to-back
"""


def build_lifting_prompt(profile: dict, weeks_requested: int = 8) -> str:
    return f"""\
Generate a {weeks_requested}-week weight training program for the following athlete.
Return ONLY the JSON object as specified — no other text.

ATHLETE PROFILE:
- Training goal: {profile.get('weight_training_goal', 'general_fitness')}
- Training days per week: {profile.get('training_days_per_week', 3)}
- Preferred training days: {', '.join(profile.get('training_preferred_days', ['monday','wednesday','friday']))}
- Available equipment: {profile.get('available_equipment', 'full_gym')}
- Also runs: {bool(profile.get('running_goal_race'))} — plan must complement running schedule
- Available days overall: {', '.join(profile.get('available_days', ['monday','wednesday','friday']))}
- Time constraints: {profile.get('session_time_constraints', {})}
- Weight units: {profile.get('units_weight', 'kg')}

Generate exactly {weeks_requested} weeks with sessions on the preferred training days only.
Use "rest" session_type for non-training days. Include deload week(s) as appropriate.
"""
