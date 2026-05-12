"""ai integration.

Revision ID: 0009_ai_integration
Revises: 0008_compliance_tracker
Create Date: 2026-05-13 15:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0009_ai_integration"
down_revision = "0008_compliance_tracker"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_suggestion_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("suggestion_type", sa.String(64), nullable=False),
        sa.Column("context_entity_type", sa.String(64), nullable=False),
        sa.Column("context_entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("suggestion_text", sa.Text(), nullable=False),
        sa.Column("structured_payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("model_used", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False, server_default=sa.text("'openrouter'")),
        sa.Column("pii_masked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("estimated_cost_usd", sa.Numeric(12, 6), nullable=False, server_default=sa.text("0")),
        sa.Column("accepted", sa.Boolean(), nullable=True),
        sa.Column("user_edited_version", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_suggestion_log_user_id", "ai_suggestion_log", ["user_id"])
    op.create_index("ix_ai_suggestion_log_suggestion_type", "ai_suggestion_log", ["suggestion_type"])
    op.create_index("ix_ai_suggestion_log_context_entity_id", "ai_suggestion_log", ["context_entity_id"])

    op.create_table(
        "ai_inline_help",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("indikator_id", UUID(as_uuid=True), sa.ForeignKey("indikator.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("apa_itu", sa.Text(), nullable=False),
        sa.Column("formula_explanation", sa.Text(), nullable=False),
        sa.Column("best_practice", sa.Text(), nullable=False),
        sa.Column("common_pitfalls", sa.Text(), nullable=False),
        sa.Column("related_indikator", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("generated_by_model", sa.String(100), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_ai_inline_help_indikator", "ai_inline_help", ["indikator_id"])


def downgrade() -> None:
    op.drop_index("idx_ai_inline_help_indikator", table_name="ai_inline_help")
    op.drop_table("ai_inline_help")
    op.drop_index("ix_ai_suggestion_log_context_entity_id", table_name="ai_suggestion_log")
    op.drop_index("ix_ai_suggestion_log_suggestion_type", table_name="ai_suggestion_log")
    op.drop_index("ix_ai_suggestion_log_user_id", table_name="ai_suggestion_log")
    op.drop_table("ai_suggestion_log")
