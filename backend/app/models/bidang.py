"""Bidang master (REQ-bidang-master).

Hierarchical organisation unit used to scope per-bidang reads (`pic_bidang`)
and to anchor every assessment row to a responsible organisation. `parent_id`
is a self-FK so the bidang tree can model BIDANG → SUB-BIDANG without an
extra table; ON DELETE SET NULL avoids orphaning children when an internal
reorg deletes a parent (Phase-2 hierarchy expansion will refine this).

Audit columns follow CONTEXT.md "Data Model": ``created_at``, ``updated_at``,
``deleted_at`` (soft-delete). ``created_by`` / ``updated_by`` are deferred to
Phase 2 alongside the audit log (FK cycle on ``users`` not yet broken).

Auto-discovery: ``app/db/base.py`` walks ``app/models/`` and imports this
module, so Alembic ``--autogenerate`` sees ``bidang`` without any edits to
``base.py``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Bidang(Base):
    __tablename__ = "bidang"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    kode: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    nama: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bidang.id", ondelete="SET NULL"),
        nullable=True,
    )

    # audit + soft delete
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
