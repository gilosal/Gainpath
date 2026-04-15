"""
Unified scheduling prompt + Pydantic response model.

This prompt takes pre-generated running, lifting, and mobility plans and
coordinates them into a single conflict-free weekly schedule, respecting
recovery, progressive overload, and the athlete's time constraints.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ── Response models ───────────────────────────────────────────────────────────

class ScheduledBlock(BaseModel):
    plan_type: str              # running | lifting | mobility
    session_subtype: str        # e.g. "long_run", "legs", "post_run_static"
    title: str
    estimated_duration_minutes: int
    order_in_day: int           # 1 = first session of the day, 2 = second (stacked)
    is_stacked: bool            # True if paired with another session same day
    notes: str = ""


class ScheduledDay(BaseModel):
    day_of_week: str
    date: str                   # ISO date "YYYY-MM-DD"
    total_duration_minutes: int
    recovery_level: str         # high | moderate | low (how hard this day is overall)
    blocks: list[ScheduledBlock]
    day_notes: str = ""


class ScheduledWeek(BaseModel):
    week_number: int
    week_start_date: str        # ISO date "YYYY-MM-DD"
    theme: str
    weekly_notes: str = ""
    days: list[ScheduledDay]    # always 7 days


class UnifiedScheduleResponse(BaseModel):
    total_weeks: int
    scheduling_rationale: str = Field(..., description="2–3 sentences explaining key coordination decisions")
    weeks: list[ScheduledWeek]


# ── Prompt builder ────────────────────────────────────────────────────────────

SCHEDULING_SYSTEM_PROMPT = """\
You are an expert athletic performance coordinator who creates integrated multi-discipline
training schedules.
You MUST respond with a single JSON object — no markdown, no commentary, no code fences.
The JSON must exactly match the schema below.

SCHEMA:
{
  "total_weeks": integer,
  "scheduling_rationale": string,
  "weeks": [
    {
      "week_number": integer,
      "week_start_date": string,   // "YYYY-MM-DD"
      "theme": string,
      "weekly_notes": string,
      "days": [
        {
          "day_of_week": string,
          "date": string,              // "YYYY-MM-DD"
          "total_duration_minutes": integer,
          "recovery_level": string,    // "high" | "moderate" | "low"
          "day_notes": string,
          "blocks": [
            {
              "plan_type": string,          // "running" | "lifting" | "mobility"
              "session_subtype": string,
              "title": string,
              "estimated_duration_minutes": integer,
              "order_in_day": integer,      // 1 for first, 2 for second session
              "is_stacked": boolean,
              "notes": string
            }
          ]
        }
      ]
    }
  ]
}

Coordination rules (MUST follow):
1. NEVER place a heavy leg day (squats/deadlifts/lunges) the day before or after a long run or interval session
2. NEVER place two high-intensity sessions (tempo run, intervals, heavy strength) on consecutive days
3. ALWAYS append a 10–20 min post-run static stretch block on long run and tempo days
4. ALWAYS prepend a 5–10 min dynamic warm-up block on interval and heavy lifting days
5. Schedule at least one complete rest day per week (no sessions at all)
6. Foam rolling / active recovery yoga belongs on rest days or after easy sessions
7. Morning session order: mobility warm-up → main session → cool-down/stretch
8. Respect per-day time caps — never exceed them even if it means splitting a session
9. If a day has a run AND a lift, separate them by at least 4 hours if possible (morning + evening)
10. Recovery level: "high" = long run / heavy compound lifting, "moderate" = tempo / moderate lifting, "low" = easy run / mobility / rest
"""


def build_scheduling_prompt(
    profile: dict,
    running_plan_summary: Optional[dict],
    lifting_plan_summary: Optional[dict],
    mobility_plan_summary: Optional[dict],
    week_start_date: str,
    weeks_requested: int = 1,
) -> str:
    parts = ["Coordinate the following training blocks into a unified weekly schedule."]
    parts.append("Return ONLY the JSON object as specified — no other text.\n")

    parts.append(f"ATHLETE PROFILE:")
    parts.append(f"- Available days: {', '.join(profile.get('available_days', []))}")
    parts.append(f"- Time constraints per day: {profile.get('session_time_constraints', {})}")
    parts.append(f"- No morning sessions on: {profile.get('no_morning_days', [])}")
    parts.append(f"- Schedule start date: {week_start_date}")
    parts.append(f"- Weeks to schedule: {weeks_requested}\n")

    if running_plan_summary:
        parts.append(f"RUNNING SESSIONS THIS PERIOD:")
        for w in running_plan_summary.get("weeks", []):
            for s in w.get("sessions", []):
                parts.append(
                    f"  Week {w['week_number']} {s['day_of_week']}: {s['session_type']} "
                    f"— {s.get('distance_km', '?')}km / {s.get('duration_minutes', '?')}min"
                )

    if lifting_plan_summary:
        parts.append(f"\nLIFTING SESSIONS THIS PERIOD:")
        for w in lifting_plan_summary.get("weeks", []):
            for s in w.get("sessions", []):
                if s.get("session_type") != "rest":
                    parts.append(
                        f"  Week {w['week_number']} {s['day_of_week']}: {s['session_type']} "
                        f"— ~{s.get('estimated_duration_minutes', '?')}min"
                    )

    if mobility_plan_summary:
        parts.append(f"\nMOBILITY SESSIONS THIS PERIOD:")
        for w in mobility_plan_summary.get("weeks", []):
            for s in w.get("sessions", []):
                if s.get("session_subtype") != "rest":
                    parts.append(
                        f"  Week {w['week_number']} {s['day_of_week']}: {s['session_subtype']} "
                        f"— {s.get('estimated_duration_minutes', '?')}min"
                    )

    parts.append(
        "\nProduce a day-by-day schedule for all 7 days of each week. "
        "Empty days get an empty blocks list. Apply all coordination rules strictly."
    )
    return "\n".join(parts)


# ── Recalculation prompt ──────────────────────────────────────────────────────

RECALCULATION_SYSTEM_PROMPT = """\
You are an expert athletic coach who adjusts training plans based on logged progress and athlete feedback.
You MUST respond with a single JSON object — no markdown, no commentary, no code fences.
Respond with the same schema as a standard plan response for the given plan_type.
"""


def build_recalculation_prompt(
    plan_type: str,
    original_plan_summary: dict,
    recent_logs: list[dict],
    body_feedback: list[dict],
    weeks_remaining: int,
) -> str:
    return f"""\
Adjust the remaining {weeks_remaining} weeks of this {plan_type} training plan based on the athlete's recent performance.
Return ONLY the JSON object — no other text.

ORIGINAL PLAN GOAL: {original_plan_summary.get('goal', 'not specified')}
WEEKS REMAINING: {weeks_remaining}

RECENT SESSION LOGS (last 2 weeks):
{_format_logs(recent_logs)}

BODY FEEDBACK:
{_format_feedback(body_feedback)}

ADJUSTMENT INSTRUCTIONS:
- If athlete is consistently performing above prescription → increase intensity/volume by 5–10%
- If athlete is struggling (high RPE, missed sessions) → reduce volume by 10–15%, add recovery
- If recurring body area pain/tightness is flagged → reduce load on that area, add targeted mobility
- Maintain the overall goal and peak week timing
- Do not change the plan_type or goal structure — only adjust the upcoming week sessions
"""


def _format_logs(logs: list[dict]) -> str:
    if not logs:
        return "  No recent logs."
    lines = []
    for log in logs[-10:]:  # last 10 logs max
        lines.append(
            f"  {log.get('session_date')} | {log.get('session_type')} | "
            f"status={log.get('status')} | rpe={log.get('overall_rpe')} | "
            f"distance={log.get('actual_distance')} | duration={log.get('actual_duration')}"
        )
    return "\n".join(lines)


def _format_feedback(feedback: list[dict]) -> str:
    if not feedback:
        return "  No body feedback logged."
    lines = []
    for fb in feedback[-20:]:
        lines.append(
            f"  {fb.get('logged_at', '')[:10]} | {fb.get('body_area')} → "
            f"{fb.get('feeling')} (severity {fb.get('severity', '?')})"
        )
    return "\n".join(lines)
