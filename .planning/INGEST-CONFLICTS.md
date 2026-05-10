## Conflict Detection Report

### BLOCKERS (0)

(none)

### WARNINGS (0)

(none)

### INFO (16)

[INFO] Auto-resolved: ADR DEC-001 supersedes project name in all SPEC/DOC sources
  Note: UPDATE-001-pulse-rebrand-ai-features.md (locked, precedence=0) renames the application from `SISKONKIN` to `PULSE`. The legacy name still appears in `01_DOMAIN_MODEL.md`, `02_FUNCTIONAL_SPEC.md`, `03_DATA_MODEL.md`, `04_API_SPEC.md`, `05_FRONTEND_ARCHITECTURE.md`, `06_DESIGN_SYSTEM_SKEUOMORPHIC.md`, `07_AI_INTEGRATION.md`, `08_DEPLOYMENT.md`, `09_DEVELOPMENT_ROADMAP.md`, `10_CLAUDE_CODE_INSTRUCTIONS.md`, `README.md`. ADR wins — synthesized intel uses `PULSE` everywhere; verbatim DOC excerpts in `intel/context.md` retain the legacy name as historical record with an explicit override notice.

[INFO] Auto-resolved: ADR DEC-002 supersedes container/network/DB identifier names in 08_DEPLOYMENT.md
  Note: UPDATE-001 §1.3 maps `siskonkin-net → pulse-net`, `siskonkin-db → pulse-db`, `siskonkin-backend → pulse-backend`, `siskonkin-frontend → pulse-frontend`, `siskonkin-redis → pulse-redis`, `siskonkin-nginx → pulse-nginx`, `POSTGRES_DB=siskonkin → POSTGRES_DB=pulse`, `POSTGRES_USER=siskonkin → POSTGRES_USER=pulse`, `BACKUP_DIR=/var/backups/siskonkin → BACKUP_DIR=/var/backups/pulse`. The base SPEC `08_DEPLOYMENT.md` §3-§4 still shows the legacy names. ADR wins. `intel/constraints.md` (CONSTR-network-naming, CONSTR-env-secrets) records the post-rebrand identifiers as authoritative.

[INFO] Auto-resolved: ADR DEC-002 supersedes domain placeholder in 04_API_SPEC.md and 08_DEPLOYMENT.md
  Note: UPDATE-001 §1.3 maps `siskonkin.tenayan.local → pulse.tenayan.local`. `04_API_SPEC.md` §1 shows `https://siskonkin.tenayan.local/api/v1`; `08_DEPLOYMENT.md` §3 shows `APP_BASE_URL=https://siskonkin.tenayan.local` and similar in nginx `server_name`. ADR wins. `intel/constraints.md` (CONSTR-api-versioning, CONSTR-domain-pulse) records the post-rebrand domain.

[INFO] Auto-resolved: ADR DEC-003 supersedes design-system motion section in 06_DESIGN_SYSTEM_SKEUOMORPHIC.md
  Note: UPDATE-001 §1.5 inserts a new "Tema Pulse — Sinyal Kehidupan Pembangkit" subsection plus §6.6 "Pulse Signature Animation" into `06_DESIGN_SYSTEM_SKEUOMORPHIC.md` (LED heartbeat, NKO update ripple, loading wave, optional LCD waveform). The base SPEC `06_DESIGN_SYSTEM_SKEUOMORPHIC.md` §1 (Filosofi Desain) and Animation Patterns section did not include this. ADR wins. `intel/decisions.md` DEC-003 and `intel/requirements.md` REQ-pulse-heartbeat-animation record the addition; `intel/constraints.md` CONSTR-design-philosophy notes it.

[INFO] Auto-resolved: ADR DEC-004/DEC-005/DEC-008 supersede AI feature roadmap in 07_AI_INTEGRATION.md and 09_DEVELOPMENT_ROADMAP.md
  Note: UPDATE-001 §2 adds two new MVP AI features (Inline Help #7, Comparative Analysis #8) and rewrites the Fase 5 deliverable list. Base sources `07_AI_INTEGRATION.md` §8 (Roadmap AI Features table) and `09_DEVELOPMENT_ROADMAP.md` §7 (Fase 5 Deliverable) listed only 6 AI features and a smaller deliverable set. ADR wins. `intel/decisions.md` DEC-004/DEC-005/DEC-008 carry the locked positions; `intel/requirements.md` REQ-ai-inline-help and REQ-ai-comparative-analysis carry the locked specs; `intel/context.md` §11.7 carries the post-ADR Fase 5 deliverable list verbatim with the two new items inserted.

[INFO] Auto-resolved: ADR DEC-006 adds new table `ai_inline_help` to the data model
  Note: UPDATE-001 §2.1 introduces `ai_inline_help` (UUID PK, `indikator_id` UNIQUE FK to `indikator(id) ON DELETE CASCADE`, content fields, `generated_by_model`, `generated_at`, `expires_at`, audit columns) plus index `idx_ai_inline_help_indikator`. Base `03_DATA_MODEL.md` §3.9 only listed `ai_conversation`, `ai_message`, `pedoman_chunk`, `ai_suggestion_log`. ADR wins. `intel/constraints.md` CONSTR-data-model-core-tables and `intel/decisions.md` DEC-006 capture the new table.

[INFO] Auto-resolved: ADR DEC-007 adds new API endpoints for AI features 7 & 8
  Note: UPDATE-001 §2.1/§2.2 adds `GET /api/v1/ai/inline-help/{indikator_id}`, `POST /api/v1/ai/inline-help/{indikator_id}/regenerate`, and `POST /api/v1/ai/comparative-analysis`. Base `04_API_SPEC.md` §11 only enumerated `/ai/draft-justification`, `/ai/draft-recommendation`, `/ai/anomaly-check`, `/ai/summarize-periode`, `/ai/chat`, `/ai/generate-action-plan`. ADR wins. `intel/decisions.md` DEC-007 and `intel/requirements.md` REQ-ai-inline-help / REQ-ai-comparative-analysis carry the new endpoint contract.

[INFO] Auto-resolved: ADR DEC-009 supersedes AI cost estimate in 07_AI_INTEGRATION.md
  Note: UPDATE-001 §2.5 sets total monthly AI estimate at ~$3.15 (~Rp 50.000) including the two new features. Base `07_AI_INTEGRATION.md` §2 had ~$3-5/month with a different breakdown (no inline-help, no comparative-analysis). ADR wins. `intel/decisions.md` DEC-009 and `intel/constraints.md` CONSTR-ai-cost-budget reflect the updated number.

[INFO] Auto-resolved: ADR DEC-010 re-locks pre-existing decisions from the base blueprint
  Note: UPDATE-001 §3.2 re-locks: no evidence file upload; dynamic JSONB schema for ML rubric; HCR deferred to Fase 6; skeuomorphic dark theme default; AI routing Gemini Flash + Claude Sonnet; tech stack FastAPI + React 18 + PostgreSQL 16 + Docker Compose. These were already implied/stated across `02_FUNCTIONAL_SPEC.md` §3 and §5, `03_DATA_MODEL.md` §3.3, `06_DESIGN_SYSTEM_SKEUOMORPHIC.md` §1, `07_AI_INTEGRATION.md` §2, `08_DEPLOYMENT.md` §1, `09_DEVELOPMENT_ROADMAP.md` §8, `04_API_SPEC.md` §16, `README.md`. The ADR upgrades them to LOCKED status. `intel/decisions.md` DEC-010 records the lock.

[INFO] Auto-resolved: ADR DEC-011 deferred items kept as informational, not locked
  Note: UPDATE-001 §3.3 explicitly DEFERS final logo, SSL strategy, OpenRouter API key provisioning, and external integrations (Navitas, SAP, etc.) — Phase 2+. These match open questions in `10_CLAUDE_CODE_INSTRUCTIONS.md` §8 (items 1, 2, 7 partially, 6). Recorded as non-locked in `intel/decisions.md` DEC-011 and noted in `intel/context.md` §10.5. No conflict — clarification.

[INFO] Cross-ref cycles detected in DOC navigation graph (informational only — synthesis is per-doc, not transitive)
  Note: Several docs in the blueprint set form bidirectional "Selanjutnya" navigation cycles in their `cross_refs`:
    - 2-cycle: `05_FRONTEND_ARCHITECTURE.md ↔ 08_DEPLOYMENT.md` (05 refs 08, 08 refs 05).
    - 5-cycle: `02_FUNCTIONAL_SPEC.md → 07_AI_INTEGRATION.md → 08_DEPLOYMENT.md → 09_DEVELOPMENT_ROADMAP.md → 01_DOMAIN_MODEL.md → 02_FUNCTIONAL_SPEC.md`.
    - README.md and 10_CLAUDE_CODE_INSTRUCTIONS.md fan out to all of 01–10 (no cycle).
  These are documentation back-links ("Selanjutnya: X" / "See: Y"), not authoritative supersedes claims. Synthesis here is per-doc extraction with no transitive merging, so the loops do not produce garbage output. The locked ADR (UPDATE-001) explicitly establishes precedence over every doc in the cycle, which further insulates the synthesized intel from cycle-induced ambiguity. Recording as INFO rather than BLOCKER per the substantive intent of the cycle-detection rule.

[INFO] Auto-resolved: doc UI-copy adjustments in UPDATE-001 §1.6 are advisory, not locked
  Note: UPDATE-001 §1.6 lists optional UI label tweaks ("Dashboard NKO" → "Pulse Monitor", "Update terakhir" → "Pulse terakhir", "Sistem berjalan normal" → "Pulse stabil", "Refresh data" → "Sync pulse") flagged as opsional with the explicit rule "Jangan over-do". These are NOT locked decisions — recorded as advisory only in synthesis (no requirement created in `requirements.md`). The roadmapper / gsd-roadmapper may pick them up as soft suggestions.

[INFO] Auto-resolved: 09_DEVELOPMENT_ROADMAP.md `09_DEVELOPMENT_ROADMAP.md` §7 Fase 5 deliverable list is replaced by ADR-updated list
  Note: The ADR §2.4 explicitly hands a replacement deliverable list for Fase 5; `intel/context.md` §11.7 carries the post-ADR list verbatim. The original list (without inline-help / comparative-analysis) is therefore superseded.

[INFO] Auto-resolved: header and `X-Title` value sent to OpenRouter must reflect post-rebrand name
  Note: `07_AI_INTEGRATION.md` §5 OpenRouter client wrapper sets `HTTP-Referer: https://siskonkin.tenayan.local` and `X-Title: SISKONKIN`. Per ADR DEC-001/DEC-002 these become `https://pulse.tenayan.local` and `PULSE`. Recorded in `intel/constraints.md` CONSTR-llm-routing and `intel/requirements.md` REQ-ai-pii-masking.

[INFO] Auto-resolved: roadmap `09_DEVELOPMENT_ROADMAP.md` listed RAG chat under Fase 5 but ADR §2.3 reorganises features into MVP+Phase 2 split
  Note: Source `09_DEVELOPMENT_ROADMAP.md` §7 sub-fase 5b lists RAG chat / Smart Summary / Action Plan SMART. The ADR §2.3 explicitly puts AI Inline Help and Comparative Analysis at Fase 5, and keeps RAG chat / summary / action-plan at Phase 2. The two views do not contradict in MVP scope (5b was already opsional in source); harmonised via `intel/context.md` §11.7 (post-ADR Fase 5 list) plus `intel/requirements.md` Section L (REQ-ai-rag-chat / REQ-ai-summary-periode / REQ-ai-action-plan-generator) tagged Phase 2. Recorded for transparency.

[INFO] Roadmap-phase content is preserved verbatim in `intel/context.md` §11 for downstream consumption
  Note: Per the orchestrator's instruction, the phase breakdown from `09_DEVELOPMENT_ROADMAP.md` is appended verbatim into `.planning/intel/context.md` §11 so that `gsd-roadmapper` can lift the phasing without re-reading the source. The synthesizer did NOT generate `ROADMAP.md`, `PROJECT.md`, `REQUIREMENTS.md`, or `STATE.md` — those are downstream responsibilities.
