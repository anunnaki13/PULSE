from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.role import Role
from app.models.user import User


@pytest_asyncio.fixture
async def admin_user(db_session):
    role = await db_session.scalar(select(Role).where(Role.name == "super_admin"))
    assert role is not None
    user = User(
        email="audit-admin@pulse.local",
        full_name="Audit Admin",
        password_hash=hash_password("audit-secret"),
    )
    user.roles = [role]
    db_session.add(user)
    await db_session.flush()
    return user


async def _login(client, email: str, password: str = "audit-secret") -> tuple[str, str]:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"], response.cookies["csrf_token"]


@pytest.mark.asyncio
async def test_successful_login_creates_auth_audit_row(client, db_session, admin_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "audit-secret"},
    )
    assert response.status_code == 200

    rows = (
        await db_session.scalars(
            select(AuditLog).where(
                AuditLog.entity_type == "auth",
                AuditLog.entity_id == admin_user.id,
            )
        )
    ).all()
    assert rows
    assert rows[-1].after_data["event"] == "login.success"


@pytest.mark.asyncio
async def test_failed_login_is_audited_immediately(client, db_session, admin_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "wrong"},
    )
    assert response.status_code == 401

    row = await db_session.scalar(
        select(AuditLog)
        .where(AuditLog.entity_type == "auth", AuditLog.entity_id == admin_user.id)
        .order_by(AuditLog.created_at.desc())
    )
    assert row is not None
    assert row.after_data["event"] == "login.failure"
    assert row.after_data["reason"] == "bad_password"


@pytest.mark.asyncio
async def test_auth_refresh_is_not_captured(client, db_session, admin_user):
    _access, _csrf = await _login(client, admin_user.email)
    refresh = (await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "audit-secret"},
    )).json()["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200, response.text

    rows = (
        await db_session.scalars(
            select(AuditLog).where(AuditLog.action == "POST /api/v1/auth/refresh")
        )
    ).all()
    assert rows == []


def test_audit_middleware_does_not_read_response_body():
    source = open("app/services/audit_middleware.py", encoding="utf-8").read()
    assert "response.body" not in source
    assert "await response.body" not in source
    assert "CAPTURE_VERBS" in source
    assert "auth/refresh" in source
