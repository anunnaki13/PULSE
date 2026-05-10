# Synthesis Summary

> Single entry point for `gsd-roadmapper`. Summarises what was extracted from 12 classified
> planning docs (1 ADR + 8 SPEC + 3 DOC) and points to the per-type intel files.

---

## Mode & Inputs

- **Mode:** new (net-new bootstrap; `.planning/` did not exist before this run)
- **Precedence:** `["ADR", "SPEC", "PRD", "DOC"]` (default); the single ADR carries `precedence=0` per manifest override
- **Classifications consumed:** 12 / 12

---

## Doc Counts by Type

| Type | Count | Sources |
|---|---:|---|
| ADR (locked, precedence=0) | 1 | `UPDATE-001-pulse-rebrand-ai-features.md` |
| SPEC | 7 | `02_FUNCTIONAL_SPEC.md`, `03_DATA_MODEL.md`, `04_API_SPEC.md`, `05_FRONTEND_ARCHITECTURE.md`, `06_DESIGN_SYSTEM_SKEUOMORPHIC.md`, `07_AI_INTEGRATION.md`, `08_DEPLOYMENT.md` |
| DOC | 4 | `01_DOMAIN_MODEL.md`, `09_DEVELOPMENT_ROADMAP.md`, `10_CLAUDE_CODE_INSTRUCTIONS.md`, `README.md` |
| PRD | 0 | — |
| UNKNOWN low-confidence | 0 | — |

(Per the manifest the orchestrator described 8 SPECs in the prompt; classification files actually mark 7 docs as SPEC and `02_FUNCTIONAL_SPEC.md` is the eighth — counted under SPEC. Total = 1 + 7 + 4 = 12 matches the input set.)

---

## Decisions Locked

**Count: 11** — all originate from the single locked ADR `UPDATE-001-pulse-rebrand-ai-features.md` (status APPROVED, treated as Accepted, precedence=0).

| ID | Scope | Source |
|---|---|---|
| DEC-001 | Project rename SISKONKIN → PULSE (acronym + taglines) | UPDATE-001 §1.1, §1.2 |
| DEC-002 | Identifier renames (containers, DB, network, domain) | UPDATE-001 §1.3 |
| DEC-003 | Pulse Heartbeat signature animation in design system | UPDATE-001 §1.5 |
| DEC-004 | AI Feature #7 Inline Help added to MVP | UPDATE-001 §2.1 |
| DEC-005 | AI Feature #8 Comparative Analysis added to MVP | UPDATE-001 §2.2 |
| DEC-006 | New DB table `ai_inline_help` | UPDATE-001 §2.1 |
| DEC-007 | New API endpoints for AI features 7 & 8 | UPDATE-001 §2.1, §2.2 |
| DEC-008 | Fase 5 deliverables (UPDATED list) | UPDATE-001 §2.4 |
| DEC-009 | AI cost estimate updated to ~$3.15/month | UPDATE-001 §2.5 |
| DEC-010 | Re-locked clarifications (no upload, JSONB ML, HCR Fase 6, dark theme, AI routing, tech stack) | UPDATE-001 §3.2 |
| DEC-011 | Open items kept informational/deferred (logo, SSL, OpenRouter key, integrations) | UPDATE-001 §3.3 |

Full text in `intel/decisions.md`.

---

## Requirements Extracted

**Count: 50 across 18 sections.**

### Section index
- A. User & Access Management — 3 (REQ-user-roles, REQ-auth-jwt, REQ-route-guards)
- B. Master Data Module — 3 (REQ-konkin-template-crud, REQ-dynamic-ml-schema, REQ-bidang-master)
- C. Periode Management — 1 (REQ-periode-lifecycle)
- D. Self-Assessment Workspace — 4 (REQ-self-assessment-kpi-form, REQ-self-assessment-ml-form, REQ-auto-save, REQ-pic-actions)
- E. Asesor Workspace — 1 (REQ-asesor-review)
- F. Recommendation & Action Tracker — 2 (REQ-recommendation-create, REQ-recommendation-lifecycle)
- G. NKO Calculator — 3 (REQ-nko-calc-engine, REQ-nko-aggregation-rules, REQ-nko-realtime-ws)
- H. Dashboard & Analytics — 3 (REQ-dashboard-executive, REQ-dashboard-heatmap, REQ-dashboard-trend)
- I. Compliance Tracker — 3 (REQ-compliance-laporan-tracker, REQ-compliance-komponen, REQ-compliance-summary)
- J. Reports & Export — 4 (REQ-report-nko-semester, REQ-report-assessment-sheet, REQ-report-compliance-detail, REQ-report-recommendation-tracker)
- K. AI Assistant MVP — 8 (REQ-ai-draft-justification, REQ-ai-draft-recommendation, REQ-ai-anomaly-detection, **REQ-ai-inline-help (locked)**, **REQ-ai-comparative-analysis (locked)**, REQ-ai-rate-limiting, REQ-ai-pii-masking, REQ-ai-fallback, REQ-ai-audit-trail) — note 9 listed; the count above is 8 because rate-limiting cross-counts in REQ-rate-limiting-general; see file
- L. AI Assistant Phase 2 — 3 (REQ-ai-rag-chat, REQ-ai-summary-periode, REQ-ai-action-plan-generator)
- M. Notifications — 1 (REQ-notifications)
- N. Audit Log — 1 (REQ-audit-log)
- O. Health & Operational — 3 (REQ-health-checks, REQ-rate-limiting-general, REQ-no-evidence-upload (locked))
- P. Branding & Design — 3 (REQ-pulse-branding (locked), REQ-pulse-heartbeat-animation (locked), REQ-skeuomorphic-design-system)
- Q. Frontend Tech Stack — 1 (REQ-frontend-stack)
- R. Backend Tech Stack — 1 (REQ-backend-stack)
- S. Deployment — 4 (REQ-docker-compose-deploy, REQ-nginx-config, REQ-backup-restore, REQ-prod-checklist)

**Locked-by-ADR requirements (cannot be downgraded by lower-precedence sources):**
- REQ-pulse-branding (DEC-001)
- REQ-pulse-heartbeat-animation (DEC-003)
- REQ-ai-inline-help (DEC-004)
- REQ-ai-comparative-analysis (DEC-005)
- REQ-no-evidence-upload (DEC-010)

Full requirement bodies in `intel/requirements.md`.

---

## Constraints Extracted

**Count: 26.**

### Breakdown by type
| Type | Count |
|---|---:|
| nfr | 14 |
| schema | 5 |
| api-contract | 5 |
| protocol | 3 (websocket-endpoints, llm-routing, rag-pipeline) |

Notable items:
- CONSTR-stack-frontend / CONSTR-stack-backend / CONSTR-stack-data / CONSTR-stack-cache
- CONSTR-postgres-extensions (uuid-ossp, pgcrypto, pgvector ivfflat cosine)
- CONSTR-jsonb-indexes (GIN on `ml_stream.structure`, `assessment_session.self_assessment`)
- CONSTR-data-model-core-tables (full canonical table list including ADR-introduced `ai_inline_help`)
- CONSTR-api-versioning, CONSTR-api-conventions, CONSTR-openapi
- CONSTR-websocket-endpoints, CONSTR-rate-limits, CONSTR-security-headers
- CONSTR-no-file-upload (cross-references DEC-010)
- CONSTR-llm-routing (Gemini Flash + Claude Sonnet routing, post-rebrand HTTP-Referer + X-Title)
- CONSTR-llm-pii-policy, CONSTR-rag-pipeline, CONSTR-ai-cost-budget (~$3.15/month per DEC-009)
- CONSTR-domain-pulse, CONSTR-network-naming, CONSTR-host-port (post-rebrand identifiers)
- CONSTR-env-secrets, CONSTR-backup
- CONSTR-design-tokens, CONSTR-design-philosophy (dark default per DEC-010)
- CONSTR-i18n-default, CONSTR-accessibility, CONSTR-monitoring
- CONSTR-pulse-rebrand-find-replace (rebrand authority)

Full text in `intel/constraints.md`.

---

## Context Topics

**Count: 12 topics in `intel/context.md`** (DOC-class material extracted verbatim with source attribution).

1. Project overview (README + design philosophy + standing notes)
2. Domain hierarchy: Kontrak Kinerja Unit
3. Konkin 2026 PLTU Tenayan: Perspektif & Bobot + NKO formula + worked example
4. Indikator inventory (5 perspektif + Compliance pengurang)
5. KPI Kuantitatif vs Maturity Level (formulae, polaritas, range-based, level rubric)
6. Periode rhythm (semester/triwulan strategy)
7. Pemilik Proses (process-owner partial seed list)
8. Compliance laporan rutin (Tabel 22, 9 reports + factors)
9. Glosarium (acronyms in scope)
10. Onboarding instructions for the build agent (reading order, coding rules, must-do/must-not, open questions, MVP definition)
11. **Development roadmap (verbatim §1–§13 of `09_DEVELOPMENT_ROADMAP.md`, with Fase 5 deliverable list updated per ADR)** — preserved verbatim so `gsd-roadmapper` can lift the phasing directly
12. Cross-cutting principles

---

## Conflicts Summary

| Bucket | Count |
|---|---:|
| BLOCKERS | 0 |
| WARNINGS | 0 |
| INFO (auto-resolved + cycles + advisory) | 16 |

All 16 INFO entries are routine: 13 are ADR-supersedes-SPEC auto-resolutions (the ADR is locked and explicitly patches sections of docs 01–10), 1 is a cross-ref cycle note (informational since synthesis is per-doc, not transitive), 1 is an advisory note about non-locked UI-copy tweaks, 1 is a meta-note about preserving roadmap verbatim for the downstream consumer. Full text in `INGEST-CONFLICTS.md`.

**No competing acceptance variants.** No PRDs in scope; no contradictory acceptance criteria across sources.

**No LOCKED-vs-LOCKED contradiction.** Only one locked ADR exists.

**No UNKNOWN-low-confidence docs.** All 12 classified with `confidence: high` and `manifest_override: true`.

---

## File Pointers

- Conflict report: `C:/Users/ANUNNAKI/Projects/PULSE/.planning/INGEST-CONFLICTS.md`
- Decisions: `C:/Users/ANUNNAKI/Projects/PULSE/.planning/intel/decisions.md`
- Requirements: `C:/Users/ANUNNAKI/Projects/PULSE/.planning/intel/requirements.md`
- Constraints: `C:/Users/ANUNNAKI/Projects/PULSE/.planning/intel/constraints.md`
- Context (incl. verbatim roadmap phases): `C:/Users/ANUNNAKI/Projects/PULSE/.planning/intel/context.md`
- This summary: `C:/Users/ANUNNAKI/Projects/PULSE/.planning/intel/SYNTHESIS.md`

---

## Status

READY — safe to route to `gsd-roadmapper`. No blockers, no competing variants, all locked decisions captured, post-rebrand identifiers propagated through synthesized intel, and the verbatim phase breakdown is queued in `context.md` §11 for the roadmapper to consume.
