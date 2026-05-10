# Decisions (locked)

> Extracted from ADR-class sources. Each entry preserves source path and decision scope.
> Locked decisions cannot be auto-overridden by lower-precedence sources (SPEC, PRD, DOC).

---

## ADR-001 — UPDATE-001: Rebranding ke PULSE & Penambahan Fitur AI

- source: `C:/Users/ANUNNAKI/Projects/PULSE/UPDATE-001-pulse-rebrand-ai-features.md`
- status: APPROVED (treated as Accepted → locked)
- locked: true
- precedence: 0 (manifest override, beats default ADR=0)
- date: Mei 2026
- author: Budi (technical lead, CV Panda Global Teknologi)
- supersedes: applicable statements in `01_DOMAIN_MODEL.md`, `02_FUNCTIONAL_SPEC.md`, `03_DATA_MODEL.md`, `04_API_SPEC.md`, `05_FRONTEND_ARCHITECTURE.md`, `06_DESIGN_SYSTEM_SKEUOMORPHIC.md`, `07_AI_INTEGRATION.md`, `08_DEPLOYMENT.md`, `09_DEVELOPMENT_ROADMAP.md`, `10_CLAUDE_CODE_INSTRUCTIONS.md`, `README.md`

### Decision DEC-001 — Project rename SISKONKIN → PULSE

- scope: project naming, acronym, taglines
- statement: The application is officially renamed from `SISKONKIN` to `PULSE`.
  - Acronym: **P**erformance & **U**nit **L**ive **S**coring **E**ngine
  - Tagline (id): "Denyut Kinerja Pembangkit, Real-Time."
  - Tagline (en, alt): "The Heartbeat of Power Performance."
  - Tagline (formal): "Sistem Monitoring Kinerja Unit Pembangkit Real-Time PT PLN Nusantara Power."
- rationale: Pulse metaphor reinforces the existing "control room digital" design theme; NKO is the organisation's pulse.
- override: Replaces every occurrence of `SISKONKIN` / `Siskonkin` / `siskonkin` in docs 01–10, README, CHANGELOG, code, configs.

### Decision DEC-002 — Identifier renames (containers, DB, network, domain)

- scope: code identifiers, infrastructure naming
- statement: Apply case-sensitive find-and-replace across the repo:
  - `siskonkin_blueprint` → `pulse_blueprint`
  - `siskonkin-net` → `pulse-net`
  - `siskonkin-db` → `pulse-db`
  - `siskonkin-backend` → `pulse-backend`
  - `siskonkin-frontend` → `pulse-frontend`
  - `siskonkin-redis` → `pulse-redis`
  - `siskonkin-nginx` → `pulse-nginx`
  - `siskonkin.tenayan.local` → `pulse.tenayan.local`
  - `POSTGRES_DB=siskonkin` → `POSTGRES_DB=pulse`
  - `POSTGRES_USER=siskonkin` → `POSTGRES_USER=pulse`
  - `BACKUP_DIR=/var/backups/siskonkin` → `BACKUP_DIR=/var/backups/pulse`
  - `siskonkin-blueprint.tar.gz` → `pulse-blueprint.tar.gz`
- migration note: For existing prod DB, do NOT drop. Use `pg_dump` + restore to new `pulse` DB, or `ALTER DATABASE siskonkin RENAME TO pulse;` after disconnecting users.

### Decision DEC-003 — Pulse Heartbeat signature animation in design system

- scope: design system, motion/animation patterns
- statement: Adopt `Pulse Heartbeat` as the signature visual motion for PULSE. Adds a new section "Tema Pulse — Sinyal Kehidupan Pembangkit" to `06_DESIGN_SYSTEM_SKEUOMORPHIC.md` covering:
  - LED status: pulse rate normal saat sistem sehat (60-80 BPM equivalent)
  - Pulse rate naik saat ada anomali atau alert
  - LCD screen kadang menampilkan waveform mini di header
  - Loading state: pulse wave horizontal (bukan spinner generik)
  - NKO update ripple animation dari pusat NKO Gauge ke seluruh dashboard (300ms ease-out, opacity fade)
  - CSS keyframes `pulse-heartbeat` for `.sk-led[data-state="on"]`

### Decision DEC-004 — AI Feature #7: Inline Help (Konteks Indikator) added to MVP

- scope: AI feature set, MVP scope, Fase 5 deliverables
- statement: Add per-indikator AI Inline Help as MVP feature. Pre-computed, cached at indikator-creation time, regenerated on indikator structure change. Model: `google/gemini-2.5-flash`.
- panel content: "Apa itu [indikator]?", Formula explanation, Best practice industri, Indikator terkait, Kesalahan umum.
- cost: ~$0.10 one-time per ~62 indikator; regenerate periodik negligible.
- effort: 3–5 days (backend cache + pre-compute job + frontend side panel).

### Decision DEC-005 — AI Feature #8: Comparative Analysis (Cross-Periode) added to MVP

- scope: AI feature set, MVP scope, Fase 5 deliverables
- statement: Add cross-period comparative analysis ("Bandingkan dengan TW Lalu") as MVP feature. Backend pulls 2-period component data + 4-period historical trend, sends to LLM, caches result for 1 hour.
- model: `google/gemini-2.5-flash`.
- output contract: 3–5 sentence Bahasa Indonesia formal narrative; structured JSON `{narrative, data_points, trend_4_periods, model_used, tokens_used}`.
- cost: ~$0.20/month at ~50 requests/month.
- effort: 2 days (backend service + prompt + frontend button + modal).

### Decision DEC-006 — New DB table `ai_inline_help`

- scope: data model
- statement: Add `ai_inline_help` table to `03_DATA_MODEL.md`:
  - Columns: `id UUID PK`, `indikator_id UUID FK indikator(id) ON DELETE CASCADE UNIQUE`, `apa_itu TEXT`, `formula_explanation TEXT`, `best_practice TEXT`, `common_pitfalls TEXT`, `related_indikator JSONB`, `generated_by_model VARCHAR(100)`, `generated_at TIMESTAMP WITH TIME ZONE`, `expires_at TIMESTAMP WITH TIME ZONE`, `created_at`, `updated_at`.
  - Index: `idx_ai_inline_help_indikator ON ai_inline_help(indikator_id)`.

### Decision DEC-007 — New API endpoints for AI features 7 & 8

- scope: API surface
- statement: Add to `04_API_SPEC.md` (FastAPI under `/api/v1`):
  - `GET  /api/v1/ai/inline-help/{indikator_id}` — fetch cached help.
  - `POST /api/v1/ai/inline-help/{indikator_id}/regenerate` — admin: trigger regen.
  - `POST /api/v1/ai/comparative-analysis` — body `{indikator_id, period_a, period_b}`, response `{narrative, data_points, trend_4_periods, model_used, tokens_used}`.

### Decision DEC-008 — Fase 5 deliverables (UPDATED)

- scope: roadmap
- statement: Fase 5 deliverable list, post-update:
  - ✅ Setup OpenRouter client + routing
  - ✅ AI Suggestion Drawer component (UX pattern)
  - ✅ Draft Justifikasi (PIC) — Gemini Flash
  - ✅ Draft Rekomendasi (Asesor) — Gemini Flash
  - ✅ Anomaly Detection (rule-based + LLM hybrid)
  - ✅ AI Inline Help untuk indikator (NEW — DEC-004)
  - ✅ Comparative Analysis cross-periode (NEW — DEC-005)
  - ✅ AI Suggestion audit log (`ai_suggestion_log`)
  - ✅ Rate limiting per user (20/min)
  - ✅ Fallback graceful jika OpenRouter down

### Decision DEC-009 — AI cost estimate (UPDATED)

- scope: ops/finance
- statement: Updated total monthly AI cost estimate for MVP scale at UP Tenayan: **~$3.15/month (~Rp 50.000)**. Breakdown:
  - Draft justifikasi: 200/bln × ~$0.50
  - Draft rekomendasi: 50/bln × ~$0.20
  - Anomaly check: 100/bln × ~$0.30
  - Chat RAG: 100/bln × ~$1.50
  - Summary periode: 4/bln × ~$0.30
  - Embedding (RAG): one-time + 100/bln × ~$0.05
  - AI Inline Help (NEW): 62 indikator cached × ~$0.10
  - Comparative Analysis (NEW): 50/bln × ~$0.20
- supersedes: the lower estimate (~$3–5/month) in `07_AI_INTEGRATION.md` Section 2.

### Decision DEC-010 — Locked clarifications (re-affirmations from base blueprint)

- scope: scope guards
- statement: The following decisions remain in force (re-locked by this ADR):
  - **No evidence file upload.** Only external URL (Google Drive, etc) recorded as `link_eviden`. (BAGIAN 3 §3.2 + `04_API_SPEC.md` §16)
  - **Dynamic JSONB schema for maturity-level rubrics.** Each stream stores its own area/sub-area/criteria tree in `ml_stream.structure JSONB`. (BAGIAN 3 §3.2 + `03_DATA_MODEL.md` §3.3)
  - **HCR deferred to Fase 6.** Schema reserved; full implementation only after other streams stable. (BAGIAN 3 §3.2 + `09_DEVELOPMENT_ROADMAP.md` §8 batch 4)
  - **UI: skeuomorphic dark theme (control-room digital).** Light theme exists as variant only. (BAGIAN 3 §3.2 + `06_DESIGN_SYSTEM_SKEUOMORPHIC.md`)
  - **AI routing: Gemini 2.5 Flash for routine + Claude Sonnet 4 for complex.** Via OpenRouter. (BAGIAN 3 §3.2 + `07_AI_INTEGRATION.md` §2)
  - **Tech stack: FastAPI + React 18 + PostgreSQL 16 + Docker Compose.** (BAGIAN 3 §3.2 + `08_DEPLOYMENT.md`)

### Decision DEC-011 — Open items NOT yet decided (informational, not locked)

- scope: deferred decisions
- statement: The following are explicitly UNRESOLVED in this ADR and not to be locked downstream:
  - Final logo (placeholder for now).
  - SSL certificate strategy (decide at deploy time).
  - OpenRouter API key provisioning (Budi handles directly).
  - External integrations Navitas, SAP, etc. — Phase 2+.
