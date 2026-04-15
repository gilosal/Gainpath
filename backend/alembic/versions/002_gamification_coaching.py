"""Gamification, coaching, streaks, achievements, PRs

Revision ID: 002
Revises: 001
Create Date: 2026-04-15
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── user_profile: new columns ─────────────────────────────────────────────
    op.add_column("user_profile", sa.Column("total_xp", sa.Integer(), server_default="0", nullable=False))
    op.add_column("user_profile", sa.Column("level", sa.Integer(), server_default="1", nullable=False))
    op.add_column("user_profile", sa.Column("onboarding_completed", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("user_profile", sa.Column("fitness_goal", sa.String(50)))
    op.add_column("user_profile", sa.Column("experience_level", sa.String(20)))
    op.add_column("user_profile", sa.Column("notification_enabled", sa.Boolean(), server_default="true", nullable=False))
    op.add_column("user_profile", sa.Column("notification_time", sa.String(5), server_default="07:00"))

    # ── streak_snapshot ───────────────────────────────────────────────────────
    op.create_table(
        "streak_snapshot",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("current_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("longest_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("streak_start_date", sa.Date()),
        sa.Column("last_workout_date", sa.Date()),
        sa.Column("streak_frozen", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("freeze_used_at", sa.Date()),
    )

    # ── achievement ───────────────────────────────────────────────────────────
    op.create_table(
        "achievement",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("icon_name", sa.String(50), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("threshold", sa.Integer(), server_default="1", nullable=False),
        sa.Column("xp_reward", sa.Integer(), server_default="100", nullable=False),
    )

    # ── user_achievement ──────────────────────────────────────────────────────
    op.create_table(
        "user_achievement",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("achievement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("achievement.id", ondelete="CASCADE"), nullable=False),
        sa.Column("earned_at", sa.DateTime(), nullable=False),
        sa.Column("context_json", postgresql.JSON()),
    )
    op.create_index("ix_user_achievement_achievement_id", "user_achievement", ["achievement_id"])

    # ── xp_ledger ─────────────────────────────────────────────────────────────
    op.create_table(
        "xp_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True)),
        sa.Column("note", sa.String(200)),
    )
    op.create_index("ix_xp_ledger_created_at", "xp_ledger", ["created_at"])

    # ── coaching_message ──────────────────────────────────────────────────────
    op.create_table(
        "coaching_message",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("message_type", sa.String(30), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", postgresql.JSON()),
        sa.Column("displayed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("dismissed", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index("ix_coaching_message_created_at", "coaching_message", ["created_at"])
    op.create_index("ix_coaching_message_type", "coaching_message", ["message_type"])

    # ── chat_message ──────────────────────────────────────────────────────────
    op.create_table(
        "chat_message",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("context_json", postgresql.JSON()),
    )
    op.create_index("ix_chat_message_created_at", "chat_message", ["created_at"])

    # ── weekly_challenge ──────────────────────────────────────────────────────
    op.create_table(
        "weekly_challenge",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("week_start_date", sa.Date(), nullable=False),
        sa.Column("challenge_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=False),
        sa.Column("current_value", sa.Float(), server_default="0", nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("xp_reward", sa.Integer(), server_default="200", nullable=False),
        sa.Column("generated_by_ai", sa.Boolean(), server_default="true", nullable=False),
    )
    op.create_index("ix_weekly_challenge_week_start", "weekly_challenge", ["week_start_date"])

    # ── personal_record ───────────────────────────────────────────────────────
    op.create_table(
        "personal_record",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("exercise_name", sa.String(200), nullable=False),
        sa.Column("record_type", sa.String(30), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("previous_value", sa.Float()),
        sa.Column("set_log_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("set_log.id", ondelete="SET NULL")),
        sa.Column("session_log_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("session_log.id", ondelete="SET NULL")),
        sa.Column("celebrated", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index("ix_personal_record_exercise", "personal_record", ["exercise_name"])
    op.create_index("ix_personal_record_created_at", "personal_record", ["created_at"])


def downgrade() -> None:
    op.drop_table("personal_record")
    op.drop_table("weekly_challenge")
    op.drop_table("chat_message")
    op.drop_table("coaching_message")
    op.drop_table("xp_ledger")
    op.drop_table("user_achievement")
    op.drop_table("achievement")
    op.drop_table("streak_snapshot")
    op.drop_column("user_profile", "notification_time")
    op.drop_column("user_profile", "notification_enabled")
    op.drop_column("user_profile", "experience_level")
    op.drop_column("user_profile", "fitness_goal")
    op.drop_column("user_profile", "onboarding_completed")
    op.drop_column("user_profile", "level")
    op.drop_column("user_profile", "total_xp")
