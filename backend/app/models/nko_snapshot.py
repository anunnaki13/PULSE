"""Persisted NKO dashboard snapshots."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NkoSnapshot(Base):
    __tablename__ = "nko_snapshot"
    __table_args__ = (UniqueConstraint("periode_id", name="uq_nko_snapshot_periode"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    periode_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("periode.id", ondelete="CASCADE"), nullable=False, index=True)
    nko_total: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, server_default=text("0"))
    gross_pilar_total: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, server_default=text("0"))
    compliance_deduction: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, server_default=text("0"))
    breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    source: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'live'"))
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)
