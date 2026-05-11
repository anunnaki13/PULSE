"""auth: users + roles + user_roles (six-role seed; bidang_id added by 0003 per B-04)

Revision ID: 0002_auth_users_roles
Revises: 0001_baseline
Create Date: 2026-05-12 10:00:00

B-01 + B-02 fix: seeds SIX role rows using REQ-user-roles spec naming
verbatim — super_admin, admin_unit, pic_bidang, asesor, manajer_unit, viewer.
The seed is idempotent via `INSERT ... ON CONFLICT (name) DO NOTHING`.

B-04 fix: the `users` table does NOT carry a `bidang_id` column here. Plan 06
(master-data, revision 0003_master_data) adds the column AND its FK to
`bidang(id)` once the `bidang` table exists. Declaring the FK in this
migration would violate ordering (FK target doesn't exist yet) and is the
documented mitigation in CONTEXT.md "Migration FK ordering".

W-02 wiring: the placeholder `metrics_admin_dep` in `app/deps/metrics_admin.py`
is swapped to `require_role("super_admin", "admin_unit")` in this plan's
Python code (not in this migration) — that change makes the seeded
`super_admin` and `admin_unit` rows callable by `/health/detail` + `/metrics`.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "0002_auth_users_roles"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


# B-01 + B-02: six Phase-1 roles, spec naming used verbatim everywhere
# (Python code, tests, frontend Role union, Alembic seed).
PHASE1_ROLES: list[tuple[str, str]] = [
    (
        "super_admin",
        "Akses penuh lintas-bidang dan lintas-unit; pemilik konfigurasi sistem.",
    ),
    (
        "admin_unit",
        "Admin tingkat unit pembangkit; CRUD master data dan kelola pengguna unit.",
    ),
    (
        "pic_bidang",
        "PIC bidang yang mengisi self-assessment dan rekomendasi pada bidang_id-nya.",
    ),
    (
        "asesor",
        "Asesor yang mereview submission PIC; approve / override / request_revision.",
    ),
    (
        "manajer_unit",
        "Manajer unit yang mengonsumsi dashboard NKO dan laporan eksekutif.",
    ),
    (
        "viewer",
        "Read-only viewer untuk audit / observer; tidak ada mutasi.",
    ),
]


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "users",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        # NO bidang_id here — Plan 06 (0003_master_data) adds it after `bidang`
        # exists (B-04 fix per CONTEXT.md "Migration FK ordering").
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
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # B-01 / B-02 seed: six spec-named roles. Idempotent via ON CONFLICT.
    bind = op.get_bind()
    for name, desc in PHASE1_ROLES:
        bind.execute(
            sa.text(
                "INSERT INTO roles (name, description) VALUES (:n, :d) "
                "ON CONFLICT (name) DO NOTHING"
            ),
            {"n": name, "d": desc},
        )


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("roles")
