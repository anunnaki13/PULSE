"""periode and assessment sessions.

Revision ID: 0004_periode_and_sessions
Revises: 0003_master_data
Create Date: 2026-05-13 10:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0004_periode_and_sessions"
down_revision = "0003_master_data"
branch_labels = None
depends_on = None

periode_status = postgresql.ENUM(
    "draft",
    "aktif",
    "self_assessment",
    "asesmen",
    "finalisasi",
    "closed",
    name="periode_status",
    create_type=False,
)
session_state = postgresql.ENUM(
    "draft",
    "submitted",
    "approved",
    "overridden",
    "revision_requested",
    "abandoned",
    name="assessment_session_state",
    create_type=False,
)


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    periode_status.create(op.get_bind(), checkfirst=True)
    session_state.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "periode",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tahun", sa.Integer, nullable=False),
        sa.Column("triwulan", sa.Integer, nullable=False),
        sa.Column("semester", sa.Integer, nullable=False),
        sa.Column("nama", sa.String(255), nullable=False),
        sa.Column("status", periode_status, nullable=False, server_default=sa.text("'draft'::periode_status")),
        sa.Column("tanggal_buka", sa.Date, nullable=True),
        sa.Column("tanggal_tutup", sa.Date, nullable=True),
        sa.Column("last_transition_reason", sa.Text, nullable=True),
        sa.Column("last_transition_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("last_transition_at", sa.DateTime(timezone=True), nullable=True),
        *_audit_columns(),
        sa.UniqueConstraint("tahun", "triwulan", name="uq_periode_tahun_triwulan"),
        sa.CheckConstraint("triwulan BETWEEN 1 AND 4", name="ck_periode_triwulan"),
        sa.CheckConstraint("semester BETWEEN 1 AND 2", name="ck_periode_semester"),
    )

    op.create_table(
        "assessment_session",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("periode_id", UUID(as_uuid=True), sa.ForeignKey("periode.id", ondelete="CASCADE"), nullable=False),
        sa.Column("indikator_id", UUID(as_uuid=True), sa.ForeignKey("indikator.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("bidang_id", UUID(as_uuid=True), sa.ForeignKey("bidang.id", ondelete="SET NULL"), nullable=True),
        sa.Column("state", session_state, nullable=False, server_default=sa.text("'draft'::assessment_session_state")),
        sa.Column("payload", JSONB, nullable=True),
        sa.Column("realisasi", sa.Numeric(20, 4), nullable=True),
        sa.Column("target", sa.Numeric(20, 4), nullable=True),
        sa.Column("pencapaian", sa.Numeric(10, 4), nullable=True),
        sa.Column("nilai", sa.Numeric(10, 4), nullable=True),
        sa.Column("nilai_final", sa.Numeric(10, 4), nullable=True),
        sa.Column("catatan_pic", sa.Text, nullable=True),
        sa.Column("catatan_asesor", sa.Text, nullable=True),
        sa.Column("link_eviden", sa.String(2048), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("asesor_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("asesor_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        *_audit_columns(),
        sa.UniqueConstraint("periode_id", "indikator_id", "bidang_id", name="uq_session_periode_indikator_bidang"),
    )
    op.create_index("ix_assessment_session_periode_id", "assessment_session", ["periode_id"])
    op.create_index("ix_assessment_session_indikator_id", "assessment_session", ["indikator_id"])
    op.create_index("ix_assessment_session_bidang_id", "assessment_session", ["bidang_id"])
    op.create_index(
        "uq_session_aggregate",
        "assessment_session",
        ["periode_id", "indikator_id"],
        unique=True,
        postgresql_where=sa.text("bidang_id IS NULL"),
    )

    op.create_table(
        "assessment_session_bidang",
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("assessment_session.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("bidang_id", UUID(as_uuid=True), sa.ForeignKey("bidang.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "indikator_applicable_bidang",
        sa.Column("indikator_id", UUID(as_uuid=True), sa.ForeignKey("indikator.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("bidang_id", UUID(as_uuid=True), sa.ForeignKey("bidang.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("is_aggregate", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_table("indikator_applicable_bidang")
    op.drop_table("assessment_session_bidang")
    op.drop_index("uq_session_aggregate", table_name="assessment_session")
    op.drop_index("ix_assessment_session_bidang_id", table_name="assessment_session")
    op.drop_index("ix_assessment_session_indikator_id", table_name="assessment_session")
    op.drop_index("ix_assessment_session_periode_id", table_name="assessment_session")
    op.drop_table("assessment_session")
    op.drop_table("periode")
    session_state.drop(op.get_bind(), checkfirst=True)
    periode_status.drop(op.get_bind(), checkfirst=True)
