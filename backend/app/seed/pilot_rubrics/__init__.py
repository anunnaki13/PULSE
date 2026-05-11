"""Pilot rubric seeders (REQ-dynamic-ml-schema).

Each module here owns one MlStream row + its ``structure`` JSONB rubric tree.
Phase-1 ships four pilot streams per the plan's success criterion:

- Outage Management (OUTAGE) — full L0..L4 coverage on at least one
  sub-area
- SMAP — full L0..L4 coverage
- EAF — header-only stub (KPI form is Phase-2)
- EFOR — header-only stub (KPI form is Phase-2)

Idempotency contract: each seed function checks for an existing MlStream
row by ``kode`` and skips creation if present. Re-running ``seed_pilot_rubrics``
is a no-op against an already-seeded DB.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


async def seed_pilot_rubrics(db: AsyncSession) -> None:
    """Run every pilot-rubric seeder in sequence.

    Order does not matter — each stream is independent. We commit between
    streams (via the orchestrator) so a single failing stream doesn't lose
    the successful ones.
    """
    from .outage import seed as seed_outage
    from .smap import seed as seed_smap
    from .eaf import seed as seed_eaf
    from .efor import seed as seed_efor

    await seed_outage(db)
    await seed_smap(db)
    await seed_eaf(db)
    await seed_efor(db)
