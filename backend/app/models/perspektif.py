"""Perspektif rows hanging off a KonkinTemplate (REQ-konkin-template-crud + W-07).

Per Konkin 2026 there are six perspektif kodes — I..V are positive
contributors (Σ bobot = 100.00), and VI ("Compliance") is a **pengurang**
(reducer) with `bobot = 0.00` and `pengurang_cap = 10.00` (max −10 pp).

W-07 fix — pengurang convention:
- `is_pengurang BOOLEAN NOT NULL DEFAULT FALSE`. Perspektif VI carries
  `is_pengurang=True`.
- `pengurang_cap NUMERIC(5,2) NULL`. Phase-3 NKO calc subtracts up to this
  cap from gross NKO. Non-pengurang rows leave it NULL.
- Lock validator filters `WHERE is_pengurang = FALSE` when summing perspektif
  bobots — i.e. the I..V perspektif must sum to 100 ± 0.01, and the
  pengurang row is excluded.

Indikator bobots within each non-pengurang perspektif still sum to 100% per
REQ-konkin-template-crud (the lock validator enforces this separately).

CASCADE on `template_id` so deleting a draft template wipes its perspektif
tree (Phase 1 hard delete only on unlocked drafts; locked templates use
soft-delete on the row level).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Perspektif(Base):
    __tablename__ = "perspektif"
    __table_args__ = (
        UniqueConstraint("template_id", "kode", name="uq_perspektif_template_kode"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("konkin_template.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Roman-numeral kode: I, II, III, IV, V, VI
    kode: Mapped[str] = mapped_column(String(8), nullable=False)
    nama: Mapped[str] = mapped_column(String(255), nullable=False)
    bobot: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), nullable=False, server_default=text("0")
    )
    # W-07: pengurang convention. Stored as bobot=0.00 + is_pengurang=True for
    # perspektif VI. Lock validator filters by is_pengurang=False; Phase-3 NKO
    # calc subtracts pengurang_cap (max -10 for VI) from gross.
    is_pengurang: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    pengurang_cap: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )

    # audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False,
    )
