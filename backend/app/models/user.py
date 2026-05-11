"""User model (REQ-auth-jwt, REQ-user-roles).

B-04 fix (deliberate omission): the `bidang_id` column is NOT declared in
this model. Plan 06 (master-data) declares it via `op.add_column` +
`op.create_foreign_key` to `bidang(id)` AFTER the `bidang` table is created,
and amends this model file in-place at that time. Until Plan 06 lands, the
auth router reads the future-claim via `getattr(user, "bidang_id", None)`
so login compiles and works.

Audit columns follow CONTEXT.md "Data Model" lock: `created_at`,
`updated_at`, `deleted_at` (soft-delete). `created_by` / `updated_by` are
intentionally deferred — these are FKs to `users` and would force the
cycle to be deferred; they will be added in Phase 2 alongside the audit log.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, text
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
    # NOTE: bidang_id column intentionally NOT declared here per CONTEXT.md
    # "Migration FK ordering" (B-04 fix). Plan 06 (master data) declares it
    # via op.add_column + op.create_foreign_key after `bidang` is created,
    # and amends this model file in-place to add:
    #   bidang_id: Mapped[uuid.UUID | None] = mapped_column(
    #       UUID(as_uuid=True),
    #       ForeignKey("bidang.id", ondelete="SET NULL"),
    #       nullable=True,
    #   )
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
