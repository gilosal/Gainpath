"""Initial schema — all PaceForge tables

Revision ID: 001
Revises:
Create Date: 2026-04-15
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── user_profile ──────────────────────────────────────────────────────────
    op.create_table(
        "user_profile",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False, server_default="Athlete"),
        sa.Column("running_goal_race", sa.String(50)),
        sa.Column("running_goal_date", sa.DateTime()),
        sa.Column("running_fitness_level", sa.String(20)),
        sa.Column("running_weekly_mileage", sa.Float()),
        sa.Column("running_recent_race_time", sa.String(50)),
        sa.Column("training_days_per_week", sa.Integer(), server_default="3"),
        sa.Column("available_equipment", sa.String(50), server_default="full_gym"),
        sa.Column("weight_training_goal", sa.String(50), server_default="general_fitness"),
        sa.Column("training_preferred_days", postgresql.JSON(), server_default="[]"),
        sa.Column("mobility_goal", sa.String(50), server_default="general_flexibility"),
        sa.Column("mobility_target_areas", postgresql.JSON(), server_default="[]"),
        sa.Column("mobility_experience", sa.String(20), server_default="beginner"),
        sa.Column("mobility_session_length", sa.Integer(), server_default="20"),
        sa.Column("available_days", postgresql.JSON(), server_default="[]"),
        sa.Column("session_time_constraints", postgresql.JSON(), server_default="{}"),
        sa.Column("no_morning_days", postgresql.JSON(), server_default="[]"),
        sa.Column("units_weight", sa.String(5), server_default="kg"),
        sa.Column("units_distance", sa.String(5), server_default="km"),
        sa.Column("dark_mode", sa.Boolean(), server_default="true"),
        sa.Column("preferred_ai_model", sa.String(100)),
    )

    # ── training_plan ─────────────────────────────────────────────────────────
    op.create_table(
        "training_plan",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("plan_type", sa.String(20), nullable=False),
        sa.Column("goal", sa.String(200)),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("weeks_total", sa.Integer(), nullable=False),
        sa.Column("raw_plan_json", postgresql.JSON()),
    )

    # ── plan_week ─────────────────────────────────────────────────────────────
    op.create_table(
        "plan_week",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("training_plan.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("week_start_date", sa.Date(), nullable=False),
        sa.Column("theme", sa.String(100)),
        sa.Column("focus", sa.String(200)),
        sa.Column("total_volume_target", sa.Float()),
    )
    op.create_index("ix_plan_week_plan_id", "plan_week", ["plan_id"])

    # ── exercise_library ──────────────────────────────────────────────────────
    op.create_table(
        "exercise_library",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("subcategory", sa.String(50)),
        sa.Column("muscle_groups", postgresql.JSON(), server_default="[]"),
        sa.Column("movement_pattern", sa.String(50)),
        sa.Column("difficulty", sa.String(20), server_default="beginner"),
        sa.Column("equipment_needed", postgresql.JSON(), server_default="[]"),
        sa.Column("description", sa.Text()),
        sa.Column("cues", postgresql.JSON(), server_default="[]"),
        sa.Column("modifications", postgresql.JSON(), server_default="{}"),
        sa.Column("is_yoga_pose", sa.Boolean(), server_default="false"),
        sa.Column("hold_type", sa.String(20)),
        sa.Column("default_hold_duration", sa.Integer()),
    )

    # ── planned_session ───────────────────────────────────────────────────────
    op.create_table(
        "planned_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_week_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plan_week.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.String(10), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("session_type", sa.String(20), nullable=False),
        sa.Column("session_subtype", sa.String(50)),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("estimated_duration", sa.Integer()),
        sa.Column("exercises", postgresql.JSON(), server_default="[]"),
        sa.Column("is_stacked", sa.Boolean(), server_default="false"),
        sa.Column("order_in_stack", sa.Integer(), server_default="0"),
    )
    op.create_index("ix_planned_session_date", "planned_session", ["session_date"])
    op.create_index("ix_planned_session_week_id", "planned_session", ["plan_week_id"])

    # ── session_log ───────────────────────────────────────────────────────────
    op.create_table(
        "session_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("planned_session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("planned_session.id", ondelete="SET NULL")),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("session_type", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("status", sa.String(20), nullable=False, server_default="planned"),
        sa.Column("overall_rpe", sa.Integer()),
        sa.Column("notes", sa.Text()),
        sa.Column("actual_distance", sa.Float()),
        sa.Column("actual_duration", sa.Integer()),
        sa.Column("actual_pace", sa.Float()),
        sa.Column("total_tonnage", sa.Float()),
        sa.Column("completed_flow", sa.Boolean()),
    )
    op.create_index("ix_session_log_date", "session_log", ["session_date"])

    # ── set_log ───────────────────────────────────────────────────────────────
    op.create_table(
        "set_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_log_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("session_log.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_name", sa.String(200), nullable=False),
        sa.Column("exercise_library_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exercise_library.id", ondelete="SET NULL")),
        sa.Column("set_number", sa.Integer(), server_default="1"),
        sa.Column("set_type", sa.String(20), server_default="working"),
        sa.Column("weight", sa.Float()),
        sa.Column("reps", sa.Integer()),
        sa.Column("rpe", sa.Integer()),
        sa.Column("distance", sa.Float()),
        sa.Column("duration", sa.Integer()),
        sa.Column("pace", sa.Float()),
        sa.Column("hold_duration", sa.Integer()),
        sa.Column("body_side", sa.String(15)),
        sa.Column("tightness_notes", sa.Text()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("is_offline", sa.Boolean(), server_default="false"),
    )
    op.create_index("ix_set_log_session_id", "set_log", ["session_log_id"])

    # ── body_feedback ─────────────────────────────────────────────────────────
    op.create_table(
        "body_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_log_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("session_log.id", ondelete="CASCADE"), nullable=False),
        sa.Column("logged_at", sa.DateTime(), nullable=False),
        sa.Column("body_area", sa.String(50), nullable=False),
        sa.Column("feeling", sa.String(20), nullable=False),
        sa.Column("severity", sa.Integer()),
        sa.Column("notes", sa.Text()),
    )

    # ── offline_queue ─────────────────────────────────────────────────────────
    op.create_table(
        "offline_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("sync_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("payload", postgresql.JSON(), nullable=False),
        sa.Column("session_log_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("session_log.id", ondelete="SET NULL")),
        sa.Column("error_message", sa.Text()),
        sa.Column("retry_count", sa.Integer(), server_default="0"),
        sa.Column("synced_at", sa.DateTime()),
    )

    # ── ai_usage_log ──────────────────────────────────────────────────────────
    op.create_table(
        "ai_usage_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("feature", sa.String(50), nullable=False),
        sa.Column("plan_type", sa.String(20)),
        sa.Column("prompt_tokens", sa.Integer(), server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), server_default="0"),
        sa.Column("total_tokens", sa.Integer(), server_default="0"),
        sa.Column("cost_usd", sa.Float(), server_default="0"),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("success", sa.Boolean(), server_default="true"),
        sa.Column("error_message", sa.Text()),
        sa.Column("request_id", sa.String(100)),
    )
    op.create_index("ix_ai_usage_log_created_at", "ai_usage_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("ai_usage_log")
    op.drop_table("offline_queue")
    op.drop_table("body_feedback")
    op.drop_table("set_log")
    op.drop_table("session_log")
    op.drop_table("planned_session")
    op.drop_table("exercise_library")
    op.drop_table("plan_week")
    op.drop_table("training_plan")
    op.drop_table("user_profile")
