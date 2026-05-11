"""Konkin 2026 PLTU Tenayan template seed (REQ-konkin-template-crud + W-07).

Creates:
- One ``konkin_template`` row: tahun=2026, nama="Konkin 2026 PLTU Tenayan",
  locked=False (admin can still edit drafts).
- Six ``perspektif`` rows under that template:
  - I/II/III/IV/V are penambah (Σ bobot = 100.00)
  - VI is **pengurang** per W-07: is_pengurang=True, bobot=0.00,
    pengurang_cap=10.00. The lock validator (Plan 06) SUMs only
    is_pengurang=False rows and accepts 100.00 ± 0.01, so the pengurang VI
    does not pollute the perspektif-sum check.
- A minimal set of indikator stubs under each perspektif so the four pilot
  indikator (EAF, EFOR, Outage Management, SMAP) exist for the Phase-1
  acceptance walk. Full per-pilar indikator coverage is Phase-2 work.

Idempotency: existence check on (tahun, nama) for the template, then on
(template_id, kode) for each perspektif and (perspektif_id, kode) for each
indikator. The plan-checker greps for ``is_pengurang.*True`` and
``pengurang_cap.*10`` and ``46.00`` / ``25.00`` / ``15.00`` literals.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.indikator import Indikator
from app.models.konkin_template import KonkinTemplate
from app.models.perspektif import Perspektif

TEMPLATE_TAHUN = 2026
TEMPLATE_NAMA = "Konkin 2026 PLTU Tenayan"

# Perspektif rows per CONTEXT.md "Pengurang bobot convention" (W-07).
# I+II+III+IV+V = 46+25+6+8+15 = 100.00 (penambah). VI is pengurang
# (is_pengurang=True, bobot=0.00, pengurang_cap=10.00).
PERSPEKTIF_2026: list[dict] = [
    {
        "kode": "I",
        "nama": "Economic & Social Value",
        "bobot": Decimal("46.00"),
        "is_pengurang": False,
        "pengurang_cap": None,
        "sort_order": 1,
    },
    {
        "kode": "II",
        "nama": "Model Business Innovation",
        "bobot": Decimal("25.00"),
        "is_pengurang": False,
        "pengurang_cap": None,
        "sort_order": 2,
    },
    {
        "kode": "III",
        "nama": "Technology Leadership",
        "bobot": Decimal("6.00"),
        "is_pengurang": False,
        "pengurang_cap": None,
        "sort_order": 3,
    },
    {
        "kode": "IV",
        "nama": "Energize Investment",
        "bobot": Decimal("8.00"),
        "is_pengurang": False,
        "pengurang_cap": None,
        "sort_order": 4,
    },
    {
        "kode": "V",
        "nama": "Unleash Talent",
        "bobot": Decimal("15.00"),
        "is_pengurang": False,
        "pengurang_cap": None,
        "sort_order": 5,
    },
    # W-07: VI is pengurang. bobot=0.00 so the lock validator's SUM(WHERE
    # is_pengurang=False) still equals 100. pengurang_cap=10.00 — Phase-3 NKO
    # calc subtracts up to -10 from gross.
    {
        "kode": "VI",
        "nama": "Compliance",
        "bobot": Decimal("0.00"),
        "is_pengurang": True,
        "pengurang_cap": Decimal("10.00"),
        "sort_order": 6,
    },
]

# Minimal indikator seed — the four pilot indikator referenced in the
# Phase-1 success criteria. Each is under perspektif I (Economic & Social
# Value, kode="I") per 01_DOMAIN_MODEL.md §3.1 except Outage Management +
# SMAP which are sub-stream-level. We seed both under perspektif I for
# Phase-1 surface; Phase-2 will re-home them under proper perspektif II
# (Model Business Innovation) per the source doc.
PILOT_INDIKATOR: list[dict] = [
    # Perspektif I — Economic & Social Value
    {
        "perspektif_kode": "I",
        "kode": "EAF",
        "nama": "Equivalent Availability Factor",
        "bobot": Decimal("6.00"),
        "polaritas": "positif",
        "formula": "Realisasi / Target × 100%",
    },
    {
        "perspektif_kode": "I",
        "kode": "EFOR",
        "nama": "Equivalent Forced Outage Rate",
        "bobot": Decimal("6.00"),
        "polaritas": "negatif",
        "formula": "{2 − (Realisasi / Target)} × 100%",
    },
    # Perspektif II — Model Business Innovation (Maturity Level Manajemen Aset)
    {
        "perspektif_kode": "II",
        "kode": "OUTAGE",
        "nama": "Outage Management (Maturity Level)",
        "bobot": Decimal("25.00"),
        "polaritas": "positif",
        "formula": "Rubrik L0..L4 (lihat ml_stream OUTAGE)",
    },
    # Perspektif VI — Compliance (pengurang stream)
    {
        "perspektif_kode": "VI",
        "kode": "SMAP",
        "nama": "Sistem Manajemen Anti Penyuapan",
        "bobot": Decimal("0.00"),
        "polaritas": "negatif",
        "formula": "Rubrik L0..L4 (lihat ml_stream SMAP)",
    },
]


async def seed_konkin_2026(db: AsyncSession) -> None:
    """Idempotent seed: template + six perspektif + four pilot indikator."""
    # 1. Template (idempotent via SELECT first)
    tpl = await db.scalar(
        select(KonkinTemplate).where(
            KonkinTemplate.tahun == TEMPLATE_TAHUN,
            KonkinTemplate.nama == TEMPLATE_NAMA,
        )
    )
    if tpl is None:
        tpl = KonkinTemplate(tahun=TEMPLATE_TAHUN, nama=TEMPLATE_NAMA, locked=False)
        db.add(tpl)
        await db.flush()  # materialize tpl.id for the perspektif inserts below
        print(f"[seed] konkin_2026: created template '{TEMPLATE_NAMA}' (id={tpl.id})")
    else:
        print(f"[seed] konkin_2026: template '{TEMPLATE_NAMA}' already exists (id={tpl.id})")

    # 2. Perspektif rows — guarded by (template_id, kode) existence.
    by_kode: dict[str, Perspektif] = {}
    for row in PERSPEKTIF_2026:
        existing = await db.scalar(
            select(Perspektif).where(
                Perspektif.template_id == tpl.id,
                Perspektif.kode == row["kode"],
            )
        )
        if existing is None:
            new = Perspektif(template_id=tpl.id, **row)
            db.add(new)
            await db.flush()
            by_kode[row["kode"]] = new
            print(
                f"[seed] konkin_2026: perspektif {row['kode']} created "
                f"(bobot={row['bobot']}, is_pengurang={row['is_pengurang']})"
            )
        else:
            by_kode[row["kode"]] = existing

    # 3. Pilot indikator — guarded by (perspektif_id, kode) existence.
    for indikator in PILOT_INDIKATOR:
        parent = by_kode.get(indikator["perspektif_kode"])
        if parent is None:
            # Shouldn't happen if the perspektif step succeeded — defensive.
            print(f"[seed] konkin_2026: skip {indikator['kode']} (parent {indikator['perspektif_kode']} missing)")
            continue
        existing_ind = await db.scalar(
            select(Indikator).where(
                Indikator.perspektif_id == parent.id,
                Indikator.kode == indikator["kode"],
            )
        )
        if existing_ind is None:
            db.add(
                Indikator(
                    perspektif_id=parent.id,
                    kode=indikator["kode"],
                    nama=indikator["nama"],
                    bobot=indikator["bobot"],
                    polaritas=indikator["polaritas"],
                    formula=indikator["formula"],
                )
            )
            print(f"[seed] konkin_2026: indikator {indikator['kode']} created under {indikator['perspektif_kode']}")
