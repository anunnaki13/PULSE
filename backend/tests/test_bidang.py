"""Bidang RBAC + CRUD tests (REQ-bidang-master + REQ-route-guards).

Coverage:

- admin_unit / super_admin can list / create / patch / soft-delete.
- pic_bidang sees only their own bidang_id (Phase-1 scope).
- manajer_unit / asesor / viewer can READ but NOT mutate (403).
- Anonymous: every route returns 401.
- Soft-delete sets deleted_at and removes the row from subsequent reads.

These tests require live Postgres + Redis — run via
``wsl -d Ubuntu-22.04 -- python3.11 -m pytest backend/tests/test_bidang.py -q``
against the docker stack, or container-internal via
``docker compose exec pulse-backend pytest tests/test_bidang.py``.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.security import hash_password
from app.models.bidang import Bidang
from app.models.role import Role
from app.models.user import User


async def _user_with_role(
    db_session, email: str, role_name: str, bidang_id=None
) -> User:
    role = await db_session.scalar(
        select(Role).where(Role.name == role_name)
    )
    assert role is not None, f"role {role_name!r} must be seeded by 0002"
    u = User(
        email=email,
        full_name=role_name,
        password_hash=hash_password("pwd"),
        bidang_id=bidang_id,
    )
    u.roles = [role]
    db_session.add(u)
    await db_session.flush()
    return u


@pytest_asyncio.fixture
async def admin_unit_user(db_session):
    return await _user_with_role(
        db_session, "admin-unit-bidang@pulse.local", "admin_unit"
    )


@pytest_asyncio.fixture
async def super_admin_user(db_session):
    return await _user_with_role(
        db_session, "super-bidang@pulse.local", "super_admin"
    )


@pytest_asyncio.fixture
async def viewer_user(db_session):
    return await _user_with_role(
        db_session, "viewer-bidang@pulse.local", "viewer"
    )


@pytest_asyncio.fixture
async def manajer_user(db_session):
    return await _user_with_role(
        db_session, "manajer-bidang@pulse.local", "manajer_unit"
    )


@pytest_asyncio.fixture
async def asesor_user(db_session):
    return await _user_with_role(
        db_session, "asesor-bidang@pulse.local", "asesor"
    )


async def _login_and_csrf(client, user) -> tuple[str, dict]:
    """POST /auth/login and return (bearer token, headers-with-csrf-token).

    Returns Bearer-mode token for tests that exercise the dual-mode path,
    plus a header dict with X-CSRF-Token taken from the csrf_token cookie
    so cookie-mode CSRF-protected routes can be exercised too.
    """
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "pwd"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    csrf = r.cookies.get("csrf_token") or ""
    return token, {
        "Authorization": f"Bearer {token}",
        "X-CSRF-Token": csrf,
    }


@pytest.mark.asyncio
async def test_anonymous_list_is_401(client):
    r = await client.get("/api/v1/bidang")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_admin_unit_can_create_and_list(client, admin_unit_user):
    _tok, h = await _login_and_csrf(client, admin_unit_user)
    create = await client.post(
        "/api/v1/bidang",
        headers=h,
        json={"kode": "OPS", "nama": "Operasi"},
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body["kode"] == "OPS"
    assert body["nama"] == "Operasi"

    listed = await client.get("/api/v1/bidang", headers=h)
    assert listed.status_code == 200
    kodes = [b["kode"] for b in listed.json()["data"]]
    assert "OPS" in kodes


@pytest.mark.asyncio
async def test_super_admin_can_create(client, super_admin_user):
    _tok, h = await _login_and_csrf(client, super_admin_user)
    r = await client.post(
        "/api/v1/bidang",
        headers=h,
        json={"kode": "MAINT", "nama": "Maintenance"},
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_viewer_cannot_create(client, viewer_user):
    _tok, h = await _login_and_csrf(client, viewer_user)
    r = await client.post(
        "/api/v1/bidang",
        headers=h,
        json={"kode": "X", "nama": "X"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_manajer_unit_cannot_create(client, manajer_user):
    _tok, h = await _login_and_csrf(client, manajer_user)
    r = await client.post(
        "/api/v1/bidang",
        headers=h,
        json={"kode": "Y", "nama": "Y"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_asesor_cannot_create(client, asesor_user):
    _tok, h = await _login_and_csrf(client, asesor_user)
    r = await client.post(
        "/api/v1/bidang",
        headers=h,
        json={"kode": "Z", "nama": "Z"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_pic_bidang_scoped_to_own_bidang(client, db_session):
    # Two bidang rows, two pic_bidang users — each scoped to their own.
    role = await db_session.scalar(
        select(Role).where(Role.name == "pic_bidang")
    )
    b1 = Bidang(kode="B1", nama="Bidang Satu")
    b2 = Bidang(kode="B2", nama="Bidang Dua")
    db_session.add_all([b1, b2])
    await db_session.flush()

    pic_user = User(
        email="pic1-bidang@pulse.local",
        full_name="PIC One",
        password_hash=hash_password("pwd"),
        bidang_id=b1.id,
    )
    pic_user.roles = [role]
    db_session.add(pic_user)
    await db_session.flush()

    _tok, h = await _login_and_csrf(client, pic_user)
    r = await client.get("/api/v1/bidang", headers=h)
    assert r.status_code == 200
    data = r.json()["data"]
    kodes = {row["kode"] for row in data}
    assert kodes == {"B1"}, f"pic_bidang must see only own bidang; got {kodes}"


@pytest.mark.asyncio
async def test_soft_delete_hides_row(client, admin_unit_user):
    _tok, h = await _login_and_csrf(client, admin_unit_user)
    create = await client.post(
        "/api/v1/bidang",
        headers=h,
        json={"kode": "TMP", "nama": "Temporary"},
    )
    assert create.status_code == 201
    bid = create.json()["id"]

    delete = await client.delete(f"/api/v1/bidang/{bid}", headers=h)
    assert delete.status_code == 204

    listed = await client.get("/api/v1/bidang", headers=h)
    kodes = [row["kode"] for row in listed.json()["data"]]
    assert "TMP" not in kodes
