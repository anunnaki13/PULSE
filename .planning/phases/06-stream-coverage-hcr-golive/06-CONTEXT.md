---
phase: 06-stream-coverage-hcr-golive
status: planned
created_at: "2026-05-12T12:15:00.000+07:00"
---

# Phase 06 Context - Stream Coverage Lengkap + HCR + Go-Live

## Objective

Bring PULSE from AI-enabled MVP to full Konkin 2026 operational readiness: all remaining maturity streams, HCR/OCR, sub-indikator formulas, Pedoman Konkin RAG follow-through, and go-live checklist.

## Source Context

- Phase 6 roadmap success criteria in `ROADMAP.md`.
- Stream complexity notes in `intel/context.md`:
  - Each maturity stream has its own area/sub-area criteria and units.
  - Aggregate pairs use 50/50 fallback rules when one component is not assessed.
  - HCR/OCR/Pra Karya require weighted average normalization when components are missing.
- Phase 5 UAT deferred optional Phase 5b items here:
  - Pedoman Konkin RAG chat.
  - Summary periode.
  - SMART action-plan generator.

## Constraints

- Preserve JSONB dynamic stream schema; do not create one table per stream.
- Preserve no evidence file upload policy.
- Respect existing role boundaries and audit middleware.
- Keep dummy/sample data only where real rubric detail is not yet available; mark it clearly as seed placeholder.
- Do not weaken Nginx rate limits or auth/CSRF controls to make UAT easier.

## Planning Split

Phase 6 is split into five executable plans:

1. `06-01-stream-blueprint-seed-and-tree-editor`
2. `06-02-hcr-ocr-assessment-coverage`
3. `06-03-subindikator-formula-coverage-nko`
4. `06-04-pedoman-rag-summary-action-plan`
5. `06-05-production-hardening-final-uat`
