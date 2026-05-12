"""Seed idempotency proof (B-06 fix).

Three tests:

1. ``test_seed_runs_idempotently`` — Run ``run_seed()`` twice and assert the
   row counts of bidang / users / templates / perspektif / ml_stream do not
   change between runs.

2. ``test_admin_user_has_admin_unit_role`` — The first admin's role join
   must produce exactly the spec name ``"admin_unit"`` (CONTEXT.md Auth).

3. ``test_perspektif_VI_is_pengurang`` — Perspektif VI must carry
   ``is_pengurang=True``, ``bobot=Decimal("0.00")``, and
   ``pengurang_cap=Decimal("10.00")`` (W-07).

All tests use the host-side conftest fixtures (``db_session`` is wired to
an ephemeral pg test container; see Plan 05 SUMMARY for the pattern).
Collection-only (no DB) is fine — the imports below resolve without a live
Postgres.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models.bidang import Bidang
from app.models.indikator_applicable_bidang import IndikatorApplicableBidang
from app.models.konkin_template import KonkinTemplate
from app.models.ml_stream import MlStream
from app.models.perspektif import Perspektif
from app.models.user import User


@pytest.mark.asyncio
async def test_seed_runs_idempotently(db_session):
    """Re-running the seed must NOT create duplicates."""
    from app.seed import run_seed

    # First run — populates everything.
    await run_seed()

    async def _counts():
        return {
            "bidang": await db_session.scalar(select(func.count()).select_from(Bidang)),
            "users": await db_session.scalar(select(func.count()).select_from(User)),
            "templates": await db_session.scalar(
                select(func.count()).select_from(KonkinTemplate)
            ),
            "perspektif": await db_session.scalar(
                select(func.count()).select_from(Perspektif)
            ),
            "ml_stream": await db_session.scalar(select(func.count()).select_from(MlStream)),
            "indikator_applicable_bidang": await db_session.scalar(
                select(func.count()).select_from(IndikatorApplicableBidang)
            ),
        }

    counts1 = await _counts()
    # Second run — every guard must fire and no rows are added.
    await run_seed()
    counts2 = await _counts()

    assert counts1 == counts2, f"non-idempotent: first={counts1} second={counts2}"

    # Sanity: the first run actually populated rows (otherwise the equality
    # above is vacuous).
    assert counts1["bidang"] >= 20, f"expected ≥20 bidang rows, got {counts1['bidang']}"
    assert counts1["templates"] >= 1
    assert counts1["perspektif"] >= 6
    assert counts1["ml_stream"] >= 18
    assert counts1["indikator_applicable_bidang"] >= 30
    assert counts1["users"] >= 1


@pytest.mark.asyncio
async def test_phase6_remaining_stream_blueprints_seeded(db_session):
    from app.seed import run_seed
    from app.seed.stream_coverage import REMAINING_STREAMS

    await run_seed()

    rows = (
        await db_session.execute(
            select(MlStream.kode, MlStream.structure).where(
                MlStream.kode.in_([stream["kode"] for stream in REMAINING_STREAMS])
            )
        )
    ).all()
    by_kode = {kode: structure for kode, structure in rows}

    assert set(by_kode) == {stream["kode"] for stream in REMAINING_STREAMS}
    assert all((structure.get("areas") or []) for structure in by_kode.values())
    assert all(structure.get("placeholder") is True for structure in by_kode.values())


@pytest.mark.asyncio
async def test_phase6_hcr_ocr_blueprints_seeded(db_session):
    from app.seed import run_seed

    await run_seed()

    rows = (
        await db_session.execute(
            select(MlStream.kode, MlStream.structure).where(MlStream.kode.in_(["HCR", "OCR"]))
        )
    ).all()
    by_kode = {kode: structure for kode, structure in rows}

    assert set(by_kode) == {"HCR", "OCR"}
    assert len(by_kode["HCR"]["areas"]) == 7
    owm = next(area for area in by_kode["OCR"]["areas"] if area["kode"] == "OCR-OWM")
    assert [sub["weight"] for sub in owm["sub_areas"]] == [0.55, 0.45]


@pytest.mark.asyncio
async def test_admin_user_has_admin_unit_role(db_session):
    """First admin's role join must be the spec name 'admin_unit'."""
    from app.core.config import settings
    from app.seed import run_seed

    await run_seed()

    user = await db_session.scalar(
        select(User).where(User.email == settings.INITIAL_ADMIN_EMAIL.lower())
    )
    assert user is not None, f"admin user '{settings.INITIAL_ADMIN_EMAIL}' was not created"

    role_names = {r.name for r in (user.roles or [])}
    assert (
        "admin_unit" in role_names
    ), f"expected admin_unit role on first admin, got {role_names}"


@pytest.mark.asyncio
async def test_perspektif_VI_is_pengurang(db_session):
    """Perspektif VI must be is_pengurang=True with bobot=0 and pengurang_cap=10 (W-07)."""
    from app.seed import run_seed

    await run_seed()

    v6 = await db_session.scalar(select(Perspektif).where(Perspektif.kode == "VI"))
    assert v6 is not None, "Perspektif VI must be seeded for Konkin 2026 (W-07)"
    assert v6.is_pengurang is True, f"VI must be is_pengurang=True, got {v6.is_pengurang}"
    assert v6.bobot == Decimal("0.00"), f"VI bobot must be 0.00, got {v6.bobot}"
    assert v6.pengurang_cap == Decimal(
        "10.00"
    ), f"VI pengurang_cap must be 10.00, got {v6.pengurang_cap}"
