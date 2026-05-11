"""baseline

Revision ID: 0001_baseline
Revises:
Create Date: 2026-05-11 12:00:00

Empty baseline revision so Plans 05 (auth) and 06 (master data) can run
`alembic revision --autogenerate` against `down_revision=None` properly,
chaining their own revs to this one. No DDL here — schema work belongs
to those downstream plans.
"""
from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
