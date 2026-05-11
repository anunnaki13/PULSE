"""master data: bidang, konkin_template, perspektif (with is_pengurang +
pengurang_cap — W-07), indikator, ml_stream, konkin_import_log; AND
users.bidang_id column + FK (B-04 fix).

Revision ID: 0003_master_data
Revises: 0002_auth_users_roles
Create Date: 2026-05-12 14:00:00

Order matters here:

1. Create the six master tables (`bidang` first because everyone — including
   the deferred FK on `users` — points at it).
2. Create the GIN index on `ml_stream.structure` (REQ-dynamic-ml-schema
   acceptance: JSONB containment queries must hit an index).
3. B-04 fix — add `users.bidang_id` UUID NULL column + FK
   `fk_users_bidang_id → bidang(id) ON DELETE SET NULL`. This is the
   "FK target now exists, so add it" step deferred from Plan 05's 0002
   migration (CONTEXT.md "Migration FK ordering").

W-07 fix — `perspektif` carries TWO extra columns the source data-model
spec didn't have:
  - `is_pengurang BOOLEAN NOT NULL DEFAULT FALSE` (perspektif VI = True).
  - `pengurang_cap NUMERIC(5,2) NULL` (max −10.00 for VI per Konkin 2026).
The lock validator (Plan 06 router code) filters perspektif by
`is_pengurang = FALSE` when summing bobots — i.e. I..V must sum to 100.00.

DDL convention: every UUID PK uses `server_default=uuid_generate_v4()` from
the `uuid-ossp` extension (loaded in the baseline migration env), and every
table gets `created_at` / `updated_at` audit columns with `now()` defaults
plus `onupdate=now()` on `updated_at` (mirror of the SQLAlchemy mapper).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "0003_master_data"
down_revision = "0002_auth_users_roles"
branch_labels = None
depends_on = None


def _audit_columns() -> list[sa.Column]:
    """Shared audit columns: created_at / updated_at with now() defaults."""
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    # ------------------------------------------------------------------
    # (a) bidang — self-FK on parent_id, ON DELETE SET NULL.
    # Must come BEFORE the users.bidang_id FK at the end of this upgrade.
    # ------------------------------------------------------------------
    op.create_table(
        "bidang",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("kode", sa.String(32), nullable=False, unique=True),
        sa.Column("nama", sa.String(255), nullable=False),
        sa.Column(
            "parent_id",
            UUID(as_uuid=True),
            sa.ForeignKey("bidang.id", ondelete="SET NULL"),
            nullable=True,
        ),
        *_audit_columns(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ------------------------------------------------------------------
    # (b) konkin_template — unique (tahun, nama).
    # ------------------------------------------------------------------
    op.create_table(
        "konkin_template",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("tahun", sa.Integer, nullable=False),
        sa.Column("nama", sa.String(255), nullable=False),
        sa.Column(
            "locked",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        *_audit_columns(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "tahun", "nama", name="uq_konkin_template_tahun_nama"
        ),
    )

    # ------------------------------------------------------------------
    # (c) perspektif — W-07: is_pengurang + pengurang_cap.
    # ------------------------------------------------------------------
    op.create_table(
        "perspektif",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "template_id",
            UUID(as_uuid=True),
            sa.ForeignKey("konkin_template.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("kode", sa.String(8), nullable=False),
        sa.Column("nama", sa.String(255), nullable=False),
        sa.Column(
            "bobot",
            sa.Numeric(6, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        # W-07 — pengurang convention. Perspektif VI = (is_pengurang=True,
        # bobot=0.00, pengurang_cap=10.00). Lock validator filters
        # WHERE is_pengurang = FALSE.
        sa.Column(
            "is_pengurang",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("pengurang_cap", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "sort_order",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        *_audit_columns(),
        sa.UniqueConstraint(
            "template_id", "kode", name="uq_perspektif_template_kode"
        ),
    )

    # ------------------------------------------------------------------
    # (d) indikator — FK perspektif CASCADE; URL-only link_eviden.
    # ------------------------------------------------------------------
    op.create_table(
        "indikator",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "perspektif_id",
            UUID(as_uuid=True),
            sa.ForeignKey("perspektif.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("kode", sa.String(32), nullable=False),
        sa.Column("nama", sa.String(255), nullable=False),
        sa.Column(
            "bobot",
            sa.Numeric(6, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("polaritas", sa.String(16), nullable=False),
        sa.Column("formula", sa.String(255), nullable=True),
        sa.Column("link_eviden", sa.String(2048), nullable=True),
        *_audit_columns(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "perspektif_id", "kode", name="uq_indikator_perspektif_kode"
        ),
    )

    # ------------------------------------------------------------------
    # (e) ml_stream — JSONB structure with empty-object default.
    # ------------------------------------------------------------------
    op.create_table(
        "ml_stream",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("kode", sa.String(32), nullable=False, unique=True),
        sa.Column("nama", sa.String(255), nullable=False),
        sa.Column("version", sa.String(16), nullable=False),
        sa.Column(
            "structure",
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        *_audit_columns(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ------------------------------------------------------------------
    # (f) konkin_import_log — idempotency anchor for Excel imports.
    # ------------------------------------------------------------------
    op.create_table(
        "konkin_import_log",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "template_id",
            UUID(as_uuid=True),
            sa.ForeignKey("konkin_template.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "idempotency_key",
            sa.String(128),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "imported_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "summary",
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "imported_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        *_audit_columns(),
    )

    # ------------------------------------------------------------------
    # (g) GIN index on ml_stream.structure (REQ-dynamic-ml-schema).
    # `USING GIN` is the Postgres-native JSONB containment index; the
    # accompanying integration test runs `structure @> '{...}'::jsonb`.
    # ------------------------------------------------------------------
    op.execute(
        "CREATE INDEX idx_ml_stream_structure "
        "ON ml_stream USING GIN (structure)"
    )

    # ------------------------------------------------------------------
    # (h) B-04 fix — users.bidang_id + fk_users_bidang_id.
    # Plan 05's 0002 deliberately omitted this column because `bidang`
    # didn't exist yet. Now that we've created `bidang` above, we add
    # the column + FK in a single migration step.
    # ------------------------------------------------------------------
    # Single-line form so static greps like `add_column.+users.+bidang_id` match.
    op.add_column("users", sa.Column("bidang_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_users_bidang_id",
        source_table="users",
        referent_table="bidang",
        local_cols=["bidang_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Reverse of upgrade(): drop FK + column on users first, then GIN index,
    # then the six tables in child-before-parent order so cascading FKs
    # don't fight Alembic.
    op.drop_constraint(
        "fk_users_bidang_id", "users", type_="foreignkey"
    )
    op.drop_column("users", "bidang_id")

    op.execute("DROP INDEX IF EXISTS idx_ml_stream_structure")

    op.drop_table("konkin_import_log")
    op.drop_table("ml_stream")
    op.drop_table("indikator")
    op.drop_table("perspektif")
    op.drop_table("konkin_template")
    op.drop_table("bidang")
