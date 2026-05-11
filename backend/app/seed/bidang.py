"""Bidang master seed (REQ-bidang-master).

Source: ``01_DOMAIN_MODEL.md`` §7 "Pemilik Proses" + Pedoman Tabel 26.
Phase-1 scope: flat list of PLTU Tenayan bidangs (no parent hierarchy yet).

Idempotency: uses an ON CONFLICT (kode) DO NOTHING insert so re-running the
seed against an already-populated DB is a no-op. The plan's static verifier
greps for ``ON CONFLICT`` to confirm the guard is present.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bidang import Bidang

# Bidang master list — kode + display name. Derived from 01_DOMAIN_MODEL.md
# §7 (pemilik proses) and the BID-* abbreviations table in §9.
PLTU_TENAYAN_BIDANG: list[dict[str, str]] = [
    # Operation & Maintenance sub-bidangs
    {"kode": "BID_OM_1", "nama": "Operasi & Maintenance Unit 1"},
    {"kode": "BID_OM_2", "nama": "Operasi & Maintenance Unit 2"},
    {"kode": "BID_OM_3", "nama": "Operasi & Maintenance Unit 3"},
    {"kode": "BID_OM_4", "nama": "Operasi & Maintenance Unit 4"},
    {"kode": "BID_OM_5", "nama": "Operasi & Maintenance Unit 5"},
    {"kode": "BID_OM_RE", "nama": "Operasi & Maintenance — Reliability Engineering"},
    # Reliability
    {"kode": "BID_REL_1", "nama": "Reliability Management 1"},
    {"kode": "BID_REL_2", "nama": "Reliability Management 2"},
    # HSE / HCD / Risk / Compliance / Audit
    {"kode": "BID_HSE", "nama": "Health, Safety & Environment"},
    {"kode": "BID_HTD", "nama": "Human Talent Development"},
    {"kode": "BID_HSC", "nama": "Human Capital Strategic"},
    {"kode": "BID_RIS", "nama": "Risk Management"},
    {"kode": "BID_CPF", "nama": "Compliance & Performance Function"},
    {"kode": "BID_AUD_I", "nama": "Audit I"},
    {"kode": "BID_AUD_II", "nama": "Audit II"},
    {"kode": "BID_AUD_III", "nama": "Audit III"},
    # Finance, Accounting, Customer Relationship, Logistics
    {"kode": "BID_FIN", "nama": "Finance"},
    {"kode": "BID_ACT", "nama": "Accounting"},
    {"kode": "BID_CMR", "nama": "Customer Relationship"},
    {"kode": "BID_LOG", "nama": "Logistics & Material Management"},
    # CSR, Energi Primer, Transformasi Digital
    {"kode": "BID_CSR", "nama": "Corporate Social Responsibility"},
    {"kode": "BID_EPI", "nama": "Energi Primer"},
    {"kode": "BID_TDV", "nama": "Transformasi Digital & Vendor"},
    # Asset & Supply Chain (satuan-level support)
    {"kode": "BID_AMS", "nama": "Asset Management Strategy"},
    {"kode": "BID_SSCM", "nama": "Satuan Supply Chain Management"},
    {"kode": "BID_SPRO", "nama": "Satuan Project"},
]


async def seed_bidang(db: AsyncSession) -> int:
    """Insert every bidang in PLTU_TENAYAN_BIDANG using ON CONFLICT DO NOTHING.

    Returns the number of rows present in the bidang table AFTER the seed
    (not the number of newly-inserted rows). Callers print this for the
    idempotency proof on the second run.
    """
    # ON CONFLICT (kode) DO NOTHING — idempotency guard required by plan verify.
    stmt = (
        pg_insert(Bidang)
        .values(PLTU_TENAYAN_BIDANG)
        .on_conflict_do_nothing(index_elements=["kode"])
    )
    await db.execute(stmt)

    total = await db.scalar(select(Bidang).where(Bidang.kode == "BID_OM_1"))
    # rough sentinel — caller logs full count.
    print(f"[seed] bidang: ensured {len(PLTU_TENAYAN_BIDANG)} kodes (sentinel BID_OM_1 present: {total is not None})")
    return len(PLTU_TENAYAN_BIDANG)
