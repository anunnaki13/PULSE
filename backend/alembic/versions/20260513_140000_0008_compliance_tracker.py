"""compliance tracker.

Revision ID: 0008_compliance_tracker
Revises: 0007_nko_snapshot
Create Date: 2026-05-13 14:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0008_compliance_tracker"
down_revision = "0007_nko_snapshot"
branch_labels = None
depends_on = None

REPORTS = [
    ("PENGUSAHAAN", "Pengusahaan"),
    ("BA_TRANSFER_ENERGI", "BA Transfer Energi"),
    ("KEUANGAN", "Keuangan"),
    ("MONEV_BPP", "Monev BPP"),
    ("KINERJA_INVESTASI", "Kinerja Investasi"),
    ("MANAJEMEN_RISIKO", "Manajemen Risiko"),
    ("SELF_ASSESSMENT", "Self Assessment"),
    ("MANAJEMEN_MATERIAL", "Manajemen Material"),
    ("NAVITAS", "Navitas"),
]

COMPONENTS = [
    ("PACA", "PACA"),
    ("CRITICAL_EVENT", "Critical Event"),
    ("ICOFR", "ICOFR"),
    ("NAC", "NAC"),
]


def upgrade() -> None:
    op.create_table(
        "compliance_laporan_definisi",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("kode", sa.String(64), nullable=False, unique=True),
        sa.Column("nama", sa.String(255), nullable=False),
        sa.Column("default_due_day", sa.Integer(), nullable=False, server_default=sa.text("10")),
        sa.Column("pengurang_per_keterlambatan", sa.Numeric(8, 4), nullable=False, server_default=sa.text("0.039")),
        sa.Column("pengurang_per_invaliditas", sa.Numeric(8, 4), nullable=False, server_default=sa.text("0.039")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "compliance_laporan_submission",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("periode_id", UUID(as_uuid=True), sa.ForeignKey("periode.id", ondelete="CASCADE"), nullable=False),
        sa.Column("definisi_id", UUID(as_uuid=True), sa.ForeignKey("compliance_laporan_definisi.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("bulan", sa.Integer(), nullable=False),
        sa.Column("tanggal_jatuh_tempo", sa.Date(), nullable=False),
        sa.Column("tanggal_submit", sa.Date(), nullable=True),
        sa.Column(
            "keterlambatan_hari",
            sa.Integer(),
            sa.Computed(
                "CASE WHEN tanggal_submit IS NULL OR tanggal_submit <= tanggal_jatuh_tempo "
                "THEN 0 ELSE tanggal_submit - tanggal_jatuh_tempo END",
                persisted=True,
            ),
            nullable=False,
        ),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("catatan", sa.Text(), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("bulan BETWEEN 1 AND 12", name="ck_compliance_submission_bulan"),
        sa.UniqueConstraint("periode_id", "definisi_id", "bulan", name="uq_compliance_laporan_submission_period_def_month"),
    )
    op.create_index("ix_compliance_laporan_submission_periode_id", "compliance_laporan_submission", ["periode_id"])
    op.create_index("ix_compliance_laporan_submission_definisi_id", "compliance_laporan_submission", ["definisi_id"])

    op.create_table(
        "compliance_komponen",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("kode", sa.String(64), nullable=False, unique=True),
        sa.Column("nama", sa.String(255), nullable=False),
        sa.Column("formula", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("pengurang_cap", sa.Numeric(8, 4), nullable=False, server_default=sa.text("10")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "compliance_komponen_realisasi",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("periode_id", UUID(as_uuid=True), sa.ForeignKey("periode.id", ondelete="CASCADE"), nullable=False),
        sa.Column("komponen_id", UUID(as_uuid=True), sa.ForeignKey("compliance_komponen.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("nilai", sa.Numeric(10, 4), nullable=False),
        sa.Column("pengurang", sa.Numeric(10, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("catatan", sa.Text(), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("periode_id", "komponen_id", name="uq_compliance_komponen_realisasi_period_component"),
    )
    op.create_index("ix_compliance_komponen_realisasi_periode_id", "compliance_komponen_realisasi", ["periode_id"])
    op.create_index("ix_compliance_komponen_realisasi_komponen_id", "compliance_komponen_realisasi", ["komponen_id"])

    reports_table = sa.table(
        "compliance_laporan_definisi",
        sa.column("kode", sa.String),
        sa.column("nama", sa.String),
        sa.column("default_due_day", sa.Integer),
        sa.column("pengurang_per_keterlambatan", sa.Numeric),
        sa.column("pengurang_per_invaliditas", sa.Numeric),
    )
    op.bulk_insert(
        reports_table,
        [
            {
                "kode": kode,
                "nama": nama,
                "default_due_day": 10,
                "pengurang_per_keterlambatan": 0.039,
                "pengurang_per_invaliditas": 0.039,
            }
            for kode, nama in REPORTS
        ],
    )
    components_table = sa.table(
        "compliance_komponen",
        sa.column("kode", sa.String),
        sa.column("nama", sa.String),
        sa.column("formula", JSONB),
        sa.column("pengurang_cap", sa.Numeric),
    )
    op.bulk_insert(
        components_table,
        [{"kode": kode, "nama": nama, "formula": {"type": "manual_pengurang"}, "pengurang_cap": 10} for kode, nama in COMPONENTS],
    )


def downgrade() -> None:
    op.drop_index("ix_compliance_komponen_realisasi_komponen_id", table_name="compliance_komponen_realisasi")
    op.drop_index("ix_compliance_komponen_realisasi_periode_id", table_name="compliance_komponen_realisasi")
    op.drop_table("compliance_komponen_realisasi")
    op.drop_table("compliance_komponen")
    op.drop_index("ix_compliance_laporan_submission_definisi_id", table_name="compliance_laporan_submission")
    op.drop_index("ix_compliance_laporan_submission_periode_id", table_name="compliance_laporan_submission")
    op.drop_table("compliance_laporan_submission")
    op.drop_table("compliance_laporan_definisi")
