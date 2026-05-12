"""FastAPI auth dependencies (REQ-auth-jwt, REQ-route-guards backend half).

`current_user` is RESEARCH.md Pattern 3: dual-mode token transport — accepts
EITHER ``Authorization: Bearer <token>`` OR an ``access_token`` httpOnly
cookie. Bearer wins when both are present (explicit > implicit).

`require_role(*allowed)` is the factory used by every privileged route. It
takes spec role names verbatim per B-01/B-02:

    require_role("super_admin", "admin_unit")
    require_role("pic_bidang")
    require_role("manajer_unit")

If the decoded token has no roles overlapping ``allowed``, the dep raises
403 Forbidden. Missing / invalid token raises 401 (via `current_user`).
"""

from __future__ import annotations

import uuid

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.deps.db import get_db
from app.models.user import User


def _extract_token(
    authorization: str | None, access_cookie: str | None
) -> str | None:
    """Return the bearer token or the cookie token; None if neither present."""
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip() or None
    if access_cookie:
        return access_cookie
    return None


async def current_user(
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a Bearer header OR access cookie.

    Raises 401 on:
    - no token present
    - token decode failure (signature/expiry/malformed/alg-not-in-allow-list)
    - wrong token typ (refresh token used in access slot)
    - user not found, soft-deleted, or inactive
    """
    token = _extract_token(authorization, access_token)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    if payload.get("typ") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token missing subject")

    # Cast to UUID — `sub` is stored as a string in the JWT, but the DB column is UUID.
    try:
        user_id = uuid.UUID(sub)
    except (ValueError, TypeError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid subject")

    user = await db.scalar(
        select(User).where(
            User.id == user_id,
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
    )
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer active")
    return user


async def current_user_optional(request: Request, db: AsyncSession) -> User | None:
    """Best-effort user resolver for cross-cutting middleware.

    Middleware cannot use FastAPI dependency injection, so this mirrors
    ``current_user`` with explicit request/session inputs and returns ``None``
    for anonymous or invalid credentials.
    """
    token = _extract_token(
        request.headers.get("authorization"),
        request.cookies.get("access_token"),
    )
    if not token:
        return None
    try:
        payload = decode_token(token)
        if payload.get("typ") != "access":
            return None
        user_id = uuid.UUID(str(payload.get("sub")))
    except (JWTError, ValueError, TypeError):
        return None
    return await db.scalar(
        select(User).where(
            User.id == user_id,
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
    )


def require_role(*allowed: str):
    """Return a FastAPI dependency that asserts the user has at least one allowed role.

    Usage::

        @router.get("/admin-only", dependencies=[Depends(require_role("super_admin", "admin_unit"))])
        async def admin_only(): ...

    Callers pass SPEC role names verbatim (B-01/B-02): super_admin,
    admin_unit, pic_bidang, asesor, manajer_unit, viewer. Mis-spellings are
    silent (the role set just won't intersect) — keep the names in sync with
    REQ-user-roles and `PHASE1_ROLES` in the 0002 migration.
    """
    allowed_set = set(allowed)

    async def _check(user: User = Depends(current_user)) -> User:
        user_role_names = {r.name for r in user.roles}
        if not user_role_names & allowed_set:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user

    return _check
