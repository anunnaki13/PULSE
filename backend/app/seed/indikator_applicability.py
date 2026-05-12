"""Phase-2 pilot indikator applicability seed.

The assessment session creator reads ``indikator_applicable_bidang`` to decide
which sessions exist for a periode. These rows are domain setup data, not user
input, so the seed is idempotent and can be re-run safely.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bidang import Bidang
from app.models.indikator import Indikator
from app.models.indikator_applicable_bidang import IndikatorApplicableBidang

AGGREGATE_OM_BIDANG = (
    "BID_OM_1",
    "BID_OM_2",
    "BID_OM_3",
    "BID_OM_4",
    "BID_OM_5",
    "BID_OM_RE",
)

OUTAGE_BIDANG = AGGREGATE_OM_BIDANG


async def seed_indikator_applicability(db: AsyncSession) -> int:
    """Seed applicability rows for the Phase-2 pilot assessment workflow."""

    indikator_rows = (
        await db.execute(
            select(Indikator.kode, Indikator.id).where(
                Indikator.kode.in_(("EAF", "EFOR", "OUTAGE", "SMAP")),
                Indikator.deleted_at.is_(None),
            )
        )
    ).all()
    indikator_by_kode = {kode: indikator_id for kode, indikator_id in indikator_rows}

    bidang_rows = (
        await db.execute(
            select(Bidang.kode, Bidang.id).where(Bidang.deleted_at.is_(None))
        )
    ).all()
    bidang_by_kode = {kode: bidang_id for kode, bidang_id in bidang_rows}

    values: list[dict] = []

    for indikator_kode in ("EAF", "EFOR"):
        indikator_id = indikator_by_kode.get(indikator_kode)
        if indikator_id is None:
            continue
        for bidang_kode in AGGREGATE_OM_BIDANG:
            bidang_id = bidang_by_kode.get(bidang_kode)
            if bidang_id is not None:
                values.append(
                    {
                        "indikator_id": indikator_id,
                        "bidang_id": bidang_id,
                        "is_aggregate": True,
                    }
                )

    outage_id = indikator_by_kode.get("OUTAGE")
    if outage_id is not None:
        for bidang_kode in OUTAGE_BIDANG:
            bidang_id = bidang_by_kode.get(bidang_kode)
            if bidang_id is not None:
                values.append(
                    {
                        "indikator_id": outage_id,
                        "bidang_id": bidang_id,
                        "is_aggregate": False,
                    }
                )

    smap_id = indikator_by_kode.get("SMAP")
    if smap_id is not None:
        for bidang_id in bidang_by_kode.values():
            values.append(
                {
                    "indikator_id": smap_id,
                    "bidang_id": bidang_id,
                    "is_aggregate": False,
                }
            )

    if values:
        stmt = (
            pg_insert(IndikatorApplicableBidang)
            .values(values)
            .on_conflict_do_nothing(index_elements=["indikator_id", "bidang_id"])
        )
        await db.execute(stmt)

    sentinel = await db.scalar(select(IndikatorApplicableBidang))
    print(
        "[seed] indikator_applicability: ensured "
        f"{len(values)} pilot mappings (sentinel present: {sentinel is not None})"
    )
    return len(values)
