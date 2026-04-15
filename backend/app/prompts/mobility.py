"""
Mobility / yoga / stretching plan prompt + Pydantic response model.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ── Response models ───────────────────────────────────────────────────────────

class MobilityMove(BaseModel):
    name: str
    target_area: str                    # hips | hamstrings | shoulders | lower_back | etc.
    hold_duration_seconds: Optional[int] = None   # for static holds
    reps: Optional[int] = None          # for dynamic movements
    sets: Optional[int] = None
    body_side: str = "bilateral"        # bilateral | left_right | left | right
    instructions: str
    beginner_modification: Optional[str] = None
    advanced_progression: Optional[str] = None
    props_needed: list[str] = []        # ["yoga block", "strap"] or []


class MobilitySession(BaseModel):
    day_of_week: str
    session_subtype: str    # active_recovery_yoga | pre_run_dynamic | post_run_static |
                            # dedicated_flexibility | foam_rolling | rest
    title: str
    description: str
    estimated_duration_minutes: int
    focus_areas: list[str]
    sequence: list[MobilityMove]
    session_notes: str = ""


class MobilityWeek(BaseModel):
    week_number: int
    theme: str
    sessions: list[MobilitySession]


class MobilityPlanResponse(BaseModel):
    goal: str
    total_weeks: int
    plan_rationale: str = Field(..., description="2–3 sentence explanation")
    weeks: list[MobilityWeek]


# ── Prompt builder ────────────────────────────────────────────────────────────

MOBILITY_SYSTEM_PROMPT = """\
You are a certified yoga instructor and mobility specialist who designs evidence-based flexibility
and recovery programs.
You MUST respond with a single JSON object — no markdown, no commentary, no code fences.
The JSON must exactly match the schema below.

SCHEMA:
{
  "goal": string,
  "total_weeks": integer,
  "plan_rationale": string,
  "weeks": [
    {
      "week_number": integer,
      "theme": string,
      "sessions": [
        {
          "day_of_week": string,
          "session_subtype": string,   // active_recovery_yoga | pre_run_dynamic | post_run_static | dedicated_flexibility | foam_rolling | rest
          "title": string,
          "description": string,
          "estimated_duration_minutes": integer,
          "focus_areas": [string],
          "session_notes": string,
          "sequence": [
            {
              "name": string,
              "target_area": string,
              "hold_duration_seconds": integer | null,
              "reps": integer | null,
              "sets": integer | null,
              "body_side": string,            // "bilateral" | "left_right" | "left" | "right"
              "instructions": string,
              "beginner_modification": string | null,
              "advanced_progression": string | null,
              "props_needed": [string]
            }
          ]
        }
      ]
    }
  ]
}

Design principles:
- Pre-run sessions: dynamic movements only (leg swings, hip circles, high knees, arm circles) — 5–10 min
- Post-run sessions: static holds 30–60 sec focused on calves, hamstrings, hip flexors, quads
- Active recovery yoga: flowing sequences, moderate holds, full-body focus — 20–45 min
- Dedicated flexibility: targeted long holds (60–120 sec), PNF techniques for problem areas
- Foam rolling: 30–60 sec per muscle group, 2–3 passes, pause on tender spots
- Schedule pre-run sessions on run days (before), post-run sessions on run days (after)
- Schedule active recovery / dedicated flexibility on rest days or easy days
- Adapt based on stated problem areas — give them extra attention each week
- Progress gradually: begin with shorter holds and simpler poses, advance over weeks
"""


def build_mobility_prompt(profile: dict, weeks_requested: int = 4) -> str:
    return f"""\
Generate a {weeks_requested}-week mobility and flexibility program for the following athlete.
Return ONLY the JSON object as specified — no other text.

ATHLETE PROFILE:
- Mobility goal: {profile.get('mobility_goal', 'general_flexibility')}
- Problem / target areas: {', '.join(profile.get('mobility_target_areas', ['hips', 'hamstrings']))}
- Experience level: {profile.get('mobility_experience', 'beginner')}
- Preferred session length: {profile.get('mobility_session_length', 20)} minutes
- Available days: {', '.join(profile.get('available_days', ['monday','wednesday','friday','sunday']))}
- Also runs: {bool(profile.get('running_goal_race'))} on days: {profile.get('running_days_hint', 'unknown')}
- Also lifts: {bool(profile.get('weight_training_goal'))} — schedule mobility to complement

Generate exactly {weeks_requested} weeks. Include pre/post-run sessions on run days where applicable.
Use "rest" subtype for days with no mobility work. Each session's sequence should be ordered
for safe flow (dynamic before static, large muscle groups before small).
"""
