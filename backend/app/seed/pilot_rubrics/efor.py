"""EFOR (Equivalent Forced Outage Rate) pilot stub (REQ-dynamic-ml-schema).

EFOR is a KPI Kuantitatif (polaritas negatif per 01_DOMAIN_MODEL.md §3.1
formula `{2 − (Realisasi / Target)} × 100%`) — Phase 1 ships a header-only
MlStream stub with an empty areas list. Phase 2 will replace this with the
proper KPI form schema once the assessment workflow lands.

Idempotency: existence check on MlStream.kode == "EFOR".
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ml_stream import MlStream

KODE = "EFOR"
NAMA = "Equivalent Forced Outage Rate"
VERSION = "2026.1"

STRUCTURE: dict = {"areas": [], "kpi_form": {"phase": 2, "note": "deferred to Phase 2"}}


async def seed(db: AsyncSession) -> None:
    existing = await db.scalar(select(MlStream).where(MlStream.kode == KODE))
    if existing is not None:
        print(f"[seed] ml_stream {KODE}: already exists (id={existing.id})")
        return
    db.add(MlStream(kode=KODE, nama=NAMA, version=VERSION, structure=STRUCTURE))
    await db.flush()
    print(f"[seed] ml_stream {KODE}: created (header-only, Phase-2 will add KPI form)")
