# Phase 1: Foundation (Master Data + Auth) - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning
**Source:** Auto-derived from `.planning/intel/` (post-ingest of 12 docs)

<domain>
## Phase Boundary

**Goal (from ROADMAP.md):** User dapat login ke aplikasi PULSE dan menelusuri struktur master data Konkin 2026 (perspektif → indikator → stream ML rubrik) di lingkungan Docker Compose yang sudah berjalan, dengan branding, design system, dan kebijakan no-evidence-upload sudah aktif sejak hari pertama.

**Requirements scoped to this phase (16):**
- Auth & access — REQ-user-roles, REQ-auth-jwt, REQ-route-guards
- Master data — REQ-konkin-template-crud, REQ-dynamic-ml-schema, REQ-bidang-master
- Tech stack — REQ-frontend-stack, REQ-backend-stack
- Deployment — REQ-docker-compose-deploy, REQ-nginx-config
- Branding & design — REQ-pulse-branding (LOCKED), REQ-pulse-heartbeat-animation (LOCKED), REQ-skeuomorphic-design-system
- Operational — REQ-health-checks, REQ-no-evidence-upload (LOCKED), REQ-backup-restore

**Out of scope (deferred to later phases):**
- Self-assessment workflow (Phase 2)
- NKO calculator + dashboards (Phase 3)
- Compliance tracker + reports (Phase 4)
- AI features (Phase 5)
- Stream coverage beyond MVP pilot streams (Phase 6)

**MVP boundary check:** This phase is foundational, not on the MVP-usable boundary (which is end of Phase 3). Output of Phase 1 is a runnable shell — login, navigate master data, see seeded Konkin 2026 structure.

</domain>

<decisions>
## Implementation Decisions

### Branding & Identity (LOCKED — DEC-001, DEC-002)
- App name: **PULSE** (Performance & Unit Live Scoring Engine). Zero residual `SISKONKIN` references in repo (`grep -ri "siskonkin"` = 0 hits acceptance criterion).
- Tagline (id): "Denyut Kinerja Pembangkit, Real-Time."
- Container/network/db identifiers post-rebrand: `pulse-net`, `pulse-db`, `pulse-redis`, `pulse-backend`, `pulse-frontend`, `pulse-nginx`. DB name `pulse`, user `pulse`, host `pulse.tenayan.local`, backup dir `/var/backups/pulse`.

### Design System (LOCKED — DEC-003, DEC-010)
- Default theme: dark, "control-room digital". Light theme is a variant only.
- Pulse Heartbeat signature animation: LED pulse 60–80 BPM in healthy state, increases on alert. CSS keyframes `pulse-heartbeat` for `.sk-led[data-state="on"]` (login page must show this on day one).
- **Heartbeat alert glow (B-03 fix):** the keyframe MUST NOT hardcode the glow color. Either (a) ship two keyframes — `pulse-heartbeat-healthy` (yellow glow `--sk-pln-yellow-glow`) and `pulse-heartbeat-alert` (red glow on `--sk-led-alert-glow` token derived from L0 red `#ef4444`) — or (b) parameterize via a CSS custom property `--sk-led-glow` that is set per `data-state`. Test contract: `SkLed.test.tsx` asserts the alert state's computed glow color differs from the healthy state's.
- **Phase-1 skeuomorphic primitives (W-01 fix):** Phase 1 ships SIX primitives — `SkLed`, `SkButton`, `SkPanel`, **`SkInput`**, **`SkSelect`**, **`SkBadge`** — all consumed by the Login + Master Data screens. The remaining five (`SkScreenLcd`, `SkDial`, `SkGauge`, `SkSlider`, `SkToggle`) are deferred: `SkScreenLcd` + `SkDial` + `SkGauge` to Phase 3 (dashboards), `SkSlider` + `SkToggle` to Phase 2 (assessment forms). Login.tsx + master-data screens MUST consume `SkInput`/`SkSelect`/`SkBadge`/`SkButton`/`SkPanel`/`SkLed` — no raw `<input>` / `<select>` / `<button>` tags on those screens.
- **Skeuomorphic barrel file (W-10 fix):** `frontend/src/components/skeuomorphic/index.ts` re-exports all six Phase-1 primitives so consumers can `import { SkLed, SkButton, SkPanel, SkInput, SkSelect, SkBadge } from "@/components/skeuomorphic"`.
- Design tokens (CSS custom properties under `:root`): per `CONSTR-design-tokens`. Brand palette: `--sk-pln-blue #1e3a8a`, `--sk-pln-yellow #fbbf24`. Level palette L0–L4 red→emerald. LCD green `#4ade80` with glow.
- Typography: Bebas Neue + Oswald (display), Barlow (body), JetBrains Mono (mono), Share Tech Mono / DSEG7 (LCD).
- Three pillars: Tactile, Industrial Refinement, Information First. Skeuomorphic primitives are keyboard-navigable (arrow keys for SkDial).

### Tech Stack (LOCKED — CONSTR-stack-*, DEC-010)
- Frontend: React 18 + Vite + TypeScript. State: TanStack Query v5 + Zustand. Forms: React Hook Form + Zod. Routing: React Router v6. Styling: Tailwind + custom skeuomorphic tokens. UI: shadcn/ui forked. Charts: Recharts/ECharts. Animation: framer-motion (Motion). Toast: Sonner.
- Backend: FastAPI on Python 3.11-slim. Gunicorn + UvicornWorker, 4 workers, 0.0.0.0:8000. Pydantic, SQLAlchemy + asyncpg, Alembic.
- Database: PostgreSQL 16+ with `uuid-ossp`, `pgcrypto`, `vector` (pgvector ivfflat cosine). UUID PKs everywhere; JSONB for dynamic schemas.
- Cache: Redis 7-alpine, maxmemory 256mb, allkeys-lru.
- Deploy: Docker Compose, Nginx reverse proxy on host port 3399. Postgres never exposed publicly.

### Auth (DEC-locked via DEC-010 + CONSTR-api-conventions, CONSTR-env-secrets)
- JWT auth. Bearer token OR httpOnly cookie. Access TTL 60 min, refresh 14 days.
- **All six roles from REQ-user-roles seeded in Phase 1, using spec naming verbatim:** `super_admin`, `admin_unit`, `pic_bidang`, `asesor`, `manajer_unit`, `viewer`. (Earlier draft of this CONTEXT.md said "three roles" — that was a scope-reduction error; corrected per plan-checker B-01/B-02. Reasoning: REQ-user-roles + REQ-route-guards both reference these exact identifiers; downstream phases will rely on them.)
- Role-based routing per REQ-route-guards: `/master/*` requires `super_admin` or `admin_unit`; `pic_bidang` is redirected to `/dashboard`; access scoped by `bidang_id`. ROADMAP.md success criterion #1 ("Admin dapat login…") refers to a user with role `admin_unit`.
- Frontend `Role` type union, backend `require_role(*roles)` calls, seed migration, ProtectedRoute `allow` lists, and ROADMAP success criterion #1 must ALL use this 6-role spec naming consistently.
- Required env vars: `APP_SECRET_KEY`, `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`. Secrets in `.env`, never committed.
- **First admin via `.env`** (per RESEARCH OQ#3, ADOPTED): seed reads `INITIAL_ADMIN_EMAIL` + `INITIAL_ADMIN_PASSWORD` and creates one `admin_unit` user idempotently if no user with that email exists. Password rotation expected immediately after first login.

### Data Model (LOCKED — DEC-010, CONSTR-data-model-core-tables)
- All PKs `UUID PRIMARY KEY DEFAULT uuid_generate_v4()`. No sequential int IDs in URLs.
- Audit columns on every table: `created_at, updated_at, created_by, updated_by`. Soft delete via `deleted_at` on critical entities.
- `ml_stream.structure` is JSONB with GIN index. Each stream owns its area/sub-area/criteria tree.
- Versioning via `konkin_template` rows + `ml_stream.version`.
- Phase-1 seed scope: bidang master, Konkin 2026 PLTU Tenayan template (perspektif + indikator + bobot), pilot rubrics for Outage / SMAP / EAF / EFOR streams.
- **Pengurang bobot convention (locked here, was W-07):** Perspektif VI (Compliance) is a *pengurang* (negative contribution capped at -10). Stored representation: `bobot = 0.00` on the perspektif row + `is_pengurang BOOLEAN NOT NULL DEFAULT FALSE` + `pengurang_cap NUMERIC(5,2) NULL` columns on the `perspektif` table. Phase-1 lock validator on `konkin_template` SUMs only `bobot WHERE is_pengurang = FALSE` and asserts equals 100.00 ± 0.01. Phase-3 NKO calculator subtracts from gross NKO using `pengurang_cap` (max -10 for VI). This avoids the alternative of storing `-10.00` and special-casing the validator.
- **konkin_import_log table** (per RESEARCH OQ#2, ADOPTED): added in master-data migration with columns `id UUID PK, template_id UUID FK, idempotency_key TEXT UNIQUE, imported_at TIMESTAMP, summary JSONB, created_at, updated_at`.
- **Migration FK ordering (B-04 fix):** the `users.bidang_id` column is declared and FK-constrained ENTIRELY in the master-data migration (after the `bidang` table is created), NOT in the auth migration. The auth migration's `users` table has no `bidang_id` column.

### API (LOCKED — CONSTR-api-versioning, CONSTR-api-conventions, CONSTR-no-file-upload)
- Base: `/api/v1`. JSON UTF-8. Pagination `?page=&page_size=` with `{data, meta}` envelope. Sort `?sort=-created_at`. Error envelope `{error: {code, message, details}}`.
- Auth header `Authorization: Bearer <jwt>` or httpOnly cookie.
- Status codes: 200/201/204/400/401/403/404/409/422/500.
- Health: `GET /api/v1/health` must return 200. Additional: `GET /api/v1/health/detail` (admin-only, DB+Redis connectivity probe) and `GET /api/v1/metrics` (admin-only, Prometheus text format) per REQ-health-checks (W-02 fix).
- **No evidence-file upload endpoints.** Only `link_eviden` URL fields. Single multipart endpoint allowed: admin-only `POST /konkin/templates/{id}/import-from-excel`.
- **CSRF on the Excel-import endpoint (B-07 fix):** `import-from-excel` MUST require CSRF (`Depends(require_csrf)`) like every other mutating cookie-reachable route. The earlier "Bearer-only" rationale was wrong — the frontend uses cookie auth with `withCredentials: true`. CSRF token sent via `X-CSRF-Token` header (existing pattern).
- **OpenAPI no-upload introspection test (per RESEARCH OQ#5, ADOPTED):** in-process `app.openapi()` test asserts EXACTLY one multipart endpoint AND that it is `POST /konkin/templates/{id}/import-from-excel`.
- OpenAPI: Swagger at `/api/v1/docs`, ReDoc at `/api/v1/redoc` (may be auth-gated/disabled in prod).

### Deployment (LOCKED — CONSTR-host-port, CONSTR-network-naming, CONSTR-backup, CONSTR-security-headers)
- Nginx publishes host port 3399 (HTTP) or 443 (HTTPS) only.
- Security headers (Nginx): `X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `X-XSS-Protection`, `Strict-Transport-Security`, `Referrer-Policy strict-origin-when-cross-origin`. CSRF on cookie-based endpoints.
- Daily backup: `pg_dump | gzip` at 02:00 → `${BACKUP_DIR}`. 30-day retention. Weekly rsync to NAS at 03:00 Sunday. Restore script accepts a backup filename, pipes into `psql`.
- Default i18n: Bahasa Indonesia formal. Structure ready for later English.
- Accessibility: WCAG AA minimum; semantic HTML + ARIA; keyboard nav.

### Test Infrastructure (LOCKED — Wave 0 placement, B-06 fix)
- Test scaffolds (`backend/pyproject.toml [dev] extras`, `backend/tests/conftest.py`, `frontend/vite.config.ts test block`, `frontend/src/test/setup.ts`, vitest globals types in tsconfig) are created in **Wave 0**, BEFORE any feature task references pytest or vitest as `<automated>`.
- **Vitest globals (B-05 fix):** `frontend/tsconfig.app.json` MUST include `"types": ["vitest/globals", "@testing-library/jest-dom"]` in `compilerOptions` so `describe`/`it`/`expect` resolve under tsc.
- After Wave 0, every Wave-2/3/4 task that creates source code in module X MUST have an `<automated>` block that ACTUALLY runs `pytest backend/tests/test_X.py -x` (or `pnpm exec vitest run src/.../X.test.tsx`) — not just an `ast.parse` shim. Where the test depends on a running container, use `docker compose exec pulse-backend pytest …`.
- **Docker preflight gate:** every Wave-2+ `<automated>` block that shells to `docker` runs `docker info` first; failure exits early with a clear message.

### Claude's Discretion
- Project layout (monorepo vs split). Recommended: monorepo with `frontend/`, `backend/`, `nginx/`, `infra/backup/`, `docker-compose.yml`, `.env.example` at root.
- Migration tool concrete naming (Alembic versioning scheme).
- Seed data file format (SQL fixtures vs Python scripts vs YAML+loader).
- Specific shadcn/ui component fork strategy (copy-into-repo recommended over npm dep).
- Error/log structure beyond "structured JSON to stdout".
- CI scaffolding scope (out of phase, but if added must not conflict with Phase 6 prod-checklist).
- Backup sidecar cron daemon choice: `dcron` is recommended over `busybox-suid` for Alpine stability (W-08).
- `pulse-frontend` deployment shape: separate Nginx container serving the Vite build, with `pulse-nginx` (the public-facing reverse proxy) upstream'ing to it (per RESEARCH OQ#1, ADOPTED).
- `make seed` invocation: shells `docker compose exec pulse-backend python -m app.seed` for dev (per RESEARCH OQ#4, ADOPTED).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Authoritative project state (always read first)
- `.planning/PROJECT.md` — locked decisions block, project facts
- `.planning/ROADMAP.md` §"### Phase 1: Foundation (Master Data + Auth)" — phase goal + success criteria
- `.planning/REQUIREMENTS.md` §A, §B, §O, §P, §Q, §R, §S — all 16 Phase-1 requirements
- `.planning/intel/decisions.md` — all 11 ADR-locked decisions (DEC-001…DEC-011)
- `.planning/intel/constraints.md` — 26 constraints (read all; many are foundational)

### Source docs (background; the planning files above are the source of truth)
- `01_DOMAIN_MODEL.md` — Kontrak Kinerja business context, hierarchy
- `02_FUNCTIONAL_SPEC.md` §1 (User Roles), §3 (Master Data module), §4 (Auth & RBAC)
- `03_DATA_MODEL.md` §1 (principles), §3.1 (extensions), §3.3 (ml_stream JSONB), §3.5 (assessment_session JSONB stub)
- `04_API_SPEC.md` §1 (conventions), §2 (Auth), §3 (Master Data), §16 (rate limits + no-upload), §17 (OpenAPI)
- `05_FRONTEND_ARCHITECTURE.md` §1 (stack), §2 (routing), §7 (a11y), §8 (i18n)
- `06_DESIGN_SYSTEM_SKEUOMORPHIC.md` §1 (philosophy), §2 (tokens), §"Tema Pulse — Sinyal Kehidupan Pembangkit" (added per DEC-003)
- `08_DEPLOYMENT.md` §1 (architecture), §3 (.env), §4 (compose services), §5 (Dockerfiles), §7 (Nginx config), §9 (backup)
- `UPDATE-001-pulse-rebrand-ai-features.md` §1.1–§1.5, §3.2 — rebrand authority + locked clarifications
- `intel/context.md` §11 — verbatim Phase 1 deliverable list from `09_DEVELOPMENT_ROADMAP.md` §3

### Refs explicitly NOT to read in Phase 1 planning
- `07_AI_INTEGRATION.md` — Phase 5 only
- `03_DATA_MODEL.md` `ai_inline_help` table (DEC-006) — Phase 5

</canonical_refs>

<specifics>
## Specific Ideas

### Login screen (verbatim from success criterion #3)
- Tagline displayed: "Denyut Kinerja Pembangkit, Real-Time."
- Pulse Heartbeat LED visible at 60–80 BPM equivalent.
- Branding word `PULSE` prominent.

### Seed scope (success criterion #4)
- `make seed` (or equivalent script) populates:
  - bidang master (full PLTU Tenayan list)
  - Konkin 2026 PLTU Tenayan template (perspektif + indikator + bobot, full set per `01_DOMAIN_MODEL.md`)
  - Maturity-Level rubrics for pilot streams: Outage Management, SMAP, EAF, EFOR (full criteria trees in `ml_stream.structure` JSONB)
- Zero errors; idempotent (can be re-run).

### Health check (success criterion #4)
- `GET /api/v1/health` returns 200 with structured JSON `{status, db, redis, version}`. Used by Docker healthcheck and Nginx upstream.

### Acceptance for no-upload policy (success criterion #5)
- No multipart endpoint exists in OpenAPI spec EXCEPT `POST /konkin/templates/{id}/import-from-excel` (admin-only).
- `link_eviden` field accepts URL only (Pydantic `HttpUrl` or equivalent regex).
- Test that asserts `OPENAPI` doc has exactly one multipart endpoint.

### Backup acceptance (success criterion #6)
- Cron entry installed on VPS calling backup script at 02:00.
- Restore script tested manually once before phase sign-off.

</specifics>

<deferred>
## Deferred Ideas

- HCR (Human Capital Readiness) → Phase 6 batch (DEC-010).
- AI features (any) → Phase 5.
- Self-assessment workflow → Phase 2.
- Reports/exports → Phase 4.
- SSL/TLS strategy → deploy time, end of Phase 6 (DEC-011).
- Final logo → placeholder for now (DEC-011).
- OpenRouter API key provisioning → before Phase 5 (Budi handles directly, DEC-011).
- External integrations (Navitas, SAP) → Phase 2+ post-MVP (DEC-011).

</deferred>

---

*Phase: 01-foundation-master-data-auth*
*Context derived: 2026-05-11 from `.planning/intel/` synthesis (no discuss-phase run)*
