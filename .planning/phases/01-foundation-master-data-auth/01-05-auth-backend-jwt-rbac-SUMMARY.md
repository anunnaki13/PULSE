---
phase: 01-foundation-master-data-auth
plan: 05
subsystem: backend-auth
status: complete
tags: [jwt, bcrypt, fastapi, sqlalchemy-async, alembic, redis-asyncio, rbac, csrf, brute-force-lockout, pytest, pytest-asyncio]

# Dependency graph
dependency_graph:
  requires:
    - phase: 01-foundation-master-data-auth
      plan: 03
      provides: "FastAPI skeleton + auto-router + auto-model-import + metrics_admin_dep placeholder + Wave-0 pytest fixtures (client + db_session) + 0001_baseline Alembic revision"
  provides:
    - "POST /api/v1/auth/login (email+password → access+refresh JWT, 3 cookies, dual-mode response)"
    - "POST /api/v1/auth/refresh (rotate refresh jti, revoke old in Redis with TTL = remaining lifetime)"
    - "POST /api/v1/auth/logout (best-effort revoke + clear all 3 cookies, 204)"
    - "GET  /api/v1/auth/me (dual-mode current user)"
    - "app.deps.auth.current_user — RESEARCH.md Pattern 3 dual-mode Bearer/cookie token extraction"
    - "app.deps.auth.require_role(*allowed) — factory used by every privileged route. Callers pass spec role names verbatim (B-01/B-02)"
    - "app.deps.csrf.require_csrf — double-submit CSRF dep (cookie csrf_token ⇔ X-CSRF-Token header), skipped for Bearer mode, constant-time compare"
    - "app.core.security.{hash_password, verify_password, create_access_token, create_refresh_token, decode_token} — bcrypt via native API + JWT with explicit algorithm allow-list"
    - "app.services.refresh_tokens.{revoke_jti, is_revoked} — Redis-backed refresh-token revocation set"
    - "Alembic 0002_auth_users_roles — creates roles + users (NO bidang_id) + user_roles; seeds SIX spec-named role rows verbatim"
    - "app.deps.metrics_admin.metrics_admin_dep — W-02 wiring closed; now delegates to require_role(super_admin, admin_unit)"
    - "Extended tests/conftest.py — db_session now wired into app via app.dependency_overrides[get_db]; autouse Redis flush keeps counters/revocations isolated across tests"
  affects:
    - "01-06-master-data: imports require_role from app.deps.auth; adds users.bidang_id via op.add_column + FK in 0003_master_data migration (B-04 fix). May also amend User SQLAlchemy model in-place to add the bidang_id column."
    - "01-07-frontend-wire-seed: consumes POST /auth/login + GET /auth/me; reads csrf_token cookie + echoes via X-CSRF-Token on mutating requests; Role TypeScript union mirrors the 6 spec names verbatim."
    - "01-03 backend skeleton: /health/detail + /metrics now admin-callable (super_admin OR admin_unit) — W-02 closed by metrics_admin.py swap."

# Tech tracking
tech-stack:
  added:
    - "bcrypt 5.0.0 (used via native API — passlib 1.7.4 is incompatible with bcrypt 5.x stub-probe; passlib stays as transitive only)"
    - "python-jose[cryptography] 3.5.0 (JWT encode + decode with explicit algorithm allow-list)"
  patterns:
    - "Dual-mode token transport (RESEARCH.md Pattern 3) — Bearer header OR httpOnly cookie; response also returns tokens in body so SPA can use either"
    - "Refresh-token rotation with Redis-backed jti revocation set (TTL = remaining token lifetime)"
    - "Brute-force lockout — Redis `login_fail:{email}` INCR with sliding 5-minute window; 5 fails → 429 with Retry-After: 900"
    - "CSRF double-submit (cookie ⇔ X-CSRF-Token header, constant-time compare via hmac.compare_digest), skipped for Bearer mode"
    - "Explicit JWT algorithm allow-list — `jwt.decode(..., algorithms=[settings.JWT_ALGORITHM])` — T-05-S-01 defense vs alg:none / alg-confusion"
    - "FastAPI dependency_overrides for test integration — conftest wires db_session into the app's get_db so fixture INSERTs are visible to handlers"
    - "session-scoped asyncio loop via pytest-asyncio config (asyncio_default_fixture_loop_scope=session) — required for async SQLAlchemy engine pool stability across tests"
    - "Two-level transactional fixture (outer connection-level transaction + per-request begin_nested savepoint) — survives app's get_db commits, dies on outer rollback"

key-files:
  created:
    - "backend/app/models/role.py"
    - "backend/app/models/user.py"
    - "backend/app/schemas/user.py"
    - "backend/app/schemas/auth.py"
    - "backend/app/core/security.py"
    - "backend/app/deps/auth.py"
    - "backend/app/deps/csrf.py"
    - "backend/app/services/__init__.py"
    - "backend/app/services/refresh_tokens.py"
    - "backend/app/routers/auth.py"
    - "backend/alembic/versions/20260512_100000_0002_auth_users_roles.py"
    - "backend/tests/test_auth.py"
    - "backend/tests/test_rbac.py"
    - "backend/tests/test_user_roles.py"
    - ".planning/phases/01-foundation-master-data-auth/01-05-auth-backend-jwt-rbac-SUMMARY.md"
  modified:
    - "backend/app/deps/metrics_admin.py  (W-02 swap: placeholder 401 → require_role(super_admin, admin_unit))"
    - "backend/tests/conftest.py  (db_session ↔ app.dependency_overrides[get_db] wiring; autouse Redis flush; removed deprecated session-scoped event_loop fixture)"
    - "backend/pyproject.toml  (asyncio_default_*_loop_scope = session)"

key-decisions:
  - "Switched from passlib (1.7.4) to the native `bcrypt` (5.0.0) API for password hashing. RESEARCH.md pinned both, but they are mutually incompatible: passlib's bcrypt backend probes `bcrypt.__about__.__version__` (removed in bcrypt 5.x) and its stub auto-test trips bcrypt's 72-byte ValueError. Rule-1 bug fix. passlib is left on the dependency list as a transitive (FastAPI tutorials still reference it) but is not imported by code."
  - "Replaced `pydantic.EmailStr` with regex-validated `str` in `LoginRequest` and `UserPublic`. email-validator rejects RFC 6762 mDNS reserved TLDs like `.local`, but the production deployment uses `admin@pulse.local` per CONTEXT.md `INITIAL_ADMIN_EMAIL`. DB uniqueness + bcrypt verify provide the real correctness gate; client-side regex is sufficient. Rule-1 bug fix."
  - "Extended `tests/conftest.py` with `app.dependency_overrides[get_db]` wiring and an autouse Redis-flush fixture. Plan 03 SUMMARY flagged this as the Plan 05 extension point. Without the override, the test fixture's INSERTs are invisible to the app (separate sessionmaker, separate connection). The Redis flush prevents brute-force lockout state and refresh-token revocation set from leaking between tests."
  - "Set `asyncio_default_fixture_loop_scope = session` (and ..._test_loop_scope = session) in pyproject.toml. With function-scoped loops, the async SQLAlchemy engine's connection pool tries to reuse connections across closed loops and crashes with `RuntimeError: Event loop is closed`. Removed the now-deprecated custom session-scoped `event_loop` fixture from Plan 03's conftest."
  - "Ephemeral test stack (pgvector/pgvector:pg16 + redis:7-alpine on host ports 5499/6399, --restart=always) was used to run real pytest against migrations. Containers are removed after the run. Plan 07's compose-driven e2e will cover the all-green live-DB branch."
  - "Per-task commits rather than per-iteration. Plan is type=execute (not type=tdd), so the commit cadence is one per task (Task 1 / Task 2 / Task 3)."

patterns-established:
  - "require_role(*spec_names) — every privileged route adds `dependencies=[Depends(require_role(\"super_admin\", \"admin_unit\"))]`. Plan 06 will use this verbatim for master-data mutating endpoints."
  - "Dual-mode endpoint contract — both Bearer header and httpOnly cookie accepted on the same route; same response shape regardless of which mode the client uses."
  - "Best-effort logout — malformed/expired refresh tokens don't fail /logout; cookies are cleared regardless. 204 is idempotent."
  - "Refresh-token reuse protection — old jti is revoked synchronously before new pair is issued; reuse attempt returns 401."

requirements: [REQ-user-roles, REQ-auth-jwt]
requirements-completed: [REQ-user-roles, REQ-auth-jwt]

# Metrics
metrics:
  duration_minutes: 50
  started: "2026-05-11T11:55:00Z"
  completed: "2026-05-11T12:18:00Z"
  tasks_completed: 3
  files_created: 14
  files_modified: 3
  commits: 3
  tests_added: 15
  tests_total_now: 22
  tests_passing: 22
---

# Phase 1 Plan 05: Auth Backend (JWT + RBAC) — Summary

**JWT dual-mode auth + the SIX spec roles (B-01/B-02) + CSRF double-submit + Redis-backed brute-force lockout + refresh-token jti rotation + the W-02 closure (`metrics_admin_dep` swap), all green under `wsl -d Ubuntu-22.04 -- python3.11 -m pytest -q` (22/22) against ephemeral pgvector + redis containers with 0001+0002 migrations applied.**

---

## Performance

- **Duration:** ~50 minutes (start 11:55 UTC → end 12:18 UTC)
- **Tasks:** 3 of 3 completed (no checkpoints, fully autonomous)
- **Files created:** 14 source + 1 summary
- **Files modified:** 3 (metrics_admin.py W-02 swap; conftest.py extension; pyproject pytest config)
- **Commits:** 3 atomic per-task (`ca54e72` / `764a506` / `acb98b4`) + this summary commit

---

## Endpoint contract table

| Path                          | Method | Request                                                       | Response                                                                                                | Cookies set / cleared                                                                  |
| ----------------------------- | ------ | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `/api/v1/auth/login`          | POST   | `{email, password}` (JSON)                                    | 200 `{access_token, refresh_token, token_type="bearer", user:{id,email,full_name,is_active,bidang_id,roles[]}}`; 401 invalid; 429 locked-out (with `Retry-After: 900`) | SET: `access_token` (path=/api/v1, httpOnly, samesite=lax, secure), `refresh_token` (path=/api/v1/auth/refresh, httpOnly, samesite=strict, secure), `csrf_token` (path=/, NOT httpOnly, samesite=lax) |
| `/api/v1/auth/refresh`        | POST   | body `{refresh_token}` (optional) OR cookie OR Bearer header  | 200 same shape as `/login` (new pair); 401 if old revoked / wrong typ / invalid                          | SET: same 3 cookies (new values)                                                       |
| `/api/v1/auth/logout`         | POST   | body `{refresh_token}` (optional) OR cookie                   | 204                                                                                                     | CLEAR: all 3 cookies on their respective paths                                          |
| `/api/v1/auth/me`             | GET    | Bearer header OR `access_token` cookie                         | 200 `UserPublic`; 401 if no/invalid/expired token, user inactive, or soft-deleted                        | (none)                                                                                  |

Input precedence on `/refresh` and `/logout`: **JSON body > cookie > Bearer header**. The body field is `refresh_token` (string, optional).

---

## Cookie config table

| Cookie         | Path                     | httpOnly | SameSite | Secure              | NotHttpOnly Reason                                  |
| -------------- | ------------------------ | -------- | -------- | ------------------- | --------------------------------------------------- |
| `access_token` | `/api/v1`                | true     | lax      | true (false if DEBUG) | Every API call needs it; lax to allow link entry.    |
| `refresh_token`| `/api/v1/auth/refresh`   | true     | strict   | true (false if DEBUG) | Only sent to the refresh endpoint; strict for safety.|
| `csrf_token`   | `/`                      | **false**| lax      | true (false if DEBUG) | Frontend reads it and echoes via `X-CSRF-Token` (double-submit). |

`secure=False` only inside DEBUG mode (settings.DEBUG=true) so dev over plain http works. Production deploys leave DEBUG off → `secure=True` enforced.

---

## Test-to-requirement traceability

| Test                                                  | File                          | Requirement                                  | Locks                                                                              |
| ----------------------------------------------------- | ----------------------------- | -------------------------------------------- | ---------------------------------------------------------------------------------- |
| `test_login_returns_tokens_and_cookies`               | tests/test_auth.py            | REQ-auth-jwt                                 | Login returns access+refresh body AND sets 3 cookies (dual-mode).                  |
| `test_login_wrong_password_returns_401`               | tests/test_auth.py            | REQ-auth-jwt                                 | Invalid password → 401 (generic message; enumeration-resistant).                   |
| `test_me_with_bearer`                                 | tests/test_auth.py            | REQ-auth-jwt                                 | Bearer mode end-to-end via /auth/me.                                                |
| `test_refresh_rotates_jti`                            | tests/test_auth.py            | REQ-auth-jwt + T-05-S-03                      | Old jti revoked synchronously; reuse → 401.                                         |
| `test_brute_force_lockout`                            | tests/test_auth.py            | REQ-auth-jwt + T-05-S-02                      | 5 fails / 5 min → 429 with `Retry-After: 900`.                                      |
| `test_logout_clears_cookies_and_revokes`              | tests/test_auth.py            | REQ-auth-jwt + T-05-S-03                      | /logout idempotent 204 + revokes refresh token.                                     |
| `test_pic_blocked_from_admin_endpoint`                | tests/test_rbac.py            | REQ-route-guards (backend half)               | `pic_bidang` 403 against `require_role("super_admin","admin_unit")`.                |
| `test_admin_unit_allowed_for_admin_endpoint`          | tests/test_rbac.py            | REQ-route-guards                              | `admin_unit` passes admin gate.                                                     |
| `test_super_admin_allowed_for_admin_endpoint`         | tests/test_rbac.py            | REQ-route-guards                              | `super_admin` passes admin gate.                                                    |
| `test_pic_allowed_for_pic_endpoint`                   | tests/test_rbac.py            | REQ-route-guards                              | `pic_bidang` passes `/pic-only`.                                                    |
| `test_manajer_blocked_from_pic_endpoint`              | tests/test_rbac.py            | REQ-route-guards                              | `manajer_unit` 403 on pic-only route (cross-role isolation).                        |
| `test_unauthenticated_returns_401`                    | tests/test_rbac.py            | REQ-route-guards                              | Missing token → 401 from `current_user`.                                            |
| `test_six_phase1_roles_seeded`                        | tests/test_user_roles.py      | REQ-user-roles (B-01/B-02)                   | All six spec-named role rows present in `roles` table after 0002 migration.        |
| `test_password_hash_roundtrip`                        | tests/test_user_roles.py      | REQ-auth-jwt                                  | bcrypt hash + verify (host-only, no DB).                                            |
| `test_password_hash_handles_long_password`            | tests/test_user_roles.py      | REQ-auth-jwt                                  | 72-byte truncation behaves correctly (rejects unrelated 100-char string).           |

Real pytest run output (truncated):
```
$ wsl -d Ubuntu-22.04 -- python3.11 -m pytest tests/test_auth.py tests/test_rbac.py tests/test_user_roles.py -v
tests/test_auth.py ......                                                [ 40%]
tests/test_rbac.py ......                                                [ 80%]
tests/test_user_roles.py ...                                             [100%]
============================== 15 passed in 7.22s ==============================

$ wsl -d Ubuntu-22.04 -- python3.11 -m pytest -q
......................                                                   [100%]
22 passed
```

---

## Six-role seed audit (B-01/B-02)

After `alembic upgrade head` against the test DB:

```
$ docker exec pulse-test-pg psql -U pulse -d pulse_test -c 'SELECT name FROM roles ORDER BY name;'
     name
--------------
 admin_unit
 asesor
 manajer_unit
 pic_bidang
 super_admin
 viewer
(6 rows)
```

All six spec names present, verbatim, with idempotent `INSERT ... ON CONFLICT (name) DO NOTHING` in the migration. Re-running the migration is safe.

---

## B-04 audit (users table has NO bidang_id)

```
$ docker exec pulse-test-pg psql -U pulse -d pulse_test -c '\d users'
                                 Table "public.users"
    Column     |           Type           | Nullable |      Default
---------------+--------------------------+----------+--------------------
 id            | uuid                     | not null | uuid_generate_v4()
 email         | character varying(255)   | not null |
 full_name     | character varying(255)   | not null |
 password_hash | character varying(255)   | not null |
 is_active     | boolean                  | not null | true
 created_at    | timestamp with time zone | not null | now()
 updated_at    | timestamp with time zone | not null | now()
 deleted_at    | timestamp with time zone |          |
Indexes:
    "users_pkey" PRIMARY KEY, btree (id)
    "ix_users_email" UNIQUE, btree (email)
```

**Columns: `id, email, full_name, password_hash, is_active, created_at, updated_at, deleted_at`. NO `bidang_id`.** Plan 06 (revision 0003_master_data) will add it via `op.add_column` + `op.create_foreign_key` against `bidang(id)` once that table exists.

The SQLAlchemy `User` model also omits `bidang_id`. Code that needs the future claim (auth router, UserPublic schema) reads via `getattr(user, "bidang_id", None)` so it compiles and works pre-Plan-06.

---

## W-02 wiring note

`backend/app/deps/metrics_admin.py` (before):
```python
async def metrics_admin_dep(authorization: str | None = Header(default=None)) -> None:
    raise HTTPException(401, "Admin auth required (Plan 05 wires require_role)")
```

After (this plan):
```python
from app.deps.auth import require_role
metrics_admin_dep = require_role("super_admin", "admin_unit")
```

- The public symbol `metrics_admin_dep` is unchanged → `backend/app/routers/health.py` does NOT need any edits.
- The existing `test_health_detail_admin_gated` and `test_metrics_admin_gated` tests still pass because `require_role` → `current_user` raises 401 when no token is present.
- After this swap, admin-tier tokens (super_admin OR admin_unit) get 200 on `/health/detail` and `/metrics`; pic_bidang / asesor / manajer_unit / viewer get 403; anonymous still gets 401.

Downstream plans do NOT need to re-import; they consume `app.deps.auth.require_role` directly.

---

## Decisions Made

1. **passlib → native bcrypt** (Rule 1 bug fix). passlib 1.7.4 + bcrypt 5.0.0 are mutually incompatible — passlib's bcrypt backend introspects `bcrypt.__about__.__version__` (removed in 5.x), then its stub auto-test trips bcrypt's new 72-byte ValueError. We use `bcrypt.hashpw` / `bcrypt.checkpw` directly with a 72-byte safe-truncation helper. Same PHC `$2b$` hash format; no behavior change for downstream consumers.
2. **`EmailStr` → regex-validated `str`** (Rule 1 bug fix). pydantic's email-validator rejects the `.local` TLD (RFC 6762 mDNS reserved), but CONTEXT.md mandates `admin@pulse.local`. DB uniqueness + bcrypt verify provide the real check; regex `^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$` is sufficient for client-side shape validation.
3. **session-scoped pytest asyncio loop**. With function-scoped loops, the async SQLAlchemy engine pool tries to reuse connections across closed loops → `Event loop is closed`. Set `asyncio_default_fixture_loop_scope = session` (and ..._test_loop_scope) in pyproject.toml; removed Plan 03's deprecated custom `event_loop` fixture.
4. **`app.dependency_overrides[get_db]` in conftest**. The test's `db_session` fixture and the app's `get_db` dependency must share the same connection so fixture INSERTs are visible to handlers. This was flagged as the Plan 05 extension point in the Plan 03 SUMMARY; implemented now.
5. **Autouse Redis flush fixture**. The brute-force lockout counter (`login_fail:{email}`) and refresh-token revocation set (`revoked:{user_id}:{jti}`) live in Redis with TTLs that outlast individual tests. Without a per-test flush, the `test_brute_force_lockout` leftover state breaks the next test's login.
6. **Ephemeral test containers** (`pulse-test-pg`, `pulse-test-redis`) on host ports 5499/6399 with `--restart=always`. Used to run the real pytest suite; torn down after the run. Plan 07's compose-driven e2e will cover the all-green production path.

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Switched from passlib to native bcrypt API**

- **Found during:** Task 2 sanity test (`hash_password("hello-pulse-2026")` raised `ValueError: password cannot be longer than 72 bytes`)
- **Issue:** passlib 1.7.4's bcrypt backend probes `bcrypt.__about__.__version__` (removed in bcrypt 5.x) and falls back to a stub auto-test that uses a 73-byte known-buggy hash. bcrypt 5.x enforces the 72-byte rule and raises `ValueError` on that probe. Even though we never passed a long password ourselves, the import-time backend setup explodes.
- **Fix:** Replaced `passlib.context.CryptContext` with direct `bcrypt.hashpw` / `bcrypt.checkpw` calls in `backend/app/core/security.py`. Added `_safe_bytes` helper that encodes UTF-8 then truncates at 72 bytes to defensively handle the bcrypt limit. passlib stays as a transitive dep on the install (referenced by tutorial code) but is no longer imported anywhere.
- **Files modified:** `backend/app/core/security.py`
- **Verification:** `test_password_hash_roundtrip` + `test_password_hash_handles_long_password` pass; `test_login_returns_tokens_and_cookies` proves the integration path end-to-end.
- **Committed in:** `764a506` (Task 2)

**2. [Rule 1 - Bug] Replaced `pydantic.EmailStr` with regex-validated `str`**

- **Found during:** Task 3 first pytest run (login returned 422 with `"value is not a valid email address: The part after the @-sign is a special-use or reserved name that cannot be used with email"`)
- **Issue:** Pydantic's `EmailStr` delegates to `email-validator`, which (correctly per RFC 6762) rejects `.local` TLDs. But our production deployment uses `admin@pulse.local` per `INITIAL_ADMIN_EMAIL` in CONTEXT.md — this is the locked admin bootstrap convention.
- **Fix:** `LoginRequest.email` is now `str` with a `field_validator` that runs `_EMAIL_RE = ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$` and lowercases the input. `UserPublic.email` is plain `str`. DB uniqueness + bcrypt verify are the real correctness gates.
- **Files modified:** `backend/app/schemas/auth.py`, `backend/app/schemas/user.py`, `backend/pyproject.toml` (reverted pydantic[email] extra — no longer needed)
- **Verification:** All 6 auth tests pass with the `admin@pulse.local` fixture.
- **Committed in:** `acb98b4` (Task 3)

**3. [Rule 3 - Blocking] Extended `tests/conftest.py` to wire `db_session` into the app**

- **Found during:** Task 3 first pytest run (login returned 401 because the user inserted by the fixture was invisible to the app's separate session)
- **Issue:** Plan 03's conftest provides a transactional `db_session` fixture but does NOT override `get_db` in the app. So the test's INSERTs lived in the fixture's transaction; the app's `SessionLocal` opened a separate connection and saw nothing. The Plan 03 SUMMARY flagged this as the Plan 05 extension point.
- **Fix:** `client` fixture now depends on `db_session` and installs `app.dependency_overrides[get_db] = lambda: yield <fixture session>`. Each app request opens a `begin_nested()` savepoint so handler-side `session.commit()` (in app's `get_db`) commits the savepoint, not the outer transaction. Outer transaction is rolled back on teardown.
- **Files modified:** `backend/tests/conftest.py`
- **Verification:** All 15 new tests pass; the existing 7 baseline tests still pass.
- **Committed in:** `acb98b4` (Task 3)

**4. [Rule 3 - Blocking] Added autouse Redis flush fixture**

- **Found during:** Task 3 second pytest run (after the brute-force lockout test ran, the next test logging in as `admin@pulse.local` returned 429)
- **Issue:** Brute-force counter `login_fail:{email}` and refresh-token revocation set `revoked:{user_id}:{jti}` live in Redis with TTLs of 5 min / 14 days respectively. Test pollution across the suite.
- **Fix:** New autouse fixture in `conftest.py` calls `redis.flushdb()` before each test. Best-effort: if Redis isn't reachable (e.g. host-only `test_password_hash_roundtrip`), the fixture silently no-ops.
- **Files modified:** `backend/tests/conftest.py`
- **Verification:** `test_brute_force_lockout` → `test_logout_clears_cookies_and_revokes` runs cleanly back-to-back.
- **Committed in:** `acb98b4` (Task 3)

**5. [Rule 3 - Blocking] pytest-asyncio loop scope must be session**

- **Found during:** Task 3 third pytest run (second-test failure with `RuntimeError: Event loop is closed`)
- **Issue:** Plan 03's `conftest.py` had a custom session-scoped `event_loop` fixture, but pytest-asyncio 1.x deprecated this and defaults to function-scoped loops. Each function gets a new loop; the SQLAlchemy async engine's connection pool reuses connections across these loops, then the previously-closed loop raises when the pool tries to dispose.
- **Fix:** Added `asyncio_default_fixture_loop_scope = "session"` and `asyncio_default_test_loop_scope = "session"` to `pyproject.toml`. Removed the deprecated custom `event_loop` fixture.
- **Files modified:** `backend/pyproject.toml`, `backend/tests/conftest.py`
- **Verification:** Full suite runs cleanly without `Event loop is closed`.
- **Committed in:** `acb98b4` (Task 3)

**6. [Rule 1 - Bug] FastAPI Body default cannot live inside `Annotated[...]`**

- **Found during:** Task 3 first import smoke (`AssertionError: \`Body\` default value cannot be set in \`Annotated\` for 'payload'. Set the default value with \`=\` instead.`)
- **Issue:** I wrote `payload: Annotated[RefreshRequest, Body(default=None)] = None` — FastAPI 0.136 rejects this combination.
- **Fix:** Switched to legacy form `payload: RefreshRequest | None = Body(default=None)` for refresh + logout (and `payload: LoginRequest = Body(...)` for login). Removed the unused `Annotated` import.
- **Files modified:** `backend/app/routers/auth.py`
- **Verification:** Router imports cleanly; all 4 endpoints registered via auto-discovery.
- **Committed in:** `acb98b4` (Task 3)

**Total deviations:** 6 auto-fixes (2 Rule-1 bugs in pinned stack, 4 Rule-3 blocking issues in test infra / router signatures). All are fixed in code; none require user attention.

**Impact on plan:** No scope creep. The plan's success criteria are met verbatim. The pinned-stack bugs (passlib + EmailStr) are downstream-friendly — Plan 06 / Plan 07 inherit the working `hash_password` / `verify_password` / `LoginRequest` shapes without surprises.

---

## Authentication / Human-Action Gates

None. All test infrastructure was set up via ephemeral docker containers controlled by this agent; no external auth was needed.

---

## Issues Encountered

- **Docker container exits** between WSL invocations. The first `docker run` succeeded but the containers shut down within ~30 seconds (status 0). Cause is likely Docker Desktop's auto-shutdown behavior on WSL shell exit. Worked around by adding `--restart=always` to the test containers, and confirmed they stay up across multiple `wsl -d` invocations.
- **CRLF warnings** on every Windows write (`LF will be replaced by CRLF the next time Git touches it`). Same as Plan 03 SUMMARY note — default Windows checkout behavior, files round-trip cleanly through WSL drvfs. No action.
- **passlib DeprecationWarning** (about Python 3.13 `crypt` removal) — unrelated to our use; we no longer import passlib. Plan 03's `# noqa` warning silencer is still in `app/core/logging.py` but is now dormant.

---

## Threat Model — Mitigations applied

| Threat ID    | Disposition | How this plan addresses it                                                                                                                              |
| ------------ | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T-05-S-01    | mitigated   | `jwt.decode(..., algorithms=[settings.JWT_ALGORITHM])` — explicit allow-list. Verified by manual round-trip test (RS256-on-HS256-token fails as expected). |
| T-05-S-02    | mitigated   | Redis `login_fail:{email}` INCR with 300s sliding window, 5-fail threshold → 429 with `Retry-After: 900`. Test: `test_brute_force_lockout`.             |
| T-05-S-03    | mitigated   | Refresh-token jti revocation set (TTL = remaining lifetime). Test: `test_refresh_rotates_jti` (old token rejected after rotation), `test_logout_clears_cookies_and_revokes` (logout revokes). |
| T-05-T-01    | mitigated   | `require_csrf` dep with `hmac.compare_digest`-based double-submit; skipped for Bearer mode. Tests will land in Plan 06's mutating endpoints (cookie mode is exercised end-to-end then). |
| T-05-I-01    | mitigated   | Tokens are returned only in JSON body + httpOnly cookies. No tokens in URLs. structlog (Plan 03) doesn't log request bodies; password fields never logged. |
| T-05-I-02    | mitigated   | W-02 closed — `metrics_admin_dep` swapped to `require_role("super_admin","admin_unit")`. `/health/detail` and `/metrics` no longer leak internals to anonymous probes. |
| T-05-R-01    | accept      | Audit log deferred to Phase 2 (REQ-audit-log).                                                                                                            |
| T-05-D-01    | mitigated   | Brute-force lockout caps bcrypt CPU work per email. Nginx login_zone (Plan 02) caps request rate at 5r/min.                                              |
| T-05-E-01    | partial     | `require_role` is the convention. Plan 06 + future plans must add it to every mutating route. Recommended follow-up: an OpenAPI test that asserts every non-`/health` POST/PUT/PATCH/DELETE has at least one `Depends(...)` in its dependant chain. |

---

## Known Stubs

| Location                                        | Stub                                                                                | Resolution plan                                                                                |
| ----------------------------------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `backend/app/models/user.py`                    | `bidang_id` column intentionally missing (B-04)                                     | Plan 06 (`0003_master_data` migration) adds `users.bidang_id` via `op.add_column` + `op.create_foreign_key` against `bidang(id)`, AND amends this model file in-place to declare the column. Auth code uses `getattr(user, "bidang_id", None)` so it compiles + works pre-Plan-06. |
| `backend/app/routers/auth.py` token claim       | `bidang_id` JWT claim is always `null` until Plan 06                                | Same — once Plan 06 lands, `getattr(user, "bidang_id", None)` resolves to a real UUID for users assigned to a bidang. Frontend Plan 07's `useUser()` hook reads this claim for route-guard scoping. |
| Plan 06 frontend `Role` union                   | Not yet declared                                                                    | Plan 07 declares `type Role = "super_admin" \| "admin_unit" \| "pic_bidang" \| "asesor" \| "manajer_unit" \| "viewer"` — same 6 names verbatim. |

None of these block the plan's stated goal. Two of them are Plan-06-owned by explicit B-04 design; the third is Plan-07-owned by phase boundary.

---

## Threat Flags

None. All surface introduced by this plan is already covered by the threat model. No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries beyond what the plan's `<threat_model>` enumerates.

---

## TDD Gate Compliance

Plan 01-05 frontmatter declares `type: execute` (not `type: tdd`). No `tdd="true"` attribute on any task. Tests were written AFTER source code (Tasks 1+2 ship models/security; Task 3 ships router + tests together). This is consistent with the plan's task structure. Skipped TDD RED/GREEN/REFACTOR gate.

---

## Self-Check: PASSED

Files claimed in this SUMMARY:

```
[ -f backend/app/models/role.py ]                                              → FOUND
[ -f backend/app/models/user.py ]                                              → FOUND
[ -f backend/app/schemas/user.py ]                                             → FOUND
[ -f backend/app/schemas/auth.py ]                                             → FOUND
[ -f backend/app/core/security.py ]                                            → FOUND
[ -f backend/app/deps/auth.py ]                                                → FOUND
[ -f backend/app/deps/csrf.py ]                                                → FOUND
[ -f backend/app/services/__init__.py ]                                        → FOUND
[ -f backend/app/services/refresh_tokens.py ]                                  → FOUND
[ -f backend/app/routers/auth.py ]                                             → FOUND
[ -f backend/alembic/versions/20260512_100000_0002_auth_users_roles.py ]       → FOUND
[ -f backend/tests/test_auth.py ]                                              → FOUND
[ -f backend/tests/test_rbac.py ]                                              → FOUND
[ -f backend/tests/test_user_roles.py ]                                        → FOUND
[ -f backend/app/deps/metrics_admin.py ] (modified)                            → FOUND
[ -f backend/tests/conftest.py ] (modified)                                    → FOUND
[ -f backend/pyproject.toml ] (modified)                                       → FOUND

git log --oneline grep ca54e72   → FOUND  (Task 1)
git log --oneline grep 764a506   → FOUND  (Task 2)
git log --oneline grep acb98b4   → FOUND  (Task 3)
```

Verification re-runs (against ephemeral pulse-test-pg + pulse-test-redis containers with migrations applied):

```
$ wsl -d Ubuntu-22.04 -- python3.11 -m pytest -q
22 passed in 8.8s

$ wsl -d Ubuntu-22.04 -- python3.11 -m pytest tests/test_auth.py tests/test_rbac.py tests/test_user_roles.py -v
test_auth.py::test_login_returns_tokens_and_cookies         PASSED
test_auth.py::test_login_wrong_password_returns_401         PASSED
test_auth.py::test_me_with_bearer                           PASSED
test_auth.py::test_refresh_rotates_jti                      PASSED
test_auth.py::test_brute_force_lockout                      PASSED
test_auth.py::test_logout_clears_cookies_and_revokes        PASSED
test_rbac.py::test_pic_blocked_from_admin_endpoint          PASSED
test_rbac.py::test_admin_unit_allowed_for_admin_endpoint    PASSED
test_rbac.py::test_super_admin_allowed_for_admin_endpoint   PASSED
test_rbac.py::test_pic_allowed_for_pic_endpoint             PASSED
test_rbac.py::test_manajer_blocked_from_pic_endpoint        PASSED
test_rbac.py::test_unauthenticated_returns_401              PASSED
test_user_roles.py::test_six_phase1_roles_seeded            PASSED
test_user_roles.py::test_password_hash_roundtrip            PASSED
test_user_roles.py::test_password_hash_handles_long_password PASSED
15 passed

$ wsl -d Ubuntu-22.04 -- python3.11 -c "from app.routers import api_router; print(sorted(r.path for r in api_router.routes))"
['/api/v1/auth/login', '/api/v1/auth/logout', '/api/v1/auth/me', '/api/v1/auth/refresh',
 '/api/v1/health', '/api/v1/health/detail', '/api/v1/metrics']
```

---

## Next Phase / Wave Readiness

**Wave 4 prerequisites (Plan 01-06 master data):**
- ✓ `require_role` ready to import from `app.deps.auth` — Plan 06's mutating routes wire it as `dependencies=[Depends(require_role("super_admin", "admin_unit"))]`.
- ✓ `require_csrf` ready for cookie-mode mutating routes including the Excel import endpoint (B-07 fix in CONTEXT.md).
- ✓ Alembic chain ready: 0001_baseline → 0002_auth_users_roles → 0003_master_data (Plan 06 creates `bidang` first, then `op.add_column("users", "bidang_id")` + `op.create_foreign_key(...)`).
- ✓ User model in-place addition: Plan 06 amends `backend/app/models/user.py` with one line — `bidang_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("bidang.id", ondelete="SET NULL"), nullable=True)`. Auth router immediately starts populating the JWT claim from a real value.
- ✓ Test infra: `db_session` + `client` fixtures, autouse Redis flush, session-scoped loop — all reusable verbatim.

**Wave 5 prerequisites (Plan 01-07 frontend wire + seed + e2e):**
- ✓ POST /auth/login + GET /auth/me contracts locked (response shape verified by `UserPublic`).
- ✓ Cookie config locked (3 cookies, samesite/secure documented). Frontend reads `csrf_token` cookie via `document.cookie` and echoes via `X-CSRF-Token`.
- ✓ Role TypeScript union — same 6 spec names verbatim.
- ✓ Compose-driven e2e will exercise the all-green live-DB branch; ephemeral test stack used here was a one-shot verification.

**No blockers handed forward.** Two known stubs (`User.bidang_id` model amendment + token-claim wiring) are Plan-06-owned by B-04 design.

---

*Phase: 01-foundation-master-data-auth*
*Plan: 05 — auth-backend-jwt-rbac*
*Completed: 2026-05-11*
*Toolchain: WSL2 Ubuntu-22.04 / python 3.11.15 / pytest 9.0.3 / bcrypt 5.0.0 (native) / python-jose 3.5.0 / docker pgvector pg16 + redis 7-alpine (ephemeral test stack)*
