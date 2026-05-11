"""RBAC tests (REQ-route-guards backend half) using the SIX spec roles.

Each test creates a user with a single spec role, logs in via /auth/login,
then hits a couple of test-only endpoints registered on the live app under
``/__test/*`` to assert require_role() returns 200 or 403 as advertised.

Test roles used (B-01/B-02 verbatim):
- super_admin / admin_unit  -> /__test/admin-only (200)
- pic_bidang                -> /__test/pic-only (200), /__test/admin-only (403)
- manajer_unit              -> /__test/manajer-only (200), /__test/pic-only (403)
- (anonymous)               -> any /__test/* (401)
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.security import hash_password
from app.deps.auth import require_role
from app.main import app
from app.models.role import Role
from app.models.user import User

# Register test-only routes on the live app, idempotent across pytest sessions
# (skip the include if the routes are already there from a previous import).
_TEST_PREFIX = "/__test"
_existing = {r.path for r in app.routes}
if f"{_TEST_PREFIX}/admin-only" not in _existing:
    _t = APIRouter(prefix=_TEST_PREFIX)

    @_t.get(
        "/admin-only",
        dependencies=[Depends(require_role("super_admin", "admin_unit"))],
    )
    async def _admin_only() -> dict:
        return {"ok": True}

    @_t.get("/pic-only", dependencies=[Depends(require_role("pic_bidang"))])
    async def _pic_only() -> dict:
        return {"ok": True}

    @_t.get("/manajer-only", dependencies=[Depends(require_role("manajer_unit"))])
    async def _manajer_only() -> dict:
        return {"ok": True}

    app.include_router(_t)


async def _user_with_role(db_session, email: str, role_name: str) -> User:
    role = await db_session.scalar(select(Role).where(Role.name == role_name))
    assert role is not None, f"role {role_name!r} not seeded — check 0002 migration (B-01/B-02)"
    u = User(
        email=email,
        full_name=role_name,
        password_hash=hash_password("pwd"),
    )
    u.roles = [role]
    db_session.add(u)
    await db_session.flush()
    return u


@pytest_asyncio.fixture
async def pic_user(db_session):
    return await _user_with_role(db_session, "pic@pulse.local", "pic_bidang")


@pytest_asyncio.fixture
async def admin_unit_user(db_session):
    return await _user_with_role(db_session, "admin-unit@pulse.local", "admin_unit")


@pytest_asyncio.fixture
async def manajer_user(db_session):
    return await _user_with_role(db_session, "manajer@pulse.local", "manajer_unit")


@pytest_asyncio.fixture
async def super_admin_user(db_session):
    return await _user_with_role(db_session, "super@pulse.local", "super_admin")


async def _login_get_token(client, user) -> str:
    r = await client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": "pwd"}
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_pic_blocked_from_admin_endpoint(client, pic_user):
    token = await _login_get_token(client, pic_user)
    r = await client.get(
        "/__test/admin-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_unit_allowed_for_admin_endpoint(client, admin_unit_user):
    token = await _login_get_token(client, admin_unit_user)
    r = await client.get(
        "/__test/admin-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_super_admin_allowed_for_admin_endpoint(client, super_admin_user):
    token = await _login_get_token(client, super_admin_user)
    r = await client.get(
        "/__test/admin-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_pic_allowed_for_pic_endpoint(client, pic_user):
    token = await _login_get_token(client, pic_user)
    r = await client.get(
        "/__test/pic-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_manajer_blocked_from_pic_endpoint(client, manajer_user):
    token = await _login_get_token(client, manajer_user)
    r = await client.get(
        "/__test/pic-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(client):
    r = await client.get("/__test/admin-only")
    assert r.status_code == 401
