"""Mapping of indikator applicability by bidang."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IndikatorApplicableBidang(Base):
    __tablename__ = "indikator_applicable_bidang"

    indikator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("indikator.id", ondelete="CASCADE"), primary_key=True)
    bidang_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bidang.id", ondelete="CASCADE"), primary_key=True)
    is_aggregate: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
