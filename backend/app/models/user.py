"""User model (REQ-auth-jwt, REQ-user-roles).

B-04 fix (amended by Plan 06): the ``bidang_id`` column is declared below.
Plan 05's 0002 migration intentionally does NOT create the column — it is
added in Plan 06's 0003_master_data migration via ``op.add_column`` +
``op.create_foreign_key`` to ``bidang(id)`` AFTER the ``bidang`` table
exists (CONTEXT.md "Migration FK ordering"). This file is now the
authoritative declaration of the column; ``getattr(user, "bidang_id",
None)`` reads in the auth router still work and now return real values.

Audit columns follow CONTEXT.md "Data Model" lock: `created_at`,
`updated_at`, `deleted_at` (soft-delete). `created_by` / `updated_by` are
intentionally deferred — these are FKs to `users` and would force the
cycle to be deferred; they will be added in Phase 2 alongside the audit log.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.role import Role, user_roles


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    # B-04: bidang_id is added here AFTER the bidang table is created in
    # Plan 06's 0003_master_data migration (op.add_column + create_foreign_key
    # with ondelete="SET NULL"). Plan 05's 0002 migration deliberately did
    # NOT touch this column to avoid an FK-ordering hazard. The auth router
    # reads it via `getattr(user, "bidang_id", None)` so legacy code paths
    # don't break; new code can use `user.bidang_id` directly.
    bidang_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bidang.id", ondelete="SET NULL"),
        nullable=True,
    )
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

    # selectin so accessing `user.roles` after a `db.scalar(select(User))`
    # doesn't trigger an implicit IO load in async context (Pitfall #4 cousin).
    roles: Mapped[list[Role]] = relationship(
        "Role", secondary=user_roles, lazy="selectin"
    )
