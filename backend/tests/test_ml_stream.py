"""ML Stream JSONB + GIN tests (REQ-dynamic-ml-schema).

Coverage:

- Inserting a stream with a nested ``structure`` tree round-trips through
  Postgres JSONB intact.
- A JSONB containment query (``structure @> '{...}'::jsonb``) returns the
  inserted row — Postgres uses the GIN index ``idx_ml_stream_structure``
  created in the 0003 migration.

These tests require live Postgres (the JSONB ``@>`` operator is a
Postgres-specific server-side feature; SQLite cannot stand in).
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.models.ml_stream import MlStream


@pytest.mark.asyncio
async def test_jsonb_round_trip(db_session):
    """Insert a stream with a nested structure tree; read it back; assert
    the tree is preserved verbatim."""
    structure = {
        "areas": [
            {
                "code": "OM-1",
                "name": "Outage Planning",
                "sub_areas": [
                    {
                        "code": "OM-1-1",
                        "uraian": "Planning horizon",
                        "criteria": {
                            "level_0": "Ad-hoc",
                            "level_4": "Optimized rolling 5y plan",
                        },
                    }
                ],
            }
        ]
    }
    stream = MlStream(
        kode="OM-T",
        nama="Outage Management (test)",
        version="2026.1",
        structure=structure,
    )
    db_session.add(stream)
    await db_session.flush()

    fetched = await db_session.get(MlStream, stream.id)
    assert fetched is not None
    assert fetched.structure["areas"][0]["code"] == "OM-1"
    assert (
        fetched.structure["areas"][0]["sub_areas"][0]["criteria"]["level_4"]
        == "Optimized rolling 5y plan"
    )


@pytest.mark.asyncio
async def test_jsonb_containment_query_uses_gin(db_session):
    """The ``structure @> '{...}'::jsonb`` query returns the row we just
    inserted. With the GIN index in place this is O(log N); without it it
    would be a seq scan — but the test only asserts correctness, not the
    plan. (Plan 07's container e2e can EXPLAIN ANALYZE to assert the
    index hit.)"""
    stream = MlStream(
        kode="OM-Q",
        nama="Outage Management (containment)",
        version="2026.1",
        structure={
            "areas": [
                {
                    "code": "OM-1",
                    "name": "Planning",
                    "sub_areas": [
                        {"code": "OM-1-1", "uraian": "Horizon"}
                    ],
                }
            ]
        },
    )
    db_session.add(stream)
    await db_session.flush()

    # @> is the JSONB containment operator; the bound parameter is the
    # JSON literal that must be present somewhere in `structure`.
    rows = (
        await db_session.execute(
            text(
                "SELECT id FROM ml_stream "
                "WHERE structure @> '{\"areas\":[{\"code\":\"OM-1\"}]}'::jsonb"
            )
        )
    ).scalars().all()
    assert stream.id in rows
