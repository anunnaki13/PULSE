"""Indikator rows hanging off a Perspektif (REQ-konkin-template-crud).

Each indikator carries a `polaritas` flag (positif/negatif/range) that the
NKO calculator uses to decide whether higher actuals are good or bad.
`formula` is a free-form short description ("MWh produksi / MWh target × 100")
— validation and execution are Phase 3 work.

`link_eviden` is a URL string (Pydantic schema uses ``HttpUrl`` to enforce
``format: uri`` in the OpenAPI components — the no-upload contract test in
``backend/tests/test_no_upload_policy.py`` walks the components schema and
rejects any non-URI definition of this field). It is a TEXT/URL field
ONLY — no multipart upload route ever stores into it (CONSTR-no-file-upload,
DEC-010).

CASCADE on `perspektif_id` so deleting a draft perspektif wipes its
indikator. Phase 2+ will switch to soft-delete-only on locked templates.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Indikator(Base):
    __tablename__ = "indikator"
    __table_args__ = (
        UniqueConstraint(
            "perspektif_id", "kode", name="uq_indikator_perspektif_kode"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    perspektif_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("perspektif.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kode: Mapped[str] = mapped_column(String(32), nullable=False)
    nama: Mapped[str] = mapped_column(String(255), nullable=False)
    bobot: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), nullable=False, server_default=text("0")
    )
    # positif | negatif | range — validated at the Pydantic layer
    polaritas: Mapped[str] = mapped_column(String(16), nullable=False)
    formula: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # URL-only (link, never file). Pydantic HttpUrl + contract test guard this.
    link_eviden: Mapped[str | None] = mapped_column(String(2048), nullable=True)

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
