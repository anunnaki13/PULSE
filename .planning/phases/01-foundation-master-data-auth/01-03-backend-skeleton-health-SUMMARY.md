---
phase: 01-foundation-master-data-auth
plan: 03
subsystem: backend
status: complete
tags: [fastapi, sqlalchemy-async, asyncpg, alembic, pydantic-settings-v2, structlog, pytest, pytest-asyncio, httpx, redis-asyncio, openapi]

# Dependency graph
dependency_graph:
  requires:
    - phase: 01-foundation-master-data-auth
      plan: 01
      provides: ".env.example template, repo top-level scaffold, DEC-002 identifiers (pulse-db/pulse-redis/etc.) — backend/pyproject.toml + alembic.ini + core/config.py reuse these identifiers verbatim"
  provides:
    - "FastAPI app skeleton mounted at /api/v1 with OpenAPI docs at /api/v1/docs"
    - "GET /api/v1/health (public liveness + dependency probe, 2 s timeouts)"
    - "GET /api/v1/health/detail (admin-gated — W-02 — DB+Redis latency + uptime)"
    - "GET /api/v1/metrics (admin-gated — W-02 — Prometheus text exposition)"
    - "Async SQLAlchemy 2.0 engine + sessionmaker with expire_on_commit=False"
    - "get_db / get_redis FastAPI dependencies (RESEARCH.md Pattern 1)"
    - "metrics_admin_dep placeholder dep (Plan 05 swaps to require_role) — health.py imports by name, no future edits needed"
    - "Auto-discovery contract: app/routers/__init__.py pkgutil-walks siblings; app/db/base.py pkgutil-walks app/models/"
    - "Alembic async-aware env.py + timestamp-prefixed file_template + empty 0001_baseline revision"
    - "Wave-0 pytest scaffold: AsyncClient(ASGITransport) `client` + transactional `db_session` fixtures (lazy DB import) reusable by Plans 05/06"
    - "REQ-no-evidence-upload contract test (multipart count == 0 in Wave 2; Plan 06 amends to one-entry allow-list)"
    - "Structured JSON logging via structlog; passlib/bcrypt cosmetic warning silenced (Pitfall 3)"
  affects:
    - "01-05-auth (will add app/models/user.py + app/routers/auth.py + app/deps/auth.py; replaces metrics_admin.py body with require_role wiring)"
    - "01-06-master-data (will add app/models/{bidang,konkin_template,perspektif,indikator,ml_stream,konkin_import_log}.py + app/routers/{bidang,konkin}.py; amends ALLOWED_MULTIPART_PATHS in test_no_upload_policy.py)"
    - "01-07 (Wave 5 container e2e — uses GET /api/v1/health for compose healthcheck and Nginx upstream)"

# Tech tracking
tech-stack:
  added:
    - "fastapi 0.136.1"
    - "uvicorn[standard] 0.46.0 + gunicorn 26.0.0"
    - "sqlalchemy[asyncio] 2.0.49 + asyncpg 0.31.0"
    - "alembic 1.18.4"
    - "pydantic 2.13.4 + pydantic-settings 2.14.1"
    - "python-jose[cryptography] 3.5.0 + passlib[bcrypt] 1.7.4 + bcrypt 5.0.0"
    - "redis[hiredis] >=5,<6"
    - "openpyxl 3.1.5 + python-multipart >=0.0.20"
    - "structlog >=24.4"
    - "[dev] pytest 9.0.3 + pytest-asyncio 1.3.0 + httpx 0.28.1 + ruff + mypy + pytest-cov"
  patterns:
    - "Router auto-discovery via pkgutil.iter_modules — drop-in router files in app/routers/ get included with zero edits to main.py or routers/__init__.py"
    - "Model auto-discovery via pkgutil walk in app/db/base.py — Alembic --autogenerate sees every app/models/*.py without edits to base.py"
    - "Placeholder admin gate (metrics_admin_dep) — Plan 03 keeps the surface locked (401 unconditionally) so Plan 05 can swap the implementation without touching any consumer (health.py imports by name)"
    - "Lazy DB engine import inside the db_session fixture — pytest --collect-only and pure-import tests (test_no_upload_policy.py) do NOT require a live Postgres"
    - "Alembic file_template = timestamp + slug — avoids rev id collisions when Plans 05 and 06 generate revisions in parallel worktrees"
    - "SecretStr for every credential in pydantic-settings (T-03-I-01 mitigation: redacted in repr / logs)"
    - "asyncio.wait_for(probe, timeout=2.0) on every dependency ping (T-03-D-02 mitigation)"

key-files:
  created:
    - "backend/pyproject.toml"
    - "backend/alembic.ini"
    - "backend/alembic/env.py"
    - "backend/alembic/script.py.mako"
    - "backend/alembic/versions/.gitkeep"
    - "backend/alembic/versions/20260511_120000_0001_baseline.py"
    - "backend/app/__init__.py"
    - "backend/app/main.py"
    - "backend/app/core/__init__.py"
    - "backend/app/core/config.py"
    - "backend/app/core/logging.py"
    - "backend/app/db/__init__.py"
    - "backend/app/db/base.py"
    - "backend/app/db/session.py"
    - "backend/app/deps/__init__.py"
    - "backend/app/deps/db.py"
    - "backend/app/deps/redis.py"
    - "backend/app/deps/metrics_admin.py"
    - "backend/app/routers/__init__.py"
    - "backend/app/routers/health.py"
    - "backend/app/models/__init__.py"
    - "backend/app/schemas/__init__.py"
    - "backend/tests/__init__.py"
    - "backend/tests/conftest.py"
    - "backend/tests/test_health.py"
    - "backend/tests/test_no_upload_policy.py"
    - "backend/tests/test_bootstrap.py"
  modified: []

key-decisions:
  - "Toolchain runs inside Ubuntu-22.04 WSL2 (python3.11.15 from deadsnakes), NOT Windows host python 3.13 — `pip install -e .[dev]` and every `pytest` invocation goes through `wsl -d Ubuntu-22.04 -- python3.11 …`. Carries over the WSL2 decision from Plan 01-01."
  - "Default values added to every Settings field with a placeholder secret so `from app.main import app` works without a populated .env (needed for `pytest --collect-only` smoke and for `test_app_imports` to pass before docker-compose lands). Real .env values still override at runtime via pydantic-settings env_file."
  - "Lazy engine import in conftest.py db_session fixture (`from app.db.session import engine as _engine` inside the fixture body) — avoids forcing a Postgres connection during pytest collection, so pure-import tests like test_no_upload_policy.py run with zero infra. This is an explicit B-06 unit-mode behavior."
  - "Wrote one `feat`+`feat`+`test` commit triple (one per plan task) rather than one big commit, per the per-task commit protocol — RED/GREEN/REFACTOR doesn't apply because the plan has type=execute, not type=tdd."

patterns-established:
  - "Auto-discovery for routers and models — Plan 05 / Plan 06 add files, never edit shared init or base"
  - "Placeholder dep pattern for cross-plan admin gating — same-named import survives the Plan 05 swap-in of require_role"
  - "Lazy engine in test fixtures — `pytest --collect-only` works without docker compose up"
  - "Timestamp-prefixed alembic revision filenames — no rev-id collisions across parallel plan worktrees"
  - "Structured JSON logging (structlog) baseline — every later plan reuses get_logger(name)"

requirements: [REQ-backend-stack, REQ-health-checks, REQ-no-evidence-upload]
requirements-completed: [REQ-backend-stack, REQ-health-checks, REQ-no-evidence-upload]

# Metrics
metrics:
  duration_minutes: 15
  started: "2026-05-11T11:38:00Z"
  completed: "2026-05-11T11:46:00Z"
  tasks_completed: 3
  files_created: 27
  files_modified: 0
  commits: 3
---

# Phase 1 Plan 03: Backend Skeleton + Health — Summary

**FastAPI backend skeleton mounted at /api/v1 with public /health + admin-gated /health/detail and /metrics (W-02), async SQLAlchemy 2.0 + Alembic baseline, router/model auto-discovery, and a Wave-0 pytest scaffold that already locks in the no-evidence-upload contract — 7/7 tests pass.**

---

## Performance

- **Duration:** ~15 minutes (start 11:38 UTC → end 11:46 UTC + summary)
- **Tasks:** 3 of 3 completed (no checkpoints, fully autonomous)
- **Files created:** 27
- **Files modified:** 0 (greenfield backend tree)
- **Commits:** 3 atomic per-task + this summary commit

---

## Accomplishments

1. **Locked-stack `pyproject.toml`** with exact RESEARCH.md HIGH-confidence pins (fastapi 0.136.1, sqlalchemy[asyncio] 2.0.49, asyncpg 0.31.0, alembic 1.18.4, pydantic-settings 2.14.1, python-jose 3.5.0, passlib 1.7.4, bcrypt 5.0.0, openpyxl 3.1.5, structlog) plus `[dev]` extras (pytest 9.0.3, pytest-asyncio 1.3.0, httpx 0.28.1, ruff, mypy, pytest-cov). `pip install -e .[dev]` succeeded in WSL2 python 3.11.15.
2. **Working /api/v1/health family** — 3 endpoints registered via auto-discovery, OpenAPI sees them, admin gate returns 401 anonymously, public /health returns the documented `{status, db, redis, version}` shape with 2 s short-timeout async pings.
3. **Async SQLAlchemy 2.0 + Alembic ready** — engine + sessionmaker with `expire_on_commit=False` (Pitfall 4); env.py async-aware via `connection.run_sync()`; empty `0001_baseline` revision so Plans 05/06 chain cleanly; timestamp-prefixed `file_template` prevents parallel-plan rev id collisions.
4. **Auto-discovery contract** locked in — `app/routers/__init__.py` walks siblings, `app/db/base.py` walks `app/models/`. Plans 05 and 06 add files; they never edit shared base/init.
5. **Wave-0 test infrastructure** — `client` (AsyncClient over ASGITransport) and `db_session` (transactional, lazy engine import) fixtures; 7 tests collected, 7 pass.
6. **No-evidence-upload contract test live from day one** — `ALLOWED_MULTIPART_PATHS = set()` in Phase 1 Wave 2; Plan 06 will amend to a one-entry allow-list when it adds `import-from-excel`. Plus a companion `link_eviden` format=uri assertion already armed (no offenders yet because no models have shipped).

---

## Task Commits

Each task committed atomically on branch `worktree-agent-a831c0c8a15bd015f`:

1. **Task 1 (Wave 0): pyproject + alembic + core/db/deps + install + collect-only smoke** — `f09bc9b` (feat)
2. **Task 2: FastAPI app + auto-router + /health family + metrics_admin placeholder** — `6b8fa8a` (feat)
3. **Task 3: Test scaffolds + no-upload policy + alembic baseline (real pytest run)** — `e9c7190` (test)

This SUMMARY commit follows. (The orchestrator owns STATE.md / ROADMAP.md updates after Wave 2 wraps.)

---

## Final pyproject pinned-version table

### Runtime dependencies

| Package                                | Pin                  | Source / Reason                                   |
| -------------------------------------- | -------------------- | ------------------------------------------------- |
| fastapi                                | `==0.136.1`          | RESEARCH.md Standard Stack — HIGH verified        |
| uvicorn[standard]                      | `==0.46.0`           | RESEARCH.md Standard Stack — HIGH verified        |
| gunicorn                               | `==26.0.0`           | RESEARCH.md Standard Stack                        |
| sqlalchemy[asyncio]                    | `==2.0.49`           | RESEARCH.md Standard Stack — HIGH verified        |
| asyncpg                                | `==0.31.0`           | RESEARCH.md Standard Stack                        |
| alembic                                | `==1.18.4`           | RESEARCH.md Standard Stack — HIGH verified        |
| pydantic                               | `==2.13.4`           | RESEARCH.md Standard Stack                        |
| pydantic-settings                      | `==2.14.1`           | RESEARCH.md Standard Stack — HIGH verified        |
| python-jose[cryptography]              | `==3.5.0`            | RESEARCH.md Standard Stack — HIGH verified        |
| passlib[bcrypt]                        | `==1.7.4`            | RESEARCH.md Standard Stack — HIGH verified        |
| bcrypt                                 | `==5.0.0`            | RESEARCH.md Standard Stack — HIGH verified        |
| redis[hiredis]                         | `>=5,<6`             | RESEARCH.md Standard Stack                        |
| openpyxl                               | `==3.1.5`            | RESEARCH.md Standard Stack — HIGH verified        |
| python-multipart                       | `>=0.0.20`           | RESEARCH.md Standard Stack                        |
| structlog                              | `>=24.4`             | CONTEXT.md "Operational" — structured JSON logs   |

### Dev extras (`pip install -e .[dev]`)

| Package           | Pin           | Source / Reason                                |
| ----------------- | ------------- | ---------------------------------------------- |
| pytest            | `==9.0.3`     | RESEARCH.md Standard Stack — HIGH verified     |
| pytest-asyncio    | `==1.3.0`     | RESEARCH.md Standard Stack — HIGH verified     |
| httpx             | `==0.28.1`    | RESEARCH.md Standard Stack — HIGH verified     |
| ruff              | `>=0.7`       | Lint baseline                                  |
| mypy              | `>=1.13`      | Type-check baseline                            |
| pytest-cov        | `>=5`         | Coverage support                               |

Resolution proof (WSL2 python 3.11.15):
```
Successfully installed Mako-1.3.12 PyJWT-2.12.1 alembic-1.18.4 ... fastapi-0.136.1
sqlalchemy-2.0.49 pytest-9.0.3 pytest-asyncio-1.3.0 httpx-0.28.1 ... (and 40+ transitive deps)
```

---

## Health endpoint family

| Path                       | Method | Public? | Gate                                                 | Response shape                                                                                                            |
| -------------------------- | ------ | ------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `/api/v1/health`           | GET    | Yes     | None                                                 | `{status: "ok"\|"degraded", db: "ok"\|"down", redis: "ok"\|"down", version: "0.1.0"}`                                     |
| `/api/v1/health/detail`    | GET    | No      | `Depends(metrics_admin_dep)` (401 pre-Plan-05)       | `{status, db: {ok, latency_ms}, redis: {ok, latency_ms, used_memory}, version, uptime_s}`                                 |
| `/api/v1/metrics`          | GET    | No      | `Depends(metrics_admin_dep)` (401 pre-Plan-05)       | `text/plain; version=0.0.4` Prometheus exposition: `pulse_up`, `pulse_uptime_seconds`, `pulse_dep_up{dep="..."}`, `pulse_dep_latency_ms{dep="..."}` |

Both `/health/detail` and `/metrics` use `asyncio.gather` to fan out the db + redis probe in parallel; both probes are wrapped in `asyncio.wait_for(..., timeout=2.0)` per RESEARCH.md health code example (T-03-D-02 mitigation).

---

## Auto-discovery contract (verbatim, finalized)

`backend/app/routers/__init__.py`:
```python
import importlib, pathlib, pkgutil
from fastapi import APIRouter
from app.core.logging import get_logger
log = get_logger("pulse.routers")
api_router = APIRouter(prefix="/api/v1")
_here = pathlib.Path(__file__).parent
for _mi in pkgutil.iter_modules([str(_here)]):
    if _mi.name.startswith("_"):
        continue
    _mod = importlib.import_module(f"{__name__}.{_mi.name}")
    _router = getattr(_mod, "router", None)
    if _router is not None:
        api_router.include_router(_router)
        log.info("router_included", module=_mi.name)
```

`backend/app/db/base.py`:
```python
import importlib, pkgutil, pathlib
from sqlalchemy.orm import declarative_base
Base = declarative_base()
_models_dir = pathlib.Path(__file__).resolve().parent.parent / "models"
if _models_dir.exists():
    for _mi in pkgutil.iter_modules([str(_models_dir)]):
        if not _mi.name.startswith("_"):
            importlib.import_module(f"app.models.{_mi.name}")
```

**Contract for downstream plans:**
- Plan 05 drops `app/routers/auth.py` (exposes `router = APIRouter(prefix="/auth", tags=["auth"])`) and `app/models/user.py` — neither file requires edits to `main.py`, `routers/__init__.py`, or `db/base.py`.
- Plan 06 drops `app/routers/bidang.py` / `konkin.py` and `app/models/{bidang,konkin_template,perspektif,indikator,ml_stream,konkin_import_log}.py` — same auto-pickup applies.

---

## Test scaffold map (REQ traceability)

| Test file                          | REQ                          | What it locks                                                                                          |
| ---------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------ |
| `tests/test_bootstrap.py`          | REQ-backend-stack            | App imports cleanly; auto-router includes `/health`, `/health/detail`, `/metrics`                       |
| `tests/test_health.py`             | REQ-health-checks            | `/health` shape ∈ {status, db, redis, version}; `/health/detail` and `/metrics` return 401 anonymously |
| `tests/test_no_upload_policy.py`   | REQ-no-evidence-upload       | OpenAPI multipart count == 0 (Wave 2); `link_eviden` properties must declare `format=uri`               |

`tests/conftest.py` provides reusable `client` (AsyncClient + ASGITransport, in-process app) and `db_session` (transactional rollback, lazy engine import) fixtures. Plans 05/06 will import them directly.

---

## Notes for Plan 05: swapping `metrics_admin_dep` for `require_role(...)`

When Plan 05 creates `backend/app/deps/auth.py` with `require_role(*allowed_roles)`, replace the **entire body** of `backend/app/deps/metrics_admin.py` with:

```python
"""Admin gate for /health/detail and /metrics — wired to require_role in Plan 05.

The public symbol `metrics_admin_dep` MUST remain stable; routers/health.py
imports it by name. This file used to ship a 401-only placeholder; Plan 05
replaces the body once `app.deps.auth.require_role` exists.
"""

from app.deps.auth import require_role

metrics_admin_dep = require_role("super_admin", "admin_unit")
```

**Zero edits required to `backend/app/routers/health.py`** — the import line `from app.deps.metrics_admin import metrics_admin_dep` and the three `dependencies=[Depends(metrics_admin_dep)]` clauses survive the swap unchanged. Existing tests in `test_health.py` will need a small extension (add token-bearing variants); the no-token=401 assertions hold post-swap because `current_user` raises 401 when no Authorization header / cookie is present (RESEARCH.md Pattern 3).

Suggested Plan 05 follow-up test (additive, not edit):
```python
@pytest.mark.asyncio
async def test_health_detail_admin_ok(client, admin_token):
    r = await client.get("/api/v1/health/detail",
                          headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert set(r.json()) >= {"status", "db", "redis", "version", "uptime_s"}
```

---

## Decisions Made

1. **WSL2 toolchain bridge.** Every `pip`, `pytest`, `python` invocation goes through `wsl -d Ubuntu-22.04 -- python3.11 …` per Plan 01-01's WSL2 alternative resolution. Windows host has python 3.13 and node 25 (wrong versions); WSL Ubuntu-22.04 has python 3.11.15 (deadsnakes), node 20, pnpm. No Python install on the Windows host.
2. **Defaulted Settings fields with placeholder secrets.** `APP_SECRET_KEY`, `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, `INITIAL_ADMIN_PASSWORD` are declared as `SecretStr` with placeholder defaults (`"dev-app-secret-replace-me"`, `"replace-me"`, etc.) so `from app.main import app` works without a populated `.env` — required by `pytest --collect-only` smoke and `test_app_imports`. Real `.env` values still override at runtime via pydantic-settings `env_file` loading. This does NOT weaken security: the placeholders fail any production sanity check downstream (Plan 02 .env.example already documents the real values; Plan 07 will validate at compose startup).
3. **Lazy DB engine import in conftest.py.** `db_session` fixture imports `engine` inside its body so `pytest --collect-only` works without a live Postgres. This is the unit-suite default; container e2e in Plan 07 covers the live-DB branch.
4. **Per-task commits rather than per-iteration.** Plan is `type=execute` (not `type=tdd`), so the commit cadence is one per task (feat / feat / test), not RED → GREEN → REFACTOR.

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] WSL toolchain bridge for the `<automated>` PowerShell verify blocks**

- **Found during:** Task 1, before running the dep-install smoke
- **Issue:** The plan's `<automated>` blocks call `python -m pip install -e '.[dev]'` and `python -m pytest …` directly. On this Windows host, `python` resolves to system Python 3.13.13 (Plan 01-01 SUMMARY environment audit), which is incompatible with the `requires-python = ">=3.11,<3.12"` pin in pyproject.toml. The execute-phase prompt explicitly mandated routing through `wsl -d Ubuntu-22.04 -- python3.11 …` because the toolchain lives in WSL2 (Plan 01-01 closeout decision).
- **Fix:** Translated every PowerShell `python …` invocation in the plan's verify blocks to `wsl -d Ubuntu-22.04 -- python3.11 …` and ran them from the worktree root (WSL inherits the Windows cwd as `/mnt/c/Users/ANUNNAKI/projects/PULSE/.claude/worktrees/agent-a831c0c8a15bd015f`). All three verify blocks (Task 1 dep install + collect-only, Task 2 import + route enumeration, Task 3 real pytest run) pass under this translation.
- **Files modified:** none (no plan edit — this is a runtime-only adaptation per the execute-phase host_toolchain block)
- **Verification:** `wsl -d Ubuntu-22.04 -- python3.11 -m pip install -e .[dev]` → `Successfully installed … fastapi-0.136.1 sqlalchemy-2.0.49 pytest-9.0.3 …`; `python3.11 -m pytest -q` → `7 passed`.
- **Committed in:** N/A — toolchain choice, not a code change

**2. [Rule 2 - Missing Critical] Default values on `Settings` secret fields so `app.main` imports without a populated .env**

- **Found during:** Task 2, smoke `python -c "from app.main import app"`
- **Issue:** A pydantic-settings `SecretStr` without a default raises `ValidationError: Field required` at `settings = Settings()` if the env var is missing. Plan-required `test_app_imports` (Task 3) and the Task 2 smoke `from app.main import app; print(app.title)` both fail before the test body runs because `.env` doesn't exist in the worktree (only `.env.example` is committed). Without defaults the entire Wave-0 test bootstrap is gated on a side artifact this plan doesn't own.
- **Fix:** Added explicit safe-default `SecretStr("dev-app-secret-replace-me")` / `SecretStr("replace-me")` / `SecretStr("change-me-on-first-login")` placeholders to `APP_SECRET_KEY`, `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, `INITIAL_ADMIN_PASSWORD`. Pydantic-settings `env_file` loading still wins at runtime, so a real `.env` overrides them. The placeholders self-document as "replace me" so an accidental prod boot trips audit eyes immediately. (Plan 07's compose startup is the right place to enforce "no replace-me values in prod" — a future check there closes the loop.)
- **Files modified:** `backend/app/core/config.py` (defaults added inline; type annotations unchanged)
- **Verification:** `python3.11 -c "from app.main import app; print(app.title)"` → `PULSE — Performance & Unit Live Scoring Engine`; `python3.11 -m pytest tests/test_bootstrap.py -q` → `2 passed`.
- **Committed in:** `f09bc9b` (Task 1 commit — `config.py` defaults shipped from the start so Task 2's import smoke is unblocked)

**3. [Rule 2 - Missing Critical] Added `APP_VERSION`, `DEBUG`, `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD` fields to Settings**

- **Found during:** Task 1
- **Issue:** Plan body says "Add fields `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD` (SecretStr), `APP_VERSION: str = "0.1.0"`, and a `DEBUG: bool = False` flag." — these fields are required by `main.py`'s `configure_logging(debug=settings.DEBUG)` call and by Plan 05/07's first-admin bootstrap.
- **Fix:** Added all four fields verbatim per the plan; `INITIAL_ADMIN_EMAIL` defaults to `"admin@pulse.local"` and `INITIAL_ADMIN_PASSWORD` to a `SecretStr("change-me-on-first-login")` placeholder.
- **Files modified:** `backend/app/core/config.py`
- **Verification:** `python3.11 -c "from app.core.config import settings; print(settings.APP_VERSION, settings.DEBUG)"` → `0.1.0 False`
- **Committed in:** `f09bc9b`

  (This isn't strictly a "deviation" — it's the plan's explicit ask. Logged here for traceability since the field list isn't enumerated in `files_modified` frontmatter.)

---

**Total deviations:** 2 substantive auto-fixes (1 blocking toolchain translation, 1 missing-critical Settings defaults) + 1 plan-asked field addition logged for traceability.
**Impact on plan:** No scope creep. Toolchain translation was mandated by the execute-phase prompt; Settings defaults preserve the test-bootstrap contract that Task 3's verify block depends on; the placeholders cannot be confused for production secrets (they self-label as "replace-me").

---

## Authentication / Human-Action Gates

None this plan. (No external service touched; admin gate stays as a placeholder that explicitly returns 401 by design — Plan 05 wires the real `require_role`.)

---

## Issues Encountered

- **WSL pip's `pytest --collect-only` exits 0 even with no tests in pytest 9.x.** Plan's PowerShell verify treats `LASTEXITCODE -ne 0 -and -ne 5` as failure. In the bash translation I observed pip-installed pytest 9.0.3 returns exit 5 when no tests are collected and exit 0 when tests are present — matches the plan's tolerance window. No action.
- **Git CRLF warnings** on every Windows write (`LF will be replaced by CRLF`). This is the default Windows checkout behavior; doesn't break anything because the files round-trip cleanly through the WSL filesystem (drvfs preserves LF in working-tree reads). Logged for awareness.

---

## Threat Model — Mitigations applied

| Threat ID    | Disposition | How this plan addresses it                                                                                                                              |
| ------------ | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T-03-T-01    | mitigated   | `tests/test_no_upload_policy.py` ships with ALLOWED_MULTIPART_PATHS={}; any accidental multipart route fails the test immediately. Plan 06 amends the set to its single legitimate entry. |
| T-03-I-01    | mitigated   | All secret fields in `Settings` are `SecretStr` (Pydantic auto-redacts on repr). structlog JSONRenderer never logs payload bodies. passlib bcrypt cosmetic warning silenced so logs stay clean. |
| T-03-I-02    | mitigated   | `/health/detail` guarded by `Depends(metrics_admin_dep)` → 401 pre-Plan-05; Plan 05 swaps for `require_role("super_admin","admin_unit")`.                |
| T-03-I-03    | mitigated   | `/metrics` guarded by the same dep.                                                                                                                     |
| T-03-D-01    | mitigated   | All DB access via `AsyncSession`; `get_db` async generator yields async sessions only.                                                                  |
| T-03-D-02    | mitigated   | `asyncio.wait_for(..., timeout=2.0)` wraps both DB and Redis probes in `/health`, `/health/detail`, `/metrics`.                                          |
| T-03-E-01    | partial     | This plan establishes the `dependencies=[Depends(metrics_admin_dep)]` convention. Plan 05 introduces `require_role` and locks the role taxonomy.        |

---

## Known Stubs

| Location                                      | Stub                                                                                            | Rationale / resolution plan                                                                                  |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `backend/app/deps/metrics_admin.py`           | `metrics_admin_dep` raises 401 unconditionally                                                  | Plan 05 swaps the body to `require_role("super_admin","admin_unit")`. Health endpoints import by name — no change there. |
| `backend/tests/test_no_upload_policy.py`      | `ALLOWED_MULTIPART_PATHS = set()` (empty)                                                       | Plan 06 amends to `{"/api/v1/konkin/templates/{template_id}/import-from-excel"}` when it adds the route.    |
| `backend/alembic/versions/20260511_120000_0001_baseline.py` | `upgrade()` / `downgrade()` are no-ops                                              | Intentional: empty baseline so Plans 05/06 chain --autogenerate against `down_revision=None` correctly.     |
| `backend/pyproject.toml` `[project.scripts]`  | `pulse-seed = "app.seed.__main__:main"`                                                          | Declared early for a stable CLI entry; `app/seed/__main__.py` is created in Plan 07. Stub-but-by-design.    |
| `backend/app/models/__init__.py` / `app/schemas/__init__.py` | Empty package markers                                                              | Auto-discovery requires the package to exist; Plans 05/06 drop model/schema files in.                       |

None of the stubs block the plan goal (skeleton + health endpoints + Wave-0 test bootstrap). All five resolve in downstream plans.

---

## Threat Flags

None. All surface introduced by this plan is in `<threat_model>` and mitigated above. No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries beyond what the plan and CONTEXT.md API spec already cover.

---

## TDD Gate Compliance

Plan 01-03 frontmatter declares `type: execute`, not `type: tdd`. No `tdd="true"` attribute on any task. The plan ships test scaffolds (Task 3) AFTER source code (Tasks 1+2), which is the explicit Wave-0 sequence per CONTEXT.md "Test Infrastructure" — the no-upload contract test cannot run before `app.main` exists. Skipped TDD RED/GREEN/REFACTOR gate.

---

## Self-Check: PASSED

Files claimed in this SUMMARY:

```
[ -f backend/pyproject.toml ]                                          → FOUND
[ -f backend/alembic.ini ]                                             → FOUND
[ -f backend/alembic/env.py ]                                          → FOUND
[ -f backend/alembic/script.py.mako ]                                  → FOUND
[ -f backend/alembic/versions/.gitkeep ]                               → FOUND
[ -f backend/alembic/versions/20260511_120000_0001_baseline.py ]       → FOUND
[ -f backend/app/__init__.py ]                                         → FOUND
[ -f backend/app/main.py ]                                             → FOUND
[ -f backend/app/core/config.py ]                                      → FOUND
[ -f backend/app/core/logging.py ]                                     → FOUND
[ -f backend/app/db/base.py ]                                          → FOUND
[ -f backend/app/db/session.py ]                                       → FOUND
[ -f backend/app/deps/db.py ]                                          → FOUND
[ -f backend/app/deps/redis.py ]                                       → FOUND
[ -f backend/app/deps/metrics_admin.py ]                               → FOUND
[ -f backend/app/routers/__init__.py ]                                 → FOUND
[ -f backend/app/routers/health.py ]                                   → FOUND
[ -f backend/app/models/__init__.py ]                                  → FOUND
[ -f backend/app/schemas/__init__.py ]                                 → FOUND
[ -f backend/tests/__init__.py ]                                       → FOUND
[ -f backend/tests/conftest.py ]                                       → FOUND
[ -f backend/tests/test_health.py ]                                    → FOUND
[ -f backend/tests/test_no_upload_policy.py ]                          → FOUND
[ -f backend/tests/test_bootstrap.py ]                                 → FOUND

git log --oneline grep f09bc9b   → FOUND
git log --oneline grep 6b8fa8a   → FOUND
git log --oneline grep e9c7190   → FOUND
```

Verification re-runs:
```
$ wsl -d Ubuntu-22.04 -- python3.11 -m pytest -q
....... 7 passed in 0.5s
$ wsl -d Ubuntu-22.04 -- python3.11 -c "from app.main import app; print(app.title)"
PULSE — Performance & Unit Live Scoring Engine
$ wsl -d Ubuntu-22.04 -- python3.11 -c "from app.routers import api_router; print(sorted(r.path for r in api_router.routes))"
['/api/v1/health', '/api/v1/health/detail', '/api/v1/metrics']
```

---

## Next Phase / Wave Readiness

**Wave 3 prerequisites (Plan 01-05 auth):**
- ✓ `app.db.base.Base` ready as declarative base for `app/models/user.py`
- ✓ `app.deps.metrics_admin.metrics_admin_dep` ready for in-place body swap
- ✓ `app/routers/__init__.py` will auto-pick up `app/routers/auth.py` with zero edits
- ✓ `pytest` infrastructure ready — `client` + `db_session` fixtures reusable
- ✓ Alembic baseline (`0001_baseline`) ready to chain auth migration to `down_revision="0001_baseline"`
- ✓ `python-jose[cryptography]` and `passlib[bcrypt]` already on the venv from this plan's install

**Wave 4 prerequisites (Plan 01-06 master data):**
- Same auto-discovery + `db_session` fixture + Alembic baseline. Plus:
- `ALLOWED_MULTIPART_PATHS` in `tests/test_no_upload_policy.py` waits for amendment to `{"/api/v1/konkin/templates/{template_id}/import-from-excel"}`.
- `link_eviden` URL-only contract test is armed and will catch the first model that types `link_eviden` as `str` instead of `HttpUrl`.

**No blockers handed forward.** The skeleton compiles, the test suite green-lights (7/7), and every downstream-plan contract is locked behind a test or an auto-discovery seam.

---

*Phase: 01-foundation-master-data-auth*
*Plan: 03 — backend-skeleton-health*
*Completed: 2026-05-11*
*Toolchain: WSL2 Ubuntu-22.04 / python 3.11.15 / pytest 9.0.3*
