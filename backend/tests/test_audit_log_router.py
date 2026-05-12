from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.role import Role
from app.models.user import User
from app.routers.audit_log import router


@pytest_asyncio.fixture
async def super_admin_user(db_session):
    role = await db_session.scalar(select(Role).where(Role.name == "super_admin"))
    assert role is not None
    user = User(
        email="audit-reader@pulse.local",
        full_name="Audit Reader",
        password_hash=hash_password("reader-secret"),
    )
    user.roles = [role]
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def admin_unit_user(db_session):
    role = await db_session.scalar(select(Role).where(Role.name == "admin_unit"))
    assert role is not None
    user = User(
        email="audit-denied@pulse.local",
        full_name="Audit Denied",
        password_hash=hash_password("reader-secret"),
    )
    user.roles = [role]
    db_session.add(user)
    await db_session.flush()
    return user


async def _token(client, user: User) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "reader-secret"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_audit_logs_requires_super_admin(client, admin_unit_user):
    token = await _token(client, admin_unit_user)
    response = await client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_audit_logs_super_admin_can_filter(client, db_session, super_admin_user):
    db_session.add(
        AuditLog(
            user_id=super_admin_user.id,
            action="PATCH /api/v1/assessment/sessions/{session_id}/self-assessment",
            entity_type="assessment_session",
            entity_id=None,
            before_data={"state": "draft"},
            after_data={"state": "submitted"},
        )
    )
    await db_session.flush()
    token = await _token(client, super_admin_user)
    response = await client.get(
        "/api/v1/audit-logs?entity_type=assessment_session",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"]
    assert all(row["entity_type"] == "assessment_session" for row in response.json()["data"])


def test_audit_log_router_is_append_only():
    methods = {method for route in router.routes for method in (route.methods or set())}
    assert methods <= {"GET", "HEAD"}
    assert not any(getattr(route, "path", "").startswith("/{") for route in router.routes)


@pytest.mark.asyncio
async def test_audit_logs_page_size_is_capped(client, super_admin_user):
    token = await _token(client, super_admin_user)
    response = await client.get(
        "/api/v1/audit-logs?page_size=10000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
