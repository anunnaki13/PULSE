from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.security import hash_password
from app.models.notification import Notification, NotificationType
from app.models.role import Role
from app.models.user import User
from app.services import notification_dispatcher


@pytest_asyncio.fixture
async def notify_user(db_session):
    role = await db_session.scalar(select(Role).where(Role.name == "viewer"))
    assert role is not None
    user = User(
        email="notify-viewer@pulse.local",
        full_name="Notify Viewer",
        password_hash=hash_password("notify-secret"),
    )
    user.roles = [role]
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_dispatch_creates_one_row_per_call(db_session, notify_user, monkeypatch):
    calls: list[tuple[str, dict]] = []

    async def fake_send(user_id: str, payload: dict) -> int:
        calls.append((user_id, payload))
        return 1

    monkeypatch.setattr(notification_dispatcher.ws_manager, "send_to_user", fake_send)
    await notification_dispatcher.dispatch(
        db_session,
        user_id=notify_user.id,
        type_=NotificationType.ASSESSMENT_DUE,
        title="A",
        body="B",
    )
    await notification_dispatcher.dispatch(
        db_session,
        user_id=notify_user.id,
        type_=NotificationType.ASSESSMENT_DUE,
        title="A2",
        body="B2",
    )

    rows = (
        await db_session.scalars(
            select(Notification).where(Notification.user_id == notify_user.id)
        )
    ).all()
    assert len(rows) == 2
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_system_announcement_is_in_app_only(db_session, notify_user, monkeypatch):
    calls: list[dict] = []

    async def fake_send(user_id: str, payload: dict) -> int:
        calls.append(payload)
        return 1

    monkeypatch.setattr(notification_dispatcher.ws_manager, "send_to_user", fake_send)
    await notification_dispatcher.dispatch(
        db_session,
        user_id=notify_user.id,
        type_=NotificationType.SYSTEM_ANNOUNCEMENT,
        title="System",
        body="No WS",
    )
    assert calls == []
    assert NotificationType.SYSTEM_ANNOUNCEMENT not in notification_dispatcher.WS_ENABLED_TYPES


@pytest.mark.asyncio
async def test_notifications_router_lists_unread_first(client, db_session, notify_user):
    await notification_dispatcher.dispatch(
        db_session,
        user_id=notify_user.id,
        type_=NotificationType.SYSTEM_ANNOUNCEMENT,
        title="Read",
        body="old",
    )
    unread = await notification_dispatcher.dispatch(
        db_session,
        user_id=notify_user.id,
        type_=NotificationType.SYSTEM_ANNOUNCEMENT,
        title="Unread",
        body="new",
    )
    first = await db_session.scalar(
        select(Notification).where(Notification.user_id == notify_user.id, Notification.title == "Read")
    )
    assert first is not None
    first.read_at = unread.created_at
    await db_session.flush()

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": notify_user.email, "password": "notify-secret"},
    )
    token = login.json()["access_token"]
    response = await client.get(
        "/api/v1/notifications",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"][0]["title"] == "Unread"
