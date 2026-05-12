"""recommendations and notifications.

Revision ID: 0005_recommendation_notification
Revises: 0004_periode_and_sessions
Create Date: 2026-05-13 11:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0005_recommendation_notification"
down_revision = "0004_periode_and_sessions"
branch_labels = None
depends_on = None

recommendation_status = postgresql.ENUM(
    "open",
    "in_progress",
    "pending_review",
    "closed",
    "carried_over",
    name="recommendation_status",
    create_type=False,
)
recommendation_severity = postgresql.ENUM(
    "low",
    "medium",
    "high",
    "critical",
    name="recommendation_severity",
    create_type=False,
)
notification_type = postgresql.ENUM(
    "assessment_due",
    "review_pending",
    "recommendation_assigned",
    "deadline_approaching",
    "periode_closed",
    "system_announcement",
    name="notification_type",
    create_type=False,
)


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    recommendation_status.create(op.get_bind(), checkfirst=True)
    recommendation_severity.create(op.get_bind(), checkfirst=True)
    notification_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "recommendation",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("source_assessment_id", UUID(as_uuid=True), sa.ForeignKey("assessment_session.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_periode_id", UUID(as_uuid=True), sa.ForeignKey("periode.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("target_periode_id", UUID(as_uuid=True), sa.ForeignKey("periode.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("carried_from_id", UUID(as_uuid=True), sa.ForeignKey("recommendation.id", ondelete="SET NULL"), nullable=True),
        sa.Column("carried_to_id", UUID(as_uuid=True), sa.ForeignKey("recommendation.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", recommendation_status, nullable=False, server_default=sa.text("'open'::recommendation_status")),
        sa.Column("severity", recommendation_severity, nullable=False),
        sa.Column("deskripsi", sa.Text, nullable=False),
        sa.Column("action_items", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("progress_percent", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("progress_notes", sa.Text, nullable=True),
        sa.Column("asesor_close_notes", sa.Text, nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint("progress_percent BETWEEN 0 AND 100", name="ck_recommendation_progress_percent"),
    )
    for col in ("source_assessment_id", "source_periode_id", "target_periode_id"):
        op.create_index(f"ix_recommendation_{col}", "recommendation", [col])

    op.create_table(
        "notification",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", notification_type, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_notification_user_read_created", "notification", ["user_id", "read_at", sa.text("created_at DESC")])


def downgrade() -> None:
    op.drop_index("ix_notification_user_read_created", table_name="notification")
    op.drop_table("notification")
    for col in ("target_periode_id", "source_periode_id", "source_assessment_id"):
        op.drop_index(f"ix_recommendation_{col}", table_name="recommendation")
    op.drop_table("recommendation")
    notification_type.drop(op.get_bind(), checkfirst=True)
    recommendation_severity.drop(op.get_bind(), checkfirst=True)
    recommendation_status.drop(op.get_bind(), checkfirst=True)
