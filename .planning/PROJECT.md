# PROJECT — PULSE

> **PULSE** — **P**erformance & **U**nit **L**ive **S**coring **E**ngine
> Tagline (id): "Denyut Kinerja Pembangkit, Real-Time."
> Tagline (en, alt): "The Heartbeat of Power Performance."
> Tagline (formal): "Sistem Monitoring Kinerja Unit Pembangkit Real-Time PT PLN Nusantara Power."

---

## Core Value

PULSE adalah **kertas kerja digital + workflow asesmen** untuk Kontrak Kinerja Unit (Konkin) di PLTU Tenayan, PT PLN Nusantara Power. Sistem ini menggantikan workflow Excel (per-stream kertas kerja) dengan platform terstruktur, auditable, dan kolaboratif yang menghitung **NKO (Nilai Kinerja Organisasi) secara real-time** dan mengelola self-assessment, asesor review, rekomendasi, serta tindak lanjut compliance.

Referensi: **Peraturan Direksi PT PLN Nusantara Power Nomor 0019.P/DIR/2025** (17 Juli 2025) tentang Pedoman Penilaian Kontrak Kinerja Unit; dirancang untuk mengakomodasi Konkin 2026.

**Primary user persona:** Solo developer (Budi, technical lead CV Panda Global Teknologi) + Claude Code sebagai implementer. Built for PT PLN NP UP Tenayan internal use.

---

## Filosofi Desain (Locked)

1. **Bukan sistem manajemen evidence.** Sistem ini adalah kertas kerja digital + workflow asesmen, bukan document repository. Evidence tetap dikelola oleh PIC bidang masing-masing di sistem internal mereka.
2. **Setiap stream punya rubrik unik.** Sistem dirancang dengan **dynamic schema per stream** (JSONB) — bukan one-size-fits-all form.
3. **Self-assessment → Asesor → Feedback → Tindak Lanjut.** Alur konsisten di semua indikator (KPI Kuantitatif maupun Maturity Level).
4. **Triwulan sebagai irama monitoring, semester sebagai irama formal.** Konkin formal dinilai per semester; monitoring & koreksi arah dilakukan per triwulan.
5. **AI sebagai asisten, bukan pengganti asesor.** LLM membantu menulis rekomendasi, mendeteksi anomali, dan mempercepat self-assessment — keputusan tetap di manusia.

---

## Locked Decisions (ADR — UPDATE-001)

> Source: `UPDATE-001-pulse-rebrand-ai-features.md` (status APPROVED, precedence=0).
> These decisions cannot be re-decided downstream.

<decisions status="LOCKED" source="UPDATE-001-pulse-rebrand-ai-features.md" precedence="0">

### DEC-001 — Project rename SISKONKIN → PULSE
- **scope:** project naming, acronym, taglines
- **statement:** Application is officially renamed to **PULSE** (Performance & Unit Live Scoring Engine). Tagline: "Denyut Kinerja Pembangkit, Real-Time." Replaces every occurrence of `SISKONKIN`/`Siskonkin`/`siskonkin` across docs, code, configs, and infrastructure.

### DEC-002 — Identifier renames (containers, DB, network, domain)
- **scope:** code identifiers, infrastructure naming
- **statement:** Apply case-sensitive find-and-replace across the repo:
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

### DEC-003 — Pulse Heartbeat signature animation
- **scope:** design system, motion/animation patterns
- **statement:** Adopt **Pulse Heartbeat** as signature visual motion. LED indicators pulse 60–80 BPM equivalent saat sehat; faster saat alert. NKO Gauge ripple animation on snapshot update (300ms ease-out). Loading state = horizontal pulse wave (no generic spinner). CSS keyframe `pulse-heartbeat` defined.

### DEC-004 — AI Feature #7: Inline Help (Konteks Indikator) added to MVP
- **scope:** AI feature set, MVP scope, Fase 5 deliverables
- **statement:** Per-indikator AI Inline Help is MVP feature. Pre-computed and cached at indikator-creation time, regenerated on indikator structure change. Model: `google/gemini-2.5-flash`. Panel content: "Apa itu [indikator]?", Formula, Best practice industri, Indikator terkait, Kesalahan umum.

### DEC-005 — AI Feature #8: Comparative Analysis (Cross-Periode) added to MVP
- **scope:** AI feature set, MVP scope, Fase 5 deliverables
- **statement:** Cross-period comparative analysis ("Bandingkan dengan TW Lalu") is MVP feature. Backend pulls 2-period component data + 4-period historical trend, sends to LLM, caches result for 1 hour. Model: `google/gemini-2.5-flash`. Output: 3–5 sentence BI formal narrative, structured JSON.

### DEC-006 — New DB table `ai_inline_help`
- **scope:** data model
- **statement:** Add `ai_inline_help` table. Columns: `id UUID PK`, `indikator_id UUID FK indikator(id) ON DELETE CASCADE UNIQUE`, `apa_itu TEXT`, `formula_explanation TEXT`, `best_practice TEXT`, `common_pitfalls TEXT`, `related_indikator JSONB`, `generated_by_model VARCHAR(100)`, `generated_at TIMESTAMP WITH TIME ZONE`, `expires_at TIMESTAMP WITH TIME ZONE`, `created_at`, `updated_at`. Index: `idx_ai_inline_help_indikator ON ai_inline_help(indikator_id)`.

### DEC-007 — New API endpoints for AI features 7 & 8
- **scope:** API surface
- **statement:** Add to `/api/v1`:
  - `GET  /api/v1/ai/inline-help/{indikator_id}` — fetch cached help.
  - `POST /api/v1/ai/inline-help/{indikator_id}/regenerate` — admin: trigger regen.
  - `POST /api/v1/ai/comparative-analysis` — body `{indikator_id, period_a, period_b}`.

### DEC-008 — Fase 5 deliverables (UPDATED)
- **scope:** roadmap
- **statement:** Fase 5 deliverable list:
  - Setup OpenRouter client + routing
  - AI Suggestion Drawer component
  - Draft Justifikasi (PIC) — Gemini Flash
  - Draft Rekomendasi (Asesor) — Gemini Flash
  - Anomaly Detection (rule-based + LLM hybrid)
  - **AI Inline Help** untuk indikator (NEW — DEC-004)
  - **Comparative Analysis** cross-periode (NEW — DEC-005)
  - AI Suggestion audit log (`ai_suggestion_log`)
  - Rate limiting per user (20/min)
  - Fallback graceful jika OpenRouter down

### DEC-009 — AI cost estimate (UPDATED)
- **scope:** ops/finance
- **statement:** Total monthly AI cost estimate for MVP scale at UP Tenayan: **~$3.15/month (~Rp 50.000)**. Breakdown:
  - Draft justifikasi: 200/bln × ~$0.50
  - Draft rekomendasi: 50/bln × ~$0.20
  - Anomaly check: 100/bln × ~$0.30
  - Chat RAG: 100/bln × ~$1.50
  - Summary periode: 4/bln × ~$0.30
  - Embedding (RAG): one-time + 100/bln × ~$0.05
  - AI Inline Help: 62 indikator cached × ~$0.10
  - Comparative Analysis: 50/bln × ~$0.20

### DEC-010 — Locked clarifications (re-affirmations from base blueprint)
- **scope:** scope guards
- **statement:** The following decisions are re-locked by this ADR:
  - **No evidence file upload.** Only external URL (`link_eviden`) recorded.
  - **Dynamic JSONB schema for maturity-level rubrics** (`ml_stream.structure JSONB`).
  - **HCR deferred to Fase 6.** Schema reserved; full implementation only after other streams stable.
  - **UI: skeuomorphic dark theme (control-room digital).** Light theme variant only.
  - **AI routing: Gemini 2.5 Flash for routine + Claude Sonnet 4 for complex.** Via OpenRouter.
  - **Tech stack: FastAPI + React 18 + PostgreSQL 16 + Docker Compose.**

### DEC-011 — Open items NOT yet decided (informational, not locked)
- **scope:** deferred decisions
- **statement:** UNRESOLVED in this ADR and not to be locked downstream:
  - Final logo (placeholder for now).
  - SSL certificate strategy (decide at deploy time).
  - OpenRouter API key provisioning (Budi handles directly).
  - External integrations (Navitas, SAP, etc.) — Phase 2+.

</decisions>

---

## Tech Stack (locked via CONSTR-stack-*)

| Layer | Choice |
|------|--------|
| Frontend | React 18 + Vite + TypeScript; TanStack Query v5; Zustand; React Hook Form + Zod; React Router v6; Tailwind + skeuomorphic tokens; Recharts/ECharts; Motion (framer-motion) |
| Backend | FastAPI on Python 3.11; gunicorn 4 workers + UvicornWorker; Pydantic v2; SQLAlchemy 2.x async + asyncpg; Alembic |
| Database | PostgreSQL 16+ (`pgvector/pgvector:pg16`); extensions `uuid-ossp`, `pgcrypto`, `vector`; UUID PKs; JSONB for dynamic schemas |
| Cache/Queue | Redis 7 alpine; `maxmemory 256mb`, `maxmemory-policy allkeys-lru` |
| Reverse proxy | Nginx; published on host port `3399`; security headers + WebSocket upgrade + rate-limit zones |
| LLM | OpenRouter only — `google/gemini-2.5-flash` (routine) + `anthropic/claude-sonnet-4` (complex) + `openai/text-embedding-3-small` (embeddings) |
| Deployment | Docker Compose on single VPS; domain `pulse.tenayan.local` |

---

## Domain Snapshot (Konkin 2026 PLTU Tenayan)

```
Kontrak Kinerja Unit (per tahun)
└── Periode (Semester 1, Semester 2)
    └── Perspektif (5 Pilar BUMN + Compliance pengurang)
        └── Indikator Kinerja Utama (KPI)
            └── Sub-Indikator / Stream Maturity Level
                └── Area / Sub-Area
                    └── Kriteria Level 0–4
```

**Bobot Pilar (Konkin 2026):**

| Kode | Perspektif | Bobot |
|------|-----------|------:|
| I | Economic & Social Value | 46.00 |
| II | Model Business Innovation | 25.00 |
| III | Technology Leadership | 6.00 |
| IV | Energize Investment | 8.00 |
| V | Unleash Talent | 15.00 |
| VI | Compliance | Max −10 (pengurang) |

**Formula:** `NKO = Σ(Pilar I..V) − Pengurang Compliance`

---

## Constraints (Critical Subset)

- **No file upload** for evidence — `link_eviden` is text/URL only (DEC-010 / CONSTR-no-file-upload).
- **Dynamic ML schema** — `ml_stream.structure JSONB` with GIN index (CONSTR-jsonb-indexes).
- **All PKs are UUID** (CONSTR-id-uuid).
- **Default UI language: Bahasa Indonesia** (CONSTR-i18n-default).
- **Dark theme default**, skeuomorphic control-room aesthetic (CONSTR-design-philosophy).
- **PII masking** before any LLM call (CONSTR-llm-pii-policy): block NIP, personal email, audit-in-progress data, exact vendor names.
- **AI cost budget:** ~$3.15/month (DEC-009 / CONSTR-ai-cost-budget).
- **HCR deferred to Fase 6** (DEC-010).

---

## Source Documents

- ADR (locked): `UPDATE-001-pulse-rebrand-ai-features.md`
- SPEC: `02_FUNCTIONAL_SPEC.md`, `03_DATA_MODEL.md`, `04_API_SPEC.md`, `05_FRONTEND_ARCHITECTURE.md`, `06_DESIGN_SYSTEM_SKEUOMORPHIC.md`, `07_AI_INTEGRATION.md`, `08_DEPLOYMENT.md`
- DOC: `01_DOMAIN_MODEL.md`, `09_DEVELOPMENT_ROADMAP.md`, `10_CLAUDE_CODE_INSTRUCTIONS.md`, `README.md`

Synthesised intel (single entry point): `.planning/intel/SYNTHESIS.md`.

---

## Workflow Context

- **Solo developer + Claude Code.** No team coordination, no sprint ceremonies.
- **Builder:** Claude Code follows reading order in `10_CLAUDE_CODE_INSTRUCTIONS.md` §5–§7.
- **Visionary/PO:** Budi (technical lead).
- **Operational client:** PT PLN Nusantara Power UP Tenayan.
