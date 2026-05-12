"""Phase-6 sub-indikator formula and temporary weighting coverage seed."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bidang import Bidang
from app.models.indikator import Indikator
from app.models.indikator_applicable_bidang import IndikatorApplicableBidang
from app.models.konkin_template import KonkinTemplate
from app.models.perspektif import Perspektif

PILAR_I_ROWS = [
    ("EAF", "Equivalent Availability Factor", Decimal("18.00"), "positif", "Realisasi / Target x 100%", ("BID_OM_1", "BID_OM_2", "BID_OM_RE")),
    ("EFOR", "Equivalent Forced Outage Rate", Decimal("18.00"), "negatif", "(2 - Realisasi / Target) x 100%", ("BID_OM_1", "BID_OM_2", "BID_OM_RE")),
    ("BPP_BIAYA_HAR", "BPP - Biaya Pemeliharaan 70/30", Decimal("9.00"), "negatif", "Weighted 70/30; negative cost polarity", ("BID_FIN", "BID_ACT", "BID_OM_RE")),
    ("BPP_FISIK_HAR", "BPP - Fisik Pemeliharaan 70/30", Decimal("7.00"), "positif", "Weighted 70/30; physical realization polarity positive", ("BID_OM_RE", "BID_AMS")),
    ("BPP_BIAYA_ADM", "BPP - Biaya Administrasi", Decimal("6.00"), "negatif", "Negative cost polarity", ("BID_FIN", "BID_ACT")),
    ("BPP_KIMIA_PELUMAS", "BPP - Biaya Kimia & Pelumas", Decimal("6.00"), "negatif", "Negative cost polarity", ("BID_FIN", "BID_LOG")),
    ("BPP_ATTB", "BPP - Penghapusan ATTB", Decimal("4.00"), "positif", "Completion against target x 100%", ("BID_ACT", "BID_AMS")),
    ("SDG_TJSL", "SDGs - TJSL", Decimal("4.00"), "positif", "Realisasi / Target x 100%", ("BID_CSR",)),
    ("SDG_PROPER", "SDGs - Tingkat Proper Unit", Decimal("4.00"), "positif", "Realisasi / Target x 100%", ("BID_HSE",)),
    ("SDG_ERM", "SDGs - ERM", Decimal("4.00"), "positif", "Realisasi / Target x 100%", ("BID_RIS",)),
    ("SDG_EMISI", "SDGs - Intensitas Emisi", Decimal("4.00"), "negatif", "Negative intensity polarity", ("BID_HSE", "BID_OM_RE")),
    ("SDG_KEPUASAN", "SDGs - Kepuasan Pelanggan", Decimal("4.00"), "range", "Range-based: target is desired index; score declines outside tolerance", ("BID_CMR",)),
    ("SDG_BATUBARA", "SDGs - Umur Persediaan Batubara", Decimal("4.00"), "range", "Range-based stock days target", ("BID_EPI",)),
    ("SDG_DIGITAL_PAY", "SDGs - Implementasi Digitalisasi Pembayaran", Decimal("8.00"), "positif", "Realisasi / Target x 100%", ("BID_TDV", "BID_FIN")),
]

PILAR_II_WEIGHTS = {
    "OUTAGE": Decimal("7.72"),
    "RELIABILITY": Decimal("7.69"),
    "EFFICIENCY": Decimal("7.69"),
    "WPC": Decimal("7.69"),
    "OPERATION": Decimal("7.69"),
    "ENERGI_PRIMER": Decimal("7.69"),
    "LCCM": Decimal("7.69"),
    "SCM": Decimal("7.69"),
    "LINGKUNGAN": Decimal("7.69"),
    "K3": Decimal("7.69"),
    "KEAMANAN": Decimal("7.69"),
    "BENDUNGAN": Decimal("7.69"),
    "DPP": Decimal("7.69"),
}

PILAR_IV_ROWS = [
    ("INV_DISB_TENAYAN", "Disburse Investasi UP Tenayan Non Tembilahan", Decimal("35.00"), "positif", "70% component of disburse investment", ("BID_SPRO", "BID_FIN")),
    ("INV_DISB_TEMBILAHAN", "Disburse Investasi PLTU Tembilahan", Decimal("15.00"), "positif", "30% component of disburse investment", ("BID_SPRO", "BID_FIN")),
    ("PRK_TENAYAN", "PRK Investasi Terkontrak UP Tenayan", Decimal("35.00"), "positif", "70% component of PRK contracted", ("BID_SPRO", "BID_FIN")),
    ("PRK_TEMBILAHAN", "PRK Investasi Terkontrak PLTU Tembilahan", Decimal("15.00"), "positif", "30% component of PRK contracted", ("BID_SPRO", "BID_FIN")),
]

PILAR_V_ROWS = [
    ("HCR", "Human Capital Readiness (Maturity Level)", Decimal("20.00"), "positif", "Rubrik L0..L4 (lihat ml_stream HCR)", ("BID_HTD", "BID_HSC")),
    ("OCR", "Organization Capital Readiness (Maturity Level)", Decimal("20.00"), "positif", "Rubrik L0..L4 (lihat ml_stream OCR)", ("BID_HTD", "BID_HSC")),
    ("SPKI", "SPKI PLN NP", Decimal("15.00"), "positif", "Realisasi / Target x 100%", ("BID_HTD",)),
    ("BUDAYA", "Penguatan Budaya", Decimal("15.00"), "positif", "Realisasi / Target x 100%", ("BID_HTD", "BID_HSC")),
    ("DISEMINASI", "Diseminasi Karya Inovasi", Decimal("10.00"), "positif", "Realisasi / Target x 100%", ("BID_HTD", "BID_TDV")),
    ("BIAYA_KESEHATAN", "Biaya Kesehatan", Decimal("8.00"), "negatif", "Negative cost polarity", ("BID_HTD", "BID_FIN")),
    ("LTIFR", "Lost Time Injury Frequency Rate", Decimal("7.00"), "negatif", "Target 0.106; lower is better", ("BID_HSE",)),
    ("PROJECT_KORPORAT", "Kontribusi Project Korporat", Decimal("5.00"), "positif", "Realisasi / Target x 100%", ("BID_TDV", "BID_SPRO")),
]


async def _perspektif_by_kode(db: AsyncSession) -> dict[str, Perspektif]:
    template = await db.scalar(select(KonkinTemplate).where(KonkinTemplate.tahun == 2026))
    if template is None:
        return {}
    rows = (
        await db.scalars(select(Perspektif).where(Perspektif.template_id == template.id))
    ).all()
    return {row.kode: row for row in rows}


async def _upsert_indikator(
    db: AsyncSession,
    perspektif: Perspektif,
    row: tuple[str, str, Decimal, str, str, tuple[str, ...]],
) -> Indikator:
    kode, nama, bobot, polaritas, formula, _bidang = row
    indikator = await db.scalar(
        select(Indikator).where(
            Indikator.perspektif_id == perspektif.id,
            Indikator.kode == kode,
            Indikator.deleted_at.is_(None),
        )
    )
    if indikator is None:
        indikator = Indikator(
            perspektif_id=perspektif.id,
            kode=kode,
            nama=nama,
            bobot=bobot,
            polaritas=polaritas,
            formula=formula,
        )
        db.add(indikator)
        await db.flush()
    else:
        indikator.nama = nama
        indikator.bobot = bobot
        indikator.polaritas = polaritas
        indikator.formula = formula
    return indikator


async def seed_subindikator_coverage(db: AsyncSession) -> int:
    by_pilar = await _perspektif_by_kode(db)
    if not {"I", "II", "IV", "V"}.issubset(by_pilar):
        print("[seed] subindikator_coverage: skip (required perspektif missing)")
        return 0

    bidang_rows = (
        await db.execute(select(Bidang.kode, Bidang.id).where(Bidang.deleted_at.is_(None)))
    ).all()
    bidang_by_kode = {kode: bidang_id for kode, bidang_id in bidang_rows}
    values: list[dict] = []
    ensured = 0

    for pilar_kode, rows in (("I", PILAR_I_ROWS), ("IV", PILAR_IV_ROWS), ("V", PILAR_V_ROWS)):
        for row in rows:
            indikator = await _upsert_indikator(db, by_pilar[pilar_kode], row)
            ensured += 1
            for bidang_kode in row[5]:
                bidang_id = bidang_by_kode.get(bidang_kode)
                if bidang_id is not None:
                    values.append({"indikator_id": indikator.id, "bidang_id": bidang_id, "is_aggregate": False})

    for kode, bobot in PILAR_II_WEIGHTS.items():
        indikator = await db.scalar(
            select(Indikator).where(
                Indikator.perspektif_id == by_pilar["II"].id,
                Indikator.kode == kode,
                Indikator.deleted_at.is_(None),
            )
        )
        if indikator is not None:
            indikator.bobot = bobot
            ensured += 1

    if values:
        stmt = (
            pg_insert(IndikatorApplicableBidang)
            .values(values)
            .on_conflict_do_nothing(index_elements=["indikator_id", "bidang_id"])
        )
        await db.execute(stmt)

    print(f"[seed] subindikator_coverage: ensured {ensured} indicators/weights and {len(values)} mappings")
    return ensured
