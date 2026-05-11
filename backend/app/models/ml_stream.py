"""ML Stream master (REQ-dynamic-ml-schema + DEC-010).

A "Maturity-Level stream" (Outage Management, SMAP, EAF, EFOR, …) owns a
rubric tree describing areas → sub-areas → kriteria L0..L4. The tree is
stored verbatim in ``structure`` as JSONB so each stream can declare its
own shape without per-stream tables — this is the locked "dynamic JSONB
schema for maturity-level rubrics" decision (DEC-010).

GIN index ``idx_ml_stream_structure`` is created in the 0003 migration so
JSONB containment queries (``structure @> '{"areas":[{"code":"OM-1"}]}'``)
hit the index instead of seq-scanning. Phase 2/6 tightens the JSON schema
via Pydantic v2 discriminated unions; Phase 1 accepts any dict.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MlStream(Base):
    __tablename__ = "ml_stream"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    kode: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    nama: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(16), nullable=False)
    # The maturity-level rubric tree. Empty object as default so freshly
    # inserted rows don't violate NOT NULL during a two-step admin flow
    # (create header → edit structure).
    structure: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
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
