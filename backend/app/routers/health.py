"""Health endpoint family (REQ-health-checks + W-02 fix).

Three endpoints:

- `GET /api/v1/health`         — public liveness + dependency probe.
  Returns `{status, db, redis, version}` with 2 s short-timeout async pings
  to db and redis. Used by Docker healthcheck and Nginx upstream.

- `GET /api/v1/health/detail`  — admin-only (W-02). Returns extended
  diagnostic JSON: `{status, db: {ok, latency_ms}, redis: {ok, latency_ms,
  used_memory}, version, uptime_s}`. Guarded by `metrics_admin_dep` so
  anonymous probes get 401 and cannot harvest internal state
  (T-03-I-02 mitigation).

- `GET /api/v1/metrics`        — admin-only Prometheus text-format
  exposition (W-02). Same admin gate (T-03-I-03 mitigation).

`asyncio.wait_for(..., timeout=2.0)` on every probe prevents a dead Redis
or hung Postgres from blocking the health endpoint indefinitely
(T-03-D-02 mitigation).
"""

import asyncio
import time

from fastapi import APIRouter, Depends, Request, Response
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.core.config import settings
from app.deps.db import get_db
from app.deps.metrics_admin import metrics_admin_dep
from app.deps.redis import get_redis
from app.services.openrouter_client import ai_available, ai_mode

router = APIRouter(tags=["health"])


async def _ping_db(db: AsyncSession) -> tuple[str, float]:
    t0 = time.perf_counter()
    try:
        await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=2.0)
        return "ok", (time.perf_counter() - t0) * 1000
    except Exception:
        return "down", (time.perf_counter() - t0) * 1000


async def _ping_redis(r: Redis) -> tuple[str, float, int | None]:
    t0 = time.perf_counter()
    try:
        await asyncio.wait_for(r.ping(), timeout=2.0)
        info = await r.info("memory")
        used = int(info.get("used_memory") or 0)
        return "ok", (time.perf_counter() - t0) * 1000, used
    except Exception:
        return "down", (time.perf_counter() - t0) * 1000, None


@router.get("/health", summary="Liveness + dependency probe (public)")
async def health(
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
) -> dict:
    db_s, _ = await _ping_db(db)
    redis_s, _, _ = await _ping_redis(r)
    overall = "ok" if db_s == "ok" and redis_s == "ok" else "degraded"
    return {"status": overall, "db": db_s, "redis": redis_s, "version": __version__}


@router.get(
    "/health/detail",
    summary="Detailed health probe (admin-only — W-02)",
    dependencies=[Depends(metrics_admin_dep)],
)
async def health_detail(
    request: Request,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
) -> dict:
    (db_s, db_ms), (redis_s, redis_ms, redis_mem) = await asyncio.gather(
        _ping_db(db), _ping_redis(r)
    )
    uptime_s = max(0.0, time.time() - getattr(request.app.state, "startup_ts", time.time()))
    overall = "ok" if db_s == "ok" and redis_s == "ok" else "degraded"
    return {
        "status": overall,
        "db": {"ok": db_s == "ok", "latency_ms": round(db_ms, 2)},
        "redis": {
            "ok": redis_s == "ok",
            "latency_ms": round(redis_ms, 2),
            "used_memory": redis_mem,
        },
        "ai": {
            "available": ai_available(),
            "mode": ai_mode(),
            "routine_model": settings.OPENROUTER_ROUTINE_MODEL,
            "complex_model": settings.OPENROUTER_COMPLEX_MODEL,
            "monthly_budget_usd": settings.AI_MONTHLY_BUDGET_USD,
        },
        "version": __version__,
        "uptime_s": round(uptime_s, 1),
    }


@router.get(
    "/metrics",
    summary="Prometheus text-format metrics (admin-only — W-02)",
    dependencies=[Depends(metrics_admin_dep)],
)
async def metrics(
    request: Request,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
) -> Response:
    (db_s, db_ms), (redis_s, redis_ms, _) = await asyncio.gather(
        _ping_db(db), _ping_redis(r)
    )
    uptime_s = max(0.0, time.time() - getattr(request.app.state, "startup_ts", time.time()))
    lines = [
        "# HELP pulse_up 1 if service is up",
        "# TYPE pulse_up gauge",
        "pulse_up 1",
        "# HELP pulse_uptime_seconds Process uptime",
        "# TYPE pulse_uptime_seconds gauge",
        f"pulse_uptime_seconds {uptime_s:.3f}",
        "# HELP pulse_dep_up 1 if dependency reachable",
        "# TYPE pulse_dep_up gauge",
        f'pulse_dep_up{{dep="db"}} {1 if db_s == "ok" else 0}',
        f'pulse_dep_up{{dep="redis"}} {1 if redis_s == "ok" else 0}',
        "# HELP pulse_dep_latency_ms Last probe latency in ms",
        "# TYPE pulse_dep_latency_ms gauge",
        f'pulse_dep_latency_ms{{dep="db"}} {db_ms:.3f}',
        f'pulse_dep_latency_ms{{dep="redis"}} {redis_ms:.3f}',
    ]
    body = "\n".join(lines) + "\n"
    return Response(content=body, media_type="text/plain; version=0.0.4; charset=utf-8")
