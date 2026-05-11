"""REQ-user-roles seed + password-hash round-trip tests.

`test_six_phase1_roles_seeded` is the canonical assertion that the 0002
Alembic migration has run and seeded the SIX spec-named roles per B-01/B-02.
This test requires a live DB (uses `db_session`).

`test_password_hash_roundtrip` is host-only: it doesn't touch the DB and
runs under `wsl -d Ubuntu-22.04 -- python3.11 -m pytest backend/tests/test_user_roles.py -q`
even when no Postgres / Redis container is available.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.core.security import hash_password, verify_password
from app.models.role import Role

PHASE1_ROLES = {
    "super_admin",
    "admin_unit",
    "pic_bidang",
    "asesor",
    "manajer_unit",
    "viewer",
}


@pytest.mark.asyncio
async def test_six_phase1_roles_seeded(db_session):
    """Assert the 0002 migration seeded all six spec-named role rows (B-01/B-02)."""
    rows = (await db_session.scalars(select(Role.name))).all()
    names = set(rows)
    missing = PHASE1_ROLES - names
    assert not missing, f"missing seeded roles (B-01/B-02): {missing}"


def test_password_hash_roundtrip():
    """bcrypt hash + verify; runs without a DB (host-only)."""
    h = hash_password("hello-pulse-2026")
    assert h.startswith("$2"), "bcrypt PHC prefix expected"
    assert verify_password("hello-pulse-2026", h)
    assert not verify_password("wrong", h)


def test_password_hash_handles_long_password():
    """bcrypt has a 72-byte limit; security.hash_password truncates safely."""
    long_pw = "x" * 100
    h = hash_password(long_pw)
    assert verify_password(long_pw, h)
    # Same prefix (first 72 bytes) verifies; an unrelated 100-char input doesn't.
    assert not verify_password("y" * 100, h)
