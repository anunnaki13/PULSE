"""First-admin bootstrap seed (CONTEXT.md §Auth — RESEARCH OQ#3 ADOPTED).

Creates exactly one user from ``settings.INITIAL_ADMIN_EMAIL`` /
``settings.INITIAL_ADMIN_PASSWORD`` and attaches the **``admin_unit``** role
(NOT capitalized "Admin"). Per CONTEXT.md and the ROADMAP success criterion
#1 wording, "Admin" in the Phase-1 acceptance walk refers specifically to a
user with role ``admin_unit``.

Idempotency contract: if a user with the configured email already exists,
the seed is a no-op. No role re-attachment, no password reset. Password
rotation is expected after first login (operator workflow, not seed
responsibility).

Dependency on Plan-05 0002 migration: the ``roles`` table must already be
populated with the six spec-name rows before this seed runs. The assertion
on ``admin_role is not None`` makes the failure mode explicit if migrations
were skipped.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User


async def seed_admin_user(db: AsyncSession) -> None:
    email = settings.INITIAL_ADMIN_EMAIL.lower()

    existing = await db.scalar(select(User).where(User.email == email))
    if existing is not None:
        # Idempotent — second run is a no-op.
        print(f"[seed] admin_user: '{email}' already exists (skip)")
        return

    # Role lookup by spec name. Plan 05's 0002 migration seeds all six
    # spec-name rows; if this assertion trips, migrations weren't applied
    # before the seed ran.
    admin_role = await db.scalar(select(Role).where(Role.name == "admin_unit"))
    assert (
        admin_role is not None
    ), "Role 'admin_unit' must be seeded by 0002 migration before seed runs"

    user = User(
        email=email,
        full_name="Administrator Unit",
        password_hash=hash_password(settings.INITIAL_ADMIN_PASSWORD.get_secret_value()),
        is_active=True,
        # bidang_id stays None — admin_unit is unit-scoped but Phase-1 admin
        # spans the whole unit (CONTEXT.md "Auth" → admin_unit users without
        # bidang_id can see/edit all bidangs).
    )
    user.roles = [admin_role]
    db.add(user)
    await db.flush()
    print(f"[seed] admin_user: created '{email}' with role 'admin_unit' (id={user.id})")
