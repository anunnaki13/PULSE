# Phase 2: Assessment Workflow (PIC + Asesor) - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning
**Source:** Operator discussion 2026-05-11 + REQUIREMENTS.md sections C/D/E/F/M/N + Phase 1 artifacts

<domain>
## Phase Boundary

**Goal (from ROADMAP.md):** PIC dapat melakukan self-assessment end-to-end (KPI Kuantitatif + Maturity Level) untuk indikator pilot, asesor dapat review/override/return, dan setiap rekomendasi yang dibuat dapat di-track sampai close atau carry-over ke periode berikutnya — semua perubahan tercatat di audit log dan notifikasi terkirim.

**Requirements scoped to this phase (10):**
- Periode management — REQ-periode-lifecycle
- Self-assessment workspace — REQ-self-assessment-kpi-form, REQ-self-assessment-ml-form, REQ-auto-save, REQ-pic-actions
- Asesor workspace — REQ-asesor-review
- Recommendation tracker — REQ-recommendation-create, REQ-recommendation-lifecycle
- Notifications — REQ-notifications *(scope reduced — see Decisions §Notifications)*
- Audit log — REQ-audit-log

**Pilot indicators (already seeded by Plan 01-07):** Outage Management + SMAP (maturity-level streams), EAF + EFOR (KPI Kuantitatif streams). All four rubrics live in `ml_stream.structure` JSONB on the seeded Konkin 2026 template. Phase 2 builds the assessment forms ON these — does NOT add new indikator rubrics.

**Out of scope (deferred to later phases):**
- NKO calculator engine + multi-tier aggregation (Phase 3 — REQ-nko-calc-engine, REQ-nko-aggregation-rules)
- Dashboard executive / heatmap / trend (Phase 3 — REQ-dashboard-*)
- Compliance laporan + komponen tracker (Phase 4)
- AI Draft Justifikasi / Anomaly Detection / Inline Help / Comparative Analysis (Phase 5; REQ-pic-actions acceptance "Use AI Suggestion" is wired to a stub button that's enabled when Phase 5 lands)
- Stream coverage beyond pilot (Phase 6 batches 1–4: Reliability, Efficiency, WPC, Operation, etc.)
- Report exports (Phase 4 — REQ-report-*)
- Mobile/PWA hardening (post-MVP)

**MVP boundary check:** Phase 2 is **inside** the MVP boundary (MVP = end of Phase 3 per source §5). Output of Phase 2 is a runnable assessment loop — PIC opens a periode, fills KPI + ML forms for 4 pilot indikator across 26 bidang, submits, asesor reviews + overrides + attaches recommendations, recommendations are tracked through their lifecycle. NKO total still NOT computed (that's Phase 3) — but all the data feeding NKO is in place.

</domain>

<decisions>
## Implementation Decisions (from 2026-05-11 discussion)

### Periode Lifecycle

#### DEC-T1-001: All transitions manual via super_admin (no scheduler in Phase 2)
- **States:** `draft → aktif → self_assessment → asesmen → finalisasi → closed` (verbatim per REQ-periode-lifecycle).
- **Trigger:** Each transition fires from a tombol on the periode-admin screen (super_admin only). No date-driven scheduler in Phase 2 — `tanggal_buka` and `tanggal_tutup` fields are informational only, not auto-acting.
- **Tombol labels:** "Buka Periode" / "Mulai Self-Assessment" / "Tutup Self-Assessment" / "Buka Asesmen" / "Finalisasi" / "Tutup Periode".
- **Side effects per transition:**
  - `aktif → self_assessment`: auto-creates `assessment_session` rows for every (indikator, bidang) pair that is applicable per master-data mapping (DEC-T1-004). Aggregate indikator gets ONE shared session with assignment list (DEC-T1-003).
  - `finalisasi → closed`: carries over open/in-progress/pending-review recommendations to the next periode (DEC-T4-004). Draft self-assessments still in `state=draft` at close are marked `state=abandoned` with audit-log entry.
- **Reasoning:** Scope-tight for Phase 2. Date-scheduler is small but enough to defer to a Phase 6 prod-hardening pass without breaking the model.

#### DEC-T1-002: super_admin can rollback closed periode to any prior state
- Tombol "Reopen ke <State>" di periode admin screen. Confirms via modal with mandatory reason field (min 20 chars).
- **Captured in audit log:** before_state, after_state, reason, user_id, timestamp.
- **Carry-over is irreversible:** rolling back `closed → finalisasi` does NOT un-carry recommendations that already moved to next periode. The carried recommendations stay where they are.
- **Why:** Late submission corrections happen in real PLN ops. Hard immutability creates manual-create workarounds that are worse for audit trail than logged rollback.

#### DEC-T1-003: Aggregate indikator = 1 session shared + bidang assignment list
- For aggregate indikator (EAF, EFOR — cover BID_OM_1..5 + BID_OM_RE collectively), `assessment_session.bidang_id` is NULL.
- New table `assessment_session_bidang(session_id, bidang_id, PRIMARY KEY (session_id, bidang_id))` enumerates which bidang are covered by the session.
- PIC from ANY bidang in the list can edit the session (last-write-wins per DEC-T2-003). All bidang see the same final value once submitted.
- **Reasoning:** Matches the domain — EAF is a unit-level metric, not per-bidang. N-sessions-with-aggregator pattern was rejected because it duplicates input work (PIC of OM-1 and OM-2 entering the same number).

#### DEC-T1-004: Skip session creation for non-applicable (indikator, bidang) pairs
- Master-data mapping table `indikator_applicable_bidang(indikator_id, bidang_id, PRIMARY KEY (indikator_id, bidang_id))` declares which bidang each indikator applies to. Seeded in Phase 2 along with periode mechanics.
- For aggregate indikator (DEC-T1-003), the mapping is between the indikator and the covered bidang list — but session is still 1 with NULL bidang_id; the mapping table just records "these bidang's PICs see this session".
- For per-bidang indikator, the mapping resolves to 1 session per (indikator, bidang) pair where the pair is in the applicable set.
- **Effect on volume:** Instead of ~50 indikator × 26 bidang = 1300 sessions per periode (option B), expected count is ~150–250 sessions per periode (option A) — manageable.
- **PIC view filtering:** PIC at `/pic/self-assessment` sees only sessions for their `bidang_id` (single-bidang case) or sessions where their `bidang_id` is in the `assessment_session_bidang` list (aggregate case).

### Self-Assessment Forms

#### DEC-T2-001: ML LevelSelector = horizontal 5-segment slider + LED row (NOT rotary dial)
- **Visual:** Horizontal slider mirroring an audio mixer fader. Divided into 5 segments labelled L0–L4. ABOVE the slider: row of 5 skeuomorphic LEDs, the LED for the currently selected level lit (uses existing `SkLed` primitive with `data-state="on"`).
- **Interaction:** Tap a segment OR drag the slider handle to select. Keyboard: arrow left/right to step levels.
- **Naming:** Component is still called `SkLevelSelector` (matches the spec language). Sits next to `SkSlider` (Phase 2-built) and `SkToggle` (Phase 2-built). Rotary dial `SkDial` is deferred to Phase 3 (NKO gauge).
- **Why the segmented slider over rotary:** User explicitly picked it. More familiar to non-technical PIC users, mobile-friendly (touch drag), simpler to make accessible.

#### DEC-T2-002: Sub-level continuous slider — always-on, range auto-updates with level
- Below the LevelSelector, an always-visible `SkSlider` (Phase 2-built skeuomorphic linear slider) with increment 0.01 and value bounds tracking the current level (L3 → range 3.01–4.00; L0 → 0.00–1.00; etc.).
- Live numeric display next to the slider (mono LCD-style readout using `SkScreenLcd` deferred-build helper — Phase 3 ships `SkScreenLcd`; Phase 2 uses a plain numeric `<span>` styled with the LCD font + `--sk-lcd-green` token).
- **Lock toggle:** "Lock to integer" toggle (`SkToggle` Phase 2 primitive) — when on, slider snaps to integer at level center (L3 → 3.50 default). Sets a per-sub-area flag in the session payload.
- **Why:** REQ-self-assessment-ml-form explicitly requires the continuous slider; defaulting visible avoids two-step interaction.

#### DEC-T2-003: Last-write-wins + server-clock + IndexedDB offline queue
- **Conflict model:** No locking. Last write to `assessment_session` wins. Acceptable for non-aggregate sessions (single PIC owns). For aggregate sessions, the implicit "first to start editing" PIC convention is documented in the UI ("Sesi ini dipakai bersama bidang X, Y, Z").
- **Clock:** `Saved Xs ago` indicator drives off the server-side `updated_at` returned in the PATCH response. Eliminates timezone / NTP drift on PIC's machine.
- **Network down:** Auto-save fails are caught; payload queued to IndexedDB (one queue per session per user). On reconnect, retry oldest-first. UI shows persistent toast "Menyimpan perubahan offline (N pending)…" until queue drains. If the server returns 409/422 on replay (rare), surface a modal with "Local copy vs server copy — pick which to keep".
- **Why:** Standard pattern for low-stakes shared docs. Stronger optimistic locking adds friction without much real-world benefit when 99% of sessions have 1 active editor.

#### DEC-T2-004: Submit gate is HARD — disabled when any sub-area unfilled
- Submit button (`SkButton` variant=primary) is `disabled` with tooltip "Lengkapi semua sub-area dulu (X dari Y tersisa)" until every sub-area in the ML form has either:
  - a numeric value, OR
  - the explicit "Tidak dinilai" toggle on (with mandatory text reason ≥ 10 chars).
- Counter pill in the form header: "Y dari Y lengkap" turns green when complete.
- Server-side enforcement: `POST /assessment/sessions/{id}/submit` re-validates the same gate and returns 422 if any sub-area is NULL without `tidak_dinilai_reason`.

#### DEC-T2-005 (derived from REQ-self-assessment-kpi-form): Polarity-aware formula compute is client-side preview + server-side authority
- Client computes `pencapaian` live as PIC types (3 modes: positif `(R/T)*100`, negatif `{2 − (R/T)}*100`, range-based three-band per `01_DOMAIN_MODEL.md` §4.1).
- On every auto-save and on Submit, server re-computes from `realisasi`, `target`, `polaritas` fields and stores authoritative `pencapaian` + `nilai`. Client preview is for UX only.
- Discrepancy between client preview and server result (rare — only on bad math edge cases or polaritas mismatch) is logged at backend ERROR level.

### Asesor Review

#### DEC-T3-001: Override justification = min 20 chars, mandatory, free-form text
- `POST /assessment/sessions/{id}/asesor-review` with `decision="override"` requires `catatan_asesor.length >= 20`. Server enforces via Pydantic validator.
- No structured template enforced. Frontend offers an optional placeholder pattern ("Sumber data: ... | Alasan: ...") but does not validate format.
- `nilai_final` is required on override (the value asesor entered); on `approve`, `nilai_final` is auto-set to PIC's `nilai`; on `request_revision`, `nilai_final` stays NULL.
- PIC reads `catatan_asesor` in the session detail screen. Manajer sees it in the asesmen breakdown view (Phase 3 dashboard).

### Recommendation Tracker

#### DEC-T4-001: Default owner = PIC of source assessment, asesor can override per item
- When asesor clicks "Add Recommendation" inline during review, the recommendation form's `action_items[i].owner_user_id` field is pre-filled with the PIC who submitted the source `assessment_session` (looked up via `bidang_id → users.bidang_id`).
- Each `action_items[i]` can have its own owner — asesor can pick different users for different items.
- If the looked-up PIC user no longer exists (deactivated / deleted), the field is empty and asesor must pick before save.

#### DEC-T4-002: No SLA timeout, no auto-escalation in Phase 2
- PIC mark-completed → status `pending_review`. Asesor verify-close happens whenever. No reminder notifs scheduled by a worker.
- Phase 6 prod-checklist can layer on SLAs (3-day reminder, 7-day escalate to super_admin) without schema changes — purely additive in worker land.

#### DEC-T4-003: Recommendation lifecycle states (from REQ-recommendation-lifecycle, verbatim)
- `open` (created) → `in_progress` (PIC PATCH `/progress` first hit) → `pending_review` (PIC POST `/mark-completed`) → `closed` (asesor POST `/verify-close`).
- Alternative tail: `carried_over` (set automatically on periode close per DEC-T4-004).
- No PIC-driven status changes outside this lifecycle. Asesor can manually set `closed` (with notes) without going through pending_review if needed (audit-logged).

#### DEC-T4-004: Carry-over policy on periode close
- **Carried:** Recommendations with status `open` OR `in_progress` OR `pending_review` at the moment of `POST /periode/{id}/close`.
- **Not carried:** `closed` recommendations (terminal).
- **Mechanism:** For each carried recommendation, create a duplicate row in next periode with:
  - `carried_from_id` set to original.
  - Original's `carried_to_id` set to new row.
  - `source_assessment_id` retained (points to original session — chain visible).
  - `status` preserved (open / in_progress / pending_review carries the same status forward).
  - `target_periode_id` resolved as: next TW (TW2 2026 → TW3 2026). If closing TW4, next is TW1 of next year. If the carry-over target periode doesn't exist yet (draft state expected before next periode opens), the carry-over is queued and runs when the target periode transitions from draft to aktif.
- **Draft self-assessments at close:** `state=draft` sessions still in periode at close are marked `state=abandoned`. Audit log entry per session. PIC sees status "Abandoned at periode close" on their /pic/sessions view (history).

### Notifications

#### DEC-T5-001: REQ-notifications scope reduced — in-app + WS only, NO email/SMTP in Phase 2
- **Channels enabled in Phase 2:** in-app (DB row in `notification` table, listed at `/notifications` + bell badge in AppShell) + WebSocket push (real-time `/ws/notifications?token=...`).
- **Channels deferred:** SMTP email. REQ-notifications acceptance "Email channel via SMTP for deadline alerts (basic in MVP)" is **explicitly descoped** at user direction 2026-05-11. Rationale recorded: "tidak perlu ada email — semua di aplikasi saja". Reconsidered in Phase 5 (SMTP infra may be needed for AI report exports) or Phase 6 prod-hardening.
- **Trace note:** This is a SCOPE-REDUCTION on a v1 requirement, not on an LOCKED ADR decision — it's allowed without ADR amendment. Project owner = Budi confirms.

#### DEC-T5-002: 1 notif per event (no bundling)
- Every triggering action (submit, override, recommendation_assigned, etc.) creates 1 `notification` row + 1 WS push.
- UI groups by date in the notifications list to reduce visual noise. No backend batching/digesting in Phase 2.

#### DEC-T5-003: Notification types — full set per REQ
- `assessment_due`, `review_pending`, `recommendation_assigned`, `deadline_approaching`, `periode_closed`, `system_announcement`.
- Type → channels mapping (in-app + WS for all, email is descoped):

| Type | in-app | WS | email |
|------|--------|-----|-------|
| assessment_due | ✓ | ✓ | (descoped) |
| review_pending | ✓ | ✓ | — |
| recommendation_assigned | ✓ | ✓ | (descoped) |
| deadline_approaching | ✓ | ✓ | (descoped) |
| periode_closed | ✓ | ✓ | — |
| system_announcement | ✓ | — | — |

### Audit Log

#### DEC-T6-001: Capture mutating actions + login/logout, mutating-only for entities
- **Captured actions:**
  - All authenticated `POST/PATCH/PUT/DELETE` to `/api/v1/*` that returns `<400` (the audit middleware sits after route handler success).
  - `POST /auth/login` success/failure (failure with reason: bad_password / locked / inactive).
  - `POST /auth/logout` success.
  - `POST /auth/refresh` is NOT captured (too high volume, not a user-decision event).
- **Captured fields per row:**
  - `user_id`, `action` (HTTP verb + route template), `entity_type` (e.g. `assessment_session`), `entity_id` (UUID), `before_data` (JSON, NULL on create), `after_data` (JSON, NULL on delete), `ip_address`, `user_agent`, `created_at`.
- **Implementation:** FastAPI middleware (`AuditMiddleware`) wraps every mutating route. Uses route-name `tag` to resolve `entity_type`. `before_data`/`after_data` are JSON dumps of the entity row pre/post the operation.
- **Reads NOT captured:** GET requests, including sensitive ones (PIC notes, audit_log itself).

#### DEC-T6-002: Same Postgres + retention forever (no auto-purge in Phase 2)
- Table `audit_log` lives in the same `pulse` DB. Indexes per REQ: `(user_id, created_at desc)`, `(entity_type, entity_id, created_at desc)`, `(created_at desc)`.
- No auto-purge. Storage assumed manageable at PLN ops scale (~100k actions/year/unit).
- Phase 6 prod-checklist may add: (a) archive policy (rotate >3 years to `audit_log_archive`), (b) restricted READ via `auditor` role addition. Both are additive.
- Append-only enforced: no `PATCH`/`DELETE` routes on `/audit-logs` resource. Read via `GET /audit-logs?filter=...` gated by `require_role("super_admin")` per REQ.

</decisions>

<frontend_changes>
## Frontend Surface Added in Phase 2

**New routes:**
- `/periode` (super_admin) — periode list + create + transition buttons
- `/periode/:id` — periode detail (sessions overview, asesmen progress, recommendations linked)
- `/pic/self-assessment` (pic_bidang) — PIC's session inbox (filtered by bidang_id + aggregate sessions)
- `/pic/self-assessment/:session_id` — KPI form OR ML form (component switches on session.indikator.tipe)
- `/pic/recommendations` (pic_bidang) — PIC's owned recommendation items + progress update form
- `/asesmen` (asesor, super_admin) — asesor inbox (submitted sessions awaiting review)
- `/asesmen/:session_id` — review screen (PIC's submission + decision buttons + inline recommendation form)
- `/recommendations` (asesor, super_admin) — full recommendation list + filters + verify-close action
- `/notifications` — notification list + mark-read + mark-all-read
- `/audit-logs` (super_admin) — filterable audit log table

**New SK primitives (built in Phase 2):**
- `SkLevelSelector` — horizontal 5-segment slider + LED row above (DEC-T2-001)
- `SkSlider` — generic skeuomorphic linear slider with grip texture (used by sub-level + KPI sliders)
- `SkToggle` — skeuomorphic on/off rocker (used by "Tidak dinilai" toggle + "Lock to integer")
- All three added to the `@/components/skeuomorphic` barrel.

**Reused from Phase 1:**
- Login + ProtectedRoute + AppShell + Dashboard
- Zustand auth store (`useAuthStore`)
- axios client with refresh-on-401 + CSRF echo
- BI i18n lookups
- Existing primitives: SkLed, SkButton, SkPanel, SkInput, SkSelect, SkBadge

**State management additions:**
- Auto-save hook `useAutoSave(sessionId, payload)` — debounced 5s, IndexedDB queue on offline
- WebSocket hook `useNotifications()` — connects to `/ws/notifications?token=...`, dispatches to a Zustand `notificationStore`
- `usePeriodeStore()` — current active periode + state transitions cache

</frontend_changes>

<backend_changes>
## Backend Surface Added in Phase 2

**New models (`backend/app/models/`):**
- `periode.py` — Periode entity (status enum, tanggal_buka, tanggal_tutup, tahun, triwulan, semester)
- `assessment_session.py` — Session per (indikator, bidang) or per indikator (aggregate); state machine draft / submitted / approved / overridden / revision_requested
- `assessment_session_bidang.py` — N:N for aggregate sessions (DEC-T1-003)
- `indikator_applicable_bidang.py` — N:N mapping (DEC-T1-004)
- `recommendation.py` — Recommendation with status enum, action_items JSONB
- `notification.py` — Notification with type enum, read_at, payload JSONB
- `audit_log.py` — Append-only audit log

**Amendments to Phase 1 models:**
- None directly. `User.bidang_id` is already in place from Plan 01-06.

**New migrations (chain on 0003 from Phase 1):**
- `0004_periode_and_sessions.py` — periode + assessment_session + assessment_session_bidang + indikator_applicable_bidang
- `0005_recommendation_notification.py` — recommendation + notification + indexes
- `0006_audit_log.py` — audit_log table + 3 indexes

**New routers (auto-discovered by Phase 1's pkgutil walk):**
- `periode.py` — periode CRUD + state transition routes (admin-only)
- `assessment_session.py` — list, get, patch auto-save, submit, withdraw (PIC-scoped); asesor-review (asesor-scoped)
- `recommendation.py` — create (inline from review or standalone), progress, mark-completed, verify-close, carry-over (admin)
- `notification.py` — list, mark-read, mark-all-read
- `ws_notifications.py` — WebSocket `/ws/notifications` (token query param auth)
- `audit_log.py` — list with filters (super_admin only)

**New services (`backend/app/services/`):**
- `audit_middleware.py` — FastAPI middleware that auto-captures mutating actions
- `notification_dispatcher.py` — central place that fires both DB insert + WS broadcast for any notif
- `session_creator.py` — called by periode transition `aktif → self_assessment` to spawn sessions per the indikator_applicable_bidang map
- `carry_over.py` — called by periode transition `finalisasi → closed` to chain open recs forward

**WebSocket plumbing:**
- `ws_manager.py` — singleton connection registry. On connect: validate JWT, register `(user_id, ws)` pair. On notify: lookup connections for `user_id`, send.
- Wired into the `notification_dispatcher` so an in-app insert plus a WS push happen atomically (or as close to atomic as the runtime allows — sequential within request, best-effort retry on WS).

</backend_changes>

<open_questions_for_research>
## Open Questions for `gsd-phase-researcher`

1. **Auto-save debounce vs throttle in React** — REQ-auto-save says "every 5 seconds (debounced)". Confirm `useDebouncedCallback` from `use-debounce` (or hand-rolled with `useEffect` cleanup) is the right primitive. Verify behavior when PIC types continuously — debounce should NOT auto-save every 5s while typing; it should save 5s AFTER last keystroke.
2. **IndexedDB libraries for the offline queue** — direct IndexedDB vs `idb` vs `dexie` vs `localforage`. Pick on bundle size + Vite SSR compatibility + ergonomic API. Default suggestion: `idb` (Jake Archibald's wrapper, ~1KB, promise-based, no React-specific opinions).
3. **WebSocket reconnect strategy** — exponential backoff with jitter, max retries before showing "Sambungan terputus" toast. Phase 1 didn't ship WS yet; this is fresh ground. RFC: 1s → 2s → 4s → 8s → 16s cap, with jitter ±30%; persistent toast after 5 fails.
4. **FastAPI middleware vs dependency for audit log** — middleware sees raw request/response; dependency sees parsed Pydantic models. For `before_data`/`after_data` capture, dependency is cleaner (typed objects) but requires every router to opt-in via `Depends(audit(entity_type="assessment_session"))`. Middleware is opt-out (default capture for all `/api/v1/*` mutating). Research the trade-off + DX cost for downstream phases.
5. **Periode state machine library** — `transitions` Python lib vs hand-rolled state machine class. Hand-rolled is fine for 6 states + ~5 transitions. Confirm.
6. **Pydantic JSON polymorphism for `action_items`** — `recommendation.action_items` is JSONB of `[{action, deadline, owner_user_id?}, ...]`. Decide schema: Pydantic `List[ActionItem]` with `model_validator` for partial owner_user_id, vs raw JSON validation in service layer. Default: typed list, server resolves missing owner to default per DEC-T4-001.
7. **WS token auth via query param** — REQ uses `WS /ws/notifications?token=...` (token in query string). Confirm that's safer than Authorization header (which WebSocket doesn't support in browsers anyway). Token is the access JWT, validated on connect, ws closed if rotated/revoked. No re-validation mid-session; client reconnects after access token refresh.
8. **Auto-save conflict UX library** — if the rare 409/422 replay-conflict modal needs a diff view (server vs local), pick a small diff library. Default: just show both as JSON in two `<pre>` blocks; advanced diff deferred.

</open_questions_for_research>

<deferred_ideas>
## Deferred Ideas (captured here, not implemented in Phase 2)

- **Email/SMTP notifications** — User explicitly descoped 2026-05-11. Reconsider in Phase 5 (AI may need SMTP for report emails) or Phase 6 prod hardening.
- **Date-driven periode scheduler** — Manual transitions only in Phase 2. A cron worker that flips states based on `tanggal_buka` / `tanggal_tutup` is a Phase 6 add.
- **Recommendation SLA + escalation** — No-timeout in Phase 2. Phase 6 prod-checklist can add 3-day reminder + 7-day escalation worker.
- **Auditor role** — Phase 2 audit log is read by super_admin only. Adding an `auditor` role to REQ-user-roles is a future ADR if PLN audit team needs read access without super_admin powers.
- **Audit log archive policy** — Retention forever in Phase 2. Phase 6 can rotate >3 years to archive table or S3.
- **Optimistic locking on sessions** — Last-write-wins in Phase 2. If aggregate session conflicts become noisy in real ops, Phase 6 can add `version` column + 409 conflict resolution UX.
- **AI Suggestion button** — REQ-pic-actions includes "Use AI Suggestion (opt-in, see REQ-ai-draft-justification)". Phase 2 ships the BUTTON disabled with tooltip "Tersedia di Phase 5". Phase 5 lights it up.
- **Mobile UX optimization beyond responsive baseline** — Forms work on mobile (slider drag, button taps) but no PWA install / push notif. Post-MVP.
- **Heatmap of submission status** (which bidang × indikator are submitted/approved/pending across the periode) — useful operationally; spec implies it's in the periode detail screen but doesn't define it precisely. Could ship a basic table-grid in Phase 2 OR defer the heatmap-styling polish to Phase 3 dashboards.

</deferred_ideas>

<phase_1_carryforward>
## Phase 1 Patterns to Honor

- **Router/model auto-discovery** is established. New router files in `backend/app/routers/` and new model files in `backend/app/models/` are picked up with no edits to `main.py` or `db/base.py`.
- **All toolchain calls go through WSL**: `wsl -d Ubuntu-22.04 -- python3.11 …`, `wsl -d Ubuntu-22.04 -- pnpm …`, `wsl -d Ubuntu-22.04 -- docker compose …`. Verify blocks in plans MUST use the WSL prefix.
- **Skeuomorphic primitives barrel** at `@/components/skeuomorphic`. New primitives (SkLevelSelector, SkSlider, SkToggle) are added to the barrel.
- **No raw HTML form elements** on PIC/asesor screens. All inputs go through SK primitives (W-01 contract continues to apply).
- **Spec role names verbatim** in all `require_role(...)` calls and frontend Role union (B-01/B-02 continues to apply).
- **CSRF echo** on all mutating routes is via the existing axios interceptor (B-07 pattern from Plan 01-06).
- **i18n lookups** via `t()` from `@/lib/i18n` — Phase 2 ADDS keys for assessment / periode / recommendation / notification domains.
- **Test scaffolding**: per-task atomic commits, real `pytest` runs (not `ast.parse`), `vitest --run` smoke. Conftest + httpx AsyncClient fixtures from Plan 01-03 are reused; per-test transactional rollback continues to be the default.

</phase_1_carryforward>

<next_steps>
## Next Steps

1. `/gsd-plan-phase 2` — produce 02-RESEARCH.md (technical research from `gsd-phase-researcher` on the open questions above) + per-plan PLAN.md files (estimate 5–7 plans across 3–4 waves).
2. `/gsd-execute-phase 2` — run the plans.
3. Operator browser-verify checkpoint at end of Phase 2 (similar pattern to Plan 01-07): open `/pic/self-assessment`, fill an EAF + a SMAP, submit, switch to asesor, override, attach recommendation, verify it shows in `/recommendations` tracker.

</next_steps>
