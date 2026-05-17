"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-05-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── agent_profiles ────────────────────────────────────────────────────────
    op.create_table(
        "agent_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("seniority_levels", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("stack_keywords", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("tools", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("access_rules", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("learning_sequence", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("ticket_criteria", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("interview_questions", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("lobster_trap_policy_file", sa.String(255), nullable=True),
        sa.Column("system_prompt_template", sa.Text, nullable=True),
        sa.Column("is_custom", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_agent_profiles_category", "agent_profiles", ["category"])
    op.create_index("ix_agent_profiles_is_custom", "agent_profiles", ["is_custom"])

    # ── onboarding_sessions ───────────────────────────────────────────────────
    op.create_table(
        "onboarding_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("seniority", sa.String(50), nullable=False),
        sa.Column("dev_email", sa.String(255), nullable=False),
        sa.Column("dev_github_username", sa.String(255), nullable=False),
        sa.Column("project_repo_url", sa.String(512), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="payment_pending"),
        sa.Column("payment_tx_hash", sa.String(255), nullable=True),
        sa.Column("interview_profile", postgresql.JSONB, nullable=True),
        sa.Column("access_status", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("onboarding_plan", postgresql.JSONB, nullable=True),
        sa.Column("assigned_ticket_id", sa.String(100), nullable=True),
        sa.Column("checkin_day3_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checkin_day7_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checkin_day14_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["agent_profile_id"],
            ["agent_profiles.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── audit_events ──────────────────────────────────────────────────────────
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("rule_triggered", sa.String(255), nullable=False),
        sa.Column("original_intent", sa.Text, nullable=True),
        sa.Column("action_taken", sa.Text, nullable=False),
        sa.Column("resource_requested", sa.Text, nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["onboarding_sessions.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_session_id", "audit_events", ["session_id"])
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("onboarding_sessions")
    op.drop_index("ix_agent_profiles_is_custom", table_name="agent_profiles")
    op.drop_index("ix_agent_profiles_category", table_name="agent_profiles")
    op.drop_table("agent_profiles")
