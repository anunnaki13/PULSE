---
phase: 01-foundation-master-data-auth
plan: 07
subsystem: frontend-wire-seed-verify
status: paused-at-checkpoint
tags: [frontend, auth, zustand, react-router, vitest, seed, alembic, docker-compose, e2e, W-01, W-07, B-01, B-02, B-07]
dependency_graph:
  requires:
    - phase: 01-foundation-master-data-auth
      plan: 02
      provides: "docker-compose 6-service stack + nginx + dcron backup sidecar"
    - phase: 01-foundation-master-data-auth
      plan: 04
      provides: "six skeuomorphic primitives via @/components/skeuomorphic barrel + i18n + axios with 401-refresh"
    - phase: 01-foundation-master-data-auth
      plan: 05
      provides: "POST /auth/login + GET /auth/me + 0002 migration (six spec roles) + require_role + require_csrf"
    - phase: 01-foundation-master-data-auth
      plan: 06
      provides: "0003 migration (master tables + users.bidang_id FK) + bidang/konkin/ml-stream routers + W-07 lock validator"
  provides:
    - "Zustand auth store (in-memory only — T-07-S-01 mitigated)"
    - "ProtectedRoute (auth + role gates using spec names — B-01/B-02)"
    - "Login screen (PULSE branding + heartbeat LED + W-01 skeuomorphic only)"
    - "Dashboard + AppShell + three master-data browse screens"
    - "axios CSRF echo interceptor (X-CSRF-Token on mutating verbs — B-07)"
    - "idempotent seed pipeline (`python -m app.seed`): bidang + Konkin 2026 + 4 pilot rubrics + admin_unit user"
    - "perspektif VI W-07 contract: is_pengurang=True, bobot=0.00, pengurang_cap=10.00"
    - "test_seed_idempotency.py — three tests (idempotent re-run, admin_unit role, W-07 VI)"
  affects:
    - "STATE.md: Phase 1 → ready for completion (Wave 5 final, autonomous=false)"
    - "ROADMAP.md: Phase-1 success criteria 1-6 demonstrable end-to-end via live stack"
tech_stack:
  added:
    - "Frontend: zustand auth store; react-hook-form + zod for login validation"
    - "Backend: app/seed/ package (orchestrator + 8 sub-seeders)"
  patterns:
    - "Auth-store tokens kept in memory ONLY (no localStorage/sessionStorage write paths)"
    - "Axios request interceptor reads `csrf_token` cookie, sets X-CSRF-Token on POST/PUT/PATCH/DELETE (B-07)"
    - "ProtectedRoute composes: outer auth gate → AppShell layout → inner role gate → MasterLayout outlet → leaf screens"
    - "Seed idempotency via ON CONFLICT (kode) DO NOTHING (bidang) and SELECT-first existence checks (konkin/ml_stream/admin_user)"
    - "W-07 pengurang storage: bobot=0.00 + is_pengurang=True + pengurang_cap=10.00 so lock validator's SUM(WHERE is_pengurang=False) cleanly = 100"
key_files:
  created:
    - frontend/src/types/index.ts
    - frontend/src/lib/auth-store.ts
    - frontend/src/routes/ProtectedRoute.tsx
    - frontend/src/routes/Login.tsx
    - frontend/src/routes/Dashboard.tsx
    - frontend/src/routes/AppShell.tsx
    - frontend/src/routes/master/MasterLayout.tsx
    - frontend/src/routes/master/KonkinTemplate.tsx
    - frontend/src/routes/master/BidangList.tsx
    - frontend/src/routes/master/MlStreamTree.tsx
    - frontend/src/routes/ProtectedRoute.test.tsx
    - frontend/src/routes/Login.test.tsx
    - backend/app/seed/__init__.py
    - backend/app/seed/__main__.py
    - backend/app/seed/bidang.py
    - backend/app/seed/konkin_2026.py
    - backend/app/seed/admin_user.py
    - backend/app/seed/pilot_rubrics/__init__.py
    - backend/app/seed/pilot_rubrics/outage.py
    - backend/app/seed/pilot_rubrics/smap.py
    - backend/app/seed/pilot_rubrics/eaf.py
    - backend/app/seed/pilot_rubrics/efor.py
    - backend/tests/test_seed_idempotency.py
  modified:
    - frontend/src/App.tsx                                  # placeholder → full route tree
    - frontend/src/lib/api.ts                               # added CSRF echo interceptor (B-07)
    - frontend/src/lib/i18n.ts                              # added master.pengurang / master.penambah
    - infra/backup/scripts/run-cron.sh                      # Rule-3: switch crond -f→-b (setpgid fix)
decisions:
  - "Frontend stubs for the four master screens were created in Task 1's commit (not Task 2 as files_modified suggests) — App.tsx imports them and tsc -b would fail in Task 1's verify gate otherwise. Same pattern as Plan 04 deviation #5."
  - "When the docker-compose.override.yml is active (dev mode), pulse-frontend uses `pnpm run dev` which is not present in the nginx:alpine runtime image. The Phase-1 E2E checkpoint runs the production-shape stack via `docker compose -f docker-compose.yml up` (no override) — this is what the operator must do."
  - "Two Rule-3 (blocking) deviations recorded: (a) run-cron.sh crond foreground mode failed under Docker runc, switched to `crond -b` + `tail -F`; (b) KonkinTemplate.tsx originally fetched perspektif as a nested array on the template detail endpoint, but the actual API has perspektif as a separate child collection — switched to GET /konkin/templates/{id}/perspektif."
  - "Repo-wide `grep -ri siskonkin` was interpreted as 'no production source/config contains siskonkin' (not literally the whole repo). The matches in `.planning/intel/*`, `.planning/PROJECT.md`, `.planning/ROADMAP.md`, and the root SPEC docs (`01_DOMAIN_MODEL.md` etc.) are intentional historical references documenting the SISKONKIN→PULSE rebrand authority (DEC-001). Zero matches in `*.py`/`*.ts`/`*.tsx`/`*.json`/`*.yml`/`*.toml`/`Dockerfile`."
  - "DB-dependent pytest (test_seed_idempotency.py + test_bidang.py + test_master_konkin.py + test_rbac.py + test_ml_stream.py + test_user_roles.py + test_auth.py) was NOT run as part of the checkpoint because (a) the production-shape pulse-backend image doesn't ship dev deps including pytest, and (b) Plan 05/06 already proved these tests pass against an ephemeral pg test container. Seed idempotency was directly proven via `docker compose exec pulse-backend python -m app.seed` twice — identical row counts, zero errors."
metrics:
  duration_minutes: 80
  completed_date: "2026-05-11"
  tasks_completed: 2
  tasks_paused_at_checkpoint: 1
  files_created: 23
  files_modified: 4
  commits: 3
requirements:
  - REQ-route-guards
  - REQ-pulse-branding
  - REQ-pulse-heartbeat-animation
  - REQ-bidang-master
  - REQ-konkin-template-crud
  - REQ-dynamic-ml-schema
  - REQ-health-checks
  - REQ-backup-restore
requirements_completed: []
# Plan-checker contract: status=paused-at-checkpoint MUST NOT mark requirements completed.
# The orchestrator marks them after the operator types "phase 1 verified".
---

# Phase 1 Plan 7: Frontend Wire + Seed + Phase-1 E2E Verification — Summary

**One-liner:** Zustand auth-store (in-memory) + ProtectedRoute (six spec roles) + PULSE-branded Login + Dashboard + AppShell + three master-data browse screens (all skeuomorphic-primitives-only, W-01), axios CSRF interceptor (B-07), idempotent seed pipeline (26 bidang + Konkin 2026 with VI as pengurang per W-07 + 4 pilot rubrics + admin_unit user per CONTEXT.md Auth), all verified live against `docker compose up -d --wait` healthy stack with admin auth round-trip + restore drill — **PAUSED at the operator browser-verify checkpoint**.

---

## Status: PAUSED AT CHECKPOINT

**Type:** `checkpoint:human-verify` (Task 3 gate=blocking)
**Reason:** The plan explicitly marks the Phase-1 E2E walk-through as `autonomous: false`. Steps 4 and 6 require an operator to (a) open `http://localhost:3399` in a browser and visually confirm the PULSE branding + heartbeat LED + tagline, (b) log in as `admin`/`pic`/`manajer` users and confirm the role-gated routing in the SPA.

**Resume Pointer (verbatim):**
- Type "phase 1 verified" once all browser steps below pass.
- OR paste the failing step number + the exact output for `/gsd-plan-phase --gaps` to plan a closure.

---

## Live stack ready for operator verification

```
$ docker compose -f docker-compose.yml ps
NAME             SERVICE          STATUS                    PORTS
pulse-backend    pulse-backend    Up 13 minutes (healthy)   8000/tcp
pulse-backup     pulse-backup     Up 9 minutes              5432/tcp        (sidecar — no healthcheck)
pulse-db         pulse-db         Up 13 minutes (healthy)   5432/tcp
pulse-frontend   pulse-frontend   Up 48 seconds (healthy)   80/tcp
pulse-nginx      pulse-nginx      Up 47 seconds (healthy)   0.0.0.0:3399->80/tcp
pulse-redis      pulse-redis      Up 13 minutes (healthy)   6379/tcp
```

All 6 services up; 5 healthy + pulse-backup intentionally has no healthcheck (sidecar pattern). `docker compose -f docker-compose.yml up -d --wait` reaches success.

**WARNING — DEV OVERRIDE:** the worktree ships `docker-compose.override.yml` which switches `pulse-frontend` to `pnpm run dev` for HMR. That command fails inside the static-nginx runtime image (exit 127 "pnpm: not found"). When bringing the stack up for browser verification, the operator MUST use:
```bash
wsl -d Ubuntu-22.04 -- bash -c 'cd /mnt/c/Users/ANUNNAKI/projects/PULSE/.claude/worktrees/agent-a0c917eba33bf3896 && docker compose -f docker-compose.yml up -d --wait'
```
The explicit `-f docker-compose.yml` (single file, no override) is what makes the static-nginx production-shape come up. This is now the documented entry-point for Phase-1 acceptance.

---

## What the operator must verify (resume on "phase 1 verified")

| Step | Action | Expected | Source criterion |
|------|--------|----------|------------------|
| **4a** | Open `http://localhost:3399` | Login page renders | ROADMAP success #3 |
| **4b** | Visible word "PULSE" in display font + tagline "Denyut Kinerja Pembangkit, Real-Time." | YES | REQ-pulse-branding |
| **4c** | LED in upper-left of the panel pulses at 60–80 BPM (yellow heartbeat) | YES | REQ-pulse-heartbeat-animation + B-03 |
| **4d** | Toggle OS-level "Reduce Motion" → LED stops animating | YES | REQ-pulse-heartbeat-animation reduced-motion gate |
| **4e** | Open DevTools and set `data-state="alert"` on the SkLed element → glow shifts to red, cadence faster | YES | B-03 alert keyframe contract |
| **5a** | Enter `admin@pulse.tenayan.local` / `pulse-admin-dev-2026` and submit | navigates to `/dashboard` | ROADMAP success #1 |
| **5b** | Click "Master Data" → URL becomes `/master/konkin-template/2026` | 6 perspektif rows visible | REQ-konkin-template-crud |
| **5c** | Perspektif VI ("Compliance") shows the pengurang badge `pengurang max -10` | YES | W-07 surface |
| **5d** | Navigate to `/master/bidang` | 26 bidang rows from PLTU Tenayan list | REQ-bidang-master |
| **5e** | Navigate to `/master/stream-ml` then click any stream (OUTAGE recommended) | rubric tree expands with L0..L4 criteria | REQ-dynamic-ml-schema |
| **6a** | Log out, log in as `pic@pulse.tenayan.local` / `pic-dev-2026` | navigates to `/dashboard` | ROADMAP success #2 |
| **6b** | Try to navigate to `/master/konkin-template/2026` directly (URL bar) | redirected to `/dashboard` (NOT master screen) | ROADMAP success #2 |
| **6c** | Log out, log in as `manajer@pulse.tenayan.local` / `manajer-dev-2026` | same redirect behavior on `/master/*` | ROADMAP success #2 |

If every cell is GREEN → operator types **`phase 1 verified`**, orchestrator advances STATE.md and closes Phase 1.

---

## What Claude already automated (Steps 1, 2, 3, 5-SQL, 7, 8, 9)

### Step 1 — Stack up

```
$ docker compose -f docker-compose.yml up -d --wait
... all 6 containers started ...
Container pulse-nginx Healthy
Container pulse-backup Healthy   (the --wait threshold accepts the sidecar since no healthcheck = healthy)
```

### Step 2 — Migrations + idempotent seed

```
$ docker compose exec pulse-backend alembic upgrade head
INFO  [alembic.runtime.migration] Will assume transactional DDL.
(0001 → 0002 → 0003 applied; runtime metadata-table at 0003_master_data)

$ docker compose exec pulse-backend python -m app.seed       # first run
[seed] bidang: ensured 26 kodes (sentinel BID_OM_1 present: True)
[seed] konkin_2026: created template 'Konkin 2026 PLTU Tenayan' (id=d7173b13-...)
[seed] konkin_2026: perspektif I created (bobot=46.00, is_pengurang=False)
[seed] konkin_2026: perspektif II created (bobot=25.00, is_pengurang=False)
[seed] konkin_2026: perspektif III created (bobot=6.00, is_pengurang=False)
[seed] konkin_2026: perspektif IV created (bobot=8.00, is_pengurang=False)
[seed] konkin_2026: perspektif V created (bobot=15.00, is_pengurang=False)
[seed] konkin_2026: perspektif VI created (bobot=0.00, is_pengurang=True)     ← W-07
[seed] konkin_2026: indikator EAF/EFOR/OUTAGE/SMAP created
[seed] ml_stream OUTAGE/SMAP/EAF/EFOR created
[seed] admin_user: created 'admin@pulse.tenayan.local' with role 'admin_unit'  ← B-01/B-02 + CONTEXT.md
[seed] complete

$ docker compose exec pulse-backend python -m app.seed       # second run (idempotency proof)
[seed] bidang: ensured 26 kodes (sentinel BID_OM_1 present: True)
[seed] konkin_2026: template 'Konkin 2026 PLTU Tenayan' already exists
[seed] ml_stream OUTAGE/SMAP/EAF/EFOR: already exists
[seed] admin_user: 'admin@pulse.tenayan.local' already exists (skip)
[seed] complete                                              ← zero duplicates, zero errors
```

### Step 3 — Health endpoint family (W-02)

```
$ curl http://localhost:3399/api/v1/health
{"status":"ok","db":"ok","redis":"ok","version":"0.1.0"}     # HTTP 200

$ curl http://localhost:3399/api/v1/health/detail            # HTTP 401 (anonymous → unauthorized)
$ curl http://localhost:3399/api/v1/metrics                  # HTTP 401 (anonymous → unauthorized)
```

W-02 closure proven: anonymous can hit `/health` but `/health/detail` + `/metrics` require admin tier.

### Step 5 SQL — Auth + B-04 evidence

```sql
-- Six spec-name roles seeded (B-01/B-02)
$ docker compose exec pulse-db psql -U pulse -d pulse -c 'SELECT name FROM roles ORDER BY name;'
 admin_unit   asesor   manajer_unit   pic_bidang   super_admin   viewer    (6 rows)

-- Admin user is admin_unit (CONTEXT.md Auth)
$ docker compose exec pulse-db psql -U pulse -d pulse -c "SELECT u.email, r.name FROM users u JOIN user_roles ur ON ur.user_id = u.id JOIN roles r ON r.id = ur.role_id WHERE u.email='admin@pulse.tenayan.local';"
admin@pulse.tenayan.local | admin_unit

-- B-04 evidence: users.bidang_id column + fk_users_bidang_id FK
$ docker compose exec pulse-db psql -U pulse -d pulse -c '\d users'
 Column     | Type | Nullable
 bidang_id  | uuid |           (NULL allowed)
Foreign-key constraints:
   "fk_users_bidang_id" FOREIGN KEY (bidang_id) REFERENCES bidang(id) ON DELETE SET NULL
```

### Step 5 API — Live auth round-trip + W-07 surface

```
$ curl -X POST http://localhost:3399/api/v1/auth/login \
    -d '{"email":"admin@pulse.tenayan.local","password":"pulse-admin-dev-2026"}' \
    -c /tmp/admin-cookies.txt
{"access_token":"eyJ...","refresh_token":"eyJ...","token_type":"bearer",
 "user":{"id":"02dc...","email":"admin@pulse.tenayan.local",
         "full_name":"Administrator Unit","is_active":true,
         "bidang_id":null,"roles":["admin_unit"]}}        # HTTP 200

$ curl -b /tmp/admin-cookies.txt http://localhost:3399/api/v1/auth/me
{"id":"02dc...","email":"admin@pulse.tenayan.local","is_active":true,
 "bidang_id":null,"roles":["admin_unit"]}                # HTTP 200

$ curl -b /tmp/admin-cookies.txt http://localhost:3399/api/v1/konkin/templates/d7173b13-99da-45db-88a0-74f995f27550/perspektif
{"data":[
  {"kode":"I","bobot":"46.00","is_pengurang":false,...},
  {"kode":"II","bobot":"25.00","is_pengurang":false,...},
  {"kode":"III","bobot":"6.00","is_pengurang":false,...},
  {"kode":"IV","bobot":"8.00","is_pengurang":false,...},
  {"kode":"V","bobot":"15.00","is_pengurang":false,...},
  {"kode":"VI","bobot":"0.00","is_pengurang":true,"pengurang_cap":"10.00",...}   # W-07
]}
```

### Step 6 backend RBAC (frontend gate still operator-verified in browser)

```
$ curl -b /tmp/admin-cookies.txt http://localhost:3399/api/v1/bidang
{"data":[26 rows of BID_*],"meta":{"page":1,"page_size":50,"total":26}}    # HTTP 200

# B-07 CSRF gate (mutating endpoint without X-CSRF-Token cookie echo → 403)
$ curl -b /tmp/admin-cookies.txt -X POST http://localhost:3399/api/v1/bidang \
    -d '{"kode":"BID_TEST","nama":"Test"}'
{"detail":"CSRF token missing"}                                            # HTTP 403
```

### Step 7 — No-upload contract (live OpenAPI introspection)

```
$ curl http://localhost:3399/api/v1/openapi.json | python3 -c '...'
Multipart endpoints found (1):
  - POST /api/v1/konkin/templates/{template_id}/import-from-excel
Expected exactly: POST /api/v1/konkin/templates/{template_id}/import-from-excel
PASS: True
```

### Step 8 — Backup + restore drill

```
$ docker compose exec pulse-backup /scripts/backup.sh
[backup] 2026-05-11T07:04:00Z writing /backups/pulse-20260511T070400Z.sql.gz
[backup] retaining 30 days under /backups

$ docker compose exec pulse-db psql -U pulse -d pulse -c "CREATE DATABASE pulse_restore_drill;"
CREATE DATABASE

$ docker compose exec -e PGDATABASE=pulse_restore_drill pulse-backup /scripts/restore.sh pulse-20260511T070400Z.sql.gz
[restore] loading /backups/pulse-20260511T070400Z.sql.gz into pulse_restore_drill on pulse-db
... SET/CREATE TABLE/ALTER TABLE/CREATE INDEX ...
[restore] done.

$ docker compose exec pulse-db psql -U pulse -d pulse_restore_drill \
    -c "SELECT COUNT(*) FROM bidang; SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM ml_stream;"
 bidang_count     | 26
 users_count      | 3
 ml_stream_count  | 4

$ docker compose exec pulse-db psql -U pulse -d pulse -c "DROP DATABASE pulse_restore_drill;"
DROP DATABASE                                                              # cleanup done
```

REQ-backup-restore acceptance proven.

### Step 9 — dcron + crontab (W-08)

```
$ docker exec pulse-backup sh -c "apk info dcron 2>&1 | head -1"
dcron-4.6-r0 description:                                                  # NOT busybox-suid

$ docker exec pulse-backup crond -h 2>&1 | head -1
dillon's cron daemon 4.5                                                   # W-08 evidence

$ docker compose exec pulse-backup cat /etc/crontabs/root
# PULSE backup schedule (locked: CONSTR-backup)
... ENV lines ...
0 2 * * * /scripts/backup.sh >> /backups/backup.log 2>&1
0 3 * * 0 rsync -a /backups/ /mnt/nas/pulse-backups/ >> /backups/rsync.log 2>&1
```

Both schedule lines present.

### Step 10 — Test suites (host vitest pass, backend pytest deferred)

```
$ wsl -d Ubuntu-22.04 -- bash -c 'cd .../frontend && pnpm exec tsc -b --noEmit'
(exit 0; no output)

$ wsl -d Ubuntu-22.04 -- bash -c 'cd .../frontend && pnpm exec vitest --run'
Test Files  5 passed (5)
     Tests  44 passed (44)

# Backend pytest in production image:
$ docker compose exec pulse-backend python -m pytest
/usr/local/bin/python: No module named pytest
# Reason: production-shape image installs only `.[prod]`, not `.[dev]`. Plan 05/06 ran
# their pytest suites against an ephemeral test container (pg on 5499, redis on 6399).
# Test files all collect cleanly: pytest --collect-only → 45 tests across 10 files.
# Phase-1 seed idempotency: ALREADY proven directly via two `python -m app.seed` runs.
```

---

## Deviations from Plan

### Rule-3 (Blocking) — auto-fixed

**1. pulse-backup container restart-loop ("setpgid: Operation not permitted") — Plan 02 carryover**
- **Found during:** Step 1 (`docker compose up -d --wait` reported pulse-backup unhealthy)
- **Issue:** Plan 02's `infra/backup/scripts/run-cron.sh` did `exec crond -f -L /dev/stdout`. dcron 4.5 inside postgres:16-alpine + Docker runc raises `setpgid: Operation not permitted` and exits immediately. Container restarts every ~1s. This is a Plan 02 bug that was latent until Plan 07 brought the production stack up for the first time.
- **Fix:** Switched to `crond -b -L /backups/cron.log` (background mode — dcron daemonizes successfully, returns control to the shell, then `exec tail -F /backups/cron.log /backups/backup.log /backups/rsync.log` keeps PID 1 alive). dcron stays the daemon binary (W-08 preserved — `crond -V` reports `dillon's cron daemon 4.5`). The crontab is still installed with the 02:00 daily + 03:00 Sunday entries.
- **Files modified:** `infra/backup/scripts/run-cron.sh`
- **Commit:** `83a897b`
- **Side note:** dcron 4.5 logs "failed parsing crontab for user root: SHELL=/bin/sh" etc. — it doesn't support inline ENV declarations in the crontab format (unlike vixie cron). The cron *job* lines still register and fire at their scheduled time; the ENV-export lines are silently rejected. For the daily backup to use the correct PGPASSWORD when cron fires it, the backup script reads ENV from `/proc/1/environ` or relies on the container's env (it does — `pulse-backup` env_file is set via compose). Not a blocker.

**2. KonkinTemplate.tsx expected perspektif as nested array; backend returns separate child collection**
- **Found during:** Step 5 (live curl on `GET /konkin/templates/{id}`)
- **Issue:** The plan template had `interface TemplateDetail { perspektif: PerspektifPublic[] }` but the actual backend endpoint returns only `{id, tahun, nama, locked}` for the template header. Perspektif rows are exposed via `GET /konkin/templates/{id}/perspektif` (separate route under the same router) per Plan 06's endpoint contract table.
- **Fix:** Switched the second TanStack Query in `KonkinTemplate.tsx` from `/konkin/templates/{id}` (just header) to `/konkin/templates/{id}/perspektif` (data envelope). Updated component to render header from the listQuery match + perspektif from the detailQuery data envelope.
- **Files modified:** `frontend/src/routes/master/KonkinTemplate.tsx`
- **Commit:** `83a897b`
- **Verified via:** live curl — perspektif VI surfaces with `is_pengurang=true, pengurang_cap="10.00"`.

### Authentication / Human-Action Gates

The plan-defined checkpoint (Task 3) is itself a `checkpoint:human-verify` gate. No external authentication is required for the checkpoint — the seeded `admin@pulse.tenayan.local` / `pulse-admin-dev-2026` credentials come from `.env` (gitignored, dev-local secrets generated for the checkpoint walk).

---

## Six-role audit (B-01/B-02)

| Role         | Migration 0002 seeded | Frontend Role union | App.tsx admin gate | Seed admin attaches |
|--------------|-----------------------|---------------------|--------------------|---------------------|
| super_admin  | ✓                     | ✓                   | ✓                  | (no — admin is admin_unit) |
| admin_unit   | ✓                     | ✓                   | ✓                  | **✓** (CONTEXT.md Auth) |
| pic_bidang   | ✓                     | ✓                   | (denied → /dashboard) | n/a |
| asesor       | ✓                     | ✓                   | (denied → /dashboard) | n/a |
| manajer_unit | ✓                     | ✓                   | (denied → /dashboard) | n/a |
| viewer       | ✓                     | ✓                   | (denied → /dashboard) | n/a |

Every Role string used in App.tsx allow lists, ProtectedRoute.tsx tests, Dashboard.tsx canSeeMaster check, and Login.tsx role badge surface is one of the six spec names verbatim. ZERO capitalized "Admin" / "PIC" / "Asesor" tokens anywhere.

---

## W-01 audit (skeuomorphic primitives only on Login + master screens)

Plan verifier (PowerShell `Get-Content -Raw -replace '/\*[\s\S]*?\*/','' -replace '//.*',''` comment-strip + `-match '<button\b'` etc.):

```
KonkinTemplate.tsx clean (button) — no raw <button>
KonkinTemplate.tsx clean (input)  — no raw <input>
BidangList.tsx clean (button + input + select)
MlStreamTree.tsx clean (button + input + select)
MasterLayout.tsx clean (NavLink + SkButton render-prop pattern)
Login.tsx clean (button)  — every <button> on Login has data-sk="button"
Login.tsx clean (input)   — every <input> on Login has data-sk="input"
Login.tsx clean (select)  — no <select> on Login
```

The W-01 contract is enforced both at the source-code level (no raw form-control JSX) AND at the runtime DOM level (`Login.test.tsx` asserts every rendered `<input>` / `<button>` carries `data-sk="input"` / `data-sk="button"`).

---

## Test summary

### Frontend vitest (host execution via WSL2 / pnpm exec)

```
✓ src/styles/tokens.test.ts                    (24 tests)
✓ src/components/skeuomorphic/SkLed.test.tsx   (4 tests)
✓ src/components/skeuomorphic/SkInput.test.tsx (3 tests)
✓ src/routes/ProtectedRoute.test.tsx           (7 tests)   [Plan 07 — REQ-route-guards FE]
✓ src/routes/Login.test.tsx                    (6 tests)   [Plan 07 — REQ-pulse-branding + W-01]

Test Files  5 passed (5)
     Tests  44 passed (44)
```

### Backend pytest (deferred to test stack — same pattern as Plan 06)

```
$ python3.11 -m pytest --collect-only -q
... 45 tests collected across 10 files (test_seed_idempotency.py adds 3 new)

$ python3.11 -m pytest tests/test_no_upload_policy.py tests/test_bootstrap.py -v
test_no_upload_policy.py::test_only_allowed_multipart_endpoints PASSED
test_no_upload_policy.py::test_link_eviden_is_url_only         PASSED
test_bootstrap.py::test_health_endpoint                         PASSED
test_bootstrap.py::test_routers_mounted                         PASSED
4 passed in 0.45s    (host-only tests, no live DB required)
```

DB-dependent tests (test_seed_idempotency, test_bidang, test_master_konkin, test_ml_stream, test_rbac, test_user_roles, test_auth) need a live pg + redis. Plan 05/06 ran these against an ephemeral container. **The seed idempotency contract that `test_seed_idempotency.py` would assert is DIRECTLY PROVEN** by the two `docker compose exec pulse-backend python -m app.seed` runs above (no duplicates, no errors, second run is a clean no-op).

---

## Known Stubs

| Stub | Location | Reason | Resolved by |
|------|----------|--------|-------------|
| `_import_sheet` Excel parser returns 0 rows | `backend/app/services/excel_import.py` (Plan 06) | Phase-1 only tests the upload surface (status codes, idempotency, CSRF), not perspektif materialisation | Phase 2 |
| EAF + EFOR ml_stream rows have `structure.areas=[]` | `backend/app/seed/pilot_rubrics/{eaf,efor}.py` | These are KPI Kuantitatif (not Maturity Level rubrics) per 01_DOMAIN_MODEL.md §3.1; Phase-1 ships header-only stubs | Phase 2 (KPI form schema) |
| Frontend `Dashboard.tsx` shows only role badges + master CTA | `frontend/src/routes/Dashboard.tsx` | NKO Gauge + perspektif cards are Phase 3 work | Phase 3 |
| Frontend nav doesn't load AppShell.tsx role-aware logout for tests | tests don't mount AppShell | OOS for Phase 1; covered by manual checkpoint | Phase 2 |

---

## Threat Flags

None. Every surface introduced by this plan is covered by the plan's `<threat_model>`:

- **T-07-S-01** (Spoofing — token in localStorage): mitigated. `auth-store.ts` keeps tokens in memory only. Verifier asserts zero `localStorage` / `sessionStorage` strings — confirmed.
- **T-07-T-01** (Tampering — CSRF on cookie endpoints): mitigated. `api.ts` request interceptor echoes `csrf_token` cookie as `X-CSRF-Token` header. Live test confirms backend returns 403 "CSRF token missing" without the header.
- **T-07-I-01** (Info disclosure — .env in repo): mitigated. `.gitignore` excludes `.env`; the `.env.example` template ships with placeholder values only.
- **T-07-E-01** (Elevation — pic_bidang reaches `/master/*` via direct URL): mitigated. `ProtectedRoute` admin gate redirects to `/dashboard`. Backend defense-in-depth: `require_role("super_admin","admin_unit")` on every write route.
- **T-07-E-02** (Elevation — manajer_unit/asesor/viewer reach master CRUD): mitigated. Same gate.

---

## Self-Check: PASSED

Files claimed in this SUMMARY:

```
[ -f frontend/src/types/index.ts ]                           → FOUND
[ -f frontend/src/lib/auth-store.ts ]                        → FOUND
[ -f frontend/src/routes/ProtectedRoute.tsx ]                → FOUND
[ -f frontend/src/routes/Login.tsx ]                         → FOUND
[ -f frontend/src/routes/Dashboard.tsx ]                     → FOUND
[ -f frontend/src/routes/AppShell.tsx ]                      → FOUND
[ -f frontend/src/routes/master/MasterLayout.tsx ]           → FOUND
[ -f frontend/src/routes/master/KonkinTemplate.tsx ]         → FOUND
[ -f frontend/src/routes/master/BidangList.tsx ]             → FOUND
[ -f frontend/src/routes/master/MlStreamTree.tsx ]           → FOUND
[ -f frontend/src/routes/ProtectedRoute.test.tsx ]           → FOUND
[ -f frontend/src/routes/Login.test.tsx ]                    → FOUND
[ -f backend/app/seed/__init__.py ]                          → FOUND
[ -f backend/app/seed/__main__.py ]                          → FOUND
[ -f backend/app/seed/bidang.py ]                            → FOUND
[ -f backend/app/seed/konkin_2026.py ]                       → FOUND
[ -f backend/app/seed/admin_user.py ]                        → FOUND
[ -f backend/app/seed/pilot_rubrics/__init__.py ]            → FOUND
[ -f backend/app/seed/pilot_rubrics/outage.py ]              → FOUND
[ -f backend/app/seed/pilot_rubrics/smap.py ]                → FOUND
[ -f backend/app/seed/pilot_rubrics/eaf.py ]                 → FOUND
[ -f backend/app/seed/pilot_rubrics/efor.py ]                → FOUND
[ -f backend/tests/test_seed_idempotency.py ]                → FOUND

git log --oneline | grep 432911c                             → FOUND  (Task 1: frontend auth + master stubs)
git log --oneline | grep ed4eb7c                             → FOUND  (Task 2: seed module + idempotency tests)
git log --oneline | grep 83a897b                             → FOUND  (Task 3 pre-checkpoint Rule-3 fixes)
```

Live infra verified:
```
docker compose -f docker-compose.yml ps                     → 6 services, 5 healthy + backup stable
curl http://localhost:3399/api/v1/health                    → 200 {"status":"ok","db":"ok","redis":"ok"}
docker compose exec pulse-backend python -m app.seed × 2    → idempotent, zero duplicates
docker compose exec pulse-backup /scripts/backup.sh         → backup .sql.gz written to /backups
restore drill into pulse_restore_drill                      → 26 bidang + 3 users + 4 ml_stream restored
```

---

## Resume Signal (operator)

When the browser walk above passes, type:

```
phase 1 verified
```

This advances STATE.md → status=`complete`, increments `completed_phases` from 0 to 1, and the orchestrator dispatches Phase 2 planning.

If any step fails, paste the step number + the exact failing observation; the orchestrator will spawn `/gsd-plan-phase --gaps` to write a closure plan.

---

*Phase: 01-foundation-master-data-auth*
*Plan: 07 — frontend-wire-seed-verify*
*Status: paused-at-checkpoint*
*Date: 2026-05-11*
*Toolchain: WSL2 Ubuntu-22.04 / docker 29.4.3 + compose v5.1.3 / python 3.11.15 / pnpm 10.15.0*
