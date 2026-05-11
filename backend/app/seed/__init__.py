"""PULSE seed module (Plan 07).

Idempotent first-run seeding for Phase 1:

1. ``seed_bidang``         — REQ-bidang-master master list (PLTU Tenayan)
2. ``seed_konkin_2026``    — REQ-konkin-template-crud template + perspektif
                              (W-07: VI is pengurang, bobot=0, cap=10)
3. ``seed_pilot_rubrics``  — REQ-dynamic-ml-schema rubric trees for Outage,
                              SMAP, EAF, EFOR streams
4. ``seed_admin_user``     — first admin (CONTEXT.md Auth) with role
                              ``admin_unit`` (NOT capitalized "Admin")

Idempotency contract: running ``python -m app.seed`` twice produces no
duplicate rows and no errors. Each sub-seed module is responsible for its
own existence check (``ON CONFLICT DO NOTHING`` or ``SELECT first``).
"""

from __future__ import annotations

from app.db.session import SessionLocal


async def run_seed() -> None:
    """Orchestrator. Runs every sub-seed in dependency order.

    Each step commits before the next so partial failures leave the DB in a
    consistent state (e.g. if pilot_rubrics fails, the admin_user step is
    skipped but the bidang + konkin rows are persisted).
    """
    # Lazy imports so the module is cheap to import (tests that just want
    # ``run_seed`` don't pay for the full domain stack).
    from .bidang import seed_bidang
    from .konkin_2026 import seed_konkin_2026
    from .pilot_rubrics import seed_pilot_rubrics
    from .admin_user import seed_admin_user

    async with SessionLocal() as db:
        await seed_bidang(db)
        await db.commit()
        await seed_konkin_2026(db)
        await db.commit()
        await seed_pilot_rubrics(db)
        await db.commit()
        await seed_admin_user(db)
        await db.commit()
        print("[seed] complete")
