# Phase 2: Assessment Workflow (PIC + Asesor) — Research

**Researched:** 2026-05-11
**Domain:** Stateful assessment workflow, offline-safe auto-save, real-time notifications, audit logging
**Confidence:** HIGH overall (library picks verified against npm/PyPI; patterns cross-checked against Phase 1 SUMMARYs and official FastAPI/Starlette docs)

---

## Summary

Phase 2 sits on top of Phase 1's hardened seam (auto-discovered routers + models, async SQLAlchemy 2 + Alembic chain, six-spec-role RBAC + `require_role` + `require_csrf` + Redis-backed refresh tokens + axios with CSRF echo + Zustand auth store, Vite/Vitest/jsdom + WSL2 toolchain). The phase delivers four new operational surfaces — **periode lifecycle**, **PIC self-assessment forms (KPI + ML)**, **asesor review + recommendation tracker**, and **in-app/WebSocket notifications + audit log** — and three new SK primitives (`SkLevelSelector`, `SkSlider`, `SkToggle`).

User decisions are locked in CONTEXT.md (16 sub-decisions). This research does NOT re-decide them — it picks libraries, prescribes patterns, and lists pitfalls so the planner can write tight plans.

**Primary recommendation:** Ship Phase 2 in **6 plans across 4 waves** — see §12. Stack additions are minimal (one new npm package `use-debounce`, one new npm package `idb`, one new npm dev package `fake-indexeddb`, zero new Python packages — FastAPI 0.136 already speaks WebSocket and httpx 0.28 already speaks `websocket_connect`). The auto-save / WebSocket / audit-middleware patterns described below are all hand-rolled on top of Phase 1's primitives — no heavyweight FSM library, no notification framework, no audit-log SaaS.

---

## User Constraints (from CONTEXT.md)

> Verbatim copy of 02-CONTEXT.md `<decisions>` and `<deferred_ideas>`. Planner MUST honor these — do NOT re-decide.

### Locked Decisions

**Periode Lifecycle:**

- **DEC-T1-001:** All transitions manual via super_admin (no scheduler in Phase 2). States `draft → aktif → self_assessment → asesmen → finalisasi → closed`. Per-transition buttons on periode-admin screen. Side effects: `aktif → self_assessment` auto-creates `assessment_session` rows per DEC-T1-004; `finalisasi → closed` runs carry-over per DEC-T4-004 and marks `state=draft` self-assessments as `abandoned`.
- **DEC-T1-002:** super_admin can rollback closed periode to any prior state via "Reopen ke <State>" button with mandatory reason field (min 20 chars). Audit log captures before_state, after_state, reason, user_id, timestamp. Carry-over is irreversible (carried recs stay where they moved).
- **DEC-T1-003:** Aggregate indikator (EAF/EFOR) = 1 shared session + assessment_session_bidang N:N table. `assessment_session.bidang_id` is NULL for aggregate sessions. New table `assessment_session_bidang(session_id, bidang_id, PK(session_id, bidang_id))`. Last-write-wins per DEC-T2-003.
- **DEC-T1-004:** Skip session creation for non-applicable (indikator, bidang) pairs. New mapping table `indikator_applicable_bidang(indikator_id, bidang_id, PK(indikator_id, bidang_id))`. Expected ~150–250 sessions per periode (not ~1300).

**Self-Assessment Forms:**

- **DEC-T2-001:** `SkLevelSelector` = horizontal 5-segment slider + LED row above (NOT rotary dial). Component name stays `SkLevelSelector`. Tap segment or drag handle; arrow keys to step.
- **DEC-T2-002:** Sub-level continuous slider always-on below LevelSelector, range tracks current level (L3 → 3.01–4.00). Increment 0.01. Plain numeric span with LCD font + `--sk-lcd-green` token until Phase 3 ships `SkScreenLcd`. "Lock to integer" toggle uses `SkToggle`.
- **DEC-T2-003:** Last-write-wins + server-clock + IndexedDB offline queue. No locking. `Saved Xs ago` from server `updated_at`. On reconnect drain queue oldest-first. Persistent toast while pending > 0.
- **DEC-T2-004:** HARD submit gate — disabled until every sub-area has a value OR explicit "Tidak dinilai" toggle on with mandatory reason ≥ 10 chars. Counter pill "Y dari Y lengkap". Server-side re-validates on submit (422 if violated).
- **DEC-T2-005:** Polarity-aware formula compute is **client-side preview + server-side authority**. Client: `(R/T)*100` positif, `{2 - (R/T)}*100` negatif, three-band range per `01_DOMAIN_MODEL.md` §4.1. Server re-computes on every auto-save and Submit; client preview is UX only.

**Asesor Review:**

- **DEC-T3-001:** Override justification min 20 chars, mandatory, free-form. `POST /assessment/sessions/{id}/asesor-review` with `decision="override"` requires `catatan_asesor.length >= 20`. `nilai_final` required on override; auto-set to PIC's `nilai` on approve; NULL on request_revision.

**Recommendation Tracker:**

- **DEC-T4-001:** Default owner = PIC of source assessment (looked up via `bidang_id → users.bidang_id`). Asesor can override per `action_items[i].owner_user_id`. If looked-up PIC user is deactivated/deleted, field is empty and asesor must pick before save.
- **DEC-T4-002:** No SLA timeout, no auto-escalation in Phase 2.
- **DEC-T4-003:** Lifecycle states `open → in_progress → pending_review → closed` (or `carried_over`). PIC PATCH `/progress` flips `open → in_progress`; PIC POST `/mark-completed` flips to `pending_review`; asesor POST `/verify-close` flips to `closed`. Asesor can manually close (with notes, audit-logged) without going through pending_review.
- **DEC-T4-004:** Carry-over on `finalisasi → closed`. Carried: `open | in_progress | pending_review`. Not carried: `closed`. New row in next periode with `carried_from_id`, original's `carried_to_id`. `source_assessment_id` preserved (chain visible). `status` preserved. `target_periode_id` resolves to next TW (TW2 → TW3; TW4 → next year TW1). If next periode doesn't exist, carry-over is queued and runs when next periode transitions to `aktif`. Draft self-assessments at close marked `state=abandoned`.

**Notifications:**

- **DEC-T5-001:** REQ-notifications scope reduced — in-app + WS only, **NO email/SMTP** in Phase 2. Explicit user direction. Reconsider in Phase 5 or Phase 6 prod-hardening.
- **DEC-T5-002:** 1 notif per event (no bundling). UI groups by date.
- **DEC-T5-003:** Six types — `assessment_due`, `review_pending`, `recommendation_assigned`, `deadline_approaching`, `periode_closed`, `system_announcement`. All in-app + WS (`system_announcement` is in-app only).

**Audit Log:**

- **DEC-T6-001:** Capture mutating actions + login/logout. All authenticated POST/PATCH/PUT/DELETE to `/api/v1/*` that returns `<400` + auth login (success and failure with reason) + logout. NOT captured: GET requests, `/auth/refresh`. Fields: `user_id, action (HTTP verb + route template), entity_type, entity_id, before_data, after_data, ip_address, user_agent, created_at`. Middleware-based (`AuditMiddleware`).
- **DEC-T6-002:** Same Postgres + retention forever. Indexes: `(user_id, created_at desc)`, `(entity_type, entity_id, created_at desc)`, `(created_at desc)`. No auto-purge. Append-only enforced — no PATCH/DELETE on `/audit-logs`. READ gated by `require_role("super_admin")`.

### Claude's Discretion

CONTEXT.md does NOT have a separate "Claude's Discretion" block — every choice that isn't in `<decisions>` is open for research-driven recommendation. Areas Claude must pick:

- Exact npm packages for debounce + IndexedDB (open question 1–2)
- WebSocket reconnect cadence numbers (open question 3)
- Whether to use middleware or dependency for audit (open question 4)
- FSM library vs hand-rolled (open question 5)
- Pydantic schema for `action_items` (open question 6)
- Diff library for conflict UI (open question 8 — defer to Phase 6)
- Test infrastructure pattern for WS + auto-save (general research)
- Audit-log payload size strategy (general research)
- Plan breakdown (waves + plans)

### Deferred Ideas (OUT OF SCOPE)

- **Email/SMTP notifications** — explicitly descoped (DEC-T5-001).
- **Date-driven periode scheduler** — manual only in Phase 2.
- **Recommendation SLA + escalation** — no timeout in Phase 2.
- **Auditor role** — `audit_log` read is super_admin only in Phase 2.
- **Audit log archive policy** — retention forever in Phase 2.
- **Optimistic locking on sessions** — last-write-wins; Phase 6 may add `version` column.
- **AI Suggestion button** — Phase 2 ships the BUTTON disabled with tooltip "Tersedia di Phase 5".
- **PWA push notif** — post-MVP.
- **Heatmap polish** — basic table-grid in Phase 2 OR defer styling to Phase 3.

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-periode-lifecycle | Status transitions draft → aktif → self_assessment → asesmen → finalisasi → closed, auto-create sessions, carry-over | §5 (state machine), §4 (audit middleware captures transitions), §12 Wave 2 (periode router) |
| REQ-self-assessment-kpi-form | Polarity-aware compute, link_eviden, save/submit | §1 (auto-save), DEC-T2-005 (server authoritative), §12 Wave 3 |
| REQ-self-assessment-ml-form | Dynamic area/sub-area tree from ml_stream.structure, discrete level + continuous slider, submit gate | §12 Wave 3 (SkLevelSelector + SkSlider + SkToggle build) |
| REQ-auto-save | 5s debounced PATCH, "Saved Xs ago", rollback toast | §1 (use-debounce useDebouncedCallback), §2 (idb queue), §9 (vitest fake timers) |
| REQ-pic-actions | Save draft, submit, withdraw, AI suggestion stub | §11 (anti-patterns — AI button disabled with tooltip) |
| REQ-asesor-review | approve/override/request_revision + inline recommendations | §6 (Pydantic action_items validator), §12 Wave 4 |
| REQ-recommendation-create | severity, action_items JSONB, target_periode_id | §6 (action_items schema) |
| REQ-recommendation-lifecycle | open → in_progress → pending_review → closed; carry-over chain | §5 (state machine reused pattern), §12 Wave 2 (carry_over service) |
| REQ-notifications | 6 types, in-app + WS push, mark-read endpoints | §3 (WS hook + reconnect), §7 (token query param) |
| REQ-audit-log | Append-only, mutating actions, indexed, super_admin read | §4 (middleware + tag-based entity_type), §10 (volume + indexing) |

---

## Project Constraints (from CLAUDE.md)

No CLAUDE.md exists at the project root. Top-level constraints are sourced from `.planning/intel/constraints.md` and `.planning/PROJECT.md`:

- **Toolchain via WSL2 Ubuntu-22.04** — every `python3.11`, `pnpm`, `pytest`, `docker compose` call goes through `wsl -d Ubuntu-22.04 -- <tool>`. Phase 1 SUMMARY explicitly: "all dev tooling lives inside `Ubuntu-22.04` WSL2 distro".
- **Auto-discovery for routers + models** — new files in `backend/app/routers/` and `backend/app/models/` are picked up with zero edits to `main.py` / `db/base.py`.
- **`require_role(*spec_names)`** — never capitalize. Six verbatim names: `super_admin`, `admin_unit`, `pic_bidang`, `asesor`, `manajer_unit`, `viewer`.
- **`require_csrf` on every mutating cookie-reachable route** — bearer-only callers (tests) skip via dep's standard rule. Frontend `api.ts` already echoes via `X-CSRF-Token`.
- **All PKs UUID**, JSONB for dynamic schemas, GIN index on hot JSONB columns.
- **No file upload** for evidence — `link_eviden` URL only (DEC-010). Excel import is the SOLE multipart endpoint and is admin-only.
- **Default UI BI** — every new user-facing string goes via `t()` from `@/lib/i18n`. Phase 2 ADDS keys for `assessment.*`, `periode.*`, `recommendation.*`, `notification.*`, `audit.*`.
- **All inputs through SK primitives** (W-01 contract) — no raw `<input>` / `<button>` / `<select>` on PIC/asesor screens.
- **Rate limits** — 100 req/min mutating per-user; 1000 req/min dashboard reads. Auto-save at 5s debounce → max 12 PATCH/min/user from a single editor — well inside the limit.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Periode lifecycle state machine | API / Backend | Database (status enum) | Authoritative state; super_admin-gated; side effects (session creation, carry-over) must be transactional. |
| Auto-save debounce + payload assembly | Browser / Client | — | Pure UX timing; cannot debounce server-side. |
| Auto-save persistence | API / Backend | Database (UPDATE assessment_session) | Authoritative store; server re-computes pencapaian (DEC-T2-005). |
| Offline queue (failed auto-save replay) | Browser / Client (IndexedDB) | — | By definition there's no network when this runs. |
| Pencapaian compute | API / Backend | Browser (preview only) | DEC-T2-005 says server is authoritative; client preview is UX only. |
| ML LevelSelector / SkSlider / SkToggle UI | Browser / Client | — | Pure presentation primitives. |
| Submit gate UI (counter + disabled state) | Browser / Client | API / Backend (re-validates on submit) | Two-tier — UX feedback up front, server enforcement at the gate. |
| Asesor decision (approve/override/request_revision) | API / Backend | — | Locked nilai_final write must be server-controlled. |
| Recommendation create | API / Backend | — | Cross-entity links (source_assessment_id, action_items owner_user_id resolution) must run server-side. |
| Recommendation lifecycle transitions | API / Backend | Database (status enum) | Same pattern as periode FSM. |
| Carry-over on periode close | API / Backend | Database (carried_from_id / carried_to_id FK chain) | Must be transactional with periode state transition. |
| Notification persistence | API / Backend | Database (notification table) | Source of truth + history for `/notifications` list. |
| Notification push | API / Backend (WebSocket) | Browser (WS consumer) | Push side is server; subscribe side is client. |
| Notification reconnect / backoff | Browser / Client | — | Pure transport concern. |
| Audit-log write | API / Backend (Middleware) | Database | Captures every mutating request; defense-in-depth even if route forgets to log. |
| Audit-log read | API / Backend | — | super_admin-only `GET /audit-logs`. |

---

## Standard Stack

> NO new heavyweight libraries. Three new packages on the frontend, ZERO new packages on the backend.

### Core additions (frontend)

| Library | Version (verified) | Purpose | Why Standard |
|---------|--------------------|---------|--------------|
| `use-debounce` | `^10.1.1` (published 2026-03-29) [VERIFIED: `npm view use-debounce version` → 10.1.1] | `useDebouncedCallback` hook for 5s auto-save trigger | Most popular debounce hook for React; small (~1KB); supports `leading`, `trailing`, `maxWait`, `.cancel()`, `.flush()`. Phase 1 didn't ship it; Phase 2 brings it in. |
| `idb` | `^8.0.3` (published 2025-05-07) [VERIFIED: `npm view idb version` → 8.0.3] | IndexedDB promise wrapper for offline queue | Jake Archibald's wrapper, ~1KB, thinnest IDB abstraction, ~9.3M weekly downloads (vs Dexie 727k / localforage 4.8M). Promise-based, TypeScript-typed, no schema DSL — fits our single-queue-table use case perfectly. [CITED: https://www.npmjs.com/package/idb] |

### Dev additions (frontend)

| Library | Version (verified) | Purpose | Why Standard |
|---------|--------------------|---------|--------------|
| `fake-indexeddb` | `^6.2.5` [VERIFIED: `npm view fake-indexeddb version` → 6.2.5] | jsdom-side mock of IndexedDB for vitest tests | Pure JS in-memory IDB implementation. Used by Mozilla, Firefox SDK, etc. `import "fake-indexeddb/auto"` puts `indexedDB` on `globalThis` for the entire test run. [CITED: https://www.npmjs.com/package/fake-indexeddb] |

### Backend additions

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| (none) | — | — | FastAPI 0.136.1 ships `WebSocket` + `WebSocketDisconnect` in the public API. httpx 0.28.1 ships `websocket_connect` (used via Starlette's `TestClient` for tests). Pydantic 2.13 ships `model_validator(mode='after')`. SQLAlchemy 2.0.49 ships `event.listens_for` (used optionally — see §4). No new pip packages needed. [VERIFIED: backend/pyproject.toml] |

### Alternatives Considered (and rejected)

| Instead of | Could Use | Why we picked the standard |
|------------|-----------|---------------------------|
| `use-debounce` | Hand-rolled `useEffect` + `setTimeout` cleanup | Hand-rolled is ~10 lines but the maintenance burden (cleanup on unmount, dep-array correctness, `.flush()` for last-write-on-submit) is exactly what `use-debounce` solves. Vendored hand-rolls are how React apps grow stale. |
| `idb` (~1KB) | `dexie` (~22KB) | Dexie is overkill — we have one table (queue per session per user), one schema (incrementing key, JSONB payload, retry_count), and we read FIFO and delete on success. Dexie's `useLiveQuery` is a nice ergonomic but Phase 2 doesn't need reactive IDB. |
| `idb` | `localforage` (~9KB) | localforage's setItem/getItem is the wrong abstraction for an ordered FIFO queue. We'd be reimplementing the ordering on top. |
| `idb` | Direct `window.indexedDB` API | Direct API is callback-hell and you'd hand-roll the promise wrapper. We'd be reimplementing what `idb` already is. |
| Hand-rolled FSM | `transitions` (Python, 0.9.3) | 6 states + ~12 transitions (6 forward + 5 rollback + 1 abandoned-on-close) is too small to justify a dependency. Same call for `recommendation.status` (4 states + carry-over). Hand-rolled enum + transition-map dict is clearer for code review. [VERIFIED: `pip index versions transitions` → 0.9.3] |
| Middleware-based audit | Dependency-based audit (per-route `Depends(audit(...))`) | Middleware is opt-out (default coverage for every mutating route); dependency is opt-in (every new route is a chance to forget). DEC-T6-001 wants default coverage. The middleware reads route tag for `entity_type` resolution — see §4. |
| `dexie-react-hooks` | n/a | We don't need reactive IDB — we drain the queue from a single hook, not via component subscriptions. |

**Installation:**

```bash
wsl -d Ubuntu-22.04 -- bash -c 'cd /mnt/c/Users/ANUNNAKI/projects/PULSE/frontend && pnpm add use-debounce@^10.1.1 idb@^8.0.3 && pnpm add -D fake-indexeddb@^6.2.5'
```

Backend: no `pip install` needed. Pydantic 2.13 + FastAPI 0.136 + SQLAlchemy 2.0 + httpx 0.28 + pytest-asyncio 1.3 are already pinned by Phase 1's `pyproject.toml` and provide every primitive Phase 2 needs (WebSocket, `model_validator`, `event.listens_for`, `websocket_connect` for tests).

**Version verification:** All four packages confirmed against npm registry on 2026-05-11. `use-debounce` 10.1.1 (published 2026-03-29) is current; `idb` 8.0.3 (published 2025-05-07) is the latest 8.x line; `fake-indexeddb` 6.2.5 is current; `transitions` 0.9.3 was checked for completeness even though we're not adopting it.

---

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────── Browser ─────────────────────────┐
│                                                         │
│  /pic/self-assessment/:id                               │
│    KPI form OR ML form                                  │
│         │                                               │
│         ▼ user types                                    │
│  React Hook Form state                                  │
│         │                                               │
│         ▼ debounced 5s (useDebouncedCallback)           │
│  useAutoSave(sessionId, payload)                        │
│         │                                               │
│         ├──── PATCH /assessment/sessions/:id ──────────┐│
│         │       (axios + CSRF echo)                     ││
│         │                                               ││
│         └── on failure ──▶ idb.put("queue", payload) ───┤│
│                                  │                      ││
│              window 'online' ────┘                      ││
│                  ▼                                      ││
│           drain queue oldest-first ─────────────────────┘│
│                                                         │
│  useNotifications() ─── WS /ws/notifications?token=─────┐
│         │                                               ││
│         ▼                                               ││
│  Zustand notificationStore (badge + list)               ││
│                                                         │
└──────────────────────────│──────────────────────────────┘
                           │ HTTPS / WSS
                           ▼
┌──────────────── nginx (3399) ───────────────────────────┐
│  /api/v1/* → pulse-backend:8000                         │
│  /ws/*    → pulse-backend:8000 (upgrade headers)        │
└──────────────────────────│──────────────────────────────┘
                           │
                           ▼
┌────────── FastAPI app (pulse-backend) ──────────────────┐
│                                                         │
│  AuditMiddleware (entrance)                             │
│      │                                                  │
│      ▼                                                  │
│  require_csrf  →  require_role                          │
│      │                                                  │
│      ▼                                                  │
│  Router handlers                                        │
│      │                                                  │
│      ├──▶ periode router       (state machine + side fx)│
│      │       │                                          │
│      │       ▼                                          │
│      │   session_creator service (DEC-T1-003/004)       │
│      │   carry_over service (DEC-T4-004)                │
│      │                                                  │
│      ├──▶ assessment_session router (auto-save / submit)│
│      │       │                                          │
│      │       ▼                                          │
│      │   pencapaian compute (DEC-T2-005 authoritative)  │
│      │                                                  │
│      ├──▶ recommendation router (lifecycle, action_items)│
│      ├──▶ notification router (CRUD + mark-read)        │
│      ├──▶ ws_notifications WebSocket endpoint           │
│      └──▶ audit_log router (super_admin read only)      │
│                                                         │
│  notification_dispatcher service (DB insert + WS push)  │
│  ws_manager singleton (user_id → ws connection registry)│
│                                                         │
│  AuditMiddleware (exit) ──▶ INSERT audit_log row        │
│      after response.status < 400                        │
│                                                         │
└──────────────────────────│──────────────────────────────┘
                           │ asyncpg
                           ▼
┌──────────────── Postgres 16 ────────────────────────────┐
│  periode, assessment_session, assessment_session_bidang,│
│  indikator_applicable_bidang, recommendation,           │
│  notification, audit_log                                │
│                                                         │
│  Migrations 0004 → 0005 → 0006 (chain on 0003)          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────── Redis 7 ────────────────────────────────┐
│  Refresh-token revocation set (existing from Plan 05)   │
│  Brute-force lockout counters (existing)                │
│  (Optional Phase 2 use: WS connection presence)         │
└─────────────────────────────────────────────────────────┘
```

The diagram traces a representative user flow: PIC types in a form → auto-save debounce → PATCH → server stores + audit-log writes → notification dispatcher pushes via WS to asesor → asesor sees badge update without refresh.

### Recommended Project Structure (additions)

```
backend/app/
├── models/
│   ├── periode.py                       # NEW
│   ├── assessment_session.py            # NEW
│   ├── assessment_session_bidang.py     # NEW
│   ├── indikator_applicable_bidang.py   # NEW
│   ├── recommendation.py                # NEW
│   ├── notification.py                  # NEW
│   └── audit_log.py                     # NEW
├── schemas/
│   ├── periode.py                       # NEW
│   ├── assessment.py                    # NEW
│   ├── recommendation.py                # NEW
│   ├── notification.py                  # NEW
│   └── audit.py                         # NEW
├── routers/
│   ├── periode.py                       # NEW (state machine + side fx)
│   ├── assessment_session.py            # NEW (PIC list/get/patch/submit/withdraw + asesor-review)
│   ├── recommendation.py                # NEW (create/progress/mark-completed/verify-close/carry-over)
│   ├── notification.py                  # NEW (list/mark-read)
│   ├── ws_notifications.py              # NEW (WebSocket endpoint)
│   └── audit_log.py                     # NEW (super_admin read)
├── services/
│   ├── audit_middleware.py              # NEW (registers AuditMiddleware)
│   ├── notification_dispatcher.py       # NEW (db + ws)
│   ├── session_creator.py               # NEW (called by periode transition)
│   ├── carry_over.py                    # NEW (called by periode close)
│   ├── ws_manager.py                    # NEW (user_id → ws registry)
│   ├── periode_fsm.py                   # NEW (hand-rolled state machine)
│   └── recommendation_fsm.py            # NEW (hand-rolled state machine)
├── deps/
│   └── ws_auth.py                       # NEW (WebSocket token validator)
├── alembic/versions/
│   ├── ?_0004_periode_and_sessions.py   # NEW
│   ├── ?_0005_recommendation_notif.py   # NEW
│   └── ?_0006_audit_log.py              # NEW

frontend/src/
├── lib/
│   ├── auto-save.ts                     # NEW (idb queue + drain)
│   └── notification-store.ts            # NEW (Zustand)
├── hooks/
│   ├── useAutoSave.ts                   # NEW (debounce + IDB fallback)
│   ├── useNotifications.ts              # NEW (WS reconnect + dispatch)
│   └── usePeriodeStore.ts               # NEW (Zustand current periode)
├── routes/
│   ├── periode/
│   │   ├── PeriodeList.tsx              # NEW (super_admin index)
│   │   └── PeriodeDetail.tsx            # NEW (transitions + sessions overview)
│   ├── pic/
│   │   ├── SelfAssessmentInbox.tsx      # NEW
│   │   ├── KpiForm.tsx                  # NEW
│   │   ├── MlForm.tsx                   # NEW (data-driven tree)
│   │   └── PicRecommendations.tsx       # NEW
│   ├── asesmen/
│   │   ├── AsesorInbox.tsx              # NEW
│   │   └── AsesmenReview.tsx            # NEW (decision + inline rec form)
│   ├── recommendations/
│   │   └── RecommendationList.tsx       # NEW
│   ├── Notifications.tsx                # NEW
│   └── AuditLogs.tsx                    # NEW (super_admin)
└── components/skeuomorphic/
    ├── SkLevelSelector.tsx              # NEW (DEC-T2-001)
    ├── SkSlider.tsx                     # NEW (DEC-T2-002)
    └── SkToggle.tsx                     # NEW (DEC-T2-002)
```

### Pattern 1: Auto-save with `useDebouncedCallback` (HIGH confidence)

**What:** Trigger PATCH 5 seconds AFTER last keystroke (NOT every 5s while typing).

**When to use:** Any draft-mode form where users edit incrementally (KPI form, ML form).

**Example:**

```ts
// frontend/src/hooks/useAutoSave.ts
import { useEffect, useRef, useState } from "react";
import { useDebouncedCallback } from "use-debounce";
import { api } from "@/lib/api";
import { enqueue, drainQueue } from "@/lib/auto-save";

type Status = "idle" | "saving" | "saved" | "error" | "queued-offline";

export function useAutoSave<TPayload>(
  sessionId: string,
  payload: TPayload,
) {
  const [status, setStatus] = useState<Status>("idle");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const last = useRef<TPayload | null>(null);

  const debounced = useDebouncedCallback(
    async (p: TPayload) => {
      setStatus("saving");
      try {
        const { data } = await api.patch(
          `/assessment/sessions/${sessionId}/self-assessment`,
          p,
        );
        setUpdatedAt(data.updated_at);   // DEC-T2-003: server clock
        setStatus("saved");
      } catch (err) {
        // Network down or 5xx: enqueue locally, surface persistent toast
        if (!navigator.onLine || (err as { code?: string }).code === "ERR_NETWORK") {
          await enqueue(sessionId, p);
          setStatus("queued-offline");
        } else {
          setStatus("error");
          // Optimistic rollback: restore last successful state in caller (via prop)
        }
      }
    },
    5_000,                                // 5s after last keystroke
    { maxWait: 30_000, leading: false, trailing: true },
  );

  // Trigger debounce when payload changes
  useEffect(() => {
    if (last.current !== null) debounced(payload);
    last.current = payload;
  }, [payload, debounced]);

  // Force-flush on unmount / route-change / Submit
  useEffect(() => () => { debounced.flush(); }, [debounced]);

  // Drain offline queue when network returns
  useEffect(() => {
    const onOnline = () => drainQueue(sessionId).then(() => setStatus("saved"));
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [sessionId]);

  return { status, updatedAt };
}
```

Source: hand-derived from [CITED: https://github.com/xnimorz/use-debounce]. Pattern verified against `useDebouncedCallback` docs — `.flush()` on unmount is the standard cleanup. `maxWait: 30_000` is a safety net so a user typing continuously for 30s still gets one save (matches "Saved Xs ago" UX expectation).

### Pattern 2: IndexedDB offline queue with `idb`

**What:** Single FIFO queue per `(user_id, session_id)`. On auto-save network failure, push payload + timestamp to queue. On reconnect, drain oldest-first; on success delete the row; on conflict (4xx response) surface modal.

**Example:**

```ts
// frontend/src/lib/auto-save.ts
import { openDB, IDBPDatabase } from "idb";
import { api } from "./api";

interface QueueEntry {
  session_id: string;
  payload: unknown;
  queued_at: number;     // Date.now()
  retries: number;
}

const DB_NAME = "pulse-autosave";
const STORE = "queue";

async function db(): Promise<IDBPDatabase> {
  return openDB(DB_NAME, 1, {
    upgrade(d) {
      if (!d.objectStoreNames.contains(STORE)) {
        const s = d.createObjectStore(STORE, { autoIncrement: true });
        s.createIndex("by_session", "session_id");
        s.createIndex("by_queued_at", "queued_at");
      }
    },
  });
}

export async function enqueue(session_id: string, payload: unknown): Promise<void> {
  const d = await db();
  await d.add(STORE, { session_id, payload, queued_at: Date.now(), retries: 0 } satisfies QueueEntry);
}

export async function drainQueue(session_id: string): Promise<void> {
  const d = await db();
  const tx = d.transaction(STORE, "readwrite");
  const idx = tx.store.index("by_queued_at");
  let cur = await idx.openCursor();
  while (cur) {
    const entry = cur.value as QueueEntry;
    if (entry.session_id !== session_id) { cur = await cur.continue(); continue; }
    try {
      await api.patch(`/assessment/sessions/${session_id}/self-assessment`, entry.payload);
      await cur.delete();                          // success → drop from queue
    } catch (err) {
      const status = (err as { response?: { status?: number } }).response?.status;
      if (status === 409 || status === 422) {
        // Replay conflict: stop draining, surface to UI
        throw new ReplayConflictError(entry, status);
      }
      // Transient: leave in queue, exit drain, retry on next 'online' event
      break;
    }
    cur = await cur.continue();
  }
  await tx.done;
}

export class ReplayConflictError extends Error {
  constructor(public entry: QueueEntry, public status: number) { super("Replay conflict"); }
}
```

Source: pattern derived from [CITED: https://www.npmjs.com/package/idb] and Jake Archibald's IDB cookbook.

**Conflict handling (DEC-T2-003):** Phase 2 ships **pure last-write-wins** — no `version` column, no 409 modal. If the server returns 422 (schema error) during replay, surface a toast "Perubahan offline ditolak server (skema lama). Periksa form." with the offending payload visible in DevTools. A modal with diff view is deferred to Phase 6 if real ops show conflicts (DEC-T2-003 + open question 8 explicit guidance). The `ReplayConflictError` class is wired but the modal it would feed is intentionally not built.

### Pattern 3: WebSocket reconnect with exponential backoff + jitter

**What:** On WS close (not user-initiated logout), reconnect with delays `1s → 2s → 4s → 8s → 16s` (cap), each multiplied by `1 + jitter` where `jitter ∈ [-0.3, +0.3]`. Stop after 5 consecutive failures; surface persistent toast. Mute reconnect during access-token refresh (avoid 401 storm).

**Example:**

```ts
// frontend/src/hooks/useNotifications.ts
import { useEffect, useRef } from "react";
import { useAuthStore } from "@/lib/auth-store";
import { useNotificationStore } from "@/lib/notification-store";
import { toast } from "sonner";

const BASE_DELAYS_MS = [1_000, 2_000, 4_000, 8_000, 16_000];
const MAX_DELAY_MS = 16_000;
const MAX_FAILS_BEFORE_TOAST = 5;

function nextDelay(fails: number): number {
  const base = BASE_DELAYS_MS[Math.min(fails, BASE_DELAYS_MS.length - 1)];
  const jitter = (Math.random() - 0.5) * 0.6;   // ±30%
  return Math.min(base * (1 + jitter), MAX_DELAY_MS);
}

export function useNotifications() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const ingest = useNotificationStore((s) => s.ingest);
  const ws = useRef<WebSocket | null>(null);
  const fails = useRef(0);
  const stopped = useRef(false);
  const reconnectTimer = useRef<number | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    stopped.current = false;

    const connect = () => {
      // Token in query param (DEC-CONSTR-websocket-endpoints + open question 7)
      const url = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/notifications?token=${encodeURIComponent(accessToken)}`;
      const sock = new WebSocket(url);
      ws.current = sock;

      sock.addEventListener("open", () => {
        fails.current = 0;
        toast.dismiss("ws-disconnected");
      });

      sock.addEventListener("message", (ev) => {
        try {
          const payload = JSON.parse(ev.data);
          ingest(payload);
        } catch { /* malformed — drop */ }
      });

      sock.addEventListener("close", () => {
        if (stopped.current) return;
        fails.current += 1;
        if (fails.current === MAX_FAILS_BEFORE_TOAST) {
          toast.error("Notifikasi terputus dari server. Mencoba kembali…", {
            id: "ws-disconnected",
            duration: Infinity,
          });
        }
        const wait = nextDelay(fails.current - 1);
        reconnectTimer.current = window.setTimeout(connect, wait);
      });
    };

    connect();

    return () => {
      stopped.current = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      ws.current?.close(1000, "unmount");
    };
  }, [accessToken, ingest]);
}
```

**Pattern alignment with sources:** Source [CITED: https://websocket.org/guides/frameworks/react/] confirms `useRef` for the socket + reconnect cleanup on unmount. Source [CITED: https://dev.to/hexshift/robust-websocket-reconnection-strategies-in-javascript-with-exponential-backoff-40n1] confirms exponential backoff with cap and jitter. The 5-fail toast threshold is a UX choice — long enough to ride out brief Wi-Fi blips, short enough that a 30s outage doesn't go silent.

**Mute reconnect during token refresh:** The hook re-keys on `accessToken` change. When the axios interceptor refreshes the token (existing Phase 1 behavior), the store updates `accessToken`, the WS effect tears down the old socket cleanly (close code 1000), and reconnects with the new token. No 401-storm because the refresh is serialized through `auth-store.ts` already.

### Pattern 4: FastAPI audit middleware with tag-based entity_type resolution

**What:** A Starlette `BaseHTTPMiddleware` that wraps every request. Skip GET. On non-GET 2xx/3xx response, write an `audit_log` row.

**Why middleware over dependency:** DEC-T6-001 wants **default-on coverage**. A dependency is opt-in — every new route is a chance to forget. Middleware sits before all handlers; you can NOT accidentally bypass it. The catch is: middleware doesn't see typed Pydantic objects; it only sees the raw `Request` and `Response`. That's actually fine for our shape (`before_data` / `after_data` are JSONB blobs — they don't need typed knowledge).

**Tag-based entity_type:** FastAPI route registration accepts `tags=[...]`. We reserve a prefix `audit:<entity_type>`:

```python
# Example in routers/periode.py
router.post(
    "/{periode_id}/transition",
    tags=["audit:periode"],
    dependencies=[Depends(require_role("super_admin")), Depends(require_csrf)],
)
```

The middleware introspects `request.scope["route"].tags` to resolve `entity_type` without forcing every router to do anything special — they just add the tag.

**Before/after capture strategy:** SQLAlchemy `event.listens_for(target, "before_update")` gives us `before_data` for free at row-level, but the lifecycle is tricky to thread back into the middleware (the middleware doesn't know which rows were touched). The pragmatic Phase-2 implementation:

- For routes that fit a single-entity pattern (PATCH `/assessment/sessions/{id}/...`, POST `/recommendations/{id}/...`), the **router handler** stashes `before_data` (the row pre-mutation) into `request.state.audit_before` and `after_data` (the row post-commit) into `request.state.audit_after`. The middleware reads `request.state.audit_*` after `call_next` and writes the row.
- For multi-entity operations (periode `transition` → side effects create N sessions), the handler emits one audit row per touched entity via an explicit helper (`audit_emit(request, entity_type, entity_id, before, after)`). Middleware tolerates multiple emissions.

This is a hybrid pattern — middleware owns the row-write + IP/user-agent capture, handlers explicitly tag with `before`/`after`. The alternative (pure SQLAlchemy events) couples audit-write to ORM lifecycle and breaks for non-ORM operations.

**Example skeleton:**

```python
# backend/app/services/audit_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp
from app.deps.auth import current_user_optional
from app.models.audit_log import AuditLog
from app.db.session import async_session_factory

CAPTURE_VERBS = {"POST", "PATCH", "PUT", "DELETE"}

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in CAPTURE_VERBS:
            return await call_next(request)

        # /auth/refresh excluded (DEC-T6-001)
        path = request.url.path
        if path.endswith("/auth/refresh"):
            return await call_next(request)

        response = await call_next(request)
        if response.status_code >= 400:
            return response

        # Resolve entity_type from tag, audit fields from request.state
        route = request.scope.get("route")
        entity_type = None
        for tag in (getattr(route, "tags", None) or []):
            if isinstance(tag, str) and tag.startswith("audit:"):
                entity_type = tag.split(":", 1)[1]
                break
        # Multiple emissions allowed: state.audit_rows is a list of dicts
        rows = getattr(request.state, "audit_rows", [])
        if not rows and entity_type:
            rows = [{
                "entity_type": entity_type,
                "entity_id": getattr(request.state, "audit_entity_id", None),
                "before_data": getattr(request.state, "audit_before", None),
                "after_data": getattr(request.state, "audit_after", None),
            }]

        # Best-effort: don't block response on audit write
        if rows:
            user = await current_user_optional(request)
            async with async_session_factory() as db:
                for r in rows:
                    db.add(AuditLog(
                        user_id=user.id if user else None,
                        action=f"{request.method} {route.path if route else path}",
                        entity_type=r["entity_type"],
                        entity_id=r.get("entity_id"),
                        before_data=r.get("before_data"),
                        after_data=r.get("after_data"),
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent"),
                    ))
                await db.commit()

        return response
```

Auth login/logout capture (DEC-T6-001 says login success/failure + logout are captured) is handled inside the auth router with explicit `audit_emit(...)` calls (login failure does NOT pass through the success-only middleware path).

**Sources:** Middleware shape confirmed against [CITED: https://fastapi.tiangolo.com/tutorial/middleware/] and audit-log patterns in [CITED: https://medium.com/@danniel.shalev_46673/how-to-create-audit-log-using-fast-in-python-b30f896710ff].

### Pattern 5: Hand-rolled state machine (periode + recommendation)

**What:** A dict-of-dicts transition table, validated by a small `transition()` function, no library.

**Why not `transitions`:** 6 states + 12 transitions for periode (6 forward + 5 rollback + 1 abandoned-on-close); 4 states + ~5 transitions for recommendation. The library overhead (callbacks, hierarchical states, condition functions) is wasted complexity. Source [CITED: https://github.com/pytransitions/transitions] confirms transitions is the popular pick but acknowledges hand-rolled is appropriate for "small state sets" — quote: "the state pattern is a good idea if the logic of each state is complex and the states change frequently".

**Example:**

```python
# backend/app/services/periode_fsm.py
from enum import StrEnum

class PeriodeStatus(StrEnum):
    DRAFT = "draft"
    AKTIF = "aktif"
    SELF_ASSESSMENT = "self_assessment"
    ASESMEN = "asesmen"
    FINALISASI = "finalisasi"
    CLOSED = "closed"

# Forward transitions: each maps `from -> {to: side_effect_callable}`
FORWARD: dict[PeriodeStatus, dict[PeriodeStatus, str]] = {
    PeriodeStatus.DRAFT:           {PeriodeStatus.AKTIF: "noop"},
    PeriodeStatus.AKTIF:           {PeriodeStatus.SELF_ASSESSMENT: "create_sessions"},
    PeriodeStatus.SELF_ASSESSMENT: {PeriodeStatus.ASESMEN: "noop"},
    PeriodeStatus.ASESMEN:         {PeriodeStatus.FINALISASI: "noop"},
    PeriodeStatus.FINALISASI:      {PeriodeStatus.CLOSED: "carry_over_and_abandon_drafts"},
    PeriodeStatus.CLOSED:          {},
}

# Rollback: super_admin can jump to any earlier state (DEC-T1-002)
def can_rollback(current: PeriodeStatus, target: PeriodeStatus) -> bool:
    order = [PeriodeStatus.DRAFT, PeriodeStatus.AKTIF, PeriodeStatus.SELF_ASSESSMENT,
             PeriodeStatus.ASESMEN, PeriodeStatus.FINALISASI, PeriodeStatus.CLOSED]
    return order.index(target) < order.index(current)

def assert_transition_allowed(current: PeriodeStatus, target: PeriodeStatus, role: str) -> None:
    if target in FORWARD.get(current, {}):
        return                          # forward — anyone with super_admin allowed
    if can_rollback(current, target):
        if role != "super_admin":
            raise PermissionError("Only super_admin can rollback")
        return
    raise ValueError(f"Invalid transition: {current} -> {target}")
```

Side effects are dispatched by the router after the FSM assertion passes. Idempotency on `create_sessions` is enforced by `session_creator` (it SELECTs existing first via `(periode_id, indikator_id, bidang_id)` unique key before INSERT).

Same pattern applies to `recommendation.py`:

```python
class RecommendationStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    CLOSED = "closed"
    CARRIED_OVER = "carried_over"

# Note: open → in_progress fires on first PATCH /progress (implicit).
# All others are explicit endpoint actions.
```

### Pattern 6: Pydantic `action_items` with default owner resolution

**What:** Typed `List[ActionItem]` on `RecommendationCreate`. Each item has optional `owner_user_id` — when missing, server resolves to PIC of source assessment (DEC-T4-001).

**Example:**

```python
# backend/app/schemas/recommendation.py
from datetime import date
from typing import Annotated
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class ActionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Annotated[str, Field(min_length=1, max_length=2000)]
    deadline: date | None = None
    owner_user_id: UUID | None = None   # If None, server resolves per DEC-T4-001

class RecommendationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_assessment_id: UUID
    severity: Annotated[str, Field(pattern="^(low|medium|high|critical)$")]
    deskripsi: Annotated[str, Field(min_length=10, max_length=10_000)]
    action_items: Annotated[list[ActionItem], Field(min_length=1)]
    target_periode_id: UUID
```

Resolution is in the **service layer**, NOT in `model_validator` — the validator runs at request parse time and doesn't have a DB session. The service:

```python
# backend/app/services/recommendation_create.py
async def resolve_default_owners(
    db: AsyncSession,
    action_items: list[ActionItem],
    source_assessment_id: UUID,
) -> list[ActionItem]:
    """Per DEC-T4-001: missing owner_user_id resolves to the PIC of the source assessment."""
    default_pic_id = None
    for item in action_items:
        if item.owner_user_id is None:
            if default_pic_id is None:
                default_pic_id = await _lookup_source_pic(db, source_assessment_id)
            # If lookup returns None (deactivated user), leave as None.
            # The router then rejects the create with 422 "owner required for action item N".
            item.owner_user_id = default_pic_id
    return action_items

async def _lookup_source_pic(db: AsyncSession, session_id: UUID) -> UUID | None:
    """Look up users.id by joining assessment_session.bidang_id → users.bidang_id.
    For aggregate sessions (DEC-T1-003), join via assessment_session_bidang to any
    PIC in the list — first-found by users.created_at is deterministic enough.
    Returns None if no active PIC found."""
    ...
```

Returning 422 when no active PIC exists is intentional — the asesor sees the message and picks a user from the dropdown. Silent acceptance with NULL owner would leave the recommendation orphaned.

**Source:** Pydantic v2 schema patterns confirmed via [CITED: https://docs.pydantic.dev/latest/concepts/fields/] and [CITED: https://docs.pydantic.dev/latest/concepts/validators/]. The decision to put owner-resolution in the service layer (not in a `model_validator`) follows the well-established principle "validators are pure, services do I/O" — DB lookups inside validators get clunky fast and complicate testability.

### Pattern 7: WebSocket auth via query param

**What:** Client connects to `wss://host/ws/notifications?token=<access_jwt>`. Server validates token before `websocket.accept()`. Closes 1008 (Policy Violation) on invalid.

**Why query param:** Browser WebSocket API doesn't allow custom request headers. Token-in-query is the standard pattern; the security caveat (tokens visible in nginx access logs) is mitigated by (a) HTTPS in production, (b) nginx log redaction policy. Source [CITED: https://hexshift.medium.com/authenticating-websocket-clients-in-fastapi-with-jwt-and-dependency-injection-d636d48fdf48] and FastAPI's own docs [CITED: https://fastapi.tiangolo.com/advanced/websockets/] confirm this is the pragmatic pattern.

**Server skeleton:**

```python
# backend/app/routers/ws_notifications.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from app.core.security import decode_token
from app.services.refresh_tokens import is_revoked  # already exists from Plan 05
from app.services.ws_manager import ws_manager
from app.core.logging import get_logger

router = APIRouter()
log = get_logger("pulse.ws.notifications")

@router.websocket("/ws/notifications")
async def notifications_ws(websocket: WebSocket, token: str = Query(...)):
    try:
        claims = decode_token(token, expected_type="access")   # raises on bad alg / expired
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="invalid_token")
        return

    user_id = claims.get("sub")
    jti = claims.get("jti")
    if not user_id or not jti or await is_revoked(user_id, jti):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="revoked")
        return

    await websocket.accept()
    await ws_manager.register(user_id, websocket)
    try:
        while True:
            # We don't expect client→server messages; keep the loop alive
            # so disconnect events propagate. Optional: implement a ping.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.unregister(user_id, websocket)
```

**`ws_manager` singleton:**

```python
# backend/app/services/ws_manager.py
import asyncio
from collections import defaultdict
from fastapi import WebSocket

class WsManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._conns: dict[str, set[WebSocket]] = defaultdict(set)

    async def register(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._conns[user_id].add(ws)

    async def unregister(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._conns[user_id].discard(ws)
            if not self._conns[user_id]:
                del self._conns[user_id]

    async def send_to_user(self, user_id: str, payload: dict) -> None:
        async with self._lock:
            sockets = list(self._conns.get(user_id, set()))
        for sock in sockets:
            try:
                await sock.send_json(payload)
            except Exception:
                # Disconnected socket — let the receive loop / disconnect handler clean it up
                pass

ws_manager = WsManager()
```

**Lifecycle:** Client owns the reconnect protocol (§Pattern 3). Server doesn't proactively close on token refresh — when the access token expires, the next client message would 401 (but we don't send client→server messages); cleaner is: client triggers refresh via existing `/auth/refresh`, the `accessToken` Zustand selector changes, the `useEffect` in `useNotifications` re-runs, closes the old socket, reconnects with the new token. No mid-session re-validation needed.

### Pattern 8: Notification dispatcher (DB + WS atomic)

```python
# backend/app/services/notification_dispatcher.py
async def dispatch(
    db: AsyncSession,
    *,
    user_id: UUID,
    type_: str,
    title: str,
    body: str,
    payload: dict | None = None,
) -> Notification:
    notif = Notification(
        user_id=user_id, type=type_, title=title, body=body,
        payload=payload or {}, read_at=None,
    )
    db.add(notif)
    await db.flush()    # get the id but don't commit yet
    # Schedule the WS push for AFTER the commit so the WS client can fetch
    # the persisted row by id if it wants to (avoids race where push arrives
    # before the row is queryable).
    ws_payload = {
        "id": str(notif.id), "type": type_, "title": title,
        "body": body, "created_at": notif.created_at.isoformat(),
    }
    # Best-effort WS push; if WS fails, the DB row still serves the bell badge
    await db.commit()
    await ws_manager.send_to_user(str(user_id), ws_payload)
    return notif
```

DEC-T5-002: one dispatch per event, no batching. Caller code (e.g. `assessment_session.submit()` handler) calls `dispatch(...)` once per recipient.

### Anti-Patterns to Avoid

- **Don't bundle audit-write into the route handler.** Separation of concerns — middleware owns the row-write, handler tags entity. If you write `audit_log` inserts inside the handler, you'll forget on the 12th new route.
- **Don't compute `pencapaian` only client-side.** DEC-T2-005 — server is authoritative. Client preview only.
- **Don't create sessions in `asesor_review` decision `request_revision`.** Sessions exist; revision just changes `state=draft` and `nilai_final=NULL`. No INSERT.
- **Don't auto-close `pending_review` recommendations after N days.** DEC-T4-002 — no SLA in Phase 2.
- **Don't ship SMTP code or email templates.** DEC-T5-001 — explicitly descoped. Don't even add `aiosmtplib` to pyproject.
- **Don't drop the WebSocket token on reconnect.** Each reconnect uses `?token=` with the *current* access token (which the Zustand store has after refresh).
- **Don't capture GET requests in audit middleware.** DEC-T6-001. Performance + signal-to-noise — audit-log volume would explode.
- **Don't auto-purge audit-log rows.** DEC-T6-002 — retention forever in Phase 2.
- **Don't use `BaseHTTPMiddleware` to capture response body bytes.** Source [CITED: https://github.com/fastapi/fastapi/issues/954] confirms the streaming-response capture is fragile and breaks `StreamingResponse`. We capture `before`/`after` via `request.state`, not by reading the response body.
- **Don't store the access token in `localStorage` or `sessionStorage`.** Phase 1 already enforces this (`auth-store.ts` is in-memory only). Phase 2's WS hook reads the token from the Zustand store, NOT from `localStorage`.
- **Don't add a `version` column to `assessment_session` "just in case".** DEC-T2-003 says last-write-wins. Premature optimization.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Debounce of auto-save callback | Custom `useEffect` + `setTimeout` + `clearTimeout` cleanup | `use-debounce` `useDebouncedCallback` (^10.1.1) | `.flush()` on unmount + Submit, `.cancel()`, `maxWait` safety net, `leading`/`trailing` knobs. Vendored hand-rolls go stale on hook-rule violations. |
| IndexedDB callback wrapping | `window.indexedDB` direct calls | `idb` (^8.0.3) | Promisified API, TS types, openDB upgrade hook for schema versioning. Direct API is callback hell. |
| WebSocket reconnect | Inline `new WebSocket` + manual setTimeout | Custom hook `useNotifications` with the cadence in §Pattern 3 | Token rotation + jitter + persistent-toast threshold are exactly the parts you'll get wrong. Build the hook once, test it. (Don't add `react-use-websocket` — adds 6KB for behavior we already need to tune.) |
| Periode/recommendation FSM | Nested `if`/`else` in route handlers | Hand-rolled `assert_transition_allowed(...)` in `services/periode_fsm.py` + `recommendation_fsm.py` | Six states + a transition table is the simplest, most testable form. The `transitions` library is overkill but the lesson "use a transition table not if-chains" applies. |
| Auto-save conflict diff UI | Side-by-side JSON diff component | (defer to Phase 6) | DEC-T2-003 says last-write-wins; no conflict modal needed in Phase 2. |
| Audit-log middleware | Inline `audit_log.add(...)` in every router | `AuditMiddleware` + route tags | DEC-T6-001 wants default coverage. Middleware is opt-out, handlers add tag only. |
| WS client testing | `Jest + ws library` | Vitest + plain `WebSocket` + `start-server-and-test` against compose stack | The hook is best tested via integration (compose backend up + real WS). Unit-testing the hook alone is fragile — mock `WebSocket` constructor at `globalThis` level only if you need offline-CI runs. |
| Pydantic JSON polymorphism | Custom `__get_pydantic_core_schema__` | Typed `List[ActionItem]` + service-layer owner-resolution | Action items are NOT polymorphic — they're a single shape with optional fields. Don't reach for `Annotated[Union[...], Discriminator(...)]` for a single shape. |

**Key insight:** Phase 2's "tricky parts" (debounce, IDB, WS reconnect, audit) are well-trodden — hand-rolling them creates exactly the bugs the libraries solve. Phase 2's "domain-shape" parts (FSM, action_items, carry-over) are small enough that a library adds more complexity than it removes.

---

## Runtime State Inventory

This is a **greenfield feature phase** — Phase 2 adds new tables and new routes but does NOT rename any existing identifiers. The 5-category inventory is mostly inapplicable. Stating each explicitly:

| Category | Items found in Phase 2 scope | Action required |
|----------|------------------------------|------------------|
| Stored data (existing rows that need migration) | **None** — Phase 1 ships zero rows in `assessment_session` / `periode` / `recommendation` / `notification` / `audit_log` because those tables don't exist yet. Plan 07's seed creates 26 bidang + 1 Konkin template + 4 indikator + 4 ml_stream + 3 users — none of those refer to assessment data. | None |
| Live service config (n8n/Datadog/etc.) | **None** — PULSE doesn't yet have external services with state. Postgres + Redis + nginx + the FastAPI app and the Vite frontend, all defined in `docker-compose.yml`. Phase 2 just adds rows to existing DB, adds routes to the existing FastAPI app. | None |
| OS-registered state (Task Scheduler / pm2 / systemd / launchd) | **None** — only the dcron sidecar from Plan 02 (`pulse-backup`), and its only registered job is the 02:00 backup + 03:00 Sunday rsync. Phase 2 introduces NO new cron jobs (DEC-T1-001 — no scheduler). | None |
| Secrets / env vars | **None new.** No SMTP envs (DEC-T5-001 — descoped). No new third-party API keys. Phase 2 reuses `JWT_SECRET_KEY`, `POSTGRES_*`, `REDIS_URL` already on `.env.example`. | None |
| Build artifacts / installed packages | Three new npm packages (`use-debounce`, `idb`, `fake-indexeddb`) on the frontend. Zero new pip packages. After `pnpm add`, the `pulse-frontend` Docker image needs a rebuild (`docker compose build pulse-frontend`); after that no stale artifacts. | Plan 02-execute checklist: rebuild frontend image once after `pnpm add` lands. |

**The canonical question:** "After every file in the repo is updated, what runtime systems still have the old string cached, stored, or registered?" — answer: **nothing**, because Phase 2 is purely additive. No rename, no migration of existing records.

---

## Common Pitfalls

### Pitfall 1: Debounce + unmount race

**What goes wrong:** PIC types in the form, clicks "Submit" or navigates away within 5 seconds → the debounce timer fires AFTER the component unmounts → React warns "Can't perform state update on unmounted component" or worse, the stale write overwrites a fresh submit.

**Why it happens:** The debounce closure outlives the component if you don't `.flush()` or `.cancel()` on unmount.

**How to avoid:**
- Always include the cleanup `useEffect(() => () => debounced.flush(), [debounced])` (Pattern 1).
- On Submit, call `debounced.cancel()` then `await api.post(submit_url)` — never let auto-save race with explicit Submit.

**Warning signs:** Vitest logs "act() warnings" after Submit; ad-hoc reports of "I saved then submitted but the submitted version is missing my last change".

### Pitfall 2: Network jitter causes auto-save toast flicker

**What goes wrong:** First-class network glitches (Wi-Fi handoff) flap the connection — `navigator.onLine` flips false then true within 2 seconds — and the user sees "Menyimpan offline (1)…" toast appear and vanish.

**Why it happens:** `online`/`offline` events fire eagerly on `navigator.connection.type` changes, not on actual connectivity.

**How to avoid:** Only show the offline toast when the IDB queue length is > 0 AND the queue has been non-empty for ≥ 1 second (debounce the toast display itself). Drain immediately on `online` regardless. The toast is a state-of-queue indicator, not a state-of-network indicator.

### Pitfall 3: Focus-blur edge case on Tab key

**What goes wrong:** PIC fills field A, presses Tab, the debounce fires at 5s while field B is being edited → the saved payload includes A's final value but B is mid-edit.

**Why it happens:** Auto-save reads `payload` from React Hook Form's `watch()` at debounce-fire time, which captures whatever's in the form at that exact instant.

**How to avoid:** This is actually **desired behavior** — saving as much as the user has typed is the point. The pitfall is misreading it as a bug. The fix is documentation: REQ-auto-save acceptance criterion explicitly says "every X seconds (debounced)" — partial saves are correct. Just don't try to "wait for the user to finish field B" — there's no signal for that.

### Pitfall 4: `BaseHTTPMiddleware` and `StreamingResponse` capture

**What goes wrong:** You try to read the response body inside `AuditMiddleware` to extract `after_data` → the response is a `StreamingResponse`, you consume the iterator, the actual response sent to the client is empty.

**Why it happens:** `BaseHTTPMiddleware.dispatch` receives a fully-streaming response object; reading it consumes it.

**How to avoid:** **Do not read the response body in the audit middleware.** Capture `before` / `after` data via `request.state.audit_before` / `audit_after` set BY THE HANDLER. The handler already has typed Pydantic objects in scope — pass the dumps in there. Middleware only reads `request.state` and writes the audit row.

**Source:** [CITED: https://github.com/Kludex/starlette/discussions/2801] explicitly documents the `_StreamingResponse` issue.

**Warning signs:** Empty response bodies seen by the client after middleware is added; 500 errors with cryptic `StreamingResponse` traceback.

### Pitfall 5: WebSocket auth token refresh storm

**What goes wrong:** Access token expires while WS is connected. WS server tries to validate the (still-in-its-memory) old token on every message → fails → closes 1008 → client reconnects → reconnect uses NEW token (from Zustand) → OK. But if 5 clients all do this simultaneously within 1 second of a token expiry wave, you get 5 simultaneous `/auth/refresh` calls.

**Why it happens:** The refresh endpoint is rate-limit-aware (Plan 02 nginx config), but a synchronized wave still spikes load.

**How to avoid:**
- **Don't re-validate the token mid-WS-session.** The token is checked once on connect. Server doesn't proactively close on token expiry — let the client lifecycle drive it.
- Add jitter to reconnect delay (already in §Pattern 3).
- Frontend serializes `/auth/refresh` through a single in-flight promise (already done in Phase 1 `api.ts`).

### Pitfall 6: Aggregate-session (DEC-T1-003) editor coordination

**What goes wrong:** Two PICs in different bidang open the same EAF aggregate session simultaneously; both type values; whoever saves last wins; the first PIC's work is lost without warning.

**Why it happens:** DEC-T2-003 is explicit — last-write-wins. There is no lock. The "first PIC's work is lost" is the documented behavior.

**How to avoid:** **Document, don't engineer.** The session detail screen for aggregate sessions shows a banner: "Sesi ini dipakai bersama bidang X, Y, Z. Perubahan terakhir yang disimpan akan menang. Koordinasi via WhatsApp/teams sebelum mengedit bersama." This is the explicit DEC-T2-003 trade-off. Phase 6 may add `version` column + 409 if real ops show frequent overwrites.

### Pitfall 7: Carry-over chain ambiguity on rollback

**What goes wrong:** super_admin rolls back periode from `closed` to `finalisasi` (DEC-T1-002). The recommendations that were already carried to next periode now look orphaned — their `carried_from_id` points to the (now non-closed) source periode.

**Why it happens:** Carry-over creates rows in the NEXT periode; rollback only changes the current periode's state.

**How to avoid:** DEC-T1-002 is explicit: "carry-over is irreversible". Document in UI: when rolling back `closed → finalisasi`, modal says "Rekomendasi yang sudah carry-over ke TW berikutnya akan tetap di sana. Mengembalikan periode TIDAK akan menarik kembali rekomendasi." Add a `GET /periode/{id}/carry-over-summary` for audit visibility.

### Pitfall 8: `entity_type` missing tag on a new route

**What goes wrong:** Plan 04 adds a new route to `recommendation.py` and forgets the `tags=["audit:recommendation"]` decoration. Middleware fires but writes `entity_type=NULL`.

**Why it happens:** Tags are easy to forget; there's no compile-time check.

**How to avoid:** Add a startup-time check in `app/main.py`:

```python
# After all routers are auto-discovered
for route in app.routes:
    if isinstance(route, APIRoute) and route.methods & {"POST", "PATCH", "PUT", "DELETE"}:
        if not any(t.startswith("audit:") for t in (route.tags or [])):
            if route.path.startswith("/api/v1/") and not route.path.endswith("/auth/refresh"):
                raise RuntimeError(
                    f"Mutating route {route.methods} {route.path} missing audit:<entity> tag"
                )
```

This is a startup gate — drop the constraint when refactoring is needed, but in production it catches the new-route-forgot-tag class of bug immediately.

### Pitfall 9: JSONB `before_data`/`after_data` row size + TOAST overhead

**What goes wrong:** Submitting a fully-filled ML session with 80 sub-areas dumps a 30KB JSONB blob to `audit_log.after_data`. PostgreSQL TOASTs it (compression + out-of-line storage > 2KB). Every read of that audit row pays decompression cost.

**Why it happens:** PG TOASTs JSONB > 2KB. Source [CITED: https://www.snowflake.com/en/engineering-blog/postgres-jsonb-columns-and-toast/] documents the overhead.

**How to avoid:**
- **Store deltas, not full dumps.** For high-frequency entities (`assessment_session`), `before_data`/`after_data` carry only the FIELDS that changed in this request, NOT the full row. The full row is reconstructable from `entity_id`.
- For low-frequency entities (`periode` transitions, `recommendation` creates), full dumps are fine — TOAST is a non-issue at PLN volume.
- Document the delta strategy in `audit_middleware.py` docstring.

### Pitfall 10: Test isolation for IDB across vitest files

**What goes wrong:** Test A writes to the fake IDB queue, test B in the next file inherits the queue.

**Why it happens:** `fake-indexeddb/auto` puts `indexedDB` on `globalThis` once; the in-memory DB persists across test files within a worker.

**How to avoid:** In a global setup (`src/test/setup.ts`), add:

```ts
import { afterEach } from "vitest";
import "fake-indexeddb/auto";

afterEach(async () => {
  // Drop all IndexedDB databases between tests
  const dbs = await indexedDB.databases();
  await Promise.all(dbs.map((d) => d.name && new Promise<void>((res) => {
    const req = indexedDB.deleteDatabase(d.name!);
    req.onsuccess = req.onerror = req.onblocked = () => res();
  })));
});
```

---

## Code Examples

### Auto-save trigger inside form component

```tsx
// frontend/src/routes/pic/MlForm.tsx (excerpt)
import { useForm, useWatch } from "react-hook-form";
import { useAutoSave } from "@/hooks/useAutoSave";
import { SkLevelSelector, SkSlider, SkToggle, SkButton, SkBadge } from "@/components/skeuomorphic";

export function MlForm({ sessionId, structure }: { sessionId: string; structure: MlStructure }) {
  const { register, control, handleSubmit, getValues } = useForm<MlPayload>({ defaultValues: emptyPayload(structure) });
  const watched = useWatch({ control });           // reactive snapshot
  const { status, updatedAt } = useAutoSave(sessionId, watched);

  return (
    <form onSubmit={handleSubmit(/* submit logic; auto-save flushes via unmount or explicit cancel */)}>
      <header className="flex items-center gap-2">
        <SkBadge tone="info">{statusLabel(status)}</SkBadge>
        {updatedAt && <span className="text-xs">Tersimpan {timeAgo(updatedAt)}</span>}
      </header>
      {structure.areas.map((area) => (
        <fieldset key={area.code}>
          <legend>{area.name}</legend>
          {area.sub_areas.map((sa) => (
            <div key={sa.code}>
              <SkLevelSelector {...register(`${sa.code}.level` as const)} />
              <SkSlider {...register(`${sa.code}.value` as const)} min={0} max={4} step={0.01} />
              <SkToggle {...register(`${sa.code}.tidak_dinilai` as const)} label="Tidak dinilai" />
            </div>
          ))}
        </fieldset>
      ))}
      {/* Submit button disabled per DEC-T2-004 — see SubmitGate component */}
    </form>
  );
}
```

### Periode transition router (skeleton)

```python
# backend/app/routers/periode.py (excerpt)
from fastapi import APIRouter, Depends, HTTPException, Request
from app.deps.auth import require_role
from app.deps.csrf import require_csrf
from app.deps.db import get_db
from app.services.periode_fsm import PeriodeStatus, assert_transition_allowed
from app.services.session_creator import create_sessions_for_periode
from app.services.carry_over import close_periode_with_carry_over

router = APIRouter(prefix="/periode", tags=["periode"])

@router.post(
    "/{periode_id}/transition",
    tags=["audit:periode"],   # AuditMiddleware reads this
    dependencies=[
        Depends(require_role("super_admin")),
        Depends(require_csrf),
    ],
)
async def transition(periode_id: UUID, payload: PeriodeTransitionRequest, request: Request, db=Depends(get_db)):
    periode = await db.get(Periode, periode_id)
    if not periode:
        raise HTTPException(404)

    current_state = PeriodeStatus(periode.status)
    target_state = PeriodeStatus(payload.target_state)
    user = request.state.user   # set by auth middleware/dependency upstream
    assert_transition_allowed(current_state, target_state, user.roles[0])

    # Capture before for audit
    request.state.audit_before = {"status": current_state.value}

    # Side effects per FSM table
    if current_state == PeriodeStatus.AKTIF and target_state == PeriodeStatus.SELF_ASSESSMENT:
        await create_sessions_for_periode(db, periode_id)
    elif current_state == PeriodeStatus.FINALISASI and target_state == PeriodeStatus.CLOSED:
        await close_periode_with_carry_over(db, periode_id)
    # Rollback transitions are no-op side-effect-wise

    periode.status = target_state.value
    if payload.reason:                   # required for rollback per DEC-T1-002
        periode.last_transition_reason = payload.reason
    await db.commit()

    request.state.audit_after = {"status": target_state.value, "reason": payload.reason}
    request.state.audit_entity_id = str(periode_id)

    return {"data": serialize_periode(periode)}
```

### WebSocket consumer hook (test-friendly)

Pattern from §3 — already shown above. The hook accepts an optional `WebSocket` factory in tests (DI):

```ts
// frontend/src/hooks/useNotifications.ts (test hook)
export function useNotifications(opts?: { wsFactory?: (url: string) => WebSocket }) {
  // ...
  const sock = (opts?.wsFactory ?? ((u) => new WebSocket(u)))(url);
  // ...
}
```

In tests, inject a mock `WebSocket` that fires `open`, `message`, `close` events on demand.

### FastAPI WebSocket test

```python
# backend/tests/test_ws_notifications.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.asyncio
async def test_ws_rejects_invalid_token():
    # FastAPI's TestClient (sync) supports websocket_connect even when the app is async
    with TestClient(app) as client:
        # Starlette raises WebSocketDisconnect on close from the server
        from starlette.websockets import WebSocketDisconnect
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws/notifications?token=invalid"):
                pass
        assert exc_info.value.code == 1008  # Policy Violation

@pytest.mark.asyncio
async def test_ws_accepts_valid_token_and_pushes(admin_token, dispatch_test_notif):
    with TestClient(app) as client:
        with client.websocket_connect(f"/ws/notifications?token={admin_token}") as ws:
            # Trigger a notification via API
            await dispatch_test_notif()
            data = ws.receive_json()
            assert data["type"] == "assessment_due"
```

`TestClient.websocket_connect` is from Starlette — it works against both sync and async ASGI apps. Source [CITED: https://fastapi.tiangolo.com/advanced/testing-websockets/].

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `framer-motion` package name | `motion` package (renamed Nov 2024) | Phase 1 already on `motion` ^12.38 | No change for Phase 2 |
| `react-router-dom` v6 nested routes | v6 stable, v7 framework mode (not adopted) | Phase 1 pinned at v6.30 | Phase 2 stays on v6 — DO NOT bump to v7 (breaking API) |
| Tailwind v3 `tailwind.config.js` | Tailwind v4 `@theme inline` in CSS | Phase 1 already on v4.3 | Phase 2 adds new tokens (`--sk-slider-track`, etc.) inline |
| pydantic v1 `@validator` | pydantic v2 `@field_validator` / `@model_validator` | Phase 1 already on pydantic 2.13 | Phase 2 uses v2 idioms only |
| FastAPI sync `Depends` | FastAPI async-native `Depends` | Always — `current_user` etc. are already async | No change |
| `passlib` for bcrypt | Native `bcrypt` 5.x API | Phase 1 deviation (already documented) | Phase 2 reuses `app.core.security.hash_password` directly |

**Deprecated / outdated:**
- `crypt` module (Python 3.13 removal) — irrelevant; we use native bcrypt.
- `vitest --reporter=basic` — removed in vitest 4.x (Phase 1 already worked around).
- `pydantic.EmailStr` — Phase 1 swapped for regex-validated `str` (per `.local` TLD issue). Phase 2 uses the same regex helper.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | PLN ops scale = ~100k audit_log rows / year / unit | §10 | If volume is 10× higher, the indexes still hold but partial/partition strategy may be wanted in Phase 6. Phase 2 storage estimate (10MB/year/unit @ ~100 bytes avg row) is well within VPS capacity. [ASSUMED — sourced from CONTEXT.md note "PLN ops scale ~100k actions/year/unit"] |
| A2 | Aggregate session conflicts will be rare in practice (~< 5% of edits) | §6 (Pitfall 6) | If common, Phase 6 needs to add `version` column + 409 modal. No Phase 2 cost — pure data-driven decision later. [ASSUMED — no production telemetry yet] |
| A3 | Frontend bundle budget allows +3 KB gzipped for `use-debounce` + `idb` | §Standard Stack | If strict bundle budget exists (no evidence either way), the planner should confirm. Both libs are very small. [ASSUMED — no explicit bundle constraint in PROJECT.md] |
| A4 | Browser WebSocket auto-reconnect IS NOT shipped natively by `motion`/`zustand`/anything Phase 1 already has | §Pattern 3 | If a Phase 1 dependency already exposed a useful WS wrapper, we'd be duplicating. Verified — none of the Phase 1 deps ship WS helpers. [VERIFIED: package.json + grep] |
| A5 | The `request.state.user` attribute is populated by Phase 1's `current_user` dep before the audit middleware needs it | §Pattern 4 | If timing is wrong (middleware runs before deps), audit can't capture `user_id`. Need to ensure `AuditMiddleware` is added AFTER FastAPI's auth handling — which it is, because handler-defined `request.state.user` is set inside the handler. Middleware reads it after `call_next`. [VERIFIED: Starlette middleware runs around handler — state is populated before the exit half] |
| A6 | `httpx.AsyncClient` + `ASGITransport` does NOT speak WebSocket; Starlette `TestClient` does | §9 (test infra) | If we assumed AsyncClient supports WS, the test stub would fail. Verified [CITED: stackoverflow + FastAPI docs] — AsyncClient is HTTP-only; Starlette `TestClient` from `fastapi.testclient` handles WS via threaded sync wrapper. [VERIFIED via FastAPI docs] |
| A7 | Pydantic v2 `model_validator(mode='after')` runs synchronously — cannot await DB | §Pattern 6 | If we'd assumed async validators existed, the owner-resolution logic would belong in the validator. Confirmed sync-only; pushed to service layer. [VERIFIED: docs.pydantic.dev] |

**Risk summary:** No assumption is load-bearing on a security or compliance claim. All assumptions are operational and Phase 6 is the natural recheck point for A1/A2.

---

## Open Questions Resolved

1. **Auto-save debounce primitive** — RESOLVED. `use-debounce` `useDebouncedCallback` with 5000ms delay + `maxWait: 30000` + `.flush()` on unmount. Pattern in §1.
2. **IndexedDB library** — RESOLVED. `idb` ^8.0.3. Bundle ~1KB, promise-based, minimal abstraction, FIFO via auto-increment key + `by_queued_at` index. Pattern in §2.
3. **WebSocket reconnect strategy** — RESOLVED. `1s → 2s → 4s → 8s → 16s` base, ±30% jitter, 5-fail toast threshold, persistent toast until reconnect. Mute by tearing down on `accessToken` change. Pattern in §3.
4. **FastAPI audit: middleware vs dependency** — RESOLVED. Middleware-based with route tag `audit:<entity_type>`. `request.state.audit_before` / `audit_after` populated by handlers. Pattern in §4.
5. **Periode state machine library** — RESOLVED. Hand-rolled enum + transition table. No new dependency. Pattern in §5.
6. **Pydantic action_items schema** — RESOLVED. Typed `List[ActionItem]` in `RecommendationCreate` Pydantic schema; default owner resolution in service layer (not validator). Pattern in §6.
7. **WebSocket token via query param** — RESOLVED. `?token=<access_jwt>`. Validated once on accept. No mid-session re-validation. Client reconnects with new token after refresh. Pattern in §7.
8. **Auto-save conflict UX library** — RESOLVED (deferred). DEC-T2-003 says last-write-wins; Phase 2 ships NO conflict modal. If 422 fires on replay, surface a Sonner toast with the offending payload field for now. Phase 6 may add `version` column + side-by-side `<pre>` diff if real ops show conflict noise.

---

## §9 Test Infrastructure (Phase 2-specific)

### Frontend (vitest + jsdom + fake-indexeddb)

Add to `frontend/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom";
import "fake-indexeddb/auto";          // NEW
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(async () => {
  cleanup();
  // Wipe IDB between tests (Pitfall 10)
  if (typeof indexedDB !== "undefined" && typeof indexedDB.databases === "function") {
    const dbs = await indexedDB.databases();
    await Promise.all(dbs.map((d) => d.name ? new Promise<void>((res) => {
      const req = indexedDB.deleteDatabase(d.name!);
      req.onsuccess = req.onerror = req.onblocked = () => res();
    }) : Promise.resolve()));
  }
});
```

**Testing auto-save with fake timers:**

```ts
// useAutoSave.test.ts
import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useAutoSave } from "@/hooks/useAutoSave";

vi.mock("@/lib/api", () => ({ api: { patch: vi.fn().mockResolvedValue({ data: { updated_at: "..." } }) } }));

describe("useAutoSave", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("does NOT save during continuous typing", async () => {
    const { rerender } = renderHook(({ p }) => useAutoSave("sess-1", p), { initialProps: { p: { a: 1 } } });
    rerender({ p: { a: 2 } });
    rerender({ p: { a: 3 } });
    act(() => { vi.advanceTimersByTime(4_000); });
    rerender({ p: { a: 4 } });                     // restart debounce
    act(() => { vi.advanceTimersByTime(4_999); });
    expect((api.patch as Mock).mock.calls.length).toBe(0);   // not yet
  });

  it("saves 5s after last keystroke", async () => {
    const { rerender } = renderHook(({ p }) => useAutoSave("sess-1", p), { initialProps: { p: { a: 1 } } });
    rerender({ p: { a: 2 } });
    act(() => { vi.advanceTimersByTime(5_000); });
    await act(async () => { await Promise.resolve(); });
    expect((api.patch as Mock).mock.calls.length).toBe(1);
  });

  it("queues to IDB on network failure", async () => {
    (api.patch as Mock).mockRejectedValueOnce({ code: "ERR_NETWORK" });
    // Force navigator.onLine = false
    Object.defineProperty(window.navigator, "onLine", { value: false, configurable: true });
    const { rerender } = renderHook(({ p }) => useAutoSave("sess-1", p), { initialProps: { p: { a: 1 } } });
    rerender({ p: { a: 2 } });
    act(() => { vi.advanceTimersByTime(5_000); });
    await act(async () => { await Promise.resolve(); });
    // Verify IDB has 1 row
    const db = await openDB("pulse-autosave", 1);
    const all = await db.getAll("queue");
    expect(all.length).toBe(1);
  });
});
```

**Testing the WS hook:** prefer integration testing (compose stack up + real WS) — see Phase 2 E2E checkpoint. Unit-testing the hook requires mocking `WebSocket` globally, which is brittle. Source [CITED: https://websocket.org/guides/frameworks/react/] confirms WS hook unit tests are a pain point — integration is the pragmatic level.

### Backend (pytest + Starlette TestClient + ephemeral docker stack)

**Testing the audit middleware:**

```python
# backend/tests/test_audit_middleware.py
import pytest
from sqlalchemy import select
from app.models.audit_log import AuditLog

@pytest.mark.asyncio
async def test_patch_creates_audit_row(client, db_session, admin_token, sample_session):
    r = await client.patch(
        f"/api/v1/assessment/sessions/{sample_session.id}/self-assessment",
        json={"foo": "bar"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    rows = (await db_session.scalars(
        select(AuditLog).where(AuditLog.entity_id == sample_session.id)
    )).all()
    assert len(rows) == 1
    assert rows[0].action.startswith("PATCH ")
    assert rows[0].entity_type == "assessment_session"
    assert "self_assessment" in rows[0].after_data

@pytest.mark.asyncio
async def test_get_does_not_create_audit_row(client, admin_token, sample_session):
    await client.get(
        f"/api/v1/assessment/sessions/{sample_session.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    rows = (await db_session.scalars(select(AuditLog))).all()
    assert len(rows) == 0
```

**Testing WebSocket endpoint:**

```python
# backend/tests/test_ws_notifications.py
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from app.main import app
from app.services.notification_dispatcher import dispatch

def test_ws_invalid_token(admin_user):
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect("/ws/notifications?token=bad"):
                pass
        assert exc.value.code == 1008

@pytest.mark.asyncio
async def test_ws_receives_notification(admin_user, admin_token, db_session):
    # Note: TestClient is sync; the WS context is sync-driven.
    # Use the SDK sync wrapper.
    with TestClient(app) as client:
        with client.websocket_connect(f"/ws/notifications?token={admin_token}") as ws:
            # Trigger a notification synchronously via a sync helper that calls the async dispatch
            import asyncio
            asyncio.run(dispatch(db_session, user_id=admin_user.id, type_="assessment_due",
                                  title="Test", body="X"))
            data = ws.receive_json()
            assert data["type"] == "assessment_due"
```

**Test framework matrix:**

| Property | Value |
|----------|-------|
| Backend framework | pytest 9.0.3 + pytest-asyncio 1.3 (already pinned) |
| Backend WS test client | `from fastapi.testclient import TestClient` (Starlette) — NOT httpx AsyncClient (HTTP only) |
| Backend config file | `backend/pyproject.toml` `[tool.pytest.ini_options]` (already configured, session loop scope) |
| Frontend framework | vitest 4.1.5 (already pinned) |
| Frontend IDB mock | `fake-indexeddb` ^6.2.5 in setup |
| Quick run (backend) | `wsl -d Ubuntu-22.04 -- python3.11 -m pytest -q` |
| Quick run (frontend) | `wsl -d Ubuntu-22.04 -- bash -c 'cd frontend && pnpm exec vitest --run'` |
| Full suite gate | Both quick runs green + E2E browser checkpoint at Phase 2 end |

### Phase Requirements → Test Map

| REQ ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-periode-lifecycle | FSM transitions + side fx | integration | `pytest tests/test_periode_fsm.py -x` | ❌ Wave 0 |
| REQ-self-assessment-kpi-form | KPI form polarity compute + server authoritative | integration | `pytest tests/test_assessment_kpi.py -x` | ❌ Wave 0 |
| REQ-self-assessment-ml-form | ML form tree render + submit gate | unit + integration | `pnpm exec vitest src/routes/pic/MlForm.test.tsx` | ❌ Wave 0 |
| REQ-auto-save | Debounced PATCH + IDB queue | unit | `pnpm exec vitest src/hooks/useAutoSave.test.ts` | ❌ Wave 0 |
| REQ-pic-actions | Save / Submit / Withdraw + AI button disabled | unit | `pnpm exec vitest src/routes/pic/SubmitGate.test.tsx` | ❌ Wave 0 |
| REQ-asesor-review | approve / override / request_revision validators | integration | `pytest tests/test_asesor_review.py -x` | ❌ Wave 0 |
| REQ-recommendation-create | action_items typed + owner-resolution | integration | `pytest tests/test_recommendation_create.py -x` | ❌ Wave 0 |
| REQ-recommendation-lifecycle | progress / mark-completed / verify-close / carry-over | integration | `pytest tests/test_recommendation_lifecycle.py -x` | ❌ Wave 0 |
| REQ-notifications | DB insert + WS push + mark-read | integration | `pytest tests/test_notification_dispatcher.py -x` + `pytest tests/test_ws_notifications.py -x` | ❌ Wave 0 |
| REQ-audit-log | Middleware captures POST/PATCH/PUT/DELETE 2xx; skips GET + /auth/refresh | integration | `pytest tests/test_audit_middleware.py -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `wsl -d Ubuntu-22.04 -- python3.11 -m pytest tests/<new_file>.py -x` (backend) or `wsl … pnpm exec vitest --run <new_test>` (frontend).
- **Per wave merge:** Full backend `pytest -q` + frontend `pnpm exec vitest --run`.
- **Phase gate:** Full suite green + operator browser-verify checkpoint (similar to Plan 01-07).

### Wave 0 Gaps

All 11 test files above need to be created (none exist). Plus:
- `backend/tests/conftest.py` extension: a `sample_periode` + `sample_session` + `admin_token` fixture chain (sample_session shaped per DEC-T1-003/004).
- `frontend/src/test/setup.ts` amendment: add `import "fake-indexeddb/auto"` + IDB cleanup `afterEach`.

---

## §10 Audit-Log Volume + Indexing

**Estimate:**
- 26 bidang × ~50 indikator per periode × 1 submit + 1 asesor review + 0-2 recommendations + ~5 progress updates ≈ 250 mutating actions per session, ~500 actions per periode-session-cycle.
- 4 periode/year × 250 sessions × 5 actions = **5,000 actions/year** (high estimate) per session-cycle, multiplied by ~10× for periode admin actions, user mgmt, master-data tweaks = **~100k actions/year** matches CONTEXT.md note.
- Per-row size: ~150 bytes header + ~500 bytes typical `before_data`+`after_data` (delta) = **~650 bytes/row** → **65 MB/year**. Trivial.
- Bursts: closing a periode with carry-over of 100 recommendations fires ~100 audit rows in <1s. Still well within Postgres write capacity for a Konkin VPS.

**Index strategy:**

DEC-T6-002 mandates 3 indexes:
1. `(user_id, created_at DESC)` — "show me everything user X did, newest first" → super_admin filter.
2. `(entity_type, entity_id, created_at DESC)` — "show me the history of this specific recommendation/session" → linked-list audit display.
3. `(created_at DESC)` — "show me the most recent X across everything" → audit dashboard recent-feed.

**Are these sufficient?** Yes for Phase 2. The 3 indexes cover the 3 anticipated query shapes. Adding a covering index (INCLUDE all columns) is premature — 65 MB/year doesn't pay off the maintenance cost.

**JSONB compression notes:**
- Source [CITED: https://www.snowflake.com/en/engineering-blog/postgres-jsonb-columns-and-toast/] documents TOAST kicks in at 2KB → ML session full dumps may exceed this.
- **Mitigation (already chosen):** store **deltas, not full dumps** in `before_data`/`after_data`. Recover full state on demand by replaying audit chain backward from current entity_id.
- TOAST decompression overhead is ~10 µs per row, negligible at our read volume.

**Phase 6 extensions (NOT Phase 2 work):**
- Partition by month (`PARTITION BY RANGE (created_at)`) once table > 5GB.
- Add `audit_log_archive` table + monthly rotate >3 years.
- Add `auditor` role for read access without super_admin powers.

---

## §11 Anti-Patterns (concrete things the planner must NOT do)

> One-line bullets the planner can lift verbatim into PLAN.md guard sections.

1. **Don't bundle audit middleware logic into route handlers.** Middleware owns the row-write; handler tags entity via `audit:<type>` and stashes before/after in `request.state`.
2. **Don't compute `pencapaian` only client-side.** DEC-T2-005: server is authoritative. Client preview is UX only; server re-computes on every PATCH and Submit.
3. **Don't create sessions in `request_revision` decision.** Sessions exist; `request_revision` just flips `state=draft` + clears `nilai_final`. Session creation happens ONCE per periode at `aktif → self_assessment` transition.
4. **Don't auto-close `pending_review` recommendations after N days.** DEC-T4-002 — no SLA, no worker, no escalation in Phase 2.
5. **Don't ship SMTP/email code.** DEC-T5-001 — explicitly descoped. No `aiosmtplib`, no email templates, no Phase-2 acceptance criterion mentions email.
6. **Don't drop the WebSocket token on reconnect.** Each reconnect uses `?token=<current_access_jwt>`. The Zustand store keeps the current token.
7. **Don't capture GET requests in audit middleware.** DEC-T6-001 — mutating verbs only.
8. **Don't capture POST `/auth/refresh` in audit.** DEC-T6-001 — high volume, not a user-decision event.
9. **Don't try to lock sessions for aggregate edits.** DEC-T1-003 + DEC-T2-003 — last-write-wins. Document the convention in UI banner.
10. **Don't compute pencapaian for negative-polarity using the positive formula or vice versa.** Polaritas is per-indikator metadata; the server reads it before computing. (Already a Phase-1-shipped column.)
11. **Don't add `aiosmtplib`/`celery`/`apscheduler` to `pyproject.toml`.** No worker infrastructure in Phase 2.
12. **Don't override `AuditMiddleware` order.** Add it via `app.add_middleware(AuditMiddleware)` in `main.py` AFTER FastAPI's auth middleware (default is at the end; Starlette adds middlewares LIFO so the last `add_middleware` is the outermost).
13. **Don't put DB lookups in Pydantic `model_validator`.** Validators are sync + I/O-free. Use service layer for owner-resolution / cross-entity checks.
14. **Don't load the full ml_stream.structure on every PATCH.** The server validates submit-time only; auto-save only persists the partial payload.
15. **Don't capture the response body in the audit middleware.** Use `request.state.audit_after` (Pitfall 4).
16. **Don't read `localStorage` for the access token in `useNotifications`.** Read from `useAuthStore` (Zustand in-memory). T-07-S-01 mitigation is non-negotiable.
17. **Don't ship a "diff conflict modal" preemptively.** Phase 6 may need one; Phase 2 doesn't.
18. **Don't seed the `notification` table or `audit_log` table with sample rows.** Both are runtime-populated only.
19. **Don't expose `/audit-logs/{id}` (single-row GET) — only filterable list.** Cuts a surface; super_admin-only.
20. **Don't add `Idempotency-Key` support to auto-save PATCH.** Last-write-wins by design; idempotency is for the Excel import only.

---

## §12 Suggested Plan Breakdown (6 plans, 4 waves)

The planner should refine this based on `files_modified` overlap analysis. Initial structure follows Phase 1's pattern (sequential schema + parallel features + sequential UI + checkpoint).

### Wave 1 — Sequential schema chain (1 plan)

**Plan 02-01: Backend models + 3 migrations (sequential, type=execute)**

Files created:
- `backend/app/models/periode.py`, `assessment_session.py`, `assessment_session_bidang.py`, `indikator_applicable_bidang.py`, `recommendation.py`, `notification.py`, `audit_log.py`
- `backend/alembic/versions/?_0004_periode_and_sessions.py`
- `backend/alembic/versions/?_0005_recommendation_notification.py`
- `backend/alembic/versions/?_0006_audit_log.py`
- `backend/app/schemas/{periode,assessment,recommendation,notification,audit}.py` (Pydantic shapes)

This is a single plan because the 3 migrations must chain in order (0003 → 0004 → 0005 → 0006). No parallelism possible.

### Wave 2 — Parallel backend services (2 plans, parallel)

**Plan 02-02: Periode + assessment_session + recommendation routers + services (parallel-A)**

Files:
- `backend/app/routers/periode.py`, `assessment_session.py`, `recommendation.py`
- `backend/app/services/periode_fsm.py`, `recommendation_fsm.py`, `session_creator.py`, `carry_over.py`
- `backend/tests/test_periode_fsm.py`, `test_periode_router.py`, `test_assessment_session.py`, `test_recommendation_create.py`, `test_recommendation_lifecycle.py`, `test_carry_over.py`

**Plan 02-03: Notification + WS + audit middleware (parallel-B)**

Files:
- `backend/app/services/audit_middleware.py`, `notification_dispatcher.py`, `ws_manager.py`
- `backend/app/deps/ws_auth.py`
- `backend/app/routers/notification.py`, `ws_notifications.py`, `audit_log.py`
- `backend/app/main.py` — modified to register `AuditMiddleware`
- `backend/tests/test_audit_middleware.py`, `test_notification_dispatcher.py`, `test_ws_notifications.py`

Parallel because the routers + services touch disjoint files. Plan 02-02 doesn't touch `main.py`; Plan 02-03 adds one middleware registration. Both depend only on Wave 1 models.

### Wave 3 — Frontend primitives + PIC screens (1 plan)

**Plan 02-04: SK primitives + PIC self-assessment screens + auto-save hook**

Files created:
- `frontend/src/components/skeuomorphic/SkLevelSelector.tsx`, `SkSlider.tsx`, `SkToggle.tsx` + tests
- `frontend/src/components/skeuomorphic/index.ts` — modified barrel
- `frontend/src/lib/auto-save.ts`, `notification-store.ts`
- `frontend/src/hooks/useAutoSave.ts`, `useNotifications.ts`, `usePeriodeStore.ts`
- `frontend/src/routes/pic/SelfAssessmentInbox.tsx`, `KpiForm.tsx`, `MlForm.tsx`, `PicRecommendations.tsx`
- `frontend/src/test/setup.ts` — modified to add `fake-indexeddb/auto` + IDB afterEach cleanup
- `frontend/package.json` — added `use-debounce`, `idb`, `fake-indexeddb`
- Tests: `useAutoSave.test.ts`, `useNotifications.test.ts`, `MlForm.test.tsx`, `KpiForm.test.tsx`, `SkLevelSelector.test.tsx`, `SkSlider.test.tsx`, `SkToggle.test.tsx`

Sequential within wave (one plan) because the primitives + hooks are dependencies of the screens.

### Wave 4 — Asesor screens + recommendation flow + audit log + E2E checkpoint (2 plans, sequential)

**Plan 02-05: Asesor screens + super_admin periode screens + audit log viewer**

Files:
- `frontend/src/routes/periode/PeriodeList.tsx`, `PeriodeDetail.tsx`
- `frontend/src/routes/asesmen/AsesorInbox.tsx`, `AsesmenReview.tsx`
- `frontend/src/routes/recommendations/RecommendationList.tsx`
- `frontend/src/routes/Notifications.tsx`
- `frontend/src/routes/AuditLogs.tsx`
- `frontend/src/App.tsx` — modified to add the new routes
- Tests + role-guard tests

**Plan 02-06: Phase-2 E2E browser-verify checkpoint (`autonomous: false`)**

Files: SUMMARY.md only. No new code. The plan is a checklist:

1. `docker compose -f docker-compose.yml up -d --wait` — confirm 6/6 healthy.
2. Login as `super_admin`, open a new periode for TW2 2026, transition `draft → aktif → self_assessment`, confirm `assessment_session` rows are auto-created.
3. Login as `pic_bidang`, open one EAF (aggregate) + one SMAP (ML) session, fill values, watch "Saved Xs ago" tick, verify auto-save fires after 5s pause.
4. DevTools → Network → toggle "Offline" → keep editing → confirm IDB has pending entries → toggle "Online" → confirm queue drains.
5. Submit both sessions.
6. Login as `asesor`, open inbox, approve one (auto-fills nilai_final=PIC's), override the other (force min 20 char justification + attach a recommendation with 2 action_items), confirm one item's owner pre-fills with PIC's user_id.
7. Login back as `pic_bidang`, see notification badge increment via WS (no refresh), open `/notifications` → mark read.
8. Open `/pic/recommendations`, PATCH `/progress` to 50% on one item, POST `/mark-completed` on the other.
9. Login as `super_admin`, open `/audit-logs`, filter by `entity_type=assessment_session` → see the PATCH + submit + asesor-review entries.
10. Trigger `finalisasi → closed` → confirm `pending_review` rec carries to next periode (or queues if no next periode).
11. Rollback `closed → finalisasi` → confirm carried rec stays in next periode (DEC-T1-002 irreversibility).
12. Logout, attempt `/master/konkin-template/2026` as PIC → redirected.

Operator types **`phase 2 verified`** to close.

### Wave-to-Plan dependency graph

```
Wave 1: 02-01 (sequential, blocks everything)
  └── Wave 2: 02-02 ─┐ (parallel)
                     ├── Wave 3: 02-04 (sequential)
        02-03 ──────┤
                     │
                     └── Wave 4: 02-05 (sequential, depends on 02-04 for SK primitives + hooks)
                                 └── 02-06 (operator checkpoint)
```

### Estimated effort (relative, based on Phase 1 calibration)

| Plan | Tasks | Notes |
|------|-------|-------|
| 02-01 | 3-4 | 7 models + 3 migrations + Pydantic schemas — biggest model count of any phase but no logic |
| 02-02 | 3-4 | Sessions / periode / recommendation routers + 2 FSMs + carry_over service |
| 02-03 | 3-4 | Audit middleware + WS manager + notification dispatcher + tests |
| 02-04 | 3-4 | 3 SK primitives + 4 PIC screens + 3 hooks + IDB helpers |
| 02-05 | 3 | 6 asesor/admin/notif screens |
| 02-06 | 1 (checkpoint) | Pure operator walk-through |

### Why not 5 plans (combine 02-04 + 02-05)?

The frontend volume is large — splitting PIC screens (Wave 3) from asesor screens (Wave 4) creates natural seams and lets the planner mark Wave-3 vs Wave-4 differently in the schedule. Combining them creates a 6-7-task plan which is the edge of "too big to commit atomically".

### Why not 7 plans (split 02-02)?

Plan 02-02 covers three routers (periode/assessment_session/recommendation) but they share the `services/` directory and the FSM helpers. Splitting them into 3 plans introduces file-overlap risk in `services/__init__.py` and in `conftest.py` fixture chain. Phase 1's Plan 01-06 already did all of master-data in one plan; same call here.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 (WSL2 deadsnakes) | All backend work | ✓ | 3.11.15 | — |
| Node 20 + pnpm 10 (WSL2) | All frontend work | ✓ | 20.x / 10.15.0 | — |
| Docker + Compose (WSL2) | Stack run + e2e | ✓ | 29.4.3 / v5.1.3 | — |
| Postgres 16 + pgvector image | DB | ✓ | `pgvector/pgvector:pg16` | — |
| Redis 7 alpine | Token revocation + WS coordination optional | ✓ | 7-alpine | — |
| nginx (in compose) | WS upgrade headers | ✓ | from Plan 02 | — |
| `use-debounce` ^10.1.1 | Auto-save hook | ✗ (not installed) | — | Install via `pnpm add` |
| `idb` ^8.0.3 | Offline queue | ✗ (not installed) | — | Install via `pnpm add` |
| `fake-indexeddb` ^6.2.5 | Test IDB mock | ✗ (not installed) | — | Install via `pnpm add -D` |
| Browser ResizeObserver / MotionConfig | Slider drag | ✓ via `motion` 12.38 | — | — |
| `react-hook-form` | KPI/ML form state | ✓ | ^7.75 | — |
| Tailwind v4 `@theme inline` for new tokens | SK primitive surfaces | ✓ | ^4.3 | — |
| OpenRouter API key | (NOT needed in Phase 2) | n/a | — | — |
| SMTP server | (NOT needed in Phase 2 — descoped) | n/a | — | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** Three npm packages — installed via `pnpm add` as part of Plan 02-04 Wave 0. Frontend image rebuild needed after.

---

## Security Domain

> No `security_enforcement` flag found in `.planning/config.json` (file doesn't exist) — treating as enabled.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Existing Plan 05 `require_role` + `current_user` deps. Phase 2 reuses. WS adds query-param JWT (§7). |
| V3 Session Management | yes | Existing Plan 05 refresh-token rotation. Phase 2 reuses. WS sessions live as long as access token (no refresh on WS) — client reconnects after refresh. |
| V4 Access Control | yes | `require_role("super_admin")` on periode transitions / audit-log read. `require_role("asesor", "super_admin")` on asesor-review. `require_role("pic_bidang", "super_admin")` on session PATCH (server also filters by `bidang_id`). |
| V5 Input Validation | yes | Pydantic v2 with `ConfigDict(extra="forbid")` on all request schemas (`PeriodeTransitionRequest`, `AssessmentSelfAssessmentPatch`, `RecommendationCreate`, etc.). Server re-validates submit gate (DEC-T2-004) and pencapaian (DEC-T2-005). |
| V6 Cryptography | no (mostly) | Phase 2 doesn't introduce new crypto. JWT signing/verification reuses Plan 05's `app.core.security`. |
| V7 Error Handling | yes | FastAPI standard error envelope `{error: {code, message, details}}` (CONSTR-api-conventions). Audit-log capture errors are SWALLOWED (log + skip) so they never crash a request — DOS resistance. |
| V8 Data Protection | yes | DEC-T6-001 says `before_data`/`after_data` are JSONB dumps of mutating actions — these may include sensitive PIC notes. Mitigation: `audit_log` read is `require_role("super_admin")` only. JSON-Web-Token claim leakage prevented by httpOnly cookie + memory-only Zustand. |
| V9 Communication | yes | WS endpoint runs over `wss://` in prod (nginx terminates TLS). Token query param is encoded; nginx access log redaction is the planner's call. |
| V10 Malicious Code | yes | No new third-party PII processors. No new file upload (REQ-no-evidence-upload still enforced; multipart count == 1, locked from Phase 1). |
| V11 Business Logic | yes | FSM transitions enforced server-side. Submit gate enforced server-side. Override min 20 chars enforced via Pydantic. |
| V12 Files & Resources | n/a | No file uploads in Phase 2 (DEC-010). |

### Known Threat Patterns for FastAPI + React stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| CSRF on cookie-mode mutating routes | Tampering | `require_csrf` dep on every new mutating route (Phase 1 pattern; CSRF interceptor in axios already echoes) |
| XSS via PIC notes / catatan_asesor / action_item.action | Tampering | React auto-escapes by default. Don't use `dangerouslySetInnerHTML` anywhere on Phase-2 screens. |
| WS auth bypass via missing token check | Spoofing | `decode_token(token, expected_type="access")` + `is_revoked` check BEFORE `websocket.accept()` |
| WS replay (old token still valid until expiry) | Spoofing | Mitigated by short access-token lifetime (60min from Phase 1) + revocation set on logout |
| Audit-log bypass via direct DB write or via missing `audit:<tag>` | Repudiation | Middleware-based + startup-time tag check (Pitfall 8) |
| Mass-assignment via JSONB sub-keys | Tampering | Pydantic `ConfigDict(extra="forbid")` on every nested model (ActionItem, MlSubmitPayload, etc.) |
| SQL injection via dynamic filter on `/audit-logs?filter=` | Tampering | SQLAlchemy parameterized queries (Phase 1 standard); enumerate filter keys, no raw SQL string-concat |
| Notification spam (one user can be DOS'd) | DOS | Rate-limit notification CREATE side (admin-triggered system_announcement) at 100r/min/admin via existing nginx zone. Per-user receive is bounded by event volume. |
| WebSocket connection flood | DOS | nginx `limit_conn` per IP on `/ws/` location (Phase 6 prod-checklist) |
| Audit-log row injection via `user_agent` header (control chars) | Tampering | Pydantic `str` field with max length + Python's default repr handling; no shell echo of audit rows |

---

## Sources

### Primary (HIGH confidence)

- npm registry — `npm view use-debounce version` → `10.1.1` (published 2026-03-29)
- npm registry — `npm view idb version` → `8.0.3` (published 2025-05-07)
- npm registry — `npm view fake-indexeddb version` → `6.2.5`
- PyPI — `pip index versions transitions` → `0.9.3` (2025-07-02)
- [FastAPI WebSockets tutorial](https://fastapi.tiangolo.com/advanced/websockets/) — official
- [FastAPI Testing WebSockets](https://fastapi.tiangolo.com/advanced/testing-websockets/) — official; confirms `TestClient.websocket_connect`
- [FastAPI Middleware tutorial](https://fastapi.tiangolo.com/tutorial/middleware/) — official
- [Pydantic v2 Fields](https://docs.pydantic.dev/latest/concepts/fields/) — official
- [Pydantic v2 Validators](https://docs.pydantic.dev/latest/concepts/validators/) — official
- [use-debounce repo](https://github.com/xnimorz/use-debounce) — README + signature
- [npm idb page](https://www.npmjs.com/package/idb) — Jake Archibald
- [fake-indexeddb repo](https://github.com/dumbmatter/fakeIndexedDB) — README

### Secondary (MEDIUM confidence)

- [Robust WebSocket Reconnection in JS (DEV.to, 2025)](https://dev.to/hexshift/robust-websocket-reconnection-strategies-in-javascript-with-exponential-backoff-40n1) — backoff + jitter pattern, cross-checked with WebSocket.org
- [WebSockets in React (WebSocket.org, 2025)](https://websocket.org/guides/frameworks/react/) — hook lifecycle pitfalls
- [Authenticating WebSocket Clients in FastAPI (hexshift, Medium, 2025)](https://hexshift.medium.com/authenticating-websocket-clients-in-fastapi-with-jwt-and-dependency-injection-d636d48fdf48) — token query param pattern
- [Postgres JSONB + TOAST (Snowflake engineering blog)](https://www.snowflake.com/en/engineering-blog/postgres-jsonb-columns-and-toast/) — TOAST thresholds + decompression cost
- [How to Create Audit log on FastAPI (Daniel Shalev, Medium)](https://medium.com/@danniel.shalev_46673/how-to-create-audit-log-using-fast-in-python-b30f896710ff) — middleware skeleton
- [pytransitions/transitions repo](https://github.com/pytransitions/transitions) — confirms hand-rolled is appropriate for small state sets
- [Starlette discussion #2801 — BaseHTTPMiddleware + StreamingResponse](https://github.com/Kludex/starlette/discussions/2801) — captures the streaming-body pitfall

### Tertiary (LOW confidence, used for cross-check only)

- [npm-compare: dexie vs idb vs localforage](https://npm-compare.com/dexie,idb,localforage) — weekly download counts (used as popularity signal only)
- [npmtrends: dexie vs idb vs localforage](https://npmtrends.com/dexie-vs-idb-vs-localforage) — same
- [Smarter forms in React: useAutoSave hook (Medium)](https://darius-marlowe.medium.com/smarter-forms-in-react-building-a-useautosave-hook-with-debounce-and-react-query-d4d7f9bb052e) — confirms the pattern shape (not the only valid one)

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — every version verified against npm/PyPI registry on 2026-05-11.
- Architecture patterns: HIGH — auto-save / WS / audit middleware patterns are well-known and have official-doc support. Hand-rolled FSM choice is justified by ecosystem precedent.
- Pitfalls: HIGH — every pitfall has a concrete source link or is derived directly from a known Phase 1 pattern.
- Plan breakdown: MEDIUM — initial structure (6 plans, 4 waves) is a planner-friendly starting point but file-overlap analysis is the planner's job. Could collapse to 5 if 02-04 + 02-05 are merged.
- Audit-log volume: MEDIUM — based on the CONTEXT.md "~100k actions/year/unit" claim (A1 assumption). Real volume revealed in production.

**Research date:** 2026-05-11
**Valid until:** 2026-06-10 (30 days — stack is stable; WS/IDB ecosystem isn't moving fast)
