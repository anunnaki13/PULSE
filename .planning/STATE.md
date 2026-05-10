# STATE — PULSE

> Project memory. Updated as work progresses through phases and plans.

---

## Project Reference

- **Name:** PULSE — Performance & Unit Live Scoring Engine
- **Core Value:** Kertas kerja digital + workflow asesmen real-time NKO untuk Kontrak Kinerja Unit di PLTU Tenayan, PT PLN Nusantara Power. Replaces Excel-based per-stream kertas kerja with structured, auditable, collaborative platform.
- **Current Focus:** Bootstrap Phase 1 — Foundation (Master Data + Auth)
- **Reference Doc:** Peraturan Direksi PT PLN Nusantara Power Nomor 0019.P/DIR/2025 (17 Juli 2025)

---

## Current Position

- **Current Phase:** Phase 1 — Foundation (Master Data + Auth)
- **Current Plan:** None (not yet planned — run `/gsd-plan-phase 1`)
- **Status:** Not started
- **Progress:** 0% — `[░░░░░░░░░░] 0/6 phases complete`

---

## Performance Metrics

- **Total v1 Requirements:** 50 (across 18 sections A–S)
- **ADR-Locked Requirements:** 5 (REQ-pulse-branding, REQ-pulse-heartbeat-animation, REQ-ai-inline-help, REQ-ai-comparative-analysis, REQ-no-evidence-upload)
- **Total Phases:** 6 (Phase 1 → Phase 6)
- **MVP Boundary:** End of Phase 3 (per source §5)
- **Coverage:** 50/50 v1 requirements mapped ✓
- **Plans Completed:** 0
- **Plans Remaining:** TBD (created per phase via `/gsd-plan-phase`)
- **Locked Decisions:** 11 (DEC-001 → DEC-011, all from ADR UPDATE-001, precedence=0)

---

## Accumulated Context

### Locked Decisions (cannot be re-decided)

See `PROJECT.md` `<decisions status="LOCKED">` block for full text. Summary:

- DEC-001: Project name = PULSE (Performance & Unit Live Scoring Engine)
- DEC-002: Identifier renames across containers, DB, network, domain, env, backups
- DEC-003: Pulse Heartbeat signature animation in design system
- DEC-004: AI Inline Help per indikator added to MVP
- DEC-005: Comparative Analysis cross-periode added to MVP
- DEC-006: New DB table `ai_inline_help`
- DEC-007: New API endpoints for AI features 7 & 8
- DEC-008: Phase 5 deliverables list (updated)
- DEC-009: AI cost ~$3.15/month (updated)
- DEC-010: Re-locked clarifications (no upload, JSONB ML, HCR Phase 6, dark theme, AI routing, tech stack)
- DEC-011: Open items deferred (logo, SSL, OpenRouter key, integrations)

### Tech Stack (Locked)

- **Frontend:** React 18 + Vite + TypeScript; TanStack Query v5 + Zustand; React Hook Form + Zod; Tailwind + skeuomorphic tokens; Recharts/ECharts; Motion (framer-motion)
- **Backend:** FastAPI on Python 3.11; gunicorn 4 workers + UvicornWorker; Pydantic v2; SQLAlchemy 2.x async + asyncpg; Alembic
- **Data:** PostgreSQL 16+ (`pgvector/pgvector:pg16`); UUID PKs; JSONB dynamic schemas; pgvector ivfflat cosine for embeddings
- **Cache:** Redis 7 alpine, 256mb LRU
- **Reverse Proxy:** Nginx on host port 3399; security headers + WS upgrade + rate-limit zones
- **LLM:** OpenRouter — `google/gemini-2.5-flash` (routine) + `anthropic/claude-sonnet-4` (complex)
- **Deploy:** Docker Compose, single VPS, domain `pulse.tenayan.local`

### Key Constraints (CONSTR-*)

- **No file upload** for evidence (CONSTR-no-file-upload, locked)
- **PII masking** required before LLM call (CONSTR-llm-pii-policy)
- **Rate limits:** 100 req/min mutating, 1000 dashboard read, 20 req/min AI
- **Default UI language:** Bahasa Indonesia (CONSTR-i18n-default)
- **Dark theme default**, skeuomorphic control-room aesthetic (CONSTR-design-philosophy)
- **AI cost budget:** ~$3.15/month (CONSTR-ai-cost-budget / DEC-009)

### Active Todos

None yet — created during phase planning.

### Blockers

None.

### Open Items (deferred — DEC-011, NOT locked)

- Final logo (placeholder for now)
- SSL certificate strategy (decide at deploy time, end of Phase 6)
- OpenRouter API key provisioning (Budi handles directly before Phase 5)
- External integrations Navitas/SAP — Phase 2+

---

## Session Continuity

### Last Session

- **Activity:** Project bootstrap from intel synthesis — `gsd-roadmapper` produced PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md from 12 classified planning docs (1 ADR + 7 SPEC + 4 DOC).
- **Date:** 2026-05-11
- **Outcome:** All four planning artifacts written. Ready for phase planning.
- **Next:** Run `/gsd-plan-phase 1` to decompose Phase 1 — Foundation into executable plans.

### Resume Pointer

```
Run: /gsd-plan-phase 1
Phase: Phase 1 — Foundation (Master Data + Auth)
Goal: User dapat login ke aplikasi PULSE dan menelusuri struktur master data Konkin 2026
      (perspektif → indikator → stream ML rubrik) di lingkungan Docker Compose yang sudah berjalan,
      dengan branding, design system, dan kebijakan no-evidence-upload sudah aktif sejak hari pertama.
Requirements in scope: REQ-user-roles, REQ-auth-jwt, REQ-route-guards, REQ-konkin-template-crud,
                       REQ-dynamic-ml-schema, REQ-bidang-master, REQ-frontend-stack, REQ-backend-stack,
                       REQ-docker-compose-deploy, REQ-nginx-config, REQ-pulse-branding,
                       REQ-pulse-heartbeat-animation, REQ-skeuomorphic-design-system,
                       REQ-health-checks, REQ-no-evidence-upload, REQ-backup-restore
```

### Key File Pointers

- Roadmap: `C:/Users/ANUNNAKI/Projects/PULSE/.planning/ROADMAP.md`
- Project: `C:/Users/ANUNNAKI/Projects/PULSE/.planning/PROJECT.md`
- Requirements: `C:/Users/ANUNNAKI/Projects/PULSE/.planning/REQUIREMENTS.md`
- Intel synthesis: `C:/Users/ANUNNAKI/Projects/PULSE/.planning/intel/SYNTHESIS.md`
- Conflict report: `C:/Users/ANUNNAKI/Projects/PULSE/.planning/INGEST-CONFLICTS.md`
- Per-type intel: `C:/Users/ANUNNAKI/Projects/PULSE/.planning/intel/decisions.md`, `requirements.md`, `constraints.md`, `context.md`
