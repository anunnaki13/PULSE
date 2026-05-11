"""Auth round-trip tests (REQ-auth-jwt acceptance).

Covers:
- POST /auth/login → 200 + access+refresh tokens (body) + 3 cookies set
- POST /auth/login with wrong password → 401
- GET  /auth/me (Bearer mode) returns the user
- POST /auth/refresh rotates the refresh token (old jti revoked → 401 on reuse)
- Brute-force lockout fires after 5 failed login attempts within 5 minutes

These tests use the `db_session` fixture (transactional rollback) so a fresh
user is created per test. They require a live Postgres + Redis — run via
`wsl -d Ubuntu-22.04 -- python3.11 -m pytest backend/tests/test_auth.py -q`
against the local docker stack (or any pg+redis pair that the .env points
at).

Tests use the SIX spec-named roles (B-01/B-02): super_admin, admin_unit,
pic_bidang, asesor, manajer_unit, viewer. The "admin" fixture below
assigns `admin_unit` (NOT the legacy "Admin").
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User


@pytest_asyncio.fixture
async def admin(db_session):
    """User with role `admin_unit` (B-01/B-02 spec naming)."""
    role = await db_session.scalar(select(Role).where(Role.name == "admin_unit"))
    assert role is not None, "admin_unit role must be seeded by 0002 migration"
    u = User(
        email="admin@pulse.local",
        full_name="Admin Test",
        password_hash=hash_password("s3cret-pwd"),
    )
    u.roles = [role]
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.mark.asyncio
async def test_login_returns_tokens_and_cookies(client, admin):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": admin.email, "password": "s3cret-pwd"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == admin.email
    assert "admin_unit" in body["user"]["roles"]
    # Dual-mode: cookies set on the response too.
    assert "access_token" in r.cookies
    assert "refresh_token" in r.cookies
    assert "csrf_token" in r.cookies


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client, admin):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": admin.email, "password": "wrong"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_with_bearer(client, admin):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": admin.email, "password": "s3cret-pwd"},
    )
    access = r.json()["access_token"]
    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == admin.email
    assert "admin_unit" in me.json()["roles"]


@pytest.mark.asyncio
async def test_refresh_rotates_jti(client, admin):
    r1 = await client.post(
        "/api/v1/auth/login",
        json={"email": admin.email, "password": "s3cret-pwd"},
    )
    refresh1 = r1.json()["refresh_token"]

    r2 = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh1}
    )
    assert r2.status_code == 200, r2.text
    refresh2 = r2.json()["refresh_token"]
    assert refresh2 != refresh1

    # Reusing the old refresh token must fail — old jti revoked.
    r3 = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh1}
    )
    assert r3.status_code == 401


@pytest.mark.asyncio
async def test_brute_force_lockout(client, admin):
    """5 consecutive failures → next request returns 429 with Retry-After."""
    for _ in range(5):
        bad = await client.post(
            "/api/v1/auth/login",
            json={"email": admin.email, "password": "wrong"},
        )
        assert bad.status_code == 401
    # 6th request — even with correct password — must be locked out.
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": admin.email, "password": "s3cret-pwd"},
    )
    assert r.status_code == 429
    assert "Retry-After" in r.headers


@pytest.mark.asyncio
async def test_logout_clears_cookies_and_revokes(client, admin):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": admin.email, "password": "s3cret-pwd"},
    )
    refresh = r.json()["refresh_token"]

    lo = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": refresh}
    )
    assert lo.status_code == 204

    # Refresh token from before logout must now be rejected.
    r2 = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh}
    )
    assert r2.status_code == 401
