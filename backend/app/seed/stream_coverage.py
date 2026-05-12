"""Phase-6 remaining maturity stream coverage seed.

This seed intentionally adds placeholder rubric trees for the remaining
Pilar II streams before final bobot/formula normalization in Plan 06-03.
The goal of Plan 06-01 is workflow coverage: every stream has a structured
JSONB tree, an indikator row, and bidang applicability so sessions can be
created and exercised.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bidang import Bidang
from app.models.indikator import Indikator
from app.models.indikator_applicable_bidang import IndikatorApplicableBidang
from app.models.konkin_template import KonkinTemplate
from app.models.ml_stream import MlStream
from app.models.perspektif import Perspektif

STREAM_VERSION = "2026.1"


def _criteria(topic: str) -> dict[str, str]:
    return {
        "level_0": f"{topic} belum memiliki praktik terdokumentasi.",
        "level_1": f"{topic} sudah dilakukan ad-hoc dan belum konsisten.",
        "level_2": f"{topic} memiliki standar minimum dan bukti pelaksanaan berkala.",
        "level_3": f"{topic} terintegrasi lintas fungsi dengan monitoring dan tindak lanjut.",
        "level_4": f"{topic} sudah berbasis continuous improvement, data historis, dan evaluasi efektivitas.",
    }


def _structure(kode: str, focus: str, unit: str, areas: list[tuple[str, str]]) -> dict:
    return {
        "type": "maturity_level",
        "unit": unit,
        "placeholder": True,
        "source_note": "Phase 06-01 seed placeholder; replace criteria with final Pedoman Konkin detail when available.",
        "calculation": "average assessed maturity sub-area values",
        "areas": [
            {
                "kode": f"{kode}-{idx:02d}",
                "nama": area_name,
                "unit": unit,
                "sub_areas": [
                    {
                        "kode": f"{kode}-{idx:02d}-01",
                        "nama": topic,
                        "criteria": _criteria(f"{focus} - {topic}"),
                    }
                ],
            }
            for idx, (area_name, topic) in enumerate(areas, start=1)
        ],
    }


REMAINING_STREAMS: list[dict] = [
    {
        "kode": "RELIABILITY",
        "nama": "Reliability Management",
        "bidang": ("BID_REL_1", "BID_REL_2", "BID_OM_RE"),
        "areas": [("Strategi Reliability", "Reliability improvement program"), ("Defect Elimination", "Root cause elimination")],
    },
    {
        "kode": "EFFICIENCY",
        "nama": "Efficiency Management",
        "bidang": ("BID_OM_RE", "BID_OM_1", "BID_OM_2"),
        "areas": [("Heat Rate", "Heat-rate monitoring"), ("Losses", "Losses reduction program")],
    },
    {
        "kode": "WPC",
        "nama": "Work Planning & Control",
        "bidang": ("BID_AMS", "BID_OM_RE", "BID_LOG"),
        "areas": [("Work Identification", "Work screening and prioritization"), ("Scheduling", "Integrated weekly schedule")],
    },
    {
        "kode": "OPERATION",
        "nama": "Operation Management",
        "bidang": ("BID_OM_1", "BID_OM_2", "BID_OM_3", "BID_OM_4", "BID_OM_5"),
        "areas": [("Operating Discipline", "Shift log and procedure adherence"), ("Performance Review", "Daily operating review")],
    },
    {
        "kode": "ENERGI_PRIMER",
        "nama": "Pengelolaan Energi Primer",
        "bidang": ("BID_EPI", "BID_LOG", "BID_FIN"),
        "areas": [("Pasokan", "Fuel availability assurance"), ("Kualitas", "Fuel quality control")],
    },
    {
        "kode": "LCCM",
        "nama": "Life Cycle Cost Management",
        "bidang": ("BID_AMS", "BID_FIN", "BID_ACT"),
        "areas": [("Cost Baseline", "Lifecycle cost baseline"), ("Optimization", "Cost-risk optimization")],
    },
    {
        "kode": "SCM",
        "nama": "Supply Chain Management",
        "bidang": ("BID_SSCM", "BID_LOG", "BID_AMS"),
        "areas": [("Procurement Planning", "Procurement planning integration"), ("Inventory", "Critical spares availability")],
    },
    {
        "kode": "LINGKUNGAN",
        "nama": "Manajemen Lingkungan",
        "bidang": ("BID_HSE", "BID_CSR"),
        "areas": [("Compliance", "Environmental compliance monitoring"), ("Program", "Environmental improvement program")],
    },
    {
        "kode": "K3",
        "nama": "Manajemen K3",
        "bidang": ("BID_HSE",),
        "areas": [("Risk Control", "Hazard identification and control"), ("Learning", "Safety learning and campaign")],
    },
    {
        "kode": "KEAMANAN",
        "nama": "Manajemen Keamanan",
        "bidang": ("BID_HSE", "BID_CPF"),
        "areas": [("Security Governance", "Security risk governance"), ("Incident Response", "Security incident response")],
    },
    {
        "kode": "BENDUNGAN",
        "nama": "Pengelolaan Bendungan",
        "bidang": ("BID_AMS", "BID_HSE"),
        "areas": [("Inspection", "Dam inspection program"), ("Emergency", "Dam emergency preparedness")],
    },
    {
        "kode": "DPP",
        "nama": "Digital Power Plant",
        "bidang": ("BID_TDV", "BID_OM_RE"),
        "areas": [("Data Foundation", "Operational data reliability"), ("Digital Use Case", "Digital use-case adoption")],
    },
]


async def _perspektif_ii(db: AsyncSession) -> Perspektif | None:
    template = await db.scalar(select(KonkinTemplate).where(KonkinTemplate.tahun == 2026))
    if template is None:
        return None
    return await db.scalar(
        select(Perspektif).where(
            Perspektif.template_id == template.id,
            Perspektif.kode == "II",
        )
    )


async def seed_stream_coverage(db: AsyncSession) -> int:
    perspektif_ii = await _perspektif_ii(db)
    if perspektif_ii is None:
        print("[seed] stream_coverage: skip (Perspektif II not found)")
        return 0

    bidang_rows = (
        await db.execute(select(Bidang.kode, Bidang.id).where(Bidang.deleted_at.is_(None)))
    ).all()
    bidang_by_kode = {kode: bidang_id for kode, bidang_id in bidang_rows}
    created_or_existing = 0
    applicability_values: list[dict] = []

    for stream in REMAINING_STREAMS:
        existing_stream = await db.scalar(select(MlStream).where(MlStream.kode == stream["kode"]))
        if existing_stream is None:
            db.add(
                MlStream(
                    kode=stream["kode"],
                    nama=stream["nama"],
                    version=STREAM_VERSION,
                    structure=_structure(stream["kode"], stream["nama"], "level", stream["areas"]),
                )
            )
            await db.flush()

        indikator = await db.scalar(
            select(Indikator).where(
                Indikator.perspektif_id == perspektif_ii.id,
                Indikator.kode == stream["kode"],
                Indikator.deleted_at.is_(None),
            )
        )
        if indikator is None:
            indikator = Indikator(
                perspektif_id=perspektif_ii.id,
                kode=stream["kode"],
                nama=f"{stream['nama']} (Maturity Level)",
                bobot=Decimal("0.00"),
                polaritas="positif",
                formula=f"Rubrik L0..L4 placeholder (lihat ml_stream {stream['kode']}); bobot final ditetapkan di Plan 06-03.",
            )
            db.add(indikator)
            await db.flush()

        created_or_existing += 1
        for bidang_kode in stream["bidang"]:
            bidang_id = bidang_by_kode.get(bidang_kode)
            if bidang_id is not None:
                applicability_values.append(
                    {"indikator_id": indikator.id, "bidang_id": bidang_id, "is_aggregate": False}
                )

    if applicability_values:
        stmt = (
            pg_insert(IndikatorApplicableBidang)
            .values(applicability_values)
            .on_conflict_do_nothing(index_elements=["indikator_id", "bidang_id"])
        )
        await db.execute(stmt)

    print(
        "[seed] stream_coverage: ensured "
        f"{created_or_existing} remaining streams and {len(applicability_values)} applicability mappings"
    )
    return created_or_existing
