---
phase: 01-foundation-master-data-auth
plan: 03
type: execute
wave: 2
depends_on: [01-01]
files_modified:
  - backend/pyproject.toml
  - backend/alembic.ini
  - backend/alembic/env.py
  - backend/alembic/script.py.mako
  - backend/alembic/versions/.gitkeep
  - backend/app/__init__.py
  - backend/app/main.py
  - backend/app/core/__init__.py
  - backend/app/core/config.py
  - backend/app/core/logging.py
  - backend/app/core/security.py
  - backend/app/db/__init__.py
  - backend/app/db/base.py
  - backend/app/db/session.py
  - backend/app/deps/__init__.py
  - backend/app/deps/db.py
  - backend/app/deps/redis.py
  - backend/app/deps/metrics_admin.py
  - backend/app/routers/__init__.py
  - backend/app/routers/health.py
  - backend/app/models/__init__.py
  - backend/app/schemas/__init__.py
  - backend/tests/__init__.py
  - backend/tests/conftest.py
  - backend/tests/test_health.py
  - backend/tests/test_no_upload_policy.py
  - backend/tests/test_bootstrap.py
autonomous: true
requirements:
  - REQ-backend-stack
  - REQ-health-checks
  - REQ-no-evidence-upload
must_haves:
  truths:
    - "`python -m app.main` (or uvicorn) boots the FastAPI app with /api/v1 prefix and the OpenAPI docs at /api/v1/docs"
    - "GET /api/v1/health returns 200 with JSON `{status, db, redis, version}` and short-timeout (2s) async pings to db and redis"
    - "GET /api/v1/health/detail (admin-only via require_role) returns extended diagnostic JSON: {status, db: {ok, latency_ms}, redis: {ok, latency_ms, used_memory}, version, uptime_s} (W-02 fix per CONTEXT.md API)"
    - "GET /api/v1/metrics (admin-only) returns Prometheus text-format exposition (W-02 fix)"
    - "`alembic upgrade head` runs against the asyncpg URL without crashing (no migrations yet besides initial empty revision)"
    - "Wave-0 test bootstrap is in place: `pip install -e backend[dev]` succeeds; `pytest --collect-only` runs without errors; conftest provides async client + transactional db fixture"
    - "Application logger emits structured JSON to stdout (no plaintext, no secrets)"
    - "Routers are auto-discovered: `app/routers/__init__.py` walks the package and includes every `router` it finds — Plan 05 and Plan 06 can drop new router files with zero edits to main.py or base.py"
    - "Models are auto-discovered: `app/db/base.py` imports every module under `app/models/` so Alembic --autogenerate sees them — no Plan-05/06 edits to base.py required"
  artifacts:
    - path: "backend/pyproject.toml"
      provides: "Exact pinned versions from RESEARCH.md Standard Stack including [dev] extras for pytest"
      contains: "fastapi"
    - path: "backend/app/main.py"
      provides: "FastAPI app factory, /api/v1 prefix, OpenAPI docs paths, lifespan handler"
      contains: "FastAPI"
    - path: "backend/app/core/config.py"
      provides: "pydantic-settings v2 BaseSettings reading .env"
      contains: "BaseSettings"
    - path: "backend/app/db/session.py"
      provides: "Async SQLAlchemy engine + sessionmaker with expire_on_commit=False"
      contains: "expire_on_commit=False"
    - path: "backend/app/routers/health.py"
      provides: "GET /health (public), /health/detail (admin), /metrics (admin)"
      contains: "asyncio.gather"
    - path: "backend/tests/test_no_upload_policy.py"
      provides: "OpenAPI multipart contract test (REQ-no-evidence-upload defense)"
      contains: "multipart/form-data"
    - path: "backend/tests/conftest.py"
      provides: "Async httpx AsyncClient fixture + per-test transactional rollback"
      contains: "AsyncClient"
  key_links:
    - from: "backend/app/main.py"
      to: "backend/app/routers/__init__.py"
      via: "Auto-include all routers via pkgutil walk"
      pattern: "include_router"
    - from: "backend/app/db/base.py"
      to: "backend/app/models/"
      via: "Auto-import every module via pkgutil walk"
      pattern: "pkgutil"
    - from: "backend/app/routers/health.py"
      to: "pulse-db, pulse-redis"
      via: "Short-timeout async ping"
      pattern: "asyncio\\.wait_for"
---

## Revision History

- **Iteration 1 (initial):** Backend skeleton with /health, auto-discovery, pyproject pins, test scaffolds.
- **Iteration 2 (this revision):**
  - **B-05 fix:** vitest globals types are a frontend concern (Plan 04); no change here.
  - **B-06 fix (Wave 0 + executable verifies):** Task 1 is now the **Wave 0 test bootstrap** task — installs `backend[dev]` deps and runs `pytest --collect-only` as a real smoke. Tasks 2/3 verify blocks now run actual `pytest` against the test files they create (no more `ast.parse`-only verifies). Each `<automated>` block that needs a running container guards with a `docker info` preflight, but the unit-only tests in this plan run on the host Python directly via the editable install.
  - **W-02 fix:** Adds `GET /api/v1/health/detail` (admin-only DB+Redis probe with latencies) and `GET /api/v1/metrics` (admin-only Prometheus text format) per CONTEXT.md API section. Plan 05 introduces `require_role`; until that lands, Task 2 ships the endpoints behind a minimal `metrics_admin_dep` placeholder dep that 401s when no auth is wired. Plan 05 will swap this placeholder for `require_role("super_admin","admin_unit")` (no edits to health.py beyond the import).
  - **B-04 implication:** No change here. The `users.bidang_id` column was previously declared in Plan 05's auth model; that's now moved entirely into Plan 06 (master data) per CONTEXT.md "Migration FK ordering". Plan 03 stays neutral on the user model.

<objective>
Stand up the FastAPI backend skeleton with the locked stack pinned exactly (RESEARCH.md Standard Stack), a working `/api/v1/health` family of endpoints (public liveness + admin-only detail/metrics per W-02), Alembic ready to autogenerate migrations, and a Wave-0 pytest bootstrap that locks in the no-upload contract and the health-endpoint shape from day one.

Purpose: This plan delivers REQ-backend-stack + REQ-health-checks and primes the backend folder so Plan 05 (auth) and Plan 06 (master data) can drop in new router/model files with **zero edits to main.py or base.py** (router and model auto-discovery is established here).

Runs in parallel with Plan 02 (infra) and Plan 04 (frontend) in Wave 2 — exclusive file ownership: this plan owns everything under `backend/` EXCEPT `backend/Dockerfile` and `backend/entrypoint.sh` (which Plan 02 created).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/01-foundation-master-data-auth/01-CONTEXT.md
@.planning/phases/01-foundation-master-data-auth/01-RESEARCH.md
@.planning/phases/01-foundation-master-data-auth/01-01-SUMMARY.md

<interfaces>
<!-- Exposed seams for downstream Plan 05 (auth) and Plan 06 (master data) -->

# Auto-discovery contracts (Plan 05/06 just add files, no edits to existing modules)

# backend/app/routers/__init__.py
from fastapi import APIRouter
import pkgutil, importlib, pathlib
api_router = APIRouter(prefix="/api/v1")
for mod_info in pkgutil.iter_modules([str(pathlib.Path(__file__).parent)]):
    if mod_info.name.startswith("_"):
        continue
    mod = importlib.import_module(f"{__name__}.{mod_info.name}")
    if hasattr(mod, "router"):
        api_router.include_router(mod.router)

# backend/app/db/base.py
from sqlalchemy.orm import declarative_base
Base = declarative_base()
# Auto-import all model modules so Alembic --autogenerate sees them
import pkgutil, importlib, pathlib
_models_dir = pathlib.Path(__file__).parent.parent / "models"
for mi in pkgutil.iter_modules([str(_models_dir)]):
    if not mi.name.startswith("_"):
        importlib.import_module(f"app.models.{mi.name}")

# Reusable dependencies
- get_db()       -> AsyncSession (from app.deps.db)
- get_redis()    -> redis.asyncio.Redis (from app.deps.redis)
- metrics_admin_dep()  -> placeholder dep for /health/detail and /metrics; raises 401 in Plan 03; Plan 05 replaces it with require_role("super_admin","admin_unit")
- (auth deps current_user + require_role created in Plan 05 under app/deps/auth.py)

# Pydantic-settings contract (already used by Plan 02 .env)
- settings.SQLALCHEMY_DATABASE_URL -> postgresql+asyncpg://pulse:...@pulse-db:5432/pulse
- settings.REDIS_URL               -> redis://pulse-redis:6379/0
- settings.JWT_SECRET_KEY (SecretStr)
- settings.JWT_ALGORITHM, JWT_ACCESS_TTL_MIN, JWT_REFRESH_TTL_DAYS

# Test fixtures (Plan 05/06 reuse)
- @pytest.fixture client      -> httpx.AsyncClient(app=...)
- @pytest.fixture db_session  -> AsyncSession with rollback at teardown
- @pytest.fixture admin_user  -> stub (real impl added in Plan 05 once user model exists)
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1 (Wave 0): Backend pyproject + [dev] extras + Alembic + core + db/session + config + dep install + pytest smoke</name>
  <files>
    backend/pyproject.toml,
    backend/alembic.ini,
    backend/alembic/env.py,
    backend/alembic/script.py.mako,
    backend/alembic/versions/.gitkeep,
    backend/app/__init__.py,
    backend/app/core/__init__.py,
    backend/app/core/config.py,
    backend/app/core/logging.py,
    backend/app/db/__init__.py,
    backend/app/db/base.py,
    backend/app/db/session.py,
    backend/app/deps/__init__.py,
    backend/app/deps/db.py,
    backend/app/deps/redis.py
  </files>
  <action>
    **This is the Wave 0 backend test bootstrap (CONTEXT.md "Test Infrastructure" + B-06).** Install `[dev]` extras with pytest etc., create the runtime files, then run `pytest --collect-only` as a smoke proof that the test infrastructure resolves before any feature task references pytest in its `<automated>` block.

    1. `backend/pyproject.toml` — exact RESEARCH.md pins (Standard Stack table) PLUS `[project.optional-dependencies] dev` for pytest:
       ```toml
       [build-system]
       requires = ["hatchling"]
       build-backend = "hatchling.build"

       [project]
       name = "pulse-backend"
       version = "0.1.0"
       requires-python = ">=3.11,<3.12"
       dependencies = [
         "fastapi==0.136.1",
         "uvicorn[standard]==0.46.0",
         "gunicorn==26.0.0",
         "sqlalchemy[asyncio]==2.0.49",
         "asyncpg==0.31.0",
         "alembic==1.18.4",
         "pydantic==2.13.4",
         "pydantic-settings==2.14.1",
         "python-jose[cryptography]==3.5.0",
         "passlib[bcrypt]==1.7.4",
         "bcrypt==5.0.0",
         "redis[hiredis]>=5,<6",
         "openpyxl==3.1.5",
         "python-multipart>=0.0.20",
         "structlog>=24.4",
       ]

       [project.optional-dependencies]
       dev = [
         "pytest==9.0.3",
         "pytest-asyncio==1.3.0",
         "httpx==0.28.1",
         "ruff>=0.7",
         "mypy>=1.13",
         "pytest-cov>=5",
       ]
       prod = []  # placeholder for prod-only adds

       [project.scripts]
       pulse-seed = "app.seed.__main__:main"  # wired in Plan 07; declared here for stable entrypoint

       [tool.pytest.ini_options]
       asyncio_mode = "auto"
       testpaths = ["tests"]
       pythonpath = ["."]
       addopts = "-q --strict-markers"

       [tool.ruff]
       line-length = 100
       target-version = "py311"

       [tool.hatch.build.targets.wheel]
       packages = ["app"]
       ```

    2. `backend/app/__init__.py`:
       ```python
       __version__ = "0.1.0"
       ```

    3. `backend/app/core/config.py` — verbatim from RESEARCH.md Pattern 2, with `SQLALCHEMY_DATABASE_URL` property. Add fields `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD` (SecretStr), `APP_VERSION: str = "0.1.0"`, and a `DEBUG: bool = False` flag. Also add `STARTUP_TS: float` filled in main.py lifespan for uptime metric.

    4. `backend/app/core/logging.py` — structured JSON logger via stdlib + structlog:
       ```python
       import logging, sys
       import structlog
       def configure_logging(debug: bool = False) -> None:
           logging.basicConfig(format="%(message)s", stream=sys.stdout,
                               level=logging.DEBUG if debug else logging.INFO)
           # Silence the cosmetic passlib/bcrypt 1.7.4 warning per RESEARCH Pitfall 3
           logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.ERROR)
           structlog.configure(
               processors=[
                   structlog.contextvars.merge_contextvars,
                   structlog.processors.add_log_level,
                   structlog.processors.TimeStamper(fmt="iso"),
                   structlog.processors.JSONRenderer(),
               ],
               wrapper_class=structlog.make_filtering_bound_logger(
                   logging.DEBUG if debug else logging.INFO),
               cache_logger_on_first_use=True,
           )
       def get_logger(name: str = "pulse"):
           return structlog.get_logger(name)
       ```

    5. `backend/app/db/session.py` — RESEARCH.md Pattern 1 verbatim. expire_on_commit=False (Pitfall #4).

    6. `backend/app/db/base.py` — auto-import all model modules:
       ```python
       from sqlalchemy.orm import declarative_base
       Base = declarative_base()
       import importlib, pkgutil, pathlib
       _models_dir = pathlib.Path(__file__).resolve().parent.parent / "models"
       if _models_dir.exists():
           for mi in pkgutil.iter_modules([str(_models_dir)]):
               if not mi.name.startswith("_"):
                   importlib.import_module(f"app.models.{mi.name}")
       ```

    7. `backend/app/deps/db.py` — RESEARCH.md Pattern 1 `get_db` async generator.

    8. `backend/app/deps/redis.py`:
       ```python
       from typing import AsyncGenerator
       from redis.asyncio import Redis, from_url
       from app.core.config import settings
       async def get_redis() -> AsyncGenerator[Redis, None]:
           client = from_url(settings.REDIS_URL, decode_responses=True)
           try:
               yield client
           finally:
               await client.aclose()
       ```

    9. `backend/alembic.ini` — standard scaffold. `sqlalchemy.url` left blank (env.py reads from settings). `script_location = alembic`. `file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s` (timestamped revision filenames so Plan 05 and Plan 06 cannot collide on the same revision id).

    10. `backend/alembic/env.py` — async-aware Alembic env. Imports `Base` from `app.db.base` (which auto-imports models). Uses `settings.SQLALCHEMY_DATABASE_URL`. `run_migrations_online` uses `connection.run_sync(...)` to satisfy Alembic's sync API on top of async engine.

    11. `backend/alembic/script.py.mako` — stock Alembic template.

    12. `backend/alembic/versions/.gitkeep` — empty file so the dir is tracked. Migrations are added by Plans 05 and 06.

    13. **Wave-0 dependency install + smoke** (after files are written):
        ```bash
        cd backend
        python -m pip install -e ".[dev]"
        pytest --collect-only
        ```
        The `-e .[dev]` install puts `pytest`, `pytest-asyncio`, `httpx`, etc. on the venv. `pytest --collect-only` will currently find zero tests (the test files are added in Task 3) — that's the expected smoke output. The point is: `pytest` resolves and the project package is importable.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        if (-not (Test-Path 'backend/pyproject.toml')) { exit 1 };
        $p = Get-Content 'backend/pyproject.toml' -Raw;
        foreach ($pkg in 'fastapi==0.136.1','sqlalchemy\[asyncio\]==2.0.49','alembic==1.18.4','python-jose\[cryptography\]==3.5.0','passlib\[bcrypt\]==1.7.4','bcrypt==5.0.0','pydantic-settings==2.14.1','pytest==9.0.3','pytest-asyncio==1.3.0','httpx==0.28.1') {
          if ($p -notmatch [regex]::Escape($pkg) -and $p -notmatch $pkg) { Write-Output ('missing pin: ' + $pkg); exit 2 }
        };
        if ($p -notmatch 'optional-dependencies\][\s\S]*?dev\s*=') { Write-Output 'missing [dev] extras'; exit 3 };
        if ((Get-Content 'backend/app/db/session.py' -Raw) -notmatch 'expire_on_commit=False') { exit 4 };
        if ((Get-Content 'backend/app/db/base.py' -Raw) -notmatch 'pkgutil') { exit 5 };
        if ((Get-Content 'backend/alembic.ini' -Raw) -notmatch 'file_template') { exit 6 };
        # Wave-0 dep install + smoke (B-06): real pytest must resolve
        Push-Location backend
        python -m pip install -e '.[dev]' --quiet 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Output 'pip install failed'; exit 7 };
        python -m pytest --collect-only 2>&1 | Out-String | Write-Output
        # Exit 5 from pytest = no tests collected; that's expected at Task 1 (tests added in Task 3)
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 5) { Pop-Location; Write-Output 'pytest --collect-only crashed'; exit 8 };
        Pop-Location
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    pyproject.toml pins match RESEARCH.md verified versions and includes `[dev]` extras (pytest, pytest-asyncio, httpx); `pip install -e .[dev]` succeeds; `pytest --collect-only` resolves cleanly; expire_on_commit=False present; auto-import scaffolds in base.py + (Task 2) routers/__init__.py; Alembic timestamp-prefixed revision filenames configured.
  </done>
</task>

<task type="auto">
  <name>Task 2: FastAPI app + auto-router + /health family endpoints (public + admin-detail + metrics)</name>
  <files>
    backend/app/main.py,
    backend/app/routers/__init__.py,
    backend/app/routers/health.py,
    backend/app/deps/metrics_admin.py,
    backend/app/models/__init__.py,
    backend/app/schemas/__init__.py
  </files>
  <action>
    1. `backend/app/main.py`:
       ```python
       import time
       from contextlib import asynccontextmanager
       from fastapi import FastAPI
       from app import __version__
       from app.core.config import settings
       from app.core.logging import configure_logging, get_logger
       from app.routers import api_router

       configure_logging(debug=settings.DEBUG)
       log = get_logger("pulse.main")

       @asynccontextmanager
       async def lifespan(app: FastAPI):
           app.state.startup_ts = time.time()
           log.info("startup", version=__version__)
           yield
           log.info("shutdown")

       app = FastAPI(
           title="PULSE — Performance & Unit Live Scoring Engine",
           version=__version__,
           docs_url="/api/v1/docs",
           redoc_url="/api/v1/redoc",
           openapi_url="/api/v1/openapi.json",
           lifespan=lifespan,
       )
       app.include_router(api_router)
       ```

    2. `backend/app/routers/__init__.py` — auto-include every sibling router (interface from `<context>`). Use absolute imports under `app.routers.*`. Skip dunder modules; skip submodules without a `router` attribute. Log inclusion at INFO.

    3. `backend/app/deps/metrics_admin.py` — placeholder admin gate that Plan 05 will replace. Per CONTEXT.md API W-02 fix, `/health/detail` and `/metrics` must be admin-only. Until Plan 05 ships `require_role`, this placeholder rejects all requests with 401 (the endpoints exist in OpenAPI but cannot be called):
       ```python
       from fastapi import HTTPException, status, Header

       async def metrics_admin_dep(authorization: str | None = Header(default=None)):
           # Plan 05 replaces this implementation with require_role("super_admin", "admin_unit").
           # Pre-Plan-05, deny all to keep the surface area locked down.
           raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Admin auth required (Plan 05 wires require_role)")
       ```
       Plan 05 will modify ONLY this file to:
       ```python
       from app.deps.auth import require_role
       metrics_admin_dep = require_role("super_admin", "admin_unit")
       ```
       Health endpoints import this name and don't change.

    4. `backend/app/routers/health.py` — three endpoints (W-02):
       ```python
       import asyncio, time
       from fastapi import APIRouter, Depends, Request, Response
       from sqlalchemy import text
       from sqlalchemy.ext.asyncio import AsyncSession
       from redis.asyncio import Redis
       from app.deps.db import get_db
       from app.deps.redis import get_redis
       from app.deps.metrics_admin import metrics_admin_dep
       from app import __version__

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
       async def health(db: AsyncSession = Depends(get_db), r: Redis = Depends(get_redis)):
           db_s, _ = await _ping_db(db)
           redis_s, _, _ = await _ping_redis(r)
           status = "ok" if db_s == "ok" and redis_s == "ok" else "degraded"
           return {"status": status, "db": db_s, "redis": redis_s, "version": __version__}

       @router.get(
           "/health/detail",
           summary="Detailed health probe (admin-only — W-02)",
           dependencies=[Depends(metrics_admin_dep)],
       )
       async def health_detail(
           request: Request,
           db: AsyncSession = Depends(get_db),
           r: Redis = Depends(get_redis),
       ):
           (db_s, db_ms), (redis_s, redis_ms, redis_mem) = await asyncio.gather(_ping_db(db), _ping_redis(r))
           uptime_s = max(0.0, time.time() - getattr(request.app.state, "startup_ts", time.time()))
           overall = "ok" if db_s == "ok" and redis_s == "ok" else "degraded"
           return {
               "status": overall,
               "db":    {"ok": db_s == "ok",    "latency_ms": round(db_ms, 2)},
               "redis": {"ok": redis_s == "ok", "latency_ms": round(redis_ms, 2), "used_memory": redis_mem},
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
       ):
           (db_s, db_ms), (redis_s, redis_ms, _) = await asyncio.gather(_ping_db(db), _ping_redis(r))
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
       ```

    5. `backend/app/models/__init__.py`, `backend/app/schemas/__init__.py` — empty `__init__.py` files so the packages exist for auto-discovery and IDE awareness.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $main = Get-Content 'backend/app/main.py' -Raw;
        if ($main -notmatch '/api/v1/docs')   { exit 1 };
        if ($main -notmatch 'include_router') { exit 2 };
        if ($main -notmatch 'startup_ts')     { exit 3 };
        $h = Get-Content 'backend/app/routers/health.py' -Raw;
        if ($h -notmatch '/health/detail')    { exit 4 };
        if ($h -notmatch '/metrics')          { exit 5 };
        if ($h -notmatch 'metrics_admin_dep') { exit 6 };
        if ($h -notmatch 'asyncio\.gather')   { exit 7 };
        $r = Get-Content 'backend/app/routers/__init__.py' -Raw;
        if ($r -notmatch 'pkgutil')           { exit 8 };
        if ($r -notmatch 'prefix=.+api/v1')   { exit 9 };
        $m = Get-Content 'backend/app/deps/metrics_admin.py' -Raw;
        if ($m -notmatch 'metrics_admin_dep') { exit 10 };
        # Real import smoke (B-06): no ast.parse fakes
        Push-Location backend
        python -c 'from app.main import app; print(app.title)' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit 11 };
        # Confirm routes registered
        python -c 'from app.routers import api_router; paths = sorted(r.path for r in api_router.routes); print(paths); assert \"/api/v1/health\" in paths; assert \"/api/v1/health/detail\" in paths; assert \"/api/v1/metrics\" in paths' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit 12 };
        Pop-Location
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    FastAPI app exposes `/api/v1/docs`, `/api/v1/health`, `/api/v1/health/detail` (admin-gated via metrics_admin_dep placeholder), and `/api/v1/metrics` (admin-gated, Prometheus text format); routers auto-include works (no edits needed for Plans 05/06); Plan 05 will swap the placeholder dep for `require_role("super_admin","admin_unit")` without touching health.py.
  </done>
</task>

<task type="auto">
  <name>Task 3: Test scaffolds + no-upload contract test + initial Alembic revision (executable pytest verify)</name>
  <files>
    backend/tests/__init__.py,
    backend/tests/conftest.py,
    backend/tests/test_health.py,
    backend/tests/test_no_upload_policy.py,
    backend/tests/test_bootstrap.py,
    backend/alembic/versions/20260511_120000_0001_baseline.py
  </files>
  <action>
    1. `backend/tests/__init__.py` — empty.

    2. `backend/tests/conftest.py` — async TestClient + transactional db fixture:
       ```python
       import asyncio, os
       import pytest
       import pytest_asyncio
       from httpx import AsyncClient, ASGITransport
       from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
       from app.main import app

       @pytest.fixture(scope="session")
       def event_loop():
           loop = asyncio.new_event_loop()
           yield loop
           loop.close()

       @pytest_asyncio.fixture
       async def client():
           async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
               yield c

       @pytest_asyncio.fixture
       async def db_session() -> AsyncSession:
           # Transactional fixture: every test runs inside a SAVEPOINT and rolls back.
           # Lazy-import engine to avoid forcing a DB connection during pytest --collect-only.
           from app.db.session import engine as _engine
           async with _engine.connect() as conn:
               trans = await conn.begin()
               Session = async_sessionmaker(bind=conn, expire_on_commit=False)
               async with Session() as s:
                   try:
                       yield s
                   finally:
                       await trans.rollback()
       ```

    3. `backend/tests/test_health.py`:
       ```python
       import pytest

       @pytest.mark.asyncio
       async def test_health_shape(client):
           # Smoke: shape of payload; db/redis may be "down" if compose is not running — that's ok for unit suite
           r = await client.get("/api/v1/health")
           assert r.status_code == 200
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
       ```

    4. `backend/tests/test_no_upload_policy.py` — RESEARCH.md verbatim, with note that the allow-list `/api/v1/konkin/templates/{template_id}/import-from-excel` doesn't exist yet (Plan 06 adds it); during Wave 2, the test asserts the multipart count is **zero**; in Wave 4, Plan 06 amends the assertion to exactly the allow-list. Implement the strict-asserted version now (count == 0) and document the Plan 06 amendment in code comments:
       ```python
       from app.main import app

       # Phase 1 contract: ZERO multipart endpoints in Wave 2.
       # Plan 06 will add /api/v1/konkin/templates/{template_id}/import-from-excel AND update
       # ALLOWED_MULTIPART_PATHS in this test to {that path}.
       ALLOWED_MULTIPART_PATHS: set[str] = set()

       def _multipart_paths():
           schema = app.openapi()
           paths = set()
           for path, methods in schema["paths"].items():
               for verb, op in methods.items():
                   if verb.startswith("x-"): continue
                   body = op.get("requestBody") or {}
                   content = body.get("content") or {}
                   if "multipart/form-data" in content:
                       paths.add(path)
           return paths

       def test_only_allowed_multipart_endpoints():
           got = _multipart_paths()
           extras = got - ALLOWED_MULTIPART_PATHS
           missing = ALLOWED_MULTIPART_PATHS - got
           assert not extras, f"Unexpected multipart endpoints: {extras}"
           assert not missing, f"Expected multipart endpoints not present: {missing}"

       def test_link_eviden_is_url_only():
           schema = app.openapi()
           offenders = []
           for name, s in (schema.get("components", {}).get("schemas") or {}).items():
               for prop, spec in (s.get("properties") or {}).items():
                   if prop == "link_eviden" and spec.get("format") != "uri":
                       offenders.append(f"{name}.{prop}")
           assert not offenders, f"link_eviden must be format=uri (Pydantic HttpUrl): {offenders}"
       ```

    5. `backend/tests/test_bootstrap.py`:
       ```python
       def test_app_imports():
           # Catches circular imports, missing settings, syntax errors before the container builds.
           from app.main import app
           assert app.title.startswith("PULSE")

       def test_router_auto_include():
           from app.routers import api_router
           prefixed = {r.path for r in api_router.routes}
           assert "/api/v1/health" in prefixed, f"got {prefixed}"
           assert "/api/v1/health/detail" in prefixed
           assert "/api/v1/metrics" in prefixed
       ```

    6. `backend/alembic/versions/20260511_120000_0001_baseline.py` — baseline empty revision so Plan 05/06 can `--autogenerate` against `down_revision=None` properly:
       ```python
       """baseline

       Revision ID: 0001_baseline
       Revises:
       Create Date: 2026-05-11 12:00:00
       """
       from alembic import op  # noqa
       import sqlalchemy as sa  # noqa
       revision = "0001_baseline"
       down_revision = None
       branch_labels = None
       depends_on = None
       def upgrade() -> None: pass
       def downgrade() -> None: pass
       ```
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $tnu = Get-Content 'backend/tests/test_no_upload_policy.py' -Raw;
        if ($tnu -notmatch 'ALLOWED_MULTIPART_PATHS') { exit 1 };
        if (-not (Test-Path 'backend/alembic/versions/20260511_120000_0001_baseline.py')) { exit 2 };
        # B-06 fix: actually run pytest against the bootstrap + health + no-upload + (db-less) tests.
        # Tests that need a DB/Redis are async-marked and gated by httpx ASGITransport (no real network).
        Push-Location backend
        python -m pytest tests/test_bootstrap.py tests/test_no_upload_policy.py -x -q 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Output 'pytest failed'; exit 3 };
        # Health tests rely on a get_db / get_redis stub; they are runnable via ASGITransport because the dependencies
        # only fail when actually hitting the DB. The `degraded` branch is acceptable in unit mode (test_health_shape allows it).
        # If db/redis aren't available locally and the dependency raises before the route runs, the test will fail with 500.
        # We mark the health tests as best-effort here and rely on the container e2e in Plan 07's checkpoint for full coverage.
        python -m pytest tests/test_health.py -x -q --tb=short 2>&1 | Out-String | Write-Output
        # Permit failure if db unreachable (LASTEXITCODE 1) — but the bootstrap + no-upload tests above MUST pass.
        Pop-Location
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    Bootstrap, no-upload, and health-gating tests run via real `pytest` (not ast.parse); baseline Alembic revision exists; no-upload test starts strict (empty allow-list — Plan 06 amends to a single-entry set); conftest defines `client` and `db_session` fixtures usable by Plans 05/06; admin-gated `/health/detail` and `/metrics` return 401 pre-Plan-05.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Untrusted JSON body → FastAPI route | Crosses into backend |
| Backend → Postgres / Redis | Internal pulse-net |
| Container env → process env | Secrets injected via .env at compose start |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-03-T-01 | Tampering | Multipart upload introduced by accident in later phase | mitigate | `tests/test_no_upload_policy.py` enforced via pytest gate; CI failure on any new multipart endpoint outside allow-list (REQ-no-evidence-upload). |
| T-03-I-01 | Information disclosure | Secrets in logs | mitigate | structlog JSON; settings.JWT_SECRET_KEY is `SecretStr` (Pydantic redacts on repr); no plaintext log of payload bodies. |
| T-03-I-02 | Information disclosure | `/health/detail` reveals internal state to anonymous probe | mitigate | `metrics_admin_dep` placeholder rejects 401 in Plan 03; Plan 05 swaps for `require_role("super_admin","admin_unit")` (W-02). |
| T-03-I-03 | Information disclosure | `/metrics` exposes Prometheus internals to anonymous probe | mitigate | Same admin gate as `/health/detail` (W-02). |
| T-03-D-01 | DoS | Sync DB call in async handler blocks event loop | mitigate | Every db access goes through `AsyncSession` via `get_db`; ruff lint flags `sqlalchemy.orm.Session` (sync) imports in async routers. |
| T-03-D-02 | DoS | Health check hangs waiting on dead Redis | mitigate | `asyncio.wait_for(..., timeout=2.0)` on both probes (RESEARCH.md health code example). |
| T-03-E-01 | Elevation | Privileged endpoint added without role gate | mitigate | Plan 05 introduces `require_role`; this plan introduces convention `dependencies=[Depends(require_role(...))]` documented in routers/__init__.py header. |
</threat_model>

<verification>
- `python -c "from app.main import app; print(app.title)"` prints `PULSE — ...`
- `pytest tests/test_bootstrap.py tests/test_no_upload_policy.py -x` passes locally (real pytest run — B-06)
- `alembic upgrade head` (in container, Plan 07) succeeds
- `/api/v1/health` returns `{status, db, redis, version}` shape (Plan 07 e2e)
- `/api/v1/health/detail` and `/api/v1/metrics` return 401 anonymously; will return 200 to admin tokens after Plan 05 swaps the placeholder dep (W-02)
</verification>

<success_criteria>
- All file paths in `files_modified` exist
- pyproject pins match RESEARCH.md HIGH-confidence verified versions exactly AND ship `[dev]` extras
- Wave-0 dep install + `pytest --collect-only` smoke passes (B-06)
- expire_on_commit=False present (Pitfall #4)
- Health, health/detail, and metrics endpoints all in OpenAPI; admin-gating via `metrics_admin_dep` placeholder
- Multipart contract test exists and starts at empty allow-list
- Router and model auto-discovery work — Plans 05/06 can drop in files with no edits to base.py / main.py / routers/__init__.py
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation-master-data-auth/01-03-SUMMARY.md` listing:
1. Final pyproject pinned-version table (incl. [dev] extras)
2. Auto-discovery contract for routers and models (the snippets above, finalized)
3. Health endpoint family table (path, gate, response shape)
4. Test scaffold map (which test file covers which REQ-)
5. Notes for Plan 05: how to swap `metrics_admin_dep` for `require_role(...)` without touching health.py
</output>
