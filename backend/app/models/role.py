"""Role + user_role association table (REQ-user-roles, B-01/B-02).

Phase-1 seeds SIX roles using the spec naming verbatim per REQ-user-roles and
CONTEXT.md Auth: super_admin, admin_unit, pic_bidang, asesor, manajer_unit,
viewer. The seed lives in the 0002 Alembic migration; this module only
declares the schema so SQLAlchemy can manage the table and the
`user_roles` association.

Auto-discovery: `app/db/base.py` walks `app/models/` and imports this module,
so Alembic --autogenerate sees `roles` and `user_roles` without any edits to
`base.py`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )


# Association table: user <-> role (many-to-many). CASCADE deletes only the
# linkage rows, never the underlying user / role row.
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
