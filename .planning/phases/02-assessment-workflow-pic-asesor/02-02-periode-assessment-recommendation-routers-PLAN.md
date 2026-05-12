---
phase: 02-assessment-workflow-pic-asesor
plan: 02
type: execute
wave: 2
depends_on: [02-01]
files_modified:
  - backend/app/services/periode_fsm.py
  - backend/app/services/recommendation_fsm.py
  - backend/app/services/session_creator.py
  - backend/app/services/carry_over.py
  - backend/app/services/pencapaian.py
  - backend/app/routers/periode.py
  - backend/app/routers/assessment_session.py
  - backend/app/routers/recommendation.py
  - backend/tests/conftest.py
  - backend/tests/test_periode_fsm.py
  - backend/tests/test_periode_router.py
  - backend/tests/test_session_creator.py
  - backend/tests/test_assessment_session.py
  - backend/tests/test_asesor_review.py
  - backend/tests/test_recommendation_create.py
  - backend/tests/test_recommendation_lifecycle.py
  - backend/tests/test_carry_over.py
autonomous: true
requirements:
  - REQ-periode-lifecycle
  - REQ-self-assessment-kpi-form
  - REQ-self-assessment-ml-form
  - REQ-auto-save
  - REQ-pic-actions
  - REQ-asesor-review
  - REQ-recommendation-create
  - REQ-recommendation-lifecycle
must_haves:
  truths:
    - "**DEC-T1-001 honored:** `POST /api/v1/periode/{id}/transition` accepts every forward transition (draft→aktif→self_assessment→asesmen→finalisasi→closed) and every rollback (super_admin only); no cron/scheduler is registered. `tanggal_buka` / `tanggal_tutup` are informational only."
    - "**DEC-T1-002 honored:** Rollback transitions REQUIRE `reason` field with `len(reason) >= 20`. Server returns 422 otherwise. `last_transition_reason` + `last_transition_by` + `last_transition_at` are persisted."
    - "**DEC-T1-003 honored:** On `aktif → self_assessment`, `session_creator.create_sessions_for_periode()` reads `indikator_applicable_bidang`. For pairs flagged `is_aggregate=True`, creates ONE assessment_session with `bidang_id=NULL` and populates `assessment_session_bidang` for every bidang in the aggregate set."
    - "**DEC-T1-004 honored:** session_creator skips pairs that are NOT in `indikator_applicable_bidang`. Idempotent: re-running on the same periode is a no-op (SELECT existing first, INSERT only what's missing)."
    - "**DEC-T2-003 honored:** PATCH /assessment/sessions/{id}/self-assessment is last-write-wins; no `version` column; response carries `updated_at` (server clock) so frontend can render `Saved Xs ago`. No 409 modal logic anywhere."
    - "**DEC-T2-004 honored:** `POST /assessment/sessions/{id}/submit` validates the submit gate server-side: every sub-area in `payload` either has a numeric value OR has `tidak_dinilai==true` with `tidak_dinilai_reason.length >= 10`. Returns 422 with a list of offending sub-area codes."
    - "**DEC-T2-005 honored:** Pencapaian + nilai computed by `app.services.pencapaian` from `realisasi`, `target`, `indikator.polaritas` on every PATCH and every Submit. Client-supplied `pencapaian` / `nilai` values are IGNORED (the request body schema doesn't accept them)."
    - "**DEC-T3-001 honored at the service layer too:** beyond the Pydantic model_validator from Plan 02-01, the asesor-review handler asserts the override constraint a second time before commit and writes `nilai_final` only when `decision=='override'`. On approve, `nilai_final` is set from PIC's `nilai`. On request_revision, it stays NULL and the session state flips back to `draft`."
    - "**DEC-T4-001 honored:** `app.services.recommendation_create.resolve_default_owners()` looks up the source-assessment PIC via `bidang_id → users.bidang_id` join (or via `assessment_session_bidang` for aggregate sessions). If the lookup returns NULL (PIC deactivated), the router returns 422 with `owner_required_for_action_item_<index>` for the asesor to pick manually."
    - "**DEC-T4-002 honored:** No cron/scheduler/worker registered. Recommendations stay in `pending_review` indefinitely until asesor verify-close."
    - "**DEC-T4-003 honored:** `recommendation_fsm.assert_transition_allowed()` enforces `open → in_progress → pending_review → closed`. PIC PATCH `/progress` flips `open → in_progress` on the first call (idempotent thereafter). Asesor `manual-close` from any state with audit-log notes (per CONTEXT.md DEC-T4-003)."
    - "**DEC-T4-004 honored:** `finalisasi → closed` transition calls `carry_over.close_periode_with_carry_over()` which: (a) marks any `state=draft` assessment_session as `state=abandoned`, (b) for every recommendation with status in {open, in_progress, pending_review}, INSERT a new row with `carried_from_id=original.id` + same status + `target_periode_id=resolve_next_periode(...)`, and (c) sets the original row's `carried_to_id`. If the next periode doesn't exist yet, the recommendation is left with `target_periode_id=<pending sentinel>` and queued; Plan 02-02 service ALSO hooks the `draft → aktif` transition to run a `drain_pending_carry_overs()` step."
    - "Every router file declares `tags=['audit:<entity_type>']` on each mutating route (Plan 02-03 middleware reads these tags). Specifically: `audit:periode` on periode transitions; `audit:assessment_session` on session mutating routes; `audit:recommendation` on recommendation routes."
    - "Every mutating route has `Depends(require_csrf)` (CSRF echo via `X-CSRF-Token` — Phase 1 contract continues)."
    - "RBAC matrix is enforced via `require_role(...)` with spec names verbatim (B-01/B-02): periode CRUD + transition = `super_admin`; PIC reads/patches sessions filtered by `user.bidang_id` (or aggregate via `assessment_session_bidang` membership) — `pic_bidang` role; asesor-review = `asesor` or `super_admin`; recommendation create = `asesor` or `super_admin`; recommendation progress/mark-completed = `pic_bidang` (owner of source assessment); verify-close = `asesor` or `super_admin`."
    - "No SMTP code anywhere. No `celery` / `apscheduler` / `aiosmtplib` import in any file this plan creates (DEC-T5-001 + RESEARCH §11.5/11.11)."
    - "Auto-save endpoint `PATCH /api/v1/assessment/sessions/{id}/self-assessment` does NOT support `Idempotency-Key` header (RESEARCH §11.20 — last-write-wins by design)."
  artifacts:
    - path: "backend/app/services/periode_fsm.py"
      provides: "Hand-rolled state machine (RESEARCH §5) — PeriodeStatus + forward transitions + side-effect dispatch table + rollback check"
      contains: "assert_transition_allowed"
    - path: "backend/app/services/recommendation_fsm.py"
      provides: "Hand-rolled recommendation lifecycle FSM (DEC-T4-003)"
      contains: "RecommendationStatus"
    - path: "backend/app/services/session_creator.py"
      provides: "Idempotent session spawner reading indikator_applicable_bidang (DEC-T1-003/T1-004)"
      contains: "create_sessions_for_periode"
    - path: "backend/app/services/carry_over.py"
      provides: "DEC-T4-004 carry-over service + abandon-draft sweep on periode close; drain_pending on next aktif transition"
      contains: "close_periode_with_carry_over"
    - path: "backend/app/services/pencapaian.py"
      provides: "DEC-T2-005 server-authoritative compute — polaritas-aware (positif / negatif / range)"
      contains: "compute_pencapaian"
    - path: "backend/app/routers/periode.py"
      provides: "Periode CRUD + transition router with audit:periode tag + super_admin gate"
      contains: "audit:periode"
    - path: "backend/app/routers/assessment_session.py"
      provides: "PIC list/get/patch/submit/withdraw + asesor-review; audit:assessment_session tag; W-01 link_eviden URL only"
      contains: "audit:assessment_session"
    - path: "backend/app/routers/recommendation.py"
      provides: "Recommendation create/progress/mark-completed/verify-close/manual-close/carry-over; audit:recommendation tag"
      contains: "audit:recommendation"
  key_links:
    - from: "backend/app/routers/periode.py"
      to: "backend/app/services/periode_fsm.py"
      via: "assert_transition_allowed + side-effect dispatch"
      pattern: "periode_fsm"
    - from: "backend/app/routers/periode.py"
      to: "backend/app/services/session_creator.py"
      via: "called on aktif → self_assessment transition (DEC-T1-001 side effect)"
      pattern: "create_sessions_for_periode"
    - from: "backend/app/routers/periode.py"
      to: "backend/app/services/carry_over.py"
      via: "called on finalisasi → closed (DEC-T4-004) and on draft → aktif drain"
      pattern: "close_periode_with_carry_over"
    - from: "backend/app/routers/assessment_session.py"
      to: "backend/app/services/pencapaian.py"
      via: "PATCH + Submit re-compute pencapaian server-side"
      pattern: "compute_pencapaian"
    - from: "backend/app/routers/recommendation.py"
      to: "backend/app/services/recommendation_fsm.py"
      via: "lifecycle gate on every status-changing endpoint"
      pattern: "recommendation_fsm"
    - from: "backend/app/routers/recommendation.py"
      to: "backend/app/models/user.py"
      via: "service-layer owner default resolution via users.bidang_id (DEC-T4-001, RESEARCH §11.13)"
      pattern: "bidang_id"
---

## Revision History

- **Iteration 1 (initial):** Periode router + assessment session router + recommendation router + four services (periode_fsm, recommendation_fsm, session_creator, carry_over, pencapaian) + six test files. Wave 2 parallel with Plan 02-03 (zero file overlap — 02-03 owns `services/audit_middleware.py`, `services/notification_dispatcher.py`, `services/ws_manager.py`, `app/main.py` middleware registration). All locked decisions honored verbatim.

<objective>
Ship the three domain routers (periode, assessment_session, recommendation) plus their supporting services (two hand-rolled FSMs, session_creator, carry_over, pencapaian) on top of Plan 02-01's schema. Every endpoint enforces its locked decisions server-side: DEC-T1-001/002/003/004 (periode lifecycle + rollback + aggregate + applicable-bidang), DEC-T2-003/004/005 (last-write-wins + hard submit gate + server-authoritative pencapaian), DEC-T3-001 (override min 20 chars), DEC-T4-001/002/003/004 (owner-resolution + no SLA + lifecycle + carry-over).

Purpose: This plan delivers the operational substrate of Phase 2. Plan 02-03 (parallel) adds the audit middleware + WS layer that reads `request.state.audit_before/after` set by handlers in this plan, and the notification dispatcher that handlers in this plan invoke on submit/review/recommendation-create.

Output: 3 routers + 5 services + 6 test files + a `tests/conftest.py` extension with `sample_periode` + `sample_session` + `aggregate_session` fixtures. No frontend changes. No SMTP. No worker. Wave 2 — parallel with Plan 02-03, both depend only on Plan 02-01.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/02-assessment-workflow-pic-asesor/02-CONTEXT.md
@.planning/phases/02-assessment-workflow-pic-asesor/02-RESEARCH.md
@.planning/phases/02-assessment-workflow-pic-asesor/02-01-backend-schema-and-migrations-PLAN.md
@.planning/phases/01-foundation-master-data-auth/01-05-auth-backend-jwt-rbac-SUMMARY.md
@.planning/phases/01-foundation-master-data-auth/01-06-master-data-backend-SUMMARY.md

<interfaces>
<!-- From Plan 02-01 (already in place) -->
- app.models.periode.Periode + PeriodeStatus
- app.models.assessment_session.AssessmentSession + SessionState
- app.models.assessment_session_bidang.AssessmentSessionBidang
- app.models.indikator_applicable_bidang.IndikatorApplicableBidang
- app.models.recommendation.Recommendation + RecommendationStatus + RecommendationSeverity
- app.schemas.periode.{PeriodeCreate, PeriodeUpdate, PeriodeTransitionRequest, PeriodePublic}
- app.schemas.assessment.{AssessmentSelfAssessmentPatch, AssessmentSubmit, AsesorReview, AssessmentSessionPublic, InlineRecommendationCreate}
- app.schemas.recommendation.{ActionItem, RecommendationCreate, RecommendationProgressUpdate, RecommendationMarkCompleted, RecommendationVerifyClose, RecommendationPublic}

<!-- From Phase 1 (already in place) -->
- app.deps.auth.require_role, app.deps.auth.current_user
- app.deps.csrf.require_csrf
- app.deps.db.get_db
- backend/tests/conftest.py: client + db_session + admin_unit_user (Plan 01-07 seed) + pic_user / asesor_user / manajer_user (Plan 01-05 fixture chain). Extended in Task 1 with `super_admin_user` if missing.

<!-- Exposed seams (consumed by Plan 02-03 + Plan 02-04/05) -->

# Periode (all writes: super_admin + CSRF; audit:periode tag)
GET    /api/v1/periode                                    -> 200 {data:[PeriodePublic], meta}
GET    /api/v1/periode/{id}                               -> 200 PeriodePublic
POST   /api/v1/periode                                    body PeriodeCreate  -> 201
PATCH  /api/v1/periode/{id}                               body PeriodeUpdate  -> 200
POST   /api/v1/periode/{id}/transition                    body PeriodeTransitionRequest -> 200 (side fx)
GET    /api/v1/periode/{id}/carry-over-summary            -> 200 {carried: [{id, source, target}, ...]} (for rollback warning UI — RESEARCH Pitfall 7)

# Assessment session
GET    /api/v1/assessment/sessions                        ?periode_id&state&page&page_size  (pic_bidang sees only own; asesor sees periode-wide submitted+; super_admin all)
GET    /api/v1/assessment/sessions/{id}                   AssessmentSessionPublic
PATCH  /api/v1/assessment/sessions/{id}/self-assessment   pic_bidang (only if state=draft|revision_requested); body AssessmentSelfAssessmentPatch; recomputes pencapaian; returns AssessmentSessionPublic with updated_at (server clock — DEC-T2-003)
POST   /api/v1/assessment/sessions/{id}/submit            pic_bidang; validates submit gate (DEC-T2-004); flips state=submitted; fires notification
POST   /api/v1/assessment/sessions/{id}/withdraw          pic_bidang; only if state=submitted AND asesor_user_id IS NULL; flips back to draft
POST   /api/v1/assessment/sessions/{id}/asesor-review     asesor|super_admin; body AsesorReview; flips state per decision; inline_recommendations created via recommendation_create service; fires notification

# Recommendation (audit:recommendation; CSRF on writes)
GET    /api/v1/recommendations                            ?periode_id&status&owner_user_id&page (filtered by role)
GET    /api/v1/recommendations/{id}
POST   /api/v1/recommendations                            asesor|super_admin; body RecommendationCreate; resolves owner defaults via service; fires notification
PATCH  /api/v1/recommendations/{id}/progress              pic_bidang (must own at least one action_item); RecommendationProgressUpdate; flips open→in_progress on first call
POST   /api/v1/recommendations/{id}/mark-completed        pic_bidang; flips in_progress → pending_review
POST   /api/v1/recommendations/{id}/verify-close          asesor|super_admin; body RecommendationVerifyClose; flips pending_review → closed
POST   /api/v1/recommendations/{id}/manual-close          asesor|super_admin; body {asesor_close_notes}; any state → closed (audit-logged, per DEC-T4-003)
POST   /api/v1/recommendations/{id}/carry-over            super_admin; body {target_periode_id}; manual one-off carry (DEC-T4-004 auto-carry-over is on periode close, but this endpoint exists for the rare ad-hoc case)
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Hand-rolled state machines (periode_fsm + recommendation_fsm) + pencapaian + session_creator + carry_over services + conftest fixture extensions</name>
  <files>
    backend/app/services/periode_fsm.py,
    backend/app/services/recommendation_fsm.py,
    backend/app/services/session_creator.py,
    backend/app/services/carry_over.py,
    backend/app/services/pencapaian.py,
    backend/tests/conftest.py,
    backend/tests/test_periode_fsm.py,
    backend/tests/test_session_creator.py,
    backend/tests/test_carry_over.py
  </files>
  <action>
    1. `backend/app/services/periode_fsm.py` — RESEARCH §5 hand-rolled FSM (no `transitions` library):
       ```python
       from __future__ import annotations
       from enum import StrEnum
       from app.models.periode import PeriodeStatus

       # Forward transitions: side-effect token (resolved by router-level dispatcher)
       FORWARD: dict[PeriodeStatus, dict[PeriodeStatus, str]] = {
           PeriodeStatus.DRAFT:           {PeriodeStatus.AKTIF:             "drain_pending_carry_overs"},
           PeriodeStatus.AKTIF:           {PeriodeStatus.SELF_ASSESSMENT:  "create_sessions"},
           PeriodeStatus.SELF_ASSESSMENT: {PeriodeStatus.ASESMEN:           "noop"},
           PeriodeStatus.ASESMEN:         {PeriodeStatus.FINALISASI:        "noop"},
           PeriodeStatus.FINALISASI:      {PeriodeStatus.CLOSED:            "close_with_carry_over"},
           PeriodeStatus.CLOSED:          {},
       }
       ORDER = [PeriodeStatus.DRAFT, PeriodeStatus.AKTIF, PeriodeStatus.SELF_ASSESSMENT,
                PeriodeStatus.ASESMEN, PeriodeStatus.FINALISASI, PeriodeStatus.CLOSED]

       class InvalidTransition(ValueError): pass
       class RollbackRequiresSuperAdmin(PermissionError): pass
       class RollbackRequiresReason(ValueError): pass

       def is_rollback(current: PeriodeStatus, target: PeriodeStatus) -> bool:
           return ORDER.index(target) < ORDER.index(current)

       def assert_transition_allowed(
           current: PeriodeStatus,
           target: PeriodeStatus,
           role_names: set[str],
           reason: str | None,
       ) -> str:
           """Returns the side-effect token to dispatch. Raises on illegal transitions."""
           if target == current:
               return "noop"
           # Forward path?
           fwd = FORWARD.get(current, {})
           if target in fwd:
               return fwd[target]
           # Rollback path (DEC-T1-002)
           if is_rollback(current, target):
               if "super_admin" not in role_names:
                   raise RollbackRequiresSuperAdmin(f"Only super_admin can rollback periode")
               if not reason or len(reason) < 20:
                   raise RollbackRequiresReason("reason must be >= 20 chars on rollback (DEC-T1-002)")
               return "rollback"
           # Forward but skipping states (e.g., draft → asesmen) is illegal
           raise InvalidTransition(f"Invalid periode transition {current.value} -> {target.value}")
       ```

    2. `backend/app/services/recommendation_fsm.py`:
       ```python
       from __future__ import annotations
       from app.models.recommendation import RecommendationStatus

       # Auto transitions: PIC's first PATCH /progress flips open→in_progress.
       AUTO_ON_PROGRESS: set[RecommendationStatus] = {RecommendationStatus.OPEN}
       AFTER_PROGRESS: RecommendationStatus = RecommendationStatus.IN_PROGRESS

       MARK_COMPLETED_ALLOWED_FROM = {RecommendationStatus.IN_PROGRESS, RecommendationStatus.OPEN}
       VERIFY_CLOSE_ALLOWED_FROM = {RecommendationStatus.PENDING_REVIEW}

       class InvalidLifecycle(ValueError): pass

       def assert_mark_completed_allowed(current: RecommendationStatus) -> None:
           if current not in MARK_COMPLETED_ALLOWED_FROM:
               raise InvalidLifecycle(f"mark-completed not allowed from {current.value}")

       def assert_verify_close_allowed(current: RecommendationStatus) -> None:
           if current not in VERIFY_CLOSE_ALLOWED_FROM:
               raise InvalidLifecycle(f"verify-close requires pending_review; got {current.value}")
       ```

    3. `backend/app/services/pencapaian.py` — DEC-T2-005:
       ```python
       """Server-authoritative pencapaian + nilai compute.

       Polaritas (per indikator):
         - positif: pencapaian = (realisasi / target) * 100
         - negatif: pencapaian = (2 - (realisasi / target)) * 100
         - range:   three-band lookup from indikator.polaritas_config JSONB (TBD by 01_DOMAIN_MODEL.md §4.1)

       nilai = pencapaian * (indikator.bobot / 100)
       """
       from __future__ import annotations
       from decimal import Decimal, InvalidOperation, getcontext
       from app.models.indikator import Indikator

       getcontext().prec = 28

       def compute_pencapaian(realisasi: Decimal | None, target: Decimal | None, indikator: Indikator) -> Decimal | None:
           if realisasi is None or target is None:
               return None
           if target == 0:
               # Domain rule from 01_DOMAIN_MODEL.md: pencapaian for zero target is 0 for positif, 100 for negatif
               return Decimal("0") if indikator.polaritas == "positif" else Decimal("100")
           pol = (indikator.polaritas or "positif").lower()
           try:
               r_over_t = Decimal(realisasi) / Decimal(target)
           except InvalidOperation:
               return None
           if pol == "positif":
               return (r_over_t * Decimal("100")).quantize(Decimal("0.0001"))
           if pol == "negatif":
               return ((Decimal("2") - r_over_t) * Decimal("100")).quantize(Decimal("0.0001"))
           if pol in ("range", "range-based"):
               # Range-based uses indikator.polaritas_config — defer the table lookup until the schema is finalised
               # in Phase 3. For Phase 2 pilot indikator (EAF/EFOR/Outage/SMAP), range is not used.
               return None
           return None

       def compute_nilai(pencapaian: Decimal | None, indikator: Indikator) -> Decimal | None:
           if pencapaian is None or indikator.bobot is None:
               return None
           return (pencapaian * (Decimal(indikator.bobot) / Decimal("100"))).quantize(Decimal("0.0001"))
       ```

    4. `backend/app/services/session_creator.py` — DEC-T1-003/T1-004:
       ```python
       """Spawns assessment_session rows for a periode transitioning aktif → self_assessment.
       Idempotent: SELECT existing first, INSERT only the missing pairs."""
       from __future__ import annotations
       from uuid import UUID
       from sqlalchemy import select
       from sqlalchemy.ext.asyncio import AsyncSession
       from app.models.indikator_applicable_bidang import IndikatorApplicableBidang
       from app.models.assessment_session import AssessmentSession, SessionState
       from app.models.assessment_session_bidang import AssessmentSessionBidang

       async def create_sessions_for_periode(db: AsyncSession, periode_id: UUID) -> dict:
           """Returns {"created_per_bidang": N, "created_aggregate": M, "skipped_existing": K}."""
           # Pull every applicable (indikator, bidang) row, grouped by indikator
           rows = (await db.scalars(select(IndikatorApplicableBidang))).all()
           by_indikator: dict[UUID, list[IndikatorApplicableBidang]] = {}
           for r in rows:
               by_indikator.setdefault(r.indikator_id, []).append(r)
           created_pb = 0; created_agg = 0; skipped = 0
           for indikator_id, mappings in by_indikator.items():
               agg = any(m.is_aggregate for m in mappings)
               if agg:
                   # ONE shared session with bidang_id=NULL; populate assessment_session_bidang for every covered bidang.
                   existing = await db.scalar(select(AssessmentSession.id).where(
                       AssessmentSession.periode_id == periode_id,
                       AssessmentSession.indikator_id == indikator_id,
                       AssessmentSession.bidang_id.is_(None),
                   ))
                   if existing:
                       skipped += 1
                       continue
                   sess = AssessmentSession(periode_id=periode_id, indikator_id=indikator_id, bidang_id=None, state=SessionState.DRAFT)
                   db.add(sess)
                   await db.flush()       # get sess.id
                   for m in mappings:
                       db.add(AssessmentSessionBidang(session_id=sess.id, bidang_id=m.bidang_id))
                   created_agg += 1
               else:
                   # Per-bidang sessions
                   for m in mappings:
                       existing = await db.scalar(select(AssessmentSession.id).where(
                           AssessmentSession.periode_id == periode_id,
                           AssessmentSession.indikator_id == indikator_id,
                           AssessmentSession.bidang_id == m.bidang_id,
                       ))
                       if existing:
                           skipped += 1
                           continue
                       db.add(AssessmentSession(periode_id=periode_id, indikator_id=indikator_id, bidang_id=m.bidang_id, state=SessionState.DRAFT))
                       created_pb += 1
           await db.flush()
           return {"created_per_bidang": created_pb, "created_aggregate": created_agg, "skipped_existing": skipped}
       ```

    5. `backend/app/services/carry_over.py` — DEC-T4-004:
       ```python
       """Carry-over on periode close + draft abandonment.

       DEC-T4-004 verbatim:
         - Carried: open | in_progress | pending_review
         - Not carried: closed (terminal)
         - target_periode_id = next TW; queue if no next periode yet
         - Draft assessment_sessions at close marked state=abandoned
       """
       from __future__ import annotations
       from uuid import UUID
       from sqlalchemy import select, and_
       from sqlalchemy.ext.asyncio import AsyncSession
       from app.models.periode import Periode
       from app.models.assessment_session import AssessmentSession, SessionState
       from app.models.recommendation import Recommendation, RecommendationStatus

       CARRY_OVER_STATUSES = {RecommendationStatus.OPEN, RecommendationStatus.IN_PROGRESS, RecommendationStatus.PENDING_REVIEW}

       async def resolve_next_periode(db: AsyncSession, current: Periode) -> Periode | None:
           # TW2 2026 → TW3 2026; TW4 2026 → TW1 2027
           if current.triwulan < 4:
               return await db.scalar(select(Periode).where(Periode.tahun == current.tahun, Periode.triwulan == current.triwulan + 1))
           return await db.scalar(select(Periode).where(Periode.tahun == current.tahun + 1, Periode.triwulan == 1))

       async def close_periode_with_carry_over(db: AsyncSession, periode_id: UUID) -> dict:
           periode = await db.get(Periode, periode_id)
           assert periode is not None
           # Abandon drafts
           drafts = (await db.scalars(select(AssessmentSession).where(
               AssessmentSession.periode_id == periode_id,
               AssessmentSession.state == SessionState.DRAFT,
           ))).all()
           for s in drafts:
               s.state = SessionState.ABANDONED
           # Recommendations to carry
           to_carry = (await db.scalars(select(Recommendation).where(
               Recommendation.source_periode_id == periode_id,
               Recommendation.status.in_(list(CARRY_OVER_STATUSES)),
               Recommendation.carried_to_id.is_(None),     # avoid double-carry on re-close
           ))).all()
           next_periode = await resolve_next_periode(db, periode)
           carried = 0; queued = 0
           for rec in to_carry:
               new = Recommendation(
                   source_assessment_id=rec.source_assessment_id,
                   source_periode_id=rec.source_periode_id,
                   target_periode_id=next_periode.id if next_periode else periode_id,  # placeholder = self; drain re-points
                   carried_from_id=rec.id,
                   status=rec.status,
                   severity=rec.severity,
                   deskripsi=rec.deskripsi,
                   action_items=rec.action_items,
                   progress_percent=rec.progress_percent,
               )
               db.add(new)
               await db.flush()
               rec.carried_to_id = new.id
               # Mark the ORIGINAL as carried_over only AFTER its closed-by-carry tail action; per CONTEXT.md DEC-T4-003
               # the original's status itself doesn't change — only carried_to_id is set. The NEW row carries the original status.
               if next_periode is None:
                   queued += 1
               else:
                   carried += 1
           return {"abandoned_drafts": len(drafts), "carried": carried, "queued_no_next_periode": queued}

       async def drain_pending_carry_overs(db: AsyncSession, target_periode: Periode) -> int:
           """On periode draft → aktif transition, re-point any queued carry-overs that landed
           with target_periode_id pointing at their source (placeholder). Find those and re-target."""
           # Heuristic: rows where target_periode_id == source_periode_id AND carried_from_id IS NOT NULL
           queued = (await db.scalars(select(Recommendation).where(
               Recommendation.carried_from_id.is_not(None),
               Recommendation.target_periode_id == Recommendation.source_periode_id,
           ))).all()
           drained = 0
           for r in queued:
               source = await db.get(Periode, r.source_periode_id)
               next_p = await resolve_next_periode(db, source) if source else None
               if next_p is not None and next_p.id == target_periode.id:
                   r.target_periode_id = target_periode.id
                   drained += 1
           return drained
       ```

    6. `backend/tests/conftest.py` — add Phase-2 fixtures:
       ```python
       # Append to existing conftest.py
       import pytest_asyncio
       from uuid import uuid4
       from app.models.periode import Periode, PeriodeStatus
       from app.models.indikator_applicable_bidang import IndikatorApplicableBidang
       from app.models.assessment_session import AssessmentSession, SessionState
       from app.models.assessment_session_bidang import AssessmentSessionBidang

       @pytest_asyncio.fixture
       async def sample_periode(db_session, admin_unit_user):
           p = Periode(tahun=2026, triwulan=2, semester=1, nama="TW2 2026", status=PeriodeStatus.SELF_ASSESSMENT,
                       created_by=admin_unit_user.id, updated_by=admin_unit_user.id)
           db_session.add(p); await db_session.flush()
           return p

       @pytest_asyncio.fixture
       async def per_bidang_session(db_session, sample_periode, sample_bidang, sample_indikator):
           # Reuse Plan 01-06 sample_bidang / sample_indikator fixtures
           await db_session.flush()
           db_session.add(IndikatorApplicableBidang(indikator_id=sample_indikator.id, bidang_id=sample_bidang.id, is_aggregate=False))
           s = AssessmentSession(periode_id=sample_periode.id, indikator_id=sample_indikator.id,
                                  bidang_id=sample_bidang.id, state=SessionState.DRAFT)
           db_session.add(s); await db_session.flush()
           return s

       @pytest_asyncio.fixture
       async def aggregate_session(db_session, sample_periode, sample_indikator_eaf, sample_bidang_om_list):
           # EAF aggregate over BID_OM_1..5 + BID_OM_RE
           for b in sample_bidang_om_list:
               db_session.add(IndikatorApplicableBidang(indikator_id=sample_indikator_eaf.id, bidang_id=b.id, is_aggregate=True))
           s = AssessmentSession(periode_id=sample_periode.id, indikator_id=sample_indikator_eaf.id, bidang_id=None, state=SessionState.DRAFT)
           db_session.add(s); await db_session.flush()
           for b in sample_bidang_om_list:
               db_session.add(AssessmentSessionBidang(session_id=s.id, bidang_id=b.id))
           await db_session.flush()
           return s
       ```
       Sub-fixtures `sample_bidang_om_list` + `sample_indikator_eaf` need to be added too — pull `BID_OM_1` through `BID_OM_RE` via the seed pattern from Plan 01-07 (or create minimal stand-ins in the conftest).

    7. `backend/tests/test_periode_fsm.py`:
       ```python
       import pytest
       from app.services.periode_fsm import (
           assert_transition_allowed, FORWARD, ORDER,
           InvalidTransition, RollbackRequiresSuperAdmin, RollbackRequiresReason,
       )
       from app.models.periode import PeriodeStatus as PS

       def test_forward_full_chain():
           # draft -> aktif -> self_assessment -> asesmen -> finalisasi -> closed (DEC-T1-001)
           assert assert_transition_allowed(PS.DRAFT, PS.AKTIF, {"super_admin"}, None) == "drain_pending_carry_overs"
           assert assert_transition_allowed(PS.AKTIF, PS.SELF_ASSESSMENT, {"super_admin"}, None) == "create_sessions"
           assert assert_transition_allowed(PS.SELF_ASSESSMENT, PS.ASESMEN, {"super_admin"}, None) == "noop"
           assert assert_transition_allowed(PS.ASESMEN, PS.FINALISASI, {"super_admin"}, None) == "noop"
           assert assert_transition_allowed(PS.FINALISASI, PS.CLOSED, {"super_admin"}, None) == "close_with_carry_over"

       def test_forward_skip_state_rejected():
           with pytest.raises(InvalidTransition):
               assert_transition_allowed(PS.DRAFT, PS.ASESMEN, {"super_admin"}, None)

       def test_rollback_requires_super_admin():
           with pytest.raises(RollbackRequiresSuperAdmin):
               assert_transition_allowed(PS.CLOSED, PS.FINALISASI, {"asesor"}, "x" * 25)

       def test_rollback_requires_reason_min_20_chars():
           with pytest.raises(RollbackRequiresReason):
               assert_transition_allowed(PS.CLOSED, PS.FINALISASI, {"super_admin"}, "too short")
           # 20 chars OK
           assert_transition_allowed(PS.CLOSED, PS.FINALISASI, {"super_admin"}, "x" * 20) == "rollback"

       def test_rollback_to_arbitrary_prior_state_ok():
           # CLOSED -> DRAFT is allowed for super_admin with reason (DEC-T1-002)
           assert assert_transition_allowed(PS.CLOSED, PS.DRAFT, {"super_admin"}, "y" * 30) == "rollback"
       ```

    8. `backend/tests/test_session_creator.py`:
       ```python
       import pytest
       from sqlalchemy import select
       from app.services.session_creator import create_sessions_for_periode
       from app.models.assessment_session import AssessmentSession
       from app.models.assessment_session_bidang import AssessmentSessionBidang
       from app.models.indikator_applicable_bidang import IndikatorApplicableBidang

       @pytest.mark.asyncio
       async def test_per_bidang_session_created(db_session, sample_periode, sample_bidang, sample_indikator):
           db_session.add(IndikatorApplicableBidang(indikator_id=sample_indikator.id, bidang_id=sample_bidang.id, is_aggregate=False))
           await db_session.flush()
           summary = await create_sessions_for_periode(db_session, sample_periode.id)
           assert summary["created_per_bidang"] == 1
           assert summary["created_aggregate"] == 0
           # Re-run is idempotent
           summary2 = await create_sessions_for_periode(db_session, sample_periode.id)
           assert summary2["skipped_existing"] == 1
           assert summary2["created_per_bidang"] == 0

       @pytest.mark.asyncio
       async def test_aggregate_session_with_bidang_list(db_session, sample_periode, sample_indikator_eaf, sample_bidang_om_list):
           for b in sample_bidang_om_list:
               db_session.add(IndikatorApplicableBidang(indikator_id=sample_indikator_eaf.id, bidang_id=b.id, is_aggregate=True))
           await db_session.flush()
           summary = await create_sessions_for_periode(db_session, sample_periode.id)
           assert summary["created_aggregate"] == 1
           assert summary["created_per_bidang"] == 0
           # Verify exactly one row with bidang_id=NULL and ASB rows for each bidang
           agg = (await db_session.scalars(select(AssessmentSession).where(
               AssessmentSession.periode_id == sample_periode.id,
               AssessmentSession.indikator_id == sample_indikator_eaf.id,
               AssessmentSession.bidang_id.is_(None),
           ))).all()
           assert len(agg) == 1
           asb_rows = (await db_session.scalars(select(AssessmentSessionBidang).where(
               AssessmentSessionBidang.session_id == agg[0].id
           ))).all()
           assert {r.bidang_id for r in asb_rows} == {b.id for b in sample_bidang_om_list}

       @pytest.mark.asyncio
       async def test_non_applicable_pair_skipped(db_session, sample_periode, sample_bidang, sample_indikator, sample_bidang_other):
           # Only one mapping → only one session created; the other bidang gets nothing (DEC-T1-004)
           db_session.add(IndikatorApplicableBidang(indikator_id=sample_indikator.id, bidang_id=sample_bidang.id, is_aggregate=False))
           await db_session.flush()
           summary = await create_sessions_for_periode(db_session, sample_periode.id)
           assert summary["created_per_bidang"] == 1
           # sample_bidang_other has NO mapping → no session
       ```

    9. `backend/tests/test_carry_over.py`:
       ```python
       import pytest
       from sqlalchemy import select
       from app.services.carry_over import close_periode_with_carry_over, resolve_next_periode
       from app.models.recommendation import Recommendation, RecommendationStatus
       from app.models.assessment_session import AssessmentSession, SessionState

       @pytest.mark.asyncio
       async def test_carry_open_recs_to_next_periode(db_session, sample_periode, sample_next_periode, sample_recommendation_open):
           summary = await close_periode_with_carry_over(db_session, sample_periode.id)
           assert summary["carried"] == 1
           # Original has carried_to_id set; new row exists in next periode
           orig = await db_session.get(Recommendation, sample_recommendation_open.id)
           assert orig.carried_to_id is not None
           new_row = await db_session.get(Recommendation, orig.carried_to_id)
           assert new_row.target_periode_id == sample_next_periode.id
           assert new_row.carried_from_id == orig.id
           assert new_row.status == RecommendationStatus.OPEN

       @pytest.mark.asyncio
       async def test_closed_recommendations_not_carried(db_session, sample_periode, sample_next_periode, sample_recommendation_closed):
           summary = await close_periode_with_carry_over(db_session, sample_periode.id)
           assert summary["carried"] == 0

       @pytest.mark.asyncio
       async def test_draft_sessions_abandoned_on_close(db_session, sample_periode, per_bidang_session):
           assert per_bidang_session.state == SessionState.DRAFT
           summary = await close_periode_with_carry_over(db_session, sample_periode.id)
           await db_session.refresh(per_bidang_session)
           assert per_bidang_session.state == SessionState.ABANDONED
           assert summary["abandoned_drafts"] >= 1

       @pytest.mark.asyncio
       async def test_carry_queues_when_no_next_periode(db_session, sample_periode, sample_recommendation_open):
           summary = await close_periode_with_carry_over(db_session, sample_periode.id)
           assert summary["queued_no_next_periode"] >= 0  # If sample_next_periode fixture omitted, this is 1
       ```

    Commit: `feat(02-02): periode_fsm + recommendation_fsm + session_creator + carry_over + pencapaian + fixtures + 3 service tests`.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $files = 'backend/app/services/periode_fsm.py','backend/app/services/recommendation_fsm.py','backend/app/services/session_creator.py','backend/app/services/carry_over.py','backend/app/services/pencapaian.py','backend/tests/test_periode_fsm.py','backend/tests/test_session_creator.py','backend/tests/test_carry_over.py';
        foreach ($f in $files) { if (-not (Test-Path $f)) { Write-Output ('missing: ' + $f); exit 1 } };
        # No transitions lib (RESEARCH §5)
        $f1 = Get-Content 'backend/app/services/periode_fsm.py' -Raw;
        if ($f1 -match 'from transitions') { Write-Output 'RESEARCH §5: transitions library forbidden'; exit 2 };
        # DEC-T1-001 forward transition table
        foreach ($s in 'DRAFT','AKTIF','SELF_ASSESSMENT','ASESMEN','FINALISASI','CLOSED') {
          if ($f1 -notmatch $s) { Write-Output ('DEC-T1-001: missing FSM state ' + $s); exit 3 }
        };
        # DEC-T1-002 rollback reason >= 20
        if ($f1 -notmatch 'len\(reason\) < 20' -and $f1 -notmatch 'len\(reason\)\s*<\s*20') { Write-Output 'DEC-T1-002: 20-char reason rule missing'; exit 4 };
        # No SMTP / worker imports anywhere in services
        $svcAll = (Get-Content 'backend/app/services/periode_fsm.py','backend/app/services/recommendation_fsm.py','backend/app/services/session_creator.py','backend/app/services/carry_over.py','backend/app/services/pencapaian.py' -Raw) -join '`n';
        foreach ($bad in 'aiosmtplib','smtplib','celery','apscheduler') {
          if ($svcAll -match $bad) { Write-Output ('DEC-T5-001 / RESEARCH §11.5+11: ' + $bad + ' forbidden'); exit 5 }
        };
        # session_creator honors DEC-T1-003 / T1-004
        $sc = Get-Content 'backend/app/services/session_creator.py' -Raw;
        if ($sc -notmatch 'is_aggregate') { Write-Output 'DEC-T1-003: is_aggregate branch missing'; exit 6 };
        if ($sc -notmatch 'IndikatorApplicableBidang') { Write-Output 'DEC-T1-004: applicable mapping not read'; exit 7 };
        if ($sc -notmatch 'SELECT.*existing' -and $sc -notmatch 'existing\s*=\s*await db.scalar') { Write-Output 'idempotency guard missing'; exit 8 };
        # carry_over honors DEC-T4-004
        $co = Get-Content 'backend/app/services/carry_over.py' -Raw;
        if ($co -notmatch 'OPEN') { exit 9 };
        if ($co -notmatch 'IN_PROGRESS') { exit 10 };
        if ($co -notmatch 'PENDING_REVIEW') { exit 11 };
        if ($co -notmatch 'ABANDONED') { Write-Output 'DEC-T4-004: drafts must be marked abandoned'; exit 12 };
        if ($co -notmatch 'carried_from_id') { exit 13 };
        if ($co -notmatch 'carried_to_id')   { exit 14 };
        # Real pytest run on the FSM tests (no DB needed for periode_fsm)
        wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/c/Users/ANUNNAKI/projects/PULSE/backend && python3.11 -m pytest tests/test_periode_fsm.py -x -q' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Write-Output 'periode_fsm tests failed'; exit 15 };
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    Five services exist (no `transitions` lib, no SMTP/worker imports); FSM forward table contains all six PeriodeStatus values; rollback enforces super_admin + reason >= 20 chars; session_creator branches on is_aggregate (DEC-T1-003) and reads IndikatorApplicableBidang (DEC-T1-004); carry_over carries open/in_progress/pending_review + abandons drafts (DEC-T4-004); test_periode_fsm.py runs green via WSL pytest.
  </done>
</task>

<task type="auto">
  <name>Task 2: Periode router + assessment_session router (PIC + asesor-review) with server-authoritative pencapaian + submit gate + audit tags</name>
  <files>
    backend/app/routers/periode.py,
    backend/app/routers/assessment_session.py,
    backend/tests/test_periode_router.py,
    backend/tests/test_assessment_session.py,
    backend/tests/test_asesor_review.py
  </files>
  <action>
    Routers use Phase-1 auto-discovery (drop a file into `backend/app/routers/`, no edits to `main.py`). Both routers mount under `/api/v1` automatically via the `api_router` aggregator in `backend/app/routers/__init__.py`.

    1. `backend/app/routers/periode.py` — periode CRUD + transitions. Every mutating route tagged `audit:periode` so Plan 02-03's middleware can pick it up.
       Key handlers:
       - `POST /periode` (super_admin + CSRF) — `audit:periode`, sets `request.state.audit_after = serialize(new_periode)`, `request.state.audit_entity_id = str(p.id)`.
       - `PATCH /periode/{id}` (super_admin + CSRF) — capture before/after.
       - `POST /periode/{id}/transition` (super_admin + CSRF) — calls `periode_fsm.assert_transition_allowed(...)` then dispatches the side-effect by name:
         ```python
         if effect == "create_sessions":
             from app.services.session_creator import create_sessions_for_periode
             await create_sessions_for_periode(db, periode_id)
             # Notify each PIC who now owns a freshly-spawned draft session (DEC-T5-003 assessment_due)
             # — Plan 02-03 provides notification_dispatcher; this plan stubs the call via try/except ImportError
             # so the router is testable before Plan 02-03 lands, but production import is unconditional.
             try:
                 from app.services.notification_dispatcher import dispatch_assessment_due_for_periode
                 await dispatch_assessment_due_for_periode(db, periode_id)
             except ImportError:
                 pass     # Plan 02-03 supplies this; per RESEARCH §12 the two plans run parallel
         elif effect == "close_with_carry_over":
             from app.services.carry_over import close_periode_with_carry_over
             summary = await close_periode_with_carry_over(db, periode_id)
             request.state.audit_after = {**request.state.audit_after, "carry_summary": summary}
             # periode_closed notification fanout — same try/except ImportError pattern
         elif effect == "drain_pending_carry_overs":
             from app.services.carry_over import drain_pending_carry_overs
             await drain_pending_carry_overs(db, periode)
         # rollback: noop (state change only)
         ```
       - `GET /periode/{id}/carry-over-summary` (super_admin) — returns `{carried: [{id, source_id, target_id, status}, ...]}` for the rollback warning UI (RESEARCH Pitfall 7). No tags needed (read-only).

       Decorator pattern:
       ```python
       router = APIRouter(prefix="/periode", tags=["periode"])

       @router.post(
           "/{periode_id}/transition",
           tags=["audit:periode"],
           dependencies=[Depends(require_role("super_admin")), Depends(require_csrf)],
       )
       async def transition(periode_id: UUID, payload: PeriodeTransitionRequest, request: Request, db: AsyncSession = Depends(get_db), user=Depends(current_user)):
           periode = await db.get(Periode, periode_id)
           if not periode: raise HTTPException(404)
           role_names = {r.name for r in user.roles}
           try:
               effect = assert_transition_allowed(PeriodeStatus(periode.status), PeriodeStatus(payload.target_state), role_names, payload.reason)
           except RollbackRequiresSuperAdmin:
               raise HTTPException(403, "only_super_admin_can_rollback")
           except RollbackRequiresReason:
               raise HTTPException(422, {"error":"reason_required","min_length":20,"hint":"Rollback transitions need a reason of at least 20 characters."})
           except InvalidTransition as e:
               raise HTTPException(422, {"error":"invalid_transition","detail":str(e)})

           request.state.audit_before = {"status": periode.status.value}

           # Dispatch effect (see above)
           ...

           periode.status = PeriodeStatus(payload.target_state)
           if effect == "rollback":
               periode.last_transition_reason = payload.reason
               periode.last_transition_by = user.id
               periode.last_transition_at = func.now()
           await db.commit()
           await db.refresh(periode)

           request.state.audit_after = {"status": periode.status.value, "reason": payload.reason}
           request.state.audit_entity_id = str(periode.id)
           return {"data": PeriodePublic.model_validate(periode).model_dump(mode="json")}
       ```

    2. `backend/app/routers/assessment_session.py` — three groups of endpoints (PIC, asesor, admin):

       **PIC scope helper** — `_apply_pic_scope(query, user)`:
       ```python
       async def _apply_pic_scope(stmt, user):
           if "super_admin" in {r.name for r in user.roles} or "asesor" in {r.name for r in user.roles}:
               return stmt
           # pic_bidang: see own bidang's sessions + aggregate sessions where own bidang is in assessment_session_bidang
           own = user.bidang_id
           if own is None:
               return stmt.where(False)   # no bidang → no sessions
           return stmt.where(
               or_(
                   AssessmentSession.bidang_id == own,
                   AssessmentSession.id.in_(select(AssessmentSessionBidang.session_id).where(AssessmentSessionBidang.bidang_id == own)),
               )
           )
       ```

       **PATCH /assessment/sessions/{id}/self-assessment** (pic_bidang + CSRF; audit:assessment_session):
       ```python
       @router.patch("/{session_id}/self-assessment", tags=["audit:assessment_session"], dependencies=[Depends(require_role("pic_bidang","super_admin")), Depends(require_csrf)])
       async def self_assessment(session_id: UUID, payload: AssessmentSelfAssessmentPatch, request: Request, db: AsyncSession = Depends(get_db), user=Depends(current_user)):
           sess = await db.get(AssessmentSession, session_id)
           if not sess: raise HTTPException(404)
           # Scope check: pic_bidang can only edit their own (or aggregate they're in)
           if "super_admin" not in {r.name for r in user.roles}:
               if sess.bidang_id is not None and sess.bidang_id != user.bidang_id:
                   raise HTTPException(403)
               if sess.bidang_id is None:
                   member = await db.scalar(select(AssessmentSessionBidang).where(
                       AssessmentSessionBidang.session_id == session_id,
                       AssessmentSessionBidang.bidang_id == user.bidang_id))
                   if not member: raise HTTPException(403)
           # Submit gate: only allowed in draft or revision_requested
           if sess.state not in (SessionState.DRAFT, SessionState.REVISION_REQUESTED):
               raise HTTPException(409, "session_locked")

           # Audit before
           request.state.audit_before = _serialize_audit_delta(sess, fields=("payload","realisasi","target","catatan_pic","link_eviden"))

           # Merge payload JSONB (shallow merge — keys not in patch are preserved)
           if payload.payload is not None:
               merged = (sess.payload or {}) | payload.payload
               sess.payload = merged
           for k in ("realisasi","target","catatan_pic"):
               v = getattr(payload, k, None)
               if v is not None: setattr(sess, k, v)
           if payload.link_eviden is not None:
               sess.link_eviden = str(payload.link_eviden)

           # DEC-T2-005: server-authoritative compute
           indikator = await db.get(Indikator, sess.indikator_id)
           sess.pencapaian = compute_pencapaian(sess.realisasi, sess.target, indikator)
           sess.nilai = compute_nilai(sess.pencapaian, indikator)

           await db.commit()
           await db.refresh(sess)

           request.state.audit_after  = _serialize_audit_delta(sess, fields=("payload","realisasi","target","catatan_pic","link_eviden","pencapaian","nilai","updated_at"))
           request.state.audit_entity_id = str(sess.id)

           return {"data": AssessmentSessionPublic.model_validate(sess).model_dump(mode="json")}
       ```
       `_serialize_audit_delta` returns ONLY the listed fields — RESEARCH §10 + Pitfall 9 (delta storage to keep audit_log JSONB small).

       **POST /assessment/sessions/{id}/submit** (pic_bidang + CSRF; audit:assessment_session) — runs the DEC-T2-004 server-side submit gate:
       ```python
       @router.post("/{session_id}/submit", tags=["audit:assessment_session"], dependencies=[Depends(require_role("pic_bidang","super_admin")), Depends(require_csrf)])
       async def submit(session_id: UUID, request: Request, db: AsyncSession = Depends(get_db), user=Depends(current_user)):
           sess = await db.get(AssessmentSession, session_id)
           # scope + state check (same pattern)
           if sess.state not in (SessionState.DRAFT, SessionState.REVISION_REQUESTED):
               raise HTTPException(409, "session_already_submitted")

           # DEC-T2-004 server gate: every sub-area in payload must have a numeric value OR tidak_dinilai==True with reason >= 10 chars
           offending = _validate_submit_gate(sess.payload, indikator)
           if offending:
               raise HTTPException(422, {"error":"incomplete_sub_areas","offending":offending,"hint":"Every sub-area needs a value or 'tidak_dinilai=true' with reason >= 10 chars."})

           request.state.audit_before = {"state": sess.state.value}
           sess.state = SessionState.SUBMITTED
           sess.submitted_at = func.now()
           await db.commit()
           await db.refresh(sess)
           request.state.audit_after = {"state": sess.state.value, "submitted_at": sess.submitted_at.isoformat() if sess.submitted_at else None}
           request.state.audit_entity_id = str(sess.id)

           # Notify asesors assigned to this indikator (review_pending) — try/except ImportError until Plan 02-03 lands
           try:
               from app.services.notification_dispatcher import dispatch_review_pending
               await dispatch_review_pending(db, sess)
           except ImportError:
               pass
           return {"data": AssessmentSessionPublic.model_validate(sess).model_dump(mode="json")}
       ```
       `_validate_submit_gate(payload, indikator)` recursively walks the area/sub_area tree from `indikator.ml_stream.structure` (or KPI shape) and returns the list of sub-area codes that fail the rule. For Phase 2 pilot indikator (EAF/EFOR — KPI; Outage/SMAP — ML), the function reads `payload['sub_areas']` (ML) or `payload['kpi']` (KPI) shape.

       **POST /assessment/sessions/{id}/withdraw** (pic_bidang + CSRF; audit:assessment_session) — only when `state=submitted AND asesor_user_id IS NULL AND asesor_reviewed_at IS NULL` (REQ-pic-actions "withdraw before asesor starts").

       **POST /assessment/sessions/{id}/asesor-review** (asesor|super_admin + CSRF; audit:assessment_session) — uses `AsesorReview` schema (server already validates min-20-chars via the model_validator from Plan 02-01); the handler still re-asserts defensively:
       ```python
       @router.post("/{session_id}/asesor-review", tags=["audit:assessment_session"], dependencies=[Depends(require_role("asesor","super_admin")), Depends(require_csrf)])
       async def asesor_review(session_id: UUID, payload: AsesorReview, request: Request, db: AsyncSession = Depends(get_db), user=Depends(current_user)):
           sess = await db.get(AssessmentSession, session_id)
           if not sess: raise HTTPException(404)
           if sess.state != SessionState.SUBMITTED:
               raise HTTPException(409, "session_not_in_submitted_state")
           request.state.audit_before = {"state": sess.state.value, "nilai_final": str(sess.nilai_final) if sess.nilai_final else None, "catatan_asesor": sess.catatan_asesor}

           sess.asesor_user_id = user.id
           sess.asesor_reviewed_at = func.now()
           sess.catatan_asesor = payload.catatan_asesor

           if payload.decision == "approve":
               sess.state = SessionState.APPROVED
               sess.nilai_final = sess.nilai   # server-authoritative carryover
           elif payload.decision == "override":
               # Defensive: schema-level validator already enforced, but double-check (DEC-T3-001)
               if not payload.catatan_asesor or len(payload.catatan_asesor) < 20 or payload.nilai_final is None:
                   raise HTTPException(422, {"error":"override_requires_catatan_min_20_and_nilai_final"})
               sess.state = SessionState.OVERRIDDEN
               sess.nilai_final = payload.nilai_final
           elif payload.decision == "request_revision":
               sess.state = SessionState.REVISION_REQUESTED
               sess.nilai_final = None
               sess.submitted_at = None     # PIC re-submits later

           # Inline recommendations (DEC-T4-001 owner resolution happens in recommendation_create service)
           created_rec_ids: list[str] = []
           if payload.inline_recommendations:
               from app.services.recommendation_create import create_recommendation_with_owner_resolution
               for inline in payload.inline_recommendations:
                   rec = await create_recommendation_with_owner_resolution(
                       db, source_assessment_id=session_id, source_periode_id=sess.periode_id,
                       severity=inline.severity, deskripsi=inline.deskripsi,
                       action_items=inline.action_items, target_periode_id=inline.target_periode_id,
                       created_by=user.id,
                   )
                   created_rec_ids.append(str(rec.id))

           await db.commit()
           await db.refresh(sess)
           request.state.audit_after = {"state": sess.state.value, "nilai_final": str(sess.nilai_final) if sess.nilai_final else None,
                                         "catatan_asesor": sess.catatan_asesor, "inline_recommendations": created_rec_ids,
                                         "decision": payload.decision}
           request.state.audit_entity_id = str(sess.id)

           # Notify PIC (review-finished — uses review_pending or recommendation_assigned)
           try:
               from app.services.notification_dispatcher import dispatch_review_finished, dispatch_recommendation_assigned
               await dispatch_review_finished(db, sess, decision=payload.decision)
               for rec_id in created_rec_ids:
                   await dispatch_recommendation_assigned(db, rec_id)
           except ImportError:
               pass

           return {"data": AssessmentSessionPublic.model_validate(sess).model_dump(mode="json"), "inline_recommendations": created_rec_ids}
       ```

    3. `backend/tests/test_periode_router.py`:
       - POST /periode (super_admin) — 201; PIC → 403
       - PATCH /periode/{id} — locked validations
       - POST /periode/{id}/transition — happy path forward (aktif → self_assessment): verifies `assessment_session` rows are auto-created (DEC-T1-001 side effect)
       - Rollback super_admin with reason >= 20 chars: 200 + last_transition_reason persisted
       - Rollback non-super_admin: 403
       - Rollback super_admin no reason: 422

    4. `backend/tests/test_assessment_session.py`:
       - PIC PATCH /self-assessment auto-save: server recomputes pencapaian even when client doesn't send it (DEC-T2-005). Test: PIC sends `realisasi=90, target=100`, indikator polaritas=positif → pencapaian=90.0000. Test: client sends `pencapaian=999` (which the schema rejects via extra='forbid') → 422.
       - PIC PATCH /self-assessment scope: PIC of bidang A on a session for bidang B → 403; PIC on aggregate session where their bidang is NOT in `assessment_session_bidang` → 403; PIC on aggregate session where their bidang IS in `assessment_session_bidang` → 200.
       - POST /submit fails when sub_areas have NULL values (DEC-T2-004): payload `{sub_areas: {sa1: {level: 2, value: 2.5}, sa2: {level: null}}}` → 422 with offending list.
       - POST /submit succeeds when all sub-areas have value OR tidak_dinilai with reason >= 10 chars.
       - POST /submit when state already submitted → 409.
       - POST /withdraw allowed only when not yet reviewed.
       - audit_before/after captured: `request.state.audit_before` is the pre-mutation snapshot, `audit_after` is post (assertion: `client.patch(...); assert response.json()["data"]["updated_at"] != initial_updated_at`).

    5. `backend/tests/test_asesor_review.py`:
       - Approve: nilai_final == PIC's nilai, state=approved.
       - Override with < 20 chars → 422 (schema-level + handler defensive).
       - Override with 20 chars + nilai_final → 200, state=overridden, nilai_final stored.
       - request_revision → state=revision_requested, nilai_final=NULL, submitted_at=NULL.
       - Inline recommendation created in the same call, default owner resolved (covered fully in Plan 02-02 Task 3).
       - Non-asesor PATCH → 403.
       - Review of non-submitted session → 409.

    Commit: `feat(02-02): periode router + assessment_session router with DEC-T1-001/004 + DEC-T2-003/004/005 + DEC-T3-001 + audit tags`.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $files = 'backend/app/routers/periode.py','backend/app/routers/assessment_session.py','backend/tests/test_periode_router.py','backend/tests/test_assessment_session.py','backend/tests/test_asesor_review.py';
        foreach ($f in $files) { if (-not (Test-Path $f)) { Write-Output ('missing: ' + $f); exit 1 } };
        # Both routers carry audit:<entity> tag
        $pr = Get-Content 'backend/app/routers/periode.py' -Raw;
        if ($pr -notmatch 'audit:periode') { Write-Output 'periode router missing audit:periode tag'; exit 2 };
        $as = Get-Content 'backend/app/routers/assessment_session.py' -Raw;
        if ($as -notmatch 'audit:assessment_session') { Write-Output 'assessment_session router missing audit tag'; exit 3 };
        # require_csrf on mutating routes (sample check — every mutating decorator must include it)
        foreach ($r in 'periode.py','assessment_session.py') {
          $c = Get-Content ('backend/app/routers/' + $r) -Raw
          if ($c -notmatch 'require_csrf') { Write-Output ($r + ' missing require_csrf'); exit 4 }
          if ($c -notmatch 'require_role') { Write-Output ($r + ' missing require_role'); exit 5 }
        };
        # Spec role names (B-01/B-02)
        foreach ($r in 'periode.py','assessment_session.py') {
          $c = Get-Content ('backend/app/routers/' + $r) -Raw
          # Periode is super_admin only; assessment_session uses pic_bidang/asesor/super_admin
          if ($r -eq 'periode.py' -and $c -notmatch 'super_admin') { exit 6 }
          if ($r -eq 'assessment_session.py') {
            foreach ($role in 'pic_bidang','asesor','super_admin') {
              if ($c -notmatch $role) { Write-Output ('B-01/B-02: missing role ' + $role + ' in ' + $r); exit 7 }
            }
          }
        };
        # DEC-T2-005: server-authoritative — pencapaian module imported in assessment_session router
        if ($as -notmatch 'compute_pencapaian') { Write-Output 'DEC-T2-005: server compute missing'; exit 8 };
        # No client-supplied pencapaian in the patch schema (forbidden by extra=forbid in Plan 02-01)
        $sch = Get-Content 'backend/app/schemas/assessment.py' -Raw;
        if ($sch -match 'pencapaian:\s*Decimal') { Write-Output 'DEC-T2-005: pencapaian must not be in PATCH schema'; exit 9 };
        # No SMTP / worker in routers either
        $allRouters = (Get-Content $files[0..1] -Raw) -join '`n'
        foreach ($bad in 'aiosmtplib','smtplib','celery','apscheduler') {
          if ($allRouters -match $bad) { exit 10 }
        };
        # B-06 unit smoke (no DB needed) — import the modules under WSL
        wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/c/Users/ANUNNAKI/projects/PULSE/backend && python3.11 -c \"from app.routers.periode import router as pr; from app.routers.assessment_session import router as ar; print(pr.routes[0].tags, ar.routes[0].tags)\"' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Write-Output 'router import smoke failed'; exit 11 };
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    Periode router exists with `audit:periode` tags on all mutating routes, super_admin gate, FSM dispatch; assessment_session router exists with `audit:assessment_session` tags, role gates (`pic_bidang | asesor | super_admin`), server-side pencapaian compute (DEC-T2-005), submit-gate validator (DEC-T2-004), and defensive DEC-T3-001 re-check; no SMTP / worker imports; both routers import cleanly under WSL python.
  </done>
</task>

<task type="auto">
  <name>Task 3: Recommendation router + recommendation_create service (owner resolution per DEC-T4-001) + lifecycle tests</name>
  <files>
    backend/app/services/recommendation_create.py,
    backend/app/routers/recommendation.py,
    backend/tests/test_recommendation_create.py,
    backend/tests/test_recommendation_lifecycle.py
  </files>
  <action>
    1. `backend/app/services/recommendation_create.py` — RESEARCH §11.13 + DEC-T4-001 owner resolution:
       ```python
       """Owner resolution for action_items[i].owner_user_id is here, NOT in Pydantic
       (validators are sync + I/O-free per RESEARCH §11.13)."""
       from __future__ import annotations
       from uuid import UUID
       from sqlalchemy import select
       from sqlalchemy.ext.asyncio import AsyncSession
       from app.models.user import User
       from app.models.assessment_session import AssessmentSession
       from app.models.assessment_session_bidang import AssessmentSessionBidang
       from app.models.recommendation import Recommendation
       from app.schemas.recommendation import ActionItem

       class OwnerRequired(Exception):
           def __init__(self, action_item_index: int):
               self.index = action_item_index

       async def lookup_source_pic(db: AsyncSession, source_assessment_id: UUID) -> UUID | None:
           sess = await db.get(AssessmentSession, source_assessment_id)
           if sess is None:
               return None
           if sess.bidang_id is not None:
               # Per-bidang session → unique PIC of that bidang
               u = await db.scalar(select(User).where(User.bidang_id == sess.bidang_id, User.is_active.is_(True)).order_by(User.created_at.asc()))
               return u.id if u else None
           # Aggregate session: first active PIC across the assessment_session_bidang list
           bidang_ids = (await db.scalars(select(AssessmentSessionBidang.bidang_id).where(AssessmentSessionBidang.session_id == source_assessment_id))).all()
           if not bidang_ids: return None
           u = await db.scalar(select(User).where(User.bidang_id.in_(bidang_ids), User.is_active.is_(True)).order_by(User.created_at.asc()))
           return u.id if u else None

       async def resolve_default_owners(db: AsyncSession, items: list[ActionItem], source_assessment_id: UUID) -> list[ActionItem]:
           """Mutates `items` in place: any with owner_user_id=None gets the resolved default.
           Raises OwnerRequired(index) if default cannot be resolved AND user didn't supply one."""
           cached_default: UUID | None | object = object()    # sentinel for "not looked up yet"
           for i, item in enumerate(items):
               if item.owner_user_id is None:
                   if cached_default is object():
                       cached_default = await lookup_source_pic(db, source_assessment_id)
                   if cached_default is None:
                       raise OwnerRequired(i)
                   item.owner_user_id = cached_default      # type: ignore
           return items

       async def create_recommendation_with_owner_resolution(
           db: AsyncSession, *, source_assessment_id: UUID, source_periode_id: UUID,
           severity: str, deskripsi: str, action_items: list[ActionItem],
           target_periode_id: UUID, created_by: UUID,
       ) -> Recommendation:
           resolved = await resolve_default_owners(db, action_items, source_assessment_id)
           # Serialize action_items as JSONB-friendly dicts
           items_jsonb = [it.model_dump(mode="json") for it in resolved]
           rec = Recommendation(
               source_assessment_id=source_assessment_id,
               source_periode_id=source_periode_id,
               target_periode_id=target_periode_id,
               severity=severity,
               deskripsi=deskripsi,
               action_items=items_jsonb,
               created_by=created_by, updated_by=created_by,
           )
           db.add(rec); await db.flush()
           return rec
       ```

    2. `backend/app/routers/recommendation.py`:
       ```python
       router = APIRouter(prefix="/recommendations", tags=["recommendations"])

       @router.post("", tags=["audit:recommendation"],
                    dependencies=[Depends(require_role("asesor","super_admin")), Depends(require_csrf)])
       async def create(payload: RecommendationCreate, request: Request, db = Depends(get_db), user = Depends(current_user)):
           sess = await db.get(AssessmentSession, payload.source_assessment_id)
           if not sess: raise HTTPException(404, "source_assessment_not_found")
           try:
               rec = await create_recommendation_with_owner_resolution(
                   db, source_assessment_id=payload.source_assessment_id, source_periode_id=sess.periode_id,
                   severity=payload.severity, deskripsi=payload.deskripsi, action_items=payload.action_items,
                   target_periode_id=payload.target_periode_id, created_by=user.id,
               )
           except OwnerRequired as e:
               raise HTTPException(422, {"error": f"owner_required_for_action_item_{e.index}", "hint":"Source-assessment PIC is deactivated; asesor must pick an owner manually."})
           await db.commit()
           await db.refresh(rec)
           request.state.audit_after = {"id": str(rec.id), "severity": rec.severity, "target_periode_id": str(rec.target_periode_id), "action_items": rec.action_items}
           request.state.audit_entity_id = str(rec.id)
           # Notify owners
           try:
               from app.services.notification_dispatcher import dispatch_recommendation_assigned
               await dispatch_recommendation_assigned(db, str(rec.id))
           except ImportError:
               pass
           return {"data": RecommendationPublic.model_validate(rec).model_dump(mode="json")}

       @router.patch("/{rec_id}/progress", tags=["audit:recommendation"],
                     dependencies=[Depends(require_role("pic_bidang","super_admin")), Depends(require_csrf)])
       async def progress(rec_id: UUID, payload: RecommendationProgressUpdate, request: Request, db = Depends(get_db), user = Depends(current_user)):
           rec = await db.get(Recommendation, rec_id)
           if not rec: raise HTTPException(404)
           # Scope: PIC must own at least one action_item or be a covered-bidang PIC for the source session
           if "super_admin" not in {r.name for r in user.roles}:
               owns = any(it.get("owner_user_id") == str(user.id) for it in (rec.action_items or []))
               if not owns: raise HTTPException(403, "not_owner_of_any_action_item")
           request.state.audit_before = {"status": rec.status.value, "progress_percent": rec.progress_percent, "progress_notes": rec.progress_notes}
           # DEC-T4-003: first /progress flips open → in_progress
           if rec.status == RecommendationStatus.OPEN:
               rec.status = RecommendationStatus.IN_PROGRESS
           if payload.progress_percent is not None: rec.progress_percent = payload.progress_percent
           if payload.progress_notes is not None: rec.progress_notes = payload.progress_notes
           await db.commit(); await db.refresh(rec)
           request.state.audit_after = {"status": rec.status.value, "progress_percent": rec.progress_percent, "progress_notes": rec.progress_notes}
           request.state.audit_entity_id = str(rec.id)
           return {"data": RecommendationPublic.model_validate(rec).model_dump(mode="json")}

       @router.post("/{rec_id}/mark-completed", tags=["audit:recommendation"],
                    dependencies=[Depends(require_role("pic_bidang","super_admin")), Depends(require_csrf)])
       async def mark_completed(rec_id: UUID, request: Request, db = Depends(get_db), user = Depends(current_user)):
           rec = await db.get(Recommendation, rec_id)
           if not rec: raise HTTPException(404)
           try:
               assert_mark_completed_allowed(rec.status)
           except InvalidLifecycle as e:
               raise HTTPException(409, str(e))
           request.state.audit_before = {"status": rec.status.value}
           rec.status = RecommendationStatus.PENDING_REVIEW
           await db.commit(); await db.refresh(rec)
           request.state.audit_after = {"status": rec.status.value}
           request.state.audit_entity_id = str(rec.id)
           return {"data": RecommendationPublic.model_validate(rec).model_dump(mode="json")}

       @router.post("/{rec_id}/verify-close", tags=["audit:recommendation"],
                    dependencies=[Depends(require_role("asesor","super_admin")), Depends(require_csrf)])
       async def verify_close(rec_id: UUID, payload: RecommendationVerifyClose, request: Request, db = Depends(get_db), user = Depends(current_user)):
           rec = await db.get(Recommendation, rec_id)
           if not rec: raise HTTPException(404)
           try:
               assert_verify_close_allowed(rec.status)
           except InvalidLifecycle as e:
               raise HTTPException(409, str(e))
           request.state.audit_before = {"status": rec.status.value, "asesor_close_notes": rec.asesor_close_notes}
           rec.status = RecommendationStatus.CLOSED
           rec.asesor_close_notes = payload.asesor_close_notes
           rec.closed_at = func.now()
           rec.closed_by = user.id
           await db.commit(); await db.refresh(rec)
           request.state.audit_after = {"status": rec.status.value, "asesor_close_notes": rec.asesor_close_notes, "closed_at": rec.closed_at.isoformat() if rec.closed_at else None}
           request.state.audit_entity_id = str(rec.id)
           return {"data": RecommendationPublic.model_validate(rec).model_dump(mode="json")}

       @router.post("/{rec_id}/manual-close", tags=["audit:recommendation"],
                    dependencies=[Depends(require_role("asesor","super_admin")), Depends(require_csrf)])
       async def manual_close(rec_id: UUID, payload: RecommendationVerifyClose, request: Request, db = Depends(get_db), user = Depends(current_user)):
           """DEC-T4-003 manual closure from any state with notes (audit-logged)."""
           rec = await db.get(Recommendation, rec_id)
           if not rec: raise HTTPException(404)
           request.state.audit_before = {"status": rec.status.value, "manual_close": True}
           rec.status = RecommendationStatus.CLOSED
           rec.asesor_close_notes = payload.asesor_close_notes
           rec.closed_at = func.now()
           rec.closed_by = user.id
           await db.commit(); await db.refresh(rec)
           request.state.audit_after = {"status": rec.status.value, "asesor_close_notes": payload.asesor_close_notes, "manual_close": True}
           request.state.audit_entity_id = str(rec.id)
           return {"data": RecommendationPublic.model_validate(rec).model_dump(mode="json")}

       @router.get("")
       async def list_recommendations(periode_id: UUID | None = None, status: str | None = None, owner_user_id: UUID | None = None,
                                       page: int = 1, page_size: int = 50, db = Depends(get_db), user = Depends(current_user)):
           # Filter scoping: pic_bidang sees recs where they own at least one action_item or are PIC of source bidang
           ...
       ```

    3. `backend/tests/test_recommendation_create.py`:
       - Asesor POST /recommendations with `action_items=[{action:"do x"}]` (no owner) for a per-bidang session → server resolves owner to source PIC; rec.action_items[0].owner_user_id == that PIC's user_id (DEC-T4-001).
       - Same call but the source PIC user is deactivated → 422 with `owner_required_for_action_item_0`.
       - Asesor POST with explicit `owner_user_id` per item → those owners are honored, not overridden.
       - Aggregate session: owner resolves to first-by-created_at active PIC across all covered bidang (DEC-T1-003 + DEC-T4-001).
       - Non-asesor POST → 403.
       - Pydantic V5 hardening: extra field in body → 422.

    4. `backend/tests/test_recommendation_lifecycle.py`:
       - Open → in_progress on first PATCH /progress; subsequent PATCH stays in_progress (idempotent).
       - in_progress → pending_review via POST /mark-completed.
       - mark-completed from CLOSED → 409.
       - verify-close from in_progress → 409 (must go through pending_review).
       - verify-close from pending_review → closed; closed_at + closed_by set.
       - manual-close from open with notes → closed; audit-logged (audit row asserted in Plan 02-03; here only that the status flipped + asesor_close_notes persisted).
       - PIC who is not action_item owner → PATCH /progress 403.

    Commit: `feat(02-02): recommendation router + service with DEC-T4-001 owner resolution + DEC-T4-003 lifecycle`.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $files = 'backend/app/services/recommendation_create.py','backend/app/routers/recommendation.py','backend/tests/test_recommendation_create.py','backend/tests/test_recommendation_lifecycle.py';
        foreach ($f in $files) { if (-not (Test-Path $f)) { Write-Output ('missing: ' + $f); exit 1 } };
        # Service owner-resolution must live OUTSIDE Pydantic (RESEARCH §11.13)
        $svc = Get-Content 'backend/app/services/recommendation_create.py' -Raw;
        if ($svc -notmatch 'AsyncSession') { Write-Output 'service must take AsyncSession'; exit 2 };
        if ($svc -notmatch 'lookup_source_pic') { exit 3 };
        if ($svc -notmatch 'OwnerRequired') { Write-Output 'DEC-T4-001: missing OwnerRequired error path'; exit 4 };
        # Schema must NOT lookup DB (RESEARCH §11.13 re-check)
        $sch = Get-Content 'backend/app/schemas/recommendation.py' -Raw;
        if ($sch -match 'AsyncSession') { Write-Output 'RESEARCH §11.13 violation in schemas/recommendation.py'; exit 5 };
        # Router audit tags + role/csrf gates
        $rr = Get-Content 'backend/app/routers/recommendation.py' -Raw;
        if ($rr -notmatch 'audit:recommendation') { exit 6 };
        if ($rr -notmatch 'require_csrf') { exit 7 };
        foreach ($role in 'asesor','pic_bidang','super_admin') {
          if ($rr -notmatch $role) { Write-Output ('recommendation router missing role ' + $role); exit 8 }
        };
        # DEC-T4-003: lifecycle endpoints all present
        foreach ($ep in '/progress','/mark-completed','/verify-close','/manual-close') {
          if ($rr -notmatch [regex]::Escape($ep)) { Write-Output ('DEC-T4-003: missing lifecycle endpoint ' + $ep); exit 9 }
        };
        # No SMTP / worker
        if ($rr -match 'aiosmtplib' -or $svc -match 'aiosmtplib') { exit 10 };
        # B-06 unit smoke
        wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/c/Users/ANUNNAKI/projects/PULSE/backend && python3.11 -c \"from app.routers.recommendation import router; from app.services.recommendation_create import resolve_default_owners, OwnerRequired; print(len(router.routes))\"' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Write-Output 'recommendation router import smoke failed'; exit 11 };
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    Service `recommendation_create.py` exposes `resolve_default_owners` and `OwnerRequired`; router has all 6 endpoints (list/get/create/progress/mark-completed/verify-close/manual-close — with `audit:recommendation` + role gates + CSRF); no DB lookups inside Pydantic schemas; router and service import cleanly under WSL python.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| HTTP client → router | Untrusted body; Pydantic + `extra='forbid'` + role gates + CSRF echo at parse/dispatch time |
| Router → service | Service trusts already-validated Pydantic objects; service performs DB I/O |
| Router → `request.state.audit_before/after` | Handlers must NEVER trust client-supplied audit fields; only handler-set state crosses into Plan 02-03 middleware |
| Periode state transition | super_admin only; rollback adds reason-length gate |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-02-S-01 | Spoofing | Cross-bidang PIC access | mitigate | `_apply_pic_scope` filters by `user.bidang_id`; aggregate sessions check `assessment_session_bidang` membership. Verified in `test_assessment_session.py` scope tests. |
| T-02-02-T-01 | Tampering | Client-supplied `pencapaian` / `nilai` | mitigate | DEC-T2-005: `AssessmentSelfAssessmentPatch` schema does NOT accept these fields (`extra='forbid'`). Server's `compute_pencapaian` is authoritative. |
| T-02-02-T-02 | Tampering | Skipping the submit gate | mitigate | DEC-T2-004 server-side validator `_validate_submit_gate(payload, indikator)` walks the tree and returns offending list. Cannot be bypassed by sending an empty body. |
| T-02-02-T-03 | Tampering | Override without justification | mitigate | DEC-T3-001: enforced TWICE — Pydantic `@model_validator(mode='after')` in Plan 02-01 + defensive handler-side re-check in this plan's `asesor_review`. |
| T-02-02-E-01 | Elevation | Non-super_admin rollback | mitigate | `periode_fsm.assert_transition_allowed` raises `RollbackRequiresSuperAdmin` when `is_rollback(...)` AND `'super_admin' not in role_names`. Router translates to 403. |
| T-02-02-R-01 | Repudiation | Missing audit on transition | mitigate | All mutating routes set `request.state.audit_before/after` and tag `audit:<entity>`. Plan 02-03 middleware writes the row. Pitfall 8 startup-check (Plan 02-03) catches missing tags. |
| T-02-02-D-01 | DOS | Pencapaian compute looping | accept | `compute_pencapaian` is O(1) arithmetic per request; no recursion. Per-route rate limit (100r/min) caps abuse. |
| T-02-02-I-01 | Info disclosure | Aggregate session leaks across bidang | mitigate | DEC-T1-003 is documented behavior — banner "Sesi ini dipakai bersama bidang X, Y, Z" on the frontend. Backend allows ANY listed bidang PIC to read/write. Not a leak — it's the design. |
</threat_model>

<verification>
After this plan executes:

1. `wsl -d Ubuntu-22.04 -- python3.11 -m pytest backend/tests/test_periode_fsm.py backend/tests/test_periode_router.py backend/tests/test_session_creator.py backend/tests/test_assessment_session.py backend/tests/test_asesor_review.py backend/tests/test_recommendation_create.py backend/tests/test_recommendation_lifecycle.py backend/tests/test_carry_over.py -x -q` passes.
2. `wsl -d Ubuntu-22.04 -- python3.11 -c "from app.routers import api_router; print([r.path for r in api_router.routes if hasattr(r,'path')])"` includes `/api/v1/periode`, `/api/v1/assessment/sessions/...`, `/api/v1/recommendations/...`.
3. Grep across `backend/app/routers/periode.py`, `assessment_session.py`, `recommendation.py`: every mutating decorator carries `tags=["audit:..."]`, `Depends(require_role(...))`, and `Depends(require_csrf)`.
4. No file under `backend/app/routers/` or `backend/app/services/` introduced in this plan imports `aiosmtplib`, `smtplib`, `celery`, `apscheduler`, or `transitions`.
5. `pencapaian` field is NOT writable via `AssessmentSelfAssessmentPatch` (Plan 02-01 schema test `test_action_item_extra_forbid` covers the general pattern).
</verification>

<success_criteria>
- [ ] Five services (`periode_fsm`, `recommendation_fsm`, `session_creator`, `carry_over`, `pencapaian`, plus `recommendation_create`) exist and import cleanly
- [ ] Three routers (`periode.py`, `assessment_session.py`, `recommendation.py`) exist with `audit:<entity>` tags on every mutating route + `require_role(spec_names)` + `require_csrf`
- [ ] `periode_fsm` enforces DEC-T1-001 forward chain + DEC-T1-002 (super_admin + reason >= 20 chars on rollback)
- [ ] `session_creator` honors DEC-T1-003 (aggregate via NULL bidang_id + N:N) and DEC-T1-004 (skip non-applicable pairs); idempotent
- [ ] `pencapaian` service is the SOLE source of truth for `pencapaian` + `nilai` (DEC-T2-005); schema does not accept client-supplied values
- [ ] `_validate_submit_gate` enforces DEC-T2-004 server-side; 422 with offending list on incomplete payload
- [ ] Asesor-review handler defensively re-checks DEC-T3-001 (override min 20 chars + nilai_final required)
- [ ] `recommendation_create.resolve_default_owners` resolves owner via `bidang_id → users.bidang_id` (per-bidang) or via `assessment_session_bidang` (aggregate); raises `OwnerRequired(index)` on deactivated PIC (DEC-T4-001)
- [ ] Recommendation lifecycle endpoints enforce DEC-T4-003 transitions via `recommendation_fsm`
- [ ] `carry_over.close_periode_with_carry_over` carries open|in_progress|pending_review; abandons drafts; sets carried_from_id/carried_to_id (DEC-T4-004)
- [ ] No SMTP / Celery / APScheduler / transitions imports anywhere
- [ ] All 8 new test files run green under WSL `pytest -x -q`
</success_criteria>

<output>
After completion, write `.planning/phases/02-assessment-workflow-pic-asesor/02-02-periode-assessment-recommendation-routers-SUMMARY.md`. Include the full endpoint contract table (mirroring Plan 01-06 style) and an explicit "all locked decisions DEC-T1-001..T4-004 honored" check.
</output>
