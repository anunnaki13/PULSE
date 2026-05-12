"""pedoman chunks.

Revision ID: 0010_pedoman_chunks
Revises: 0009_ai_integration
Create Date: 2026-05-13 16:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0010_pedoman_chunks"
down_revision = "0009_ai_integration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "pedoman_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("source_id", sa.String(80), nullable=False, unique=True),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("section", sa.String(160), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.execute("ALTER TABLE pedoman_chunks ADD COLUMN embedding vector(16) NOT NULL")
    op.create_index("ix_pedoman_chunks_source_id", "pedoman_chunks", ["source_id"])
    op.create_index("ix_pedoman_chunks_source_hash", "pedoman_chunks", ["source_hash"])
    op.execute(
        "CREATE INDEX ix_pedoman_chunks_embedding_cosine "
        "ON pedoman_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_pedoman_chunks_embedding_cosine")
    op.drop_index("ix_pedoman_chunks_source_hash", table_name="pedoman_chunks")
    op.drop_index("ix_pedoman_chunks_source_id", table_name="pedoman_chunks")
    op.drop_table("pedoman_chunks")
