"""Konkin template + perspektif + indikator + import-from-excel tests
(REQ-konkin-template-crud + B-07 CSRF contract + W-07 lock validator).

Coverage:

- admin_unit can create / clone / lock templates; pic_bidang / manajer_unit /
  viewer cannot mutate (403).
- W-07 lock validator: rejects when non-pengurang perspektif don't sum to
  100; PASSES when non-pengurang sum to 100 even if a pengurang perspektif
  (VI) has bobot=0.
- Mutation against a locked template returns 409.
- Excel import: 201 on first send, 200 + ``already_applied`` on second send
  with same Idempotency-Key (works even with a near-empty workbook).
- B-07 contract: a cookie-mode call WITHOUT the X-CSRF-Token header returns
  403. A Bearer-mode call (no cookies, no header) is allowed by
  require_csrf's standard rule.

These tests require live Postgres + Redis.
"""

from __future__ import annotations

import io
from decimal import Decimal

import openpyxl
import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.security import hash_password
from app.models.indikator import Indikator
from app.models.konkin_template import KonkinTemplate
from app.models.perspektif import Perspektif
from app.models.role import Role
from app.models.user import User


XLSX_CT = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


def _build_xlsx_bytes(rows: int = 3) -> bytes:
    """Create a minimal in-memory .xlsx with `rows` content rows on one
    sheet. Returned as raw bytes so it can be sent through the test client
    via httpx multipart.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Perspektif"
    ws.append(["kode", "nama", "bobot"])
    for i in range(rows):
        ws.append([f"I-{i}", f"Row {i}", 0.0])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


async def _user_with_role(
    db_session, email: str, role_name: str
) -> User:
    role = await db_session.scalar(
        select(Role).where(Role.name == role_name)
    )
    assert role is not None
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
async def admin_unit_user(db_session):
    return await _user_with_role(
        db_session, "admin-unit-konkin@pulse.local", "admin_unit"
    )


@pytest_asyncio.fixture
async def pic_user(db_session):
    return await _user_with_role(
        db_session, "pic-konkin@pulse.local", "pic_bidang"
    )


@pytest_asyncio.fixture
async def manajer_user(db_session):
    return await _user_with_role(
        db_session, "manajer-konkin@pulse.local", "manajer_unit"
    )


@pytest_asyncio.fixture
async def viewer_user(db_session):
    return await _user_with_role(
        db_session, "viewer-konkin@pulse.local", "viewer"
    )


async def _login_and_csrf(client, user) -> tuple[str, dict, str]:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "pwd"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    csrf = r.cookies.get("csrf_token") or ""
    return (
        token,
        {"Authorization": f"Bearer {token}", "X-CSRF-Token": csrf},
        csrf,
    )


# ---------------------------------------------------------------------------
# CRUD + RBAC
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_creates_template(client, admin_unit_user):
    _t, h, _ = await _login_and_csrf(client, admin_unit_user)
    r = await client.post(
        "/api/v1/konkin/templates",
        headers=h,
        json={"tahun": 2026, "nama": "Konkin 2026 PLTU Tenayan"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["tahun"] == 2026
    assert body["locked"] is False


@pytest.mark.asyncio
async def test_pic_cannot_create_template(client, pic_user):
    _t, h, _ = await _login_and_csrf(client, pic_user)
    r = await client.post(
        "/api/v1/konkin/templates",
        headers=h,
        json={"tahun": 2026, "nama": "X"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_manajer_cannot_create_template(client, manajer_user):
    _t, h, _ = await _login_and_csrf(client, manajer_user)
    r = await client.post(
        "/api/v1/konkin/templates",
        headers=h,
        json={"tahun": 2026, "nama": "X"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_viewer_cannot_create_template(client, viewer_user):
    _t, h, _ = await _login_and_csrf(client, viewer_user)
    r = await client.post(
        "/api/v1/konkin/templates",
        headers=h,
        json={"tahun": 2026, "nama": "X"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_clone_from_id_deep_copies_chain(
    client, admin_unit_user, db_session
):
    _t, h, _ = await _login_and_csrf(client, admin_unit_user)
    # Source template + 1 perspektif + 1 indikator
    src = KonkinTemplate(tahun=2024, nama="Konkin 2024 Source")
    db_session.add(src)
    await db_session.flush()
    sp = Perspektif(
        template_id=src.id,
        kode="I",
        nama="Source Perspektif",
        bobot=Decimal("100"),
        is_pengurang=False,
    )
    db_session.add(sp)
    await db_session.flush()
    si = Indikator(
        perspektif_id=sp.id,
        kode="K1",
        nama="Source Indikator",
        bobot=Decimal("100"),
        polaritas="positif",
    )
    db_session.add(si)
    await db_session.flush()
    await db_session.commit()

    r = await client.post(
        "/api/v1/konkin/templates",
        headers=h,
        json={
            "tahun": 2027,
            "nama": "Konkin 2027 Clone",
            "clone_from_id": str(src.id),
        },
    )
    assert r.status_code == 201, r.text
    cloned_id = r.json()["id"]
    # Confirm the clone has its own perspektif row with the same kode
    plist = await client.get(
        f"/api/v1/konkin/templates/{cloned_id}/perspektif", headers=h
    )
    assert plist.status_code == 200
    kodes = [p["kode"] for p in plist.json()["data"]]
    assert "I" in kodes


# ---------------------------------------------------------------------------
# W-07 lock validator (pengurang exclusion)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lock_fails_when_non_pengurang_sum_off(
    client, admin_unit_user, db_session
):
    _t, h, _ = await _login_and_csrf(client, admin_unit_user)
    tpl = KonkinTemplate(tahun=2030, nama="Bad Sum")
    db_session.add(tpl)
    await db_session.flush()
    # Two non-pengurang perspektif summing to 90 (off by 10).
    db_session.add(
        Perspektif(
            template_id=tpl.id,
            kode="I",
            nama="A",
            bobot=Decimal("50.00"),
            is_pengurang=False,
        )
    )
    db_session.add(
        Perspektif(
            template_id=tpl.id,
            kode="II",
            nama="B",
            bobot=Decimal("40.00"),
            is_pengurang=False,
        )
    )
    await db_session.commit()

    r = await client.post(
        f"/api/v1/konkin/templates/{tpl.id}/lock", headers=h
    )
    assert r.status_code == 422, r.text
    detail = r.json()["detail"]
    assert detail["error"] == "bobot_perspektif_invalid"
    assert detail["actual"] == "90.00"


@pytest.mark.asyncio
async def test_lock_validator_excludes_pengurang(
    client, admin_unit_user, db_session
):
    """W-07: five non-pengurang perspektif summing to 100 + one pengurang
    (VI) at bobot=0 must lock successfully (the pengurang row is
    excluded from the sum check)."""
    _t, h, _ = await _login_and_csrf(client, admin_unit_user)
    tpl = KonkinTemplate(tahun=2026, nama="Konkin 2026 Lock OK")
    db_session.add(tpl)
    await db_session.flush()

    bobots = [
        ("I", Decimal("46.00")),
        ("II", Decimal("25.00")),
        ("III", Decimal("6.00")),
        ("IV", Decimal("8.00")),
        ("V", Decimal("15.00")),
    ]
    for kode, b in bobots:
        sp = Perspektif(
            template_id=tpl.id,
            kode=kode,
            nama=kode,
            bobot=b,
            is_pengurang=False,
        )
        db_session.add(sp)
        await db_session.flush()
        # one indikator per perspektif with bobot=100 so the inner sum
        # check passes too.
        db_session.add(
            Indikator(
                perspektif_id=sp.id,
                kode=f"{kode}-K1",
                nama="Single",
                bobot=Decimal("100.00"),
                polaritas="positif",
            )
        )

    # Perspektif VI: pengurang, bobot=0, pengurang_cap=10.
    db_session.add(
        Perspektif(
            template_id=tpl.id,
            kode="VI",
            nama="Compliance",
            bobot=Decimal("0.00"),
            is_pengurang=True,
            pengurang_cap=Decimal("10.00"),
        )
    )
    await db_session.commit()

    r = await client.post(
        f"/api/v1/konkin/templates/{tpl.id}/lock", headers=h
    )
    assert r.status_code == 200, r.text
    assert r.json()["locked"] is True


@pytest.mark.asyncio
async def test_mutation_against_locked_template_409(
    client, admin_unit_user, db_session
):
    _t, h, _ = await _login_and_csrf(client, admin_unit_user)
    tpl = KonkinTemplate(tahun=2026, nama="Locked Already", locked=True)
    db_session.add(tpl)
    await db_session.commit()

    r = await client.patch(
        f"/api/v1/konkin/templates/{tpl.id}",
        headers=h,
        json={"nama": "Try Edit"},
    )
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# B-07: Excel import is admin-only AND CSRF-protected
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_excel_import_idempotent(
    client, admin_unit_user, db_session
):
    _t, h, _ = await _login_and_csrf(client, admin_unit_user)
    tpl = KonkinTemplate(tahun=2026, nama="Import Target")
    db_session.add(tpl)
    await db_session.commit()

    xlsx = _build_xlsx_bytes()
    files = {"file": ("template.xlsx", xlsx, XLSX_CT)}

    first = await client.post(
        f"/api/v1/konkin/templates/{tpl.id}/import-from-excel",
        headers={**h, "Idempotency-Key": "abc-123"},
        files=files,
    )
    assert first.status_code == 201, first.text
    assert first.json()["data"]["status"] == "imported"

    # Same key — must short-circuit to 200 + already_applied
    second = await client.post(
        f"/api/v1/konkin/templates/{tpl.id}/import-from-excel",
        headers={**h, "Idempotency-Key": "abc-123"},
        files={"file": ("template.xlsx", _build_xlsx_bytes(), XLSX_CT)},
    )
    assert second.status_code == 200, second.text
    assert second.json()["data"]["status"] == "already_applied"


@pytest.mark.asyncio
async def test_excel_import_rejects_no_csrf_cookie_mode(
    client, admin_unit_user, db_session
):
    """B-07: a cookie-mode request (no Authorization header, no
    X-CSRF-Token header) must be rejected with 403 even though the user
    is admin_unit. Cookies from login are sent automatically by httpx."""
    # Log in but DO NOT use the Bearer token — strip it so the path runs
    # cookie-mode only. The csrf_token cookie is set by /auth/login.
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_unit_user.email, "password": "pwd"},
    )
    assert login.status_code == 200, login.text
    # cookies live on `client.cookies` by default.

    tpl = KonkinTemplate(tahun=2026, nama="CSRF Target")
    db_session.add(tpl)
    await db_session.commit()

    files = {"file": ("template.xlsx", _build_xlsx_bytes(), XLSX_CT)}

    # No Authorization, no X-CSRF-Token → cookie-mode + missing CSRF.
    r = await client.post(
        f"/api/v1/konkin/templates/{tpl.id}/import-from-excel",
        files=files,
    )
    assert r.status_code == 403, r.text
