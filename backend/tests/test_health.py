"""Health endpoint family tests.

`test_health_shape` accepts both "ok" and "degraded" because db/redis may
be down when running the unit suite without compose — what we are locking
here is the SHAPE of the payload (REQ-health-checks), not the live-deps
result. Plan 07's container e2e covers the all-green branch.

`test_health_detail_admin_gated` and `test_metrics_admin_gated` lock in
the W-02 admin-only contract: pre-Plan-05, `metrics_admin_dep` raises 401
unconditionally. Plan 05 will EXTEND these tests with role-bearing token
fixtures (no-token=401 still holds, non-admin=403, admin=200).
"""

import pytest


@pytest.mark.asyncio
async def test_health_shape(client):
    # Smoke: shape of payload; db/redis may be "down" if compose is not running — that's ok for unit suite
    r = await client.get("/api/v1/health")
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == {"status", "db", "redis", "version"}
    assert body["status"] in {"ok", "degraded"}
    assert body["version"]


@pytest.mark.asyncio
async def test_health_detail_admin_gated(client):
    # Pre-Plan-05: metrics_admin_dep raises 401 unconditionally, so /health/detail returns 401.
    # Post-Plan-05: 401 without auth, 403 with non-admin, 200 with admin token. Plan 05 extends this test.
    r = await client.get("/api/v1/health/detail")
    assert r.status_code == 401, r.text


@pytest.mark.asyncio
async def test_metrics_admin_gated(client):
    r = await client.get("/api/v1/metrics")
    assert r.status_code == 401, r.text
