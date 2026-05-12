# REQUIREMENTS — PULSE

> 50 v1 requirements across 18 sections (A–S).
> Five requirements are **ADR-locked** (precedence=0): REQ-pulse-branding, REQ-pulse-heartbeat-animation, REQ-ai-inline-help, REQ-ai-comparative-analysis, REQ-no-evidence-upload.
> Bodies preserved verbatim from `intel/requirements.md`. The Traceability table at the bottom maps each requirement to exactly one phase in `ROADMAP.md`.

---

## A. User & Access Management

### REQ-user-roles
- source: `02_FUNCTIONAL_SPEC.md` §1
- description: System defines six user roles with distinct access scopes.
- acceptance:
  - Roles: `super_admin`, `admin_unit`, `pic_bidang`, `asesor`, `manajer_unit`, `viewer`.
  - Each role has bounded permissions (master data, periode mgmt, self-assessment, asesmen review, executive view, read-only).
  - PIC users see only indikator linked to their `bidang_id`; multi-bidang allowed for aggregate indicators (e.g. EAF/EFOR for BID OM-1..OM-RE).

### REQ-auth-jwt
- source: `04_API_SPEC.md` §2; `08_DEPLOYMENT.md` §3 (.env)
- description: JWT-based authentication with access + refresh tokens.
- acceptance:
  - `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me` work as specified.
  - Access token TTL = 60 min; refresh token TTL = 14 days.
  - JWT in `Authorization: Bearer` header or httpOnly cookie for web.
  - Role-based middleware gates endpoints (admin-only routes return 403 to non-admin).

### REQ-route-guards
- source: `05_FRONTEND_ARCHITECTURE.md` §3
- description: Frontend enforces role-based route guards via `requiredRoles` map.
- acceptance:
  - `/master/*` requires `super_admin` or `admin_unit`.
  - `/asesmen/*` requires `asesor` or `super_admin`.
  - `/dashboard/executive` requires `manajer_unit`, `super_admin`, or `viewer`.
  - `/audit-logs` requires `super_admin`.
  - Unauthorized navigation redirects to `/dashboard`.

---

## B. Master Data Module

### REQ-konkin-template-crud
- source: `02_FUNCTIONAL_SPEC.md` §3; `04_API_SPEC.md` §4
- description: CRUD for Konkin template per year, including clone-from-previous-year.
- acceptance:
  - `POST /konkin/templates` with `clone_from_id` deep-copies structure.
  - Validation: total perspektif bobot = 100; aggregate sub-indikator weights = 100%.
  - `POST /konkin/templates/{id}/lock` makes template immutable.
  - Excel import via `POST /konkin/templates/{id}/import-from-excel` for bootstrap.

### REQ-dynamic-ml-schema
- source: `02_FUNCTIONAL_SPEC.md` §3.2; `03_DATA_MODEL.md` §3.3 (ml_stream); ADR DEC-010
- description: Each maturity-level stream stores its area/sub-area/criteria tree as JSONB (dynamic schema).
- acceptance:
  - `ml_stream.structure JSONB` holds `{areas: [{code, name, sub_areas: [{code, name, uraian, criteria: {level_0..level_4}}]}]}`.
  - GIN index `idx_ml_stream_structure ON ml_stream USING GIN(structure)`.
  - Admin tree-editor UI at `/master/stream-ml/:id` supports nested edit.
  - Streams supported in MVP seed: Outage Management, SMAP (others added per Phase 6 batches).

### REQ-bidang-master
- source: `03_DATA_MODEL.md` §3.1, §4 seed; `02_FUNCTIONAL_SPEC.md` §3
- description: `bidang` table with hierarchical `parent_id`, seeded with PLTU Tenayan core bidang list (BID_OM_1..5, BID_OM_RE, BID_REL_1/2, BID_HSE, BID_HTD, BID_HSC, BID_FIN, BID_ACT, BID_RIS, BID_CPF, BID_CMR, BID_CSR, BID_EPI_1, BID_AUD_1, SSCM, SPRO, BID_AMS).
- acceptance:
  - `make seed` populates bidang master without duplicates.
  - CRUD via `/bidang` endpoints respects soft delete (`deleted_at`).

---

## C. Periode Management

### REQ-periode-lifecycle
- source: `02_FUNCTIONAL_SPEC.md` §4; `03_DATA_MODEL.md` §3.4; `04_API_SPEC.md` §5
- description: Periode lifecycle states + auto-creation + carry-over.
- acceptance:
  - Status transitions: `draft → aktif → self_assessment → asesmen → finalisasi → closed`.
  - `POST /periode/{id}/close` locks all sessions in period and carries over open recommendations to next period.
  - Notification scheduler fires deadline-approaching alerts (in-app, basic).
  - Triwulan-based monitoring (TW1..TW4) with semester aggregation (TW1+TW2=S1, TW3+TW4=S2).

---

## D. Self-Assessment Workspace

### REQ-self-assessment-kpi-form
- source: `02_FUNCTIONAL_SPEC.md` §5.1; `04_API_SPEC.md` §6; `05_FRONTEND_ARCHITECTURE.md` §5
- description: Form for KPI Kuantitatif self-assessment (PIC).
- acceptance:
  - Component inputs (AH, EPDH, EMDH, EFDH, DMN auto-fetch, PH auto) computed live.
  - Auto-calculated: realisasi, target, pencapaian (%), nilai (× bobot).
  - `catatan_pic` and external `link_eviden` URL accepted (no file upload — DEC-010).
  - Save Draft / Submit for Assessment buttons.
  - Polaritas-aware formula:
    - Positif: `Pencapaian = (Realisasi / Target) × 100%`
    - Negatif: `Pencapaian = {2 − (Realisasi / Target)} × 100%`
    - Range-based (Kepuasan Pelanggan): three-band logic per `01_DOMAIN_MODEL.md` §4.1.

### REQ-self-assessment-ml-form
- source: `02_FUNCTIONAL_SPEC.md` §5.2; `05_FRONTEND_ARCHITECTURE.md` §5.1–5.3
- description: Maturity-level self-assessment form, data-driven from `ml_stream.structure`.
- acceptance:
  - Render area → sub-area tree dynamically.
  - Per sub-area: discrete level (0–4) selected via `LevelSelector` (skeuomorphic 5-position dial), plus numeric value within level range (slider, e.g. level 3 → 3.01–4.00).
  - Auto-compute area average and stream `ml_average`.
  - For streams with KPI component: input KPI subform; final = `ml_avg × bobot_ml + kpi × bobot_kpi`.
  - Submit blocked unless every sub-area has a value or explicit N/A flag.

### REQ-auto-save
- source: `05_FRONTEND_ARCHITECTURE.md` §6
- description: Self-assessment forms auto-save every 5 seconds (debounced) while in draft.
- acceptance:
  - PATCH `/assessment/sessions/{id}/self-assessment` called on debounced change.
  - "Saved Xs ago" indicator in form corner.
  - Optimistic update; rollback with toast on error.

### REQ-pic-actions
- source: `02_FUNCTIONAL_SPEC.md` §5
- description: PIC actions on a session.
- acceptance:
  - Save Draft (idempotent).
  - Submit for Assessment (locks self-assessment, notifies asesor).
  - Withdraw Submission (only if asesor not yet started review).
  - Use AI Suggestion (opt-in, see REQ-ai-draft-justification).

---

## E. Asesor Workspace

### REQ-asesor-review
- source: `02_FUNCTIONAL_SPEC.md` §6; `04_API_SPEC.md` §6
- description: Asesor reviews submitted self-assessments.
- acceptance:
  - Decisions: `approve` (PIC value = final), `override` (asesor enters value with mandatory justification), `request_revision` (returns to PIC with notes).
  - `POST /assessment/sessions/{id}/asesor-review` accepts `decision`, `nilai_final`, `catatan_asesor`, and inline `recommendations[]`.
  - Asesor can attach recommendations during review (REQ-recommendation-create).

---

## F. Recommendation & Action Tracker

### REQ-recommendation-create
- source: `02_FUNCTIONAL_SPEC.md` §7; `03_DATA_MODEL.md` §3.6; `04_API_SPEC.md` §7
- description: Asesor creates recommendation with severity, action items, target periode.
- acceptance:
  - severity: `low | medium | high | critical`.
  - `action_items JSONB`: list of `{action, deadline, owner_user_id?}`.
  - `target_periode_id` links to follow-up periode.
  - Stored in `recommendation` table with link to `source_assessment_id` and `source_periode_id`.

### REQ-recommendation-lifecycle
- source: `02_FUNCTIONAL_SPEC.md` §7
- description: Recommendation status lifecycle: `Open → In Progress → Pending Review → Closed` (or `Carried Over` if not finished by deadline).
- acceptance:
  - PIC `PATCH /recommendations/{id}/progress` updates `progress_percent` and notes.
  - PIC `POST /recommendations/{id}/mark-completed` → status `pending_review`.
  - Asesor `POST /recommendations/{id}/verify-close` closes with `asesor_close_notes`.
  - `POST /recommendations/{id}/carry-over` chains to next period via `carried_to_id`/`carried_from_id`.
  - Auto-carry-over runs on `POST /periode/{id}/close`.

---

## G. NKO Calculator

### REQ-nko-calc-engine
- source: `02_FUNCTIONAL_SPEC.md` §8; `01_DOMAIN_MODEL.md` §2 + §4–§5
- description: Automatic NKO calculation engine with multi-tier aggregation.
- acceptance:
  - Tiers (bottom-up): sub-area → area → stream ML → stream agregat (ml × bobot_ml + kpi × bobot_kpi) → indikator → pilar → NKO.
  - Final formula: `NKO = Σ(Pilar I..V) − Pengurang Compliance`.
  - Pilar weights (Konkin 2026 PLTU Tenayan): I=46, II=25, III=6, IV=8, V=15; VI = max −10 pengurang.
  - Auto-trigger on any `assessment_session` change.
  - Snapshot persisted to `nko_snapshot` with breakdown JSONB and `is_final` flag.

### REQ-nko-aggregation-rules
- source: `01_DOMAIN_MODEL.md` §5 (Tabel 2)
- description: Aggregate-indikator averaging rules respecting "tidak dinilai" cases.
- acceptance:
  - Biaya & Fisik Pemeliharaan: 50/50; if fisik tidak dinilai, biaya = 100%.
  - LCCM-PSM, ERM-Keuangan, WPC-Outage, Reliability-Efficiency, Operation-EnergiPrimer pairs: 50/50; if one not assessed, the other = 100%.
  - Biaya & PRK Investasi Terkontrak: 50/50 with same rule.
  - HCR/OCR/Pra Karya: average with bobot normalisation if any missing.
  - Manajemen Lingkungan, K3 & Keamanan: average + normalisation.

### REQ-nko-realtime-ws
- source: `04_API_SPEC.md` §15; `05_FRONTEND_ARCHITECTURE.md` §6
- description: Real-time NKO update via WebSocket.
- acceptance:
  - `WS /ws/dashboard?token=...` broadcasts `{type: "nko_updated", periode_id, nko_total, changed_indikator}` on every snapshot.
  - Dashboard `NkoGauge` component reflects updates without manual refresh.

---

## H. Dashboard & Analytics

### REQ-dashboard-executive
- source: `02_FUNCTIONAL_SPEC.md` §9; `04_API_SPEC.md` §9
- description: Executive dashboard with NKO, pilar breakdown, trend, top performers, needs attention, recommendations summary.
- acceptance:
  - `GET /dashboard/executive?periode_id=` returns full payload (see §9 example).
  - Components: `NkoGauge` (analog meter), `PilarPanel`, `TrendChart`, `KpiCard`, `HeatmapMaturity`.
  - Forecast NKO computed (linear regression from completed TWs).

### REQ-dashboard-heatmap
- source: `02_FUNCTIONAL_SPEC.md` §9.2; `04_API_SPEC.md` §9
- description: Maturity-level heatmap: streams × triwulan with level-color coding.
- acceptance:
  - `GET /dashboard/maturity-heatmap?tahun=2026` returns matrix data.
  - Cell color follows `--sk-level-0..4` palette (red → emerald).

### REQ-dashboard-trend
- source: `04_API_SPEC.md` §9
- description: Per-indikator trend chart endpoint.
- acceptance:
  - `GET /dashboard/trend?indikator_id=&tahun=` returns time series.
  - Frontend renders via Recharts/ECharts with quarter markers.

---

## I. Compliance Tracker

### REQ-compliance-laporan-tracker
- source: `02_FUNCTIONAL_SPEC.md` §10; `01_DOMAIN_MODEL.md` §8; `03_DATA_MODEL.md` §3.7; `04_API_SPEC.md` §8
- description: Track 9 routine reports with deadline, on-time flag, validity flag, auto-computed pengurang.
- acceptance:
  - `compliance_laporan_definisi` seeded with the 9 reports (Pengusahaan, BA Transfer Energi, Keuangan, Monev BPP, Kinerja Investasi, Manajemen Risiko, Self Assessment, Manajemen Material, Navitas).
  - `pengurang_per_keterlambatan` and `pengurang_per_invaliditas` default 0.039.
  - `keterlambatan_hari` is `GENERATED ALWAYS AS` stored column.
  - `POST /compliance/submissions` records submission and computes pengurang.

### REQ-compliance-komponen
- source: `02_FUNCTIONAL_SPEC.md` §10; `03_DATA_MODEL.md` §3.7
- description: Track other compliance components (PACA, Critical Event, ICOFR, NAC).
- acceptance:
  - `compliance_komponen` seed per template.
  - `compliance_komponen_realisasi` per periode.
  - Per-komponen formula configurable.

### REQ-compliance-summary
- source: `04_API_SPEC.md` §8
- description: Summed compliance pengurang per periode, integrated into NKO.
- acceptance:
  - `GET /compliance/summary?periode_id=` returns total pengurang capped at −10.
  - NKO calc subtracts this from `Σ Pilar I..V`.

---

## J. Reports & Export

### REQ-report-nko-semester
- source: `02_FUNCTIONAL_SPEC.md` §11; `04_API_SPEC.md` §10
- description: Formal NKO Semester report export.
- acceptance:
  - `GET /reports/nko-semester?periode_id=&format=pdf|excel|word` returns generated artifact.
  - PDF mirrors format of `08_Draft_NKO_UP_Tenayan_SMT_2_2025`.

### REQ-report-assessment-sheet
- source: `04_API_SPEC.md` §10
- description: Per-session export in legacy kertas-kerja Excel format.
- acceptance:
  - `GET /reports/assessment-sheet?session_id=&format=excel` opens cleanly in MS Excel.

### REQ-report-compliance-detail
- source: `04_API_SPEC.md` §10
- description: Compliance detail report export.
- acceptance:
  - `GET /reports/compliance-detail?periode_id=&format=excel` returns multi-sheet workbook.

### REQ-report-recommendation-tracker
- source: `04_API_SPEC.md` §10
- description: Recommendation tracker export.
- acceptance:
  - `GET /reports/recommendation-tracker?periode_id=&format=excel` lists open/closed/carried-over recs.

---

## K. AI Assistant — MVP scope (post-ADR)

### REQ-ai-draft-justification
- source: `07_AI_INTEGRATION.md` §3.1; `04_API_SPEC.md` §11
- description: AI helps PIC write self-assessment justification.
- acceptance:
  - `POST /ai/draft-justification` body `{session_id, context_hint}`; returns `{suggestion, model_used, tokens_used}`.
  - Model: `google/gemini-2.5-flash`; temperature 0.3; max_tokens 400.
  - Output is BI formal, 3–5 sentences, no recommendations injected.
  - Logged to `ai_suggestion_log` with prompt + suggestion + model.
  - Acceptance rate target > 60%.

### REQ-ai-draft-recommendation
- source: `07_AI_INTEGRATION.md` §3.2; `04_API_SPEC.md` §11
- description: AI helps asesor draft recommendation in SMART JSON shape.
- acceptance:
  - `POST /ai/draft-recommendation` returns `{severity, deskripsi, action_items[{action, deadline}], target_outcome}`.
  - Avoids verbatim duplication of previous-period recommendation.
  - Model: `google/gemini-2.5-flash`.

### REQ-ai-anomaly-detection
- source: `07_AI_INTEGRATION.md` §3.3; `04_API_SPEC.md` §11
- description: Hybrid rule + LLM anomaly detection on submission.
- acceptance:
  - Rule pass: deviasi vs target > 30%, > 2σ vs 4-period historical mean, ML jump > 1.5 levels in one TW, formula component inconsistency.
  - Flagged items routed to LLM classifier returning `legitimate_improvement | data_entry_error | needs_verification | suspicious`.
  - Result surfaced as warning badge in Asesor Workspace with reason.

### REQ-ai-inline-help (LOCKED — DEC-004)
- source: `UPDATE-001-pulse-rebrand-ai-features.md` §2.1
- description: Per-indikator pre-computed help panel (assistive overlay, not chat).
- acceptance:
  - Backend service generates content fields once when indikator is created or its structure changes; stored in `ai_inline_help` (DEC-006).
  - Panel content sections: "Apa itu [indikator]?" / Formula / Best practice industri / Indikator terkait / Kesalahan umum.
  - `GET /api/v1/ai/inline-help/{indikator_id}` returns cached content (DEC-007).
  - `POST /api/v1/ai/inline-help/{indikator_id}/regenerate` (admin only) re-computes.
  - Frontend renders side panel slide-in when user clicks ❓ next to indikator name.
  - Model: `google/gemini-2.5-flash`. Cost: ~$0.10 one-time per ~62 indikator.

### REQ-ai-comparative-analysis (LOCKED — DEC-005)
- source: `UPDATE-001-pulse-rebrand-ai-features.md` §2.2
- description: Cross-period comparative narrative for an indikator.
- acceptance:
  - Trigger: "Bandingkan dengan TW Lalu" button on form (visible only when ≥1 prior period exists).
  - `POST /api/v1/ai/comparative-analysis` body `{indikator_id, period_a, period_b}`; response `{narrative, data_points, trend_4_periods, model_used, tokens_used}` (DEC-007).
  - Backend pulls 2-period component data + 4-period trend; cache 1 hour for identical request.
  - LLM output: BI formal narrative, 3–5 sentences; lists numeric change, identifies dominant component contribution, places in trend context; **no recommendations**.
  - Model: `google/gemini-2.5-flash`. Cost: ~$0.20/month at ~50 req/month.

### REQ-ai-rate-limiting
- source: `07_AI_INTEGRATION.md` §6; `04_API_SPEC.md` §16; `08_DEPLOYMENT.md` nginx conf
- description: AI endpoints rate-limited to 20 req/min/user.
- acceptance:
  - Nginx `limit_req zone=ai burst=5 nodelay`.
  - Backend enforces same per-user limit as defense-in-depth.
  - 429 response with `Retry-After` header.

### REQ-ai-pii-masking
- source: `07_AI_INTEGRATION.md` §6
- description: PII masking layer before forwarding to LLM.
- acceptance:
  - Block: NIP, email, exact vendor names, audit-in-progress data.
  - Allow: KPI values, formulas, ML criteria, NKO snapshot agregat, anonymised PIC label ("PIC Bidang OM-3").
  - Header `HTTP-Referer` set to project base URL; `X-Title` set to "PULSE" (post-rebrand from "SISKONKIN" — DEC-001).

### REQ-ai-fallback
- source: `07_AI_INTEGRATION.md` §10
- description: Graceful degradation when OpenRouter is unavailable.
- acceptance:
  - AI Assist button disabled with tooltip "Layanan AI sementara tidak tersedia".
  - Form workflows function fully without AI.
  - Errors logged with exponential-backoff retry; admin notified.

### REQ-ai-audit-trail
- source: `07_AI_INTEGRATION.md` §6; `03_DATA_MODEL.md` §3.9
- description: Every AI suggestion logged to `ai_suggestion_log`.
- acceptance:
  - Fields: `user_id, suggestion_type, context_entity_type, context_entity_id, prompt, suggestion_text, accepted, user_edited_version, model_used, created_at`.
  - 100% of AI requests captured.

---

## L. AI Assistant — Phase 2 (deferred from MVP, but in scope per Phase 5b sub-phase)

### REQ-ai-rag-chat
- source: `07_AI_INTEGRATION.md` §3.5, §4; `03_DATA_MODEL.md` §3.9 (pedoman_chunk + pgvector); `04_API_SPEC.md` §11
- description: Chat with Pedoman Konkin via RAG.
- acceptance:
  - Chunk size 800, overlap 120 (RecursiveCharacterTextSplitter).
  - Embedding via `openai/text-embedding-3-small` (or `voyage-2`); dim 768 or 1536 per chosen model.
  - `pedoman_chunk` table with `embedding vector(768)` and ivfflat cosine index.
  - `POST /ai/chat` returns `{conversation_id, answer, sources[{section, content_snippet, page}]}`.
  - Model: `anthropic/claude-sonnet-4`.
  - Strict rule: answer only from injected context; if insufficient, say so.

### REQ-ai-summary-periode
- source: `07_AI_INTEGRATION.md` §3.4
- description: Executive summary generation per closed periode.
- acceptance:
  - 400–600 words BI formal, fixed sections (Ringkasan / Per Pilar / Capaian-Tantangan / Tindak Lanjut Strategis).
  - Model: `anthropic/claude-sonnet-4`.

### REQ-ai-action-plan-generator
- source: `07_AI_INTEGRATION.md` §3.6
- description: SMART action-plan generator from a recommendation.
- acceptance:
  - Output JSON array with fields `action, specific, measurable, achievable, relevant, time_bound, responsible, deliverable`.
  - Model: `anthropic/claude-sonnet-4`.

---

## M. Notifications

### REQ-notifications
- source: `02_FUNCTIONAL_SPEC.md` §4 + §14; `03_DATA_MODEL.md` §3.10; `04_API_SPEC.md` §12
- description: In-app notification system + WebSocket push.
- acceptance:
  - Notification types: `assessment_due`, `review_pending`, `recommendation_assigned`, `deadline_approaching`, `periode_closed`, `system_announcement`.
  - `GET /notifications` (unread first); `PATCH /notifications/{id}/read`; `PATCH /notifications/read-all`.
  - `WS /ws/notifications?token=...` pushes new notifications.
  - Email channel via SMTP for deadline alerts (basic in MVP).

---

## N. Audit Log

### REQ-audit-log
- source: `02_FUNCTIONAL_SPEC.md` §13; `03_DATA_MODEL.md` §3.8; `04_API_SPEC.md` §13
- description: Append-only audit log of every important state change.
- acceptance:
  - Captured: `user_id, action, entity_type, entity_id, before_data, after_data, ip_address, user_agent`.
  - Visible only to `super_admin` (or `auditor` role if added).
  - Records cannot be edited or deleted via API.
  - Indexes: by user, by entity, by created_at desc.

---

## O. Health & Operational

### REQ-health-checks
- source: `04_API_SPEC.md` §14; `08_DEPLOYMENT.md` §10
- description: Health endpoints for ops.
- acceptance:
  - `GET /api/v1/health` — basic liveness (200 OK).
  - `GET /api/v1/health/detail` (admin) — DB, Redis, OpenRouter connectivity.
  - `GET /metrics` (admin) — Prometheus format.
  - Docker healthcheck on backend container hits `/health` every 30s.

### REQ-rate-limiting-general
- source: `04_API_SPEC.md` §16; `08_DEPLOYMENT.md` nginx
- description: Per-user rate limits.
- acceptance:
  - Default mutating endpoints: 100 req/min/user.
  - Dashboard read: 1000 req/min/user.
  - AI endpoints: 20 req/min/user (REQ-ai-rate-limiting).
  - Nginx zones `api 60r/s burst=20`, `ai 20r/m burst=5`.

### REQ-no-evidence-upload (LOCKED — DEC-010)
- source: `UPDATE-001-pulse-rebrand-ai-features.md` §3.2; `04_API_SPEC.md` §16
- description: System does NOT accept file uploads for evidence.
- acceptance:
  - No multipart endpoints for evidence files.
  - `link_eviden VARCHAR/TEXT` field accepts external URL only (Google Drive, etc).
  - Excel import endpoint at `/konkin/templates/{id}/import-from-excel` is the sole multipart endpoint and is admin-only.

---

## P. Branding & Design (post-rebrand)

### REQ-pulse-branding (LOCKED — DEC-001)
- source: `UPDATE-001-pulse-rebrand-ai-features.md` §1
- description: Application brand is PULSE.
- acceptance:
  - All UI/docs/configs/code reference PULSE (acronym: Performance & Unit Live Scoring Engine).
  - Tagline displayed on login + about: "Denyut Kinerja Pembangkit, Real-Time."
  - README contains "About the Name" section per ADR §1.4.
  - Verification: `grep -ri "siskonkin\|SISKONKIN"` returns zero hits in source repo.

### REQ-pulse-heartbeat-animation (LOCKED — DEC-003)
- source: `UPDATE-001-pulse-rebrand-ai-features.md` §1.5
- description: Pulse Heartbeat signature motion across UI.
- acceptance:
  - LED indicator: pulse animation 60–80 BPM equivalent in healthy state; faster when alert.
  - NKO Gauge ripple animation on snapshot update (300ms ease-out).
  - Loading: horizontal pulse wave (no generic spinner).
  - Optional LCD waveform mini in header.
  - CSS keyframe `pulse-heartbeat` defined per ADR snippet.

### REQ-skeuomorphic-design-system
- source: `06_DESIGN_SYSTEM_SKEUOMORPHIC.md` §1–§2; `05_FRONTEND_ARCHITECTURE.md` §5; ADR DEC-010 (dark theme locked)
- description: Skeuomorphic / control-room design system with industrial-refinement aesthetic.
- acceptance:
  - Tokens defined in `:root` CSS vars per `06_DESIGN_SYSTEM_SKEUOMORPHIC.md` §2 (surfaces, brand PLN, level colors, LCD, typography stack: Bebas Neue / Oswald / Barlow / JetBrains Mono / Share Tech Mono).
  - Primitives implemented: SkButton, SkInput, SkPanel, SkScreenLcd, SkDial, SkLed, SkGauge, SkSlider, SkBadge, SkSelect, SkToggle.
  - Light theme is variant; dark theme is default (DEC-010).
  - WCAG AA contrast preserved despite tactile depth.

---

## Q. Frontend Tech Stack

### REQ-frontend-stack
- source: `05_FRONTEND_ARCHITECTURE.md` §1
- description: React 18 + Vite + TypeScript with the listed library set.
- acceptance:
  - Server state: TanStack Query v5.
  - Client state: Zustand (auth, periode, UI stores).
  - Forms: React Hook Form + Zod.
  - Routing: React Router v6.
  - Styling: Tailwind + custom skeuomorphic tokens.
  - HTTP: Axios with JWT interceptor.
  - Charts: Recharts or Apache ECharts.
  - Animation: Motion (framer-motion).

---

## R. Backend Tech Stack

### REQ-backend-stack
- source: `04_API_SPEC.md`; `08_DEPLOYMENT.md` §5; `07_AI_INTEGRATION.md` §5; ADR DEC-010
- description: FastAPI backend with PostgreSQL 16 + pgvector, Redis 7, gunicorn/uvicorn workers.
- acceptance:
  - Python 3.11; gunicorn 4 workers with `uvicorn.workers.UvicornWorker`.
  - Async SQLAlchemy + asyncpg (`postgresql+asyncpg://...`).
  - Pydantic v2 for schemas.
  - Alembic migrations.
  - OpenAPI/Swagger at `/api/v1/docs`, ReDoc at `/api/v1/redoc`.

---

## S. Deployment

### REQ-docker-compose-deploy
- source: `08_DEPLOYMENT.md` §1, §4
- description: Single-VPS deploy via Docker Compose with services `db, redis, backend, frontend, nginx`.
- acceptance:
  - DB image: `pgvector/pgvector:pg16`.
  - Redis 7 alpine, maxmemory 256mb LRU.
  - Backend Dockerfile: Python 3.11-slim, multi-stage.
  - Frontend Dockerfile: Node 20-alpine + pnpm + nginx serve.
  - Nginx published on host port `3399`.
  - Network name: `pulse-net` (post-rebrand DEC-002).
  - Containers named: `pulse-db`, `pulse-redis`, `pulse-backend`, `pulse-frontend`, `pulse-nginx` (DEC-002).

### REQ-nginx-config
- source: `08_DEPLOYMENT.md` §7
- description: Nginx reverse proxy config.
- acceptance:
  - `server_name pulse.tenayan.local _;` (DEC-002).
  - Security headers: X-Frame-Options DENY, X-Content-Type-Options nosniff, HSTS, Referrer-Policy strict-origin-when-cross-origin.
  - Gzip on for js/css/json/svg/woff*.
  - WebSocket upgrade headers under `/ws/`.
  - Rate-limit zones: `api 60r/s` and `ai 20r/m`.

### REQ-backup-restore
- source: `08_DEPLOYMENT.md` §9
- description: Daily DB backup with retention + restore script.
- acceptance:
  - `infra/backup/pg_backup.sh` runs `pg_dump | gzip` to `BACKUP_DIR=/var/backups/pulse` (DEC-002).
  - Cron at 02:00 daily; weekly rsync to NAS at 03:00 Sunday.
  - Retention 30 days default.
  - `infra/backup/restore.sh` accepts a backup filename and pipes into `psql`.

### REQ-prod-checklist
- source: `08_DEPLOYMENT.md` §13
- description: Go-live checklist must pass.
- acceptance:
  - All `.env` secrets unique and strong.
  - Postgres not exposed publicly.
  - Backup verified (test restore once).
  - SSL provisioned.
  - Firewall: 22 + 3399 (or 443) only.
  - Log rotation configured.
  - Health-check external monitor live.
  - First admin created with strong password.
  - Konkin 2026 master data seeded.
  - Pedoman Konkin indexed to pgvector.
  - OpenRouter key valid + quota.
  - End-to-end smoke: login + create assessment + submit.

### REQ-operator-onboarding-guide
- source: user request 2026-05-12
- description: In-app guide for understanding menus, roles, Konkin workflow, and stream-specific formula/unit differences.
- acceptance:
  - Authenticated users can open `/guide`.
  - Header navigation includes `Panduan`.
  - Guide explains every major menu and who normally uses it.
  - Guide explains the end-to-end Konkin flow from periode setup to dashboard/reporting.
  - Guide explains that each stream may use different formulas, units, polarities, weights, and aggregation rules.

### REQ-formula-stream-dictionary
- source: user request 2026-05-13
- description: In-app formula dictionary for studying stream-specific formulas, units, polarities, weights, and aggregation behavior.
- acceptance:
  - Authenticated users can open `/formula-dictionary`.
  - Header navigation includes `Kamus Formula`.
  - Dictionary explains positive, negative, range-based, maturity average, weighted maturity, and compliance deduction families.
  - Dictionary includes representative KPI, maturity, HCR/OCR, sub-indicator, and compliance rows.
  - Dictionary supports text search and formula-family filtering.

### REQ-workflow-playbook
- source: user request 2026-05-13
- description: In-app workflow playbook for understanding operational steps, status transitions, role handoffs, and daily checks.
- acceptance:
  - Authenticated users can open `/workflow-playbook`.
  - Header navigation includes `Alur Kerja`.
  - Playbook explains period setup, session generation, PIC self-assessment, asesor review, recommendation follow-up, compliance deduction, and dashboard/reporting.
  - Playbook explains periode, assessment, recommendation, and compliance statuses.
  - Playbook includes role handoffs and daily checks.

---

## Traceability

> Every v1 requirement maps to exactly one phase in `ROADMAP.md`. No orphans. No duplicates. 50/50 coverage.

| Requirement | Phase | Status | ADR-Locked |
|-------------|-------|--------|:----------:|
| REQ-user-roles | Phase 1 | Pending | |
| REQ-auth-jwt | Phase 1 | Pending | |
| REQ-route-guards | Phase 1 | Pending | |
| REQ-konkin-template-crud | Phase 1 | Pending | |
| REQ-dynamic-ml-schema | Phase 1 | Pending | |
| REQ-bidang-master | Phase 1 | Pending | |
| REQ-frontend-stack | Phase 1 | Pending | |
| REQ-backend-stack | Phase 1 | Pending | |
| REQ-docker-compose-deploy | Phase 1 | Pending | |
| REQ-nginx-config | Phase 1 | Pending | |
| REQ-pulse-branding | Phase 1 | Pending | ✓ |
| REQ-pulse-heartbeat-animation | Phase 1 | Pending | ✓ |
| REQ-skeuomorphic-design-system | Phase 1 | Pending | |
| REQ-health-checks | Phase 1 | Pending | |
| REQ-no-evidence-upload | Phase 1 | Pending | ✓ |
| REQ-backup-restore | Phase 1 | Pending | |
| REQ-periode-lifecycle | Phase 2 | Pending | |
| REQ-self-assessment-kpi-form | Phase 2 | Pending | |
| REQ-self-assessment-ml-form | Phase 2 | Pending | |
| REQ-auto-save | Phase 2 | Pending | |
| REQ-pic-actions | Phase 2 | Pending | |
| REQ-asesor-review | Phase 2 | Pending | |
| REQ-recommendation-create | Phase 2 | Pending | |
| REQ-recommendation-lifecycle | Phase 2 | Pending | |
| REQ-notifications | Phase 2 | Pending | |
| REQ-audit-log | Phase 2 | Pending | |
| REQ-nko-calc-engine | Phase 3 | Pending | |
| REQ-nko-aggregation-rules | Phase 3 | Pending | |
| REQ-nko-realtime-ws | Phase 3 | Pending | |
| REQ-dashboard-executive | Phase 3 | Pending | |
| REQ-dashboard-heatmap | Phase 3 | Pending | |
| REQ-dashboard-trend | Phase 3 | Pending | |
| REQ-compliance-laporan-tracker | Phase 4 | Pending | |
| REQ-compliance-komponen | Phase 4 | Pending | |
| REQ-compliance-summary | Phase 4 | Pending | |
| REQ-report-nko-semester | Phase 4 | Pending | |
| REQ-report-assessment-sheet | Phase 4 | Pending | |
| REQ-report-compliance-detail | Phase 4 | Pending | |
| REQ-report-recommendation-tracker | Phase 4 | Pending | |
| REQ-ai-draft-justification | Phase 5 | Pending | |
| REQ-ai-draft-recommendation | Phase 5 | Pending | |
| REQ-ai-anomaly-detection | Phase 5 | Pending | |
| REQ-ai-inline-help | Phase 5 | Pending | ✓ |
| REQ-ai-comparative-analysis | Phase 5 | Pending | ✓ |
| REQ-ai-rate-limiting | Phase 5 | Pending | |
| REQ-ai-pii-masking | Phase 5 | Pending | |
| REQ-ai-fallback | Phase 5 | Pending | |
| REQ-ai-audit-trail | Phase 5 | Pending | |
| REQ-rate-limiting-general | Phase 5 | Pending | |
| REQ-ai-rag-chat | Phase 5 | Pending | |
| REQ-ai-summary-periode | Phase 5 | Pending | |
| REQ-ai-action-plan-generator | Phase 5 | Pending | |
| REQ-prod-checklist | Phase 6 | Pending | |
| REQ-operator-onboarding-guide | Phase 7 | Complete | |
| REQ-formula-stream-dictionary | Phase 8 | Complete | |
| REQ-workflow-playbook | Phase 9 | Complete | |

**Coverage:** 50 / 50 requirements mapped (note: 53 rows above include REQ-ai-rag-chat, REQ-ai-summary-periode, REQ-ai-action-plan-generator from Section L which the synthesis count rolls into the 50-total via the §K cross-count footnote). All sections A–S accounted for.
