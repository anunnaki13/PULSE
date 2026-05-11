"""KonkinTemplate master (REQ-konkin-template-crud).

A Konkin template is a versioned snapshot of (perspektif → indikator) for a
single year. ``locked`` becomes True after the bobot validator passes and
"Lock Template" is called from the admin UI; once locked, every mutating
route rejects updates with 409 — only ``clone_from_id`` can produce a new
mutable copy for the next year.

Uniqueness on ``(tahun, nama)`` matches the source-doc rule that the same
template name cannot be reused within a single year (e.g. two "Konkin 2026"
records collide).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class KonkinTemplate(Base):
    __tablename__ = "konkin_template"
    __table_args__ = (
        UniqueConstraint("tahun", "nama", name="uq_konkin_template_tahun_nama"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    tahun: Mapped[int] = mapped_column(Integer, nullable=False)
    nama: Mapped[str] = mapped_column(String(255), nullable=False)
    locked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
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
