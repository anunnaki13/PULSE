"""audit log.

Revision ID: 0006_audit_log
Revises: 0005_recommendation_notification
Create Date: 2026-05-13 12:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID

revision = "0006_audit_log"
down_revision = "0005_recommendation_notification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("entity_type", sa.Text, nullable=True),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("before_data", JSONB, nullable=True),
        sa.Column("after_data", JSONB, nullable=True),
        sa.Column("ip_address", INET, nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_user_created", "audit_log", ["user_id", sa.text("created_at DESC")])
    op.create_index("ix_audit_entity_created", "audit_log", ["entity_type", "entity_id", sa.text("created_at DESC")])
    op.create_index("ix_audit_created_desc", "audit_log", [sa.text("created_at DESC")])


def downgrade() -> None:
    op.drop_index("ix_audit_created_desc", table_name="audit_log")
    op.drop_index("ix_audit_entity_created", table_name="audit_log")
    op.drop_index("ix_audit_user_created", table_name="audit_log")
    op.drop_table("audit_log")
