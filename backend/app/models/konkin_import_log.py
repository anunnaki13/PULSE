"""Idempotency log for Excel-template imports (CONTEXT.md Data Model).

The admin-only ``POST /konkin/templates/{id}/import-from-excel`` endpoint
gates re-runs on a unique ``idempotency_key`` (HTTP ``Idempotency-Key``
header). The very first request with a given key inserts a row here and
performs the import; every subsequent request with the same key short-
circuits to 200 + ``{"status": "already_applied", "summary": …}`` so a
flaky network or a refresh-double-submit doesn't double-import.

``imported_by`` references ``users.id`` so the audit row can be cross-joined
with the auth log — but the FK is intentionally ``ON DELETE SET NULL`` so a
user soft-delete doesn't wipe history.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class KonkinImportLog(Base):
    __tablename__ = "konkin_import_log"

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
    idempotency_key: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False
    )
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    summary: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    imported_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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
