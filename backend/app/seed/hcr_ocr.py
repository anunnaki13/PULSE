"""Phase-6 HCR/OCR maturity stream seed."""

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

VERSION = "2026.1"


def _criteria(topic: str) -> dict[str, str]:
    return {
        "level_0": f"{topic} belum diterapkan.",
        "level_1": f"{topic} dilakukan ad-hoc dan belum memiliki standar baku.",
        "level_2": f"{topic} memiliki standar, PIC, dan bukti pelaksanaan periodik.",
        "level_3": f"{topic} terintegrasi dengan sasaran unit dan dimonitor rutin.",
        "level_4": f"{topic} dioptimalkan berbasis data, evaluasi efektivitas, dan perbaikan berkelanjutan.",
    }


HCR_AREAS = [
    "Strategic Workforce Planning",
    "Talent Acquisition",
    "Talent Management & Development",
    "Performance Management",
    "Reward & Recognition",
    "Industrial Relation",
    "HC Operations",
]

HCR_STRUCTURE: dict = {
    "type": "maturity_level",
    "unit": "level",
    "placeholder": True,
    "calculation": "average assessed maturity sub-area values",
    "normalization": "average with assessed-component normalization when a component is not assessed",
    "areas": [
        {
            "kode": f"HCR-{idx:02d}",
            "nama": name,
            "sub_areas": [
                {
                    "kode": f"HCR-{idx:02d}-01",
                    "nama": name,
                    "criteria": _criteria(f"HCR - {name}"),
                }
            ],
        }
        for idx, name in enumerate(HCR_AREAS, start=1)
    ],
}

OCR_STRUCTURE: dict = {
    "type": "maturity_level",
    "unit": "level",
    "placeholder": True,
    "calculation": "weighted average when weight metadata exists; otherwise average assessed maturity values",
    "normalization": "normalize assessed weights when a component is not assessed",
    "areas": [
        {
            "kode": "OCR-01",
            "nama": "Organization Governance",
            "sub_areas": [{"kode": "OCR-01-01", "nama": "Governance clarity", "weight": 1.0, "criteria": _criteria("OCR - Governance clarity")}],
        },
        {
            "kode": "OCR-02",
            "nama": "Process & Decision Rights",
            "sub_areas": [{"kode": "OCR-02-01", "nama": "Decision-right effectiveness", "weight": 1.0, "criteria": _criteria("OCR - Decision-right effectiveness")}],
        },
        {
            "kode": "OCR-03",
            "nama": "Collaboration",
            "sub_areas": [{"kode": "OCR-03-01", "nama": "Cross-functional collaboration", "weight": 1.0, "criteria": _criteria("OCR - Cross-functional collaboration")}],
        },
        {
            "kode": "OCR-04",
            "nama": "Knowledge Management",
            "sub_areas": [{"kode": "OCR-04-01", "nama": "Knowledge capture and reuse", "weight": 1.0, "criteria": _criteria("OCR - Knowledge capture and reuse")}],
        },
        {
            "kode": "OCR-05",
            "nama": "Change Management",
            "sub_areas": [{"kode": "OCR-05-01", "nama": "Change adoption", "weight": 1.0, "criteria": _criteria("OCR - Change adoption")}],
        },
        {
            "kode": "OCR-OWM",
            "nama": "Organization Work Management",
            "sub_areas": [
                {"kode": "OCR-OWM-01", "nama": "OWM process maturity", "weight": 0.55, "criteria": _criteria("OCR OWM - process maturity")},
                {"kode": "OCR-OWM-02", "nama": "OWM adoption effectiveness", "weight": 0.45, "criteria": _criteria("OCR OWM - adoption effectiveness")},
            ],
        },
    ],
}

STREAMS = [
    {"kode": "HCR", "nama": "Human Capital Readiness", "structure": HCR_STRUCTURE, "bidang": ("BID_HTD", "BID_HSC")},
    {"kode": "OCR", "nama": "Organization Capital Readiness", "structure": OCR_STRUCTURE, "bidang": ("BID_HTD", "BID_HSC")},
]


async def _perspektif_v(db: AsyncSession) -> Perspektif | None:
    template = await db.scalar(select(KonkinTemplate).where(KonkinTemplate.tahun == 2026))
    if template is None:
        return None
    return await db.scalar(select(Perspektif).where(Perspektif.template_id == template.id, Perspektif.kode == "V"))


async def seed_hcr_ocr(db: AsyncSession) -> int:
    perspektif_v = await _perspektif_v(db)
    if perspektif_v is None:
        print("[seed] hcr_ocr: skip (Perspektif V not found)")
        return 0

    bidang_rows = (
        await db.execute(select(Bidang.kode, Bidang.id).where(Bidang.deleted_at.is_(None)))
    ).all()
    bidang_by_kode = {kode: bidang_id for kode, bidang_id in bidang_rows}
    applicability_values: list[dict] = []

    for stream in STREAMS:
        existing_stream = await db.scalar(select(MlStream).where(MlStream.kode == stream["kode"]))
        if existing_stream is None:
            db.add(MlStream(kode=stream["kode"], nama=stream["nama"], version=VERSION, structure=stream["structure"]))
            await db.flush()

        indikator = await db.scalar(
            select(Indikator).where(
                Indikator.perspektif_id == perspektif_v.id,
                Indikator.kode == stream["kode"],
                Indikator.deleted_at.is_(None),
            )
        )
        if indikator is None:
            indikator = Indikator(
                perspektif_id=perspektif_v.id,
                kode=stream["kode"],
                nama=f"{stream['nama']} (Maturity Level)",
                bobot=Decimal("0.00"),
                polaritas="positif",
                formula=f"Rubrik L0..L4 placeholder (lihat ml_stream {stream['kode']}); bobot final ditetapkan di Plan 06-03.",
            )
            db.add(indikator)
            await db.flush()

        for bidang_kode in stream["bidang"]:
            bidang_id = bidang_by_kode.get(bidang_kode)
            if bidang_id is not None:
                applicability_values.append({"indikator_id": indikator.id, "bidang_id": bidang_id, "is_aggregate": False})

    if applicability_values:
        stmt = (
            pg_insert(IndikatorApplicableBidang)
            .values(applicability_values)
            .on_conflict_do_nothing(index_elements=["indikator_id", "bidang_id"])
        )
        await db.execute(stmt)

    print(f"[seed] hcr_ocr: ensured {len(STREAMS)} streams and {len(applicability_values)} applicability mappings")
    return len(STREAMS)
