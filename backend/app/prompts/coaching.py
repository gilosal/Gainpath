"""
coaching.py — Prompt builders and Pydantic response models for AI coaching messages.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


# ── Response models ────────────────────────────────────────────────────────────

class DailyMotivationResponse(BaseModel):
    message: str
    emoji: str  # Single emoji character for visual flair


class PostWorkoutResponse(BaseModel):
    headline: str   # Short celebratory title (e.g. "Crushed It!")
    body: str       # 2-4 sentence encouraging message
    next_suggestion: str  # One-line tip for the next session


class WeeklySummaryResponse(BaseModel):
    headline: str
    highlights: list[str]       # 2-4 bullet point wins
    encouragement: str          # 1-2 sentence motivational close
    focus_next_week: str        # One area to emphasize next week


class WeeklyChallengeResponse(BaseModel):
    challenge_type: str     # consistency | volume | variety | streak
    title: str
    description: str
    target_value: float
    unit: str               # sessions | km | kg | days


# ── Prompt builders ────────────────────────────────────────────────────────────

COACHING_SYSTEM_PROMPT = """You are an expert personal fitness coach. Your communication style is:
- Encouraging and positive, never shaming or negative
- Concise and direct — no filler words
- Personalized to the athlete's actual data
- Celebrates effort over outcomes
- Aware of the science of recovery and progressive overload

Always respond in valid JSON matching the requested schema exactly."""


def build_daily_motivation_prompt(
    *,
    name: str,
    current_streak: int,
    sessions_this_week: int,
    planned_today: list[str],
    recent_feedback: Optional[str] = None,
    fitness_goal: Optional[str] = None,
) -> str:
    parts = [f"Athlete: {name}"]
    if current_streak > 0:
        parts.append(f"Current workout streak: {current_streak} days")
    parts.append(f"Sessions completed this week: {sessions_this_week}")
    if planned_today:
        parts.append(f"Today's planned sessions: {', '.join(planned_today)}")
    if recent_feedback:
        parts.append(f"Body feedback from last session: {recent_feedback}")
    if fitness_goal:
        parts.append(f"Fitness goal: {fitness_goal}")

    context = "\n".join(parts)
    return f"""Based on this athlete's data, write a short (1-2 sentence) daily motivation message to start their day.
Be specific to their situation. Don't use generic platitudes.

Athlete data:
{context}

Respond with JSON: {{"message": "...", "emoji": "🔥"}}"""


def build_post_workout_prompt(
    *,
    name: str,
    session_type: str,
    duration_minutes: Optional[int],
    rpe: Optional[int],
    new_prs: list[str],
    streak: int,
    xp_earned: int,
) -> str:
    parts = [
        f"Athlete: {name}",
        f"Session type: {session_type}",
    ]
    if duration_minutes:
        parts.append(f"Duration: {duration_minutes} minutes")
    if rpe:
        parts.append(f"Perceived effort (RPE): {rpe}/10")
    if new_prs:
        parts.append(f"New personal records: {', '.join(new_prs)}")
    if streak > 0:
        parts.append(f"Current streak: {streak} days")
    parts.append(f"XP earned this session: {xp_earned}")

    context = "\n".join(parts)
    return f"""The athlete just completed a workout. Write an enthusiastic post-workout message.

Session data:
{context}

Respond with JSON:
{{"headline": "...", "body": "...", "next_suggestion": "..."}}

Guidelines:
- headline: 2-4 words, celebratory (e.g. "Solid Work Today!", "New PR Alert!")
- body: 2-3 sentences acknowledging their effort and any PRs
- next_suggestion: one practical tip for their next session"""


def build_weekly_summary_prompt(
    *,
    name: str,
    sessions_completed: int,
    sessions_planned: int,
    running_km: float,
    lifting_tonnage: float,
    mobility_minutes: int,
    streak: int,
    new_achievements: list[str],
    new_prs: list[str],
) -> str:
    adherence = f"{sessions_completed}/{sessions_planned}" if sessions_planned > 0 else f"{sessions_completed} sessions"
    context_parts = [
        f"Athlete: {name}",
        f"Sessions this week: {adherence}",
        f"Running: {running_km:.1f} km",
        f"Lifting tonnage: {lifting_tonnage:.0f} kg",
        f"Mobility: {mobility_minutes} minutes",
        f"Current streak: {streak} days",
    ]
    if new_achievements:
        context_parts.append(f"Achievements earned: {', '.join(new_achievements)}")
    if new_prs:
        context_parts.append(f"New personal records: {', '.join(new_prs)}")

    context = "\n".join(context_parts)
    return f"""Write a weekly training summary for this athlete. Celebrate what went well.

Week data:
{context}

Respond with JSON:
{{"headline": "...", "highlights": ["...", "..."], "encouragement": "...", "focus_next_week": "..."}}

Guidelines:
- headline: 4-6 words summarizing the week (e.g. "Strong Consistency Week!")
- highlights: 2-4 specific wins from the data
- encouragement: 1-2 warm, genuine sentences
- focus_next_week: one specific area to improve or maintain"""


def build_weekly_challenge_prompt(
    *,
    name: str,
    sessions_per_week: float,
    running_km_avg: float,
    lifting_sessions_avg: float,
    current_streak: int,
    fitness_goal: Optional[str],
) -> str:
    context = f"""Athlete: {name}
Average sessions per week: {sessions_per_week:.1f}
Average weekly running: {running_km_avg:.1f} km
Average weekly lifting sessions: {lifting_sessions_avg:.1f}
Current streak: {current_streak} days
Goal: {fitness_goal or "general fitness"}"""

    return f"""Create a motivating weekly challenge for this athlete. It should be achievable but require effort.

Athlete data:
{context}

Challenge types available:
- consistency: complete N sessions this week
- volume: run N km or lift N kg total
- variety: include all 3 session types (run + lift + mobility)
- streak: maintain or start a streak of N days

Respond with JSON:
{{"challenge_type": "consistency", "title": "...", "description": "...", "target_value": 4.0, "unit": "sessions"}}"""


def build_nudge_prompt(
    *,
    name: str,
    session_type: str,
    streak: int,
    time_of_day: str,
) -> str:
    streak_note = f"You have a {streak}-day streak at risk!" if streak > 1 else ""
    return f"""Write a short nudge message to gently encourage {name} to do their {session_type} session today.
It's {time_of_day}. {streak_note}
Keep it under 2 sentences. Be warm, not pushy.

Respond with JSON: {{"message": "...", "emoji": "💪"}}"""


def build_chat_system_prompt(
    *,
    name: str,
    current_streak: int,
    sessions_completed: int,
    fitness_goal: Optional[str],
    recent_sessions_summary: str,
    recent_prs: list[str],
) -> str:
    pr_note = f"Recent PRs: {', '.join(recent_prs)}" if recent_prs else ""
    return f"""You are an expert personal fitness coach and the user's AI training partner.

About this athlete:
- Name: {name}
- Current workout streak: {current_streak} days
- Total sessions completed: {sessions_completed}
- Fitness goal: {fitness_goal or "general fitness"}
- Recent training: {recent_sessions_summary}
{pr_note}

Guidelines:
- Be conversational, warm, and knowledgeable
- Reference their actual training data when relevant
- Give evidence-based advice
- Keep responses concise (2-4 sentences unless a detailed answer is needed)
- If asked about injuries or medical concerns, recommend seeing a professional
- You can see their workout history and can answer questions about their progress"""
