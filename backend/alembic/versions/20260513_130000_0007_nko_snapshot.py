"""nko snapshot.

Revision ID: 0007_nko_snapshot
Revises: 0006_audit_log
Create Date: 2026-05-13 13:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0007_nko_snapshot"
down_revision = "0006_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "nko_snapshot",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("periode_id", UUID(as_uuid=True), sa.ForeignKey("periode.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nko_total", sa.Numeric(10, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("gross_pilar_total", sa.Numeric(10, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("compliance_deduction", sa.Numeric(10, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("breakdown", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("source", sa.String(32), nullable=False, server_default=sa.text("'live'")),
        sa.Column("is_final", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("periode_id", name="uq_nko_snapshot_periode"),
    )
    op.create_index("ix_nko_snapshot_periode_id", "nko_snapshot", ["periode_id"])
    op.create_index("ix_nko_snapshot_updated_desc", "nko_snapshot", [sa.text("updated_at DESC")])


def downgrade() -> None:
    op.drop_index("ix_nko_snapshot_updated_desc", table_name="nko_snapshot")
    op.drop_index("ix_nko_snapshot_periode_id", table_name="nko_snapshot")
    op.drop_table("nko_snapshot")
