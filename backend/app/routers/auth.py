"""Auth endpoints (REQ-auth-jwt, REQ-route-guards backend half).

Four endpoints under the auto-discovered ``/auth`` prefix (full path
``/api/v1/auth/*`` after the api_router prefix is applied):

- ``POST /auth/login``    — email + password → access + refresh JWT,
                            three cookies set (access_token, refresh_token,
                            csrf_token). Brute-force lockout via Redis
                            ``login_fail:{email}`` counter (T-05-S-02).
- ``POST /auth/refresh``  — rotates refresh token (T-05-S-03). Old jti is
                            revoked; new pair issued. Body / cookie /
                            Bearer header all accepted as input.
- ``POST /auth/logout``   — revokes active refresh jti, clears all three
                            cookies.
- ``GET  /auth/me``       — returns the current user (UserPublic).

Cookie config:
- ``access_token``  : path=/api/v1, httpOnly, samesite=lax, secure (off in DEBUG)
- ``refresh_token`` : path=/api/v1/auth/refresh, httpOnly, samesite=strict, secure
- ``csrf_token``    : path=/, NOT httpOnly (frontend reads + echoes), samesite=lax

Brute-force lockout (CONTEXT.md "Auth" + plan threat T-05-S-02):
- 5 failed logins for one email within 300 s → 429 with Retry-After: 900.
- Counter key: ``login_fail:{email}``, TTL 300 s, INCR on every failure.
- Reset on successful login.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Body,
    Cookie,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from jose import JWTError
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.deps.auth import current_user
from app.deps.db import get_db
from app.deps.redis import get_redis
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.schemas.user import UserPublic
from app.services.audit_immediate import audit_emit_immediately
from app.services.refresh_tokens import is_revoked, revoke_jti

router = APIRouter(prefix="/auth", tags=["auth"])

# --- Tunables ----------------------------------------------------------------

LOGIN_FAIL_WINDOW_S = 300       # 5 minutes
LOGIN_FAIL_THRESHOLD = 5        # locked after 5 failures
LOGIN_LOCK_RETRY_S = 900        # 15 minutes Retry-After


def _cookie_kwargs_secure(path: str, samesite: str) -> dict:
    """Centralized cookie config. `secure` is dropped in DEBUG so dev over http works."""
    kwargs = {
        "path": path,
        "httponly": True,
        "samesite": samesite,
        "secure": not settings.DEBUG,
    }
    return kwargs


def _set_auth_cookies(
    response: Response,
    access_token: str,
    access_exp: datetime,
    refresh_token: str,
    refresh_exp: datetime,
    csrf_token: str,
) -> None:
    """Set the three login cookies on the response object."""
    # access_token cookie — every API call uses it (path=/api/v1)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=int((access_exp - datetime.now(timezone.utc)).total_seconds()),
        **_cookie_kwargs_secure(path="/api/v1", samesite="lax"),
    )
    # refresh_token cookie — only sent to /auth/refresh (path-scoped)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=int((refresh_exp - datetime.now(timezone.utc)).total_seconds()),
        **_cookie_kwargs_secure(path="/api/v1/auth/refresh", samesite="strict"),
    )
    # csrf_token cookie — NOT httpOnly (frontend reads and echoes via X-CSRF-Token)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        max_age=int((access_exp - datetime.now(timezone.utc)).total_seconds()),
        path="/",
        httponly=False,
        samesite="lax",
        secure=not settings.DEBUG,
    )


def _clear_auth_cookies(response: Response) -> None:
    # delete_cookie matches by name + path; we must pass the same path each cookie was set with.
    response.delete_cookie("access_token", path="/api/v1")
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")
    response.delete_cookie("csrf_token", path="/")


def _build_user_public(user: User) -> UserPublic:
    """Use the UserPublic flatten validator to project a SQLAlchemy User."""
    return UserPublic.model_validate(user, from_attributes=True)


# --- Brute-force counter (Redis) --------------------------------------------


async def _record_login_fail(r: Redis, email: str) -> int:
    """INCR the per-email failure counter with sliding-window TTL. Return current count."""
    key = f"login_fail:{email.lower()}"
    count = await r.incr(key)
    if count == 1:
        await r.expire(key, LOGIN_FAIL_WINDOW_S)
    return int(count)


async def _is_locked(r: Redis, email: str) -> bool:
    key = f"login_fail:{email.lower()}"
    raw = await r.get(key)
    if not raw:
        return False
    try:
        return int(raw) >= LOGIN_FAIL_THRESHOLD
    except (TypeError, ValueError):
        return False


async def _reset_login_fail(r: Redis, email: str) -> None:
    await r.delete(f"login_fail:{email.lower()}")


# --- /login -----------------------------------------------------------------


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Email+password login (dual-mode)",
    tags=["audit:auth"],
)
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
) -> TokenPair:
    """Authenticate with email + password and issue access + refresh tokens.

    On success: sets three cookies AND returns the token pair in the JSON
    body (dual-mode per RESEARCH.md Pattern 3). Bearer-mode consumers ignore
    the cookies; cookie-mode consumers ignore the body tokens (they have
    them in cookies already).

    Failure modes:
    - 429 if the email has 5+ failures within the lockout window (with
      Retry-After: 900). T-05-S-02 mitigation.
    - 401 on wrong password or missing/inactive user — generic message so
      enumeration is impractical (also caught by nginx login_zone in Plan 02).
    """
    email = payload.email.lower()

    # Lockout check BEFORE any DB / bcrypt work (cheap deny).
    if await _is_locked(r, email):
        await audit_emit_immediately(
            db,
            user_id=None,
            action="POST /api/v1/auth/login",
            before=None,
            after={"event": "login.failure", "email": email, "reason": "locked"},
            entity_type="auth",
            entity_id=None,
            request=request,
        )
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed login attempts; account temporarily locked",
            headers={"Retry-After": str(LOGIN_LOCK_RETRY_S)},
        )

    user = await db.scalar(
        select(User).where(
            User.email == email,
            User.deleted_at.is_(None),
        )
    )
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        reason = "inactive" if user and not user.is_active else "bad_password"
        await _record_login_fail(r, email)
        await audit_emit_immediately(
            db,
            user_id=user.id if user else None,
            action="POST /api/v1/auth/login",
            before=None,
            after={"event": "login.failure", "email": email, "reason": reason},
            entity_type="auth",
            entity_id=user.id if user else None,
            request=request,
        )
        # Re-check lockout: the failure we just recorded may have crossed the threshold.
        # On the threshold-crossing failure we still want the user to see 401 (consistent
        # with "wrong password") — the NEXT request from the same email is what gets 429.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    # Success — reset counter, issue tokens
    await _reset_login_fail(r, email)

    user_roles = [role.name for role in user.roles]
    bidang_id = getattr(user, "bidang_id", None)  # pre-Plan-06: always None
    bidang_id_str = str(bidang_id) if bidang_id is not None else None

    access_token, access_exp = create_access_token(
        sub=str(user.id), roles=user_roles, bidang_id=bidang_id_str
    )
    refresh_token, _jti, refresh_exp = create_refresh_token(sub=str(user.id))
    csrf_token = secrets.token_urlsafe(32)

    _set_auth_cookies(
        response,
        access_token,
        access_exp,
        refresh_token,
        refresh_exp,
        csrf_token,
    )
    request.state.audit_after = {
        "event": "login.success",
        "email": email,
        "user_id": str(user.id),
    }
    request.state.audit_entity_id = str(user.id)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_build_user_public(user),
    )


# --- /refresh ---------------------------------------------------------------


@router.post("/refresh", response_model=TokenPair, summary="Rotate refresh token (revoke old jti)")
async def refresh(
    response: Response,
    payload: RefreshRequest | None = Body(default=None),
    refresh_token_cookie: str | None = Cookie(default=None, alias="refresh_token"),
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
) -> TokenPair:
    """Rotate the refresh token. The OLD jti is added to the revocation set;
    any further refresh attempt with that old token returns 401.

    Input precedence: JSON body > cookie > Bearer header.
    """
    # Resolve refresh token from one of three sources
    token: str | None = None
    if payload and payload.refresh_token:
        token = payload.refresh_token
    elif refresh_token_cookie:
        token = refresh_token_cookie
    elif authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing refresh token")

    try:
        claims = decode_token(token)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    if claims.get("typ") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")

    sub = claims.get("sub")
    jti = claims.get("jti")
    exp_ts = claims.get("exp")
    if not sub or not jti or exp_ts is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Malformed refresh token")

    # Revocation check
    if await is_revoked(r, sub, jti):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token revoked")

    # Look up user (must still be active)
    import uuid as _uuid
    try:
        user_id = _uuid.UUID(sub)
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

    # Revoke OLD jti (TTL = original remaining lifetime)
    old_exp = datetime.fromtimestamp(int(exp_ts), tz=timezone.utc)
    await revoke_jti(r, sub, jti, old_exp)

    # Issue new pair
    user_roles = [role.name for role in user.roles]
    bidang_id = getattr(user, "bidang_id", None)
    bidang_id_str = str(bidang_id) if bidang_id is not None else None

    access_token, access_exp = create_access_token(
        sub=str(user.id), roles=user_roles, bidang_id=bidang_id_str
    )
    new_refresh_token, _new_jti, new_refresh_exp = create_refresh_token(sub=str(user.id))
    csrf_token = secrets.token_urlsafe(32)

    _set_auth_cookies(
        response,
        access_token,
        access_exp,
        new_refresh_token,
        new_refresh_exp,
        csrf_token,
    )

    return TokenPair(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=_build_user_public(user),
    )


# --- /logout ----------------------------------------------------------------


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke active refresh token + clear cookies",
    tags=["audit:auth"],
)
async def logout(
    request: Request,
    response: Response,
    refresh_token_cookie: str | None = Cookie(default=None, alias="refresh_token"),
    payload: RefreshRequest | None = Body(default=None),
    r: Redis = Depends(get_redis),
) -> Response:
    """Revoke the active refresh token (best-effort) and clear all three cookies.

    Idempotent: returns 204 even if the token is missing or already revoked.
    Best-effort revoke means malformed / expired tokens don't fail logout —
    the cookies are cleared regardless.
    """
    token = None
    if payload and payload.refresh_token:
        token = payload.refresh_token
    elif refresh_token_cookie:
        token = refresh_token_cookie
    audit_user_id = None

    if token:
        try:
            claims = decode_token(token)
            if claims.get("typ") == "refresh":
                sub = claims.get("sub")
                jti = claims.get("jti")
                exp_ts = claims.get("exp")
                if sub and jti and exp_ts is not None:
                    import uuid as _uuid

                    try:
                        audit_user_id = _uuid.UUID(str(sub))
                    except (TypeError, ValueError):
                        audit_user_id = None
                    exp = datetime.fromtimestamp(int(exp_ts), tz=timezone.utc)
                    await revoke_jti(r, sub, jti, exp)
        except JWTError:
            # Best-effort: ignore malformed/expired tokens on logout.
            pass

    _clear_auth_cookies(response)
    request.state.audit_after = {
        "event": "logout",
        "user_id": str(audit_user_id) if audit_user_id else None,
    }
    request.state.audit_entity_id = str(audit_user_id) if audit_user_id else None
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


# --- /me --------------------------------------------------------------------


@router.get("/me", response_model=UserPublic, summary="Current user (dual-mode)")
async def me(user: User = Depends(current_user)) -> UserPublic:
    """Return the authenticated user. 401 if no token / inactive / soft-deleted."""
    return _build_user_public(user)
