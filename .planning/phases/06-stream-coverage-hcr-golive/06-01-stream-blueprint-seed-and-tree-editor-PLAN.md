---
status: planned
phase: 06-stream-coverage-hcr-golive
plan: 01
requirements_addressed:
  - REQ-prod-checklist
---

# Plan 06-01 - Stream Blueprint Seed And Tree Editor

## Objective

Seed and expose the remaining Pilar II maturity stream blueprints so PIC can self-assess every required stream through the existing JSONB rubric workflow.

## Scope

- Add/extend seed data for Batch 1-3 maturity streams:
  - Reliability Management
  - Efficiency Management
  - WPC Management
  - Operation Management
  - Energi Primer Batubara/Gas/BBM
  - LCCM
  - SCM
  - Manajemen Lingkungan
  - Manajemen K3
  - Manajemen Keamanan
  - Pengelolaan Bendungan
  - DPP
- Preserve stream-specific criteria, units, and applicability mapping per bidang.
- Add admin-facing JSONB tree editor support if current master UI cannot edit nested stream criteria safely.
- Keep placeholder/dummy criteria explicit where full rubric detail is unavailable.

## Verification

- Seed idempotency test.
- API test that all Batch 1-3 streams are returned with non-empty `structure.areas`.
- Browser smoke: admin can view/edit one stream, PIC can open a self-assessment form for a newly seeded stream.
