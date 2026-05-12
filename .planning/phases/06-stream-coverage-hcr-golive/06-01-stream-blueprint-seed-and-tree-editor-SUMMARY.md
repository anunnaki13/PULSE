---
status: complete
phase: 06-stream-coverage-hcr-golive
plan: 01
completed_at: "2026-05-12T13:35:00.000+07:00"
---

# Plan 06-01 Summary - Stream Blueprint Seed And Tree Editor

## Outcome

The remaining Pilar II maturity streams now have structured JSONB blueprint seeds, indikator rows, and bidang applicability mappings. They can be surfaced through the existing assessment workflow without adding per-stream tables.

## Implemented

- Added `backend/app/seed/stream_coverage.py`.
- Added 12 remaining maturity stream seeds:
  - `RELIABILITY`
  - `EFFICIENCY`
  - `WPC`
  - `OPERATION`
  - `ENERGI_PRIMER`
  - `LCCM`
  - `SCM`
  - `LINGKUNGAN`
  - `K3`
  - `KEAMANAN`
  - `BENDUNGAN`
  - `DPP`
- Each stream has:
  - `structure.type = maturity_level`
  - `unit = level`
  - two placeholder areas with L0-L4 criteria
  - `placeholder = true` so dummy criteria are clearly marked
- Added matching zero-weight indikator rows under Perspektif II.
- Added 32 initial `indikator_applicable_bidang` mappings.
- Extended NKO primitive calculator so generic rubric streams use maturity payload averaging, not KPI target/realisasi scoring.

## Verification

- Backend compile passed.
- `pytest -q tests/test_nko_calculator.py` passed: 5/5.
- Live backend rebuild passed.
- `python -m app.seed` in `pulse-backend` passed.
- Idempotency live check:
  - `ml_streams = 16`
  - `indikator_applicable_bidang mappings = 76`
  - repeated seed kept the same counts.
- Master API smoke:
  - `GET /api/v1/ml-stream?page_size=50` returned `total=16`.
  - `RELIABILITY` present.
- Assessment API smoke:
  - Ran `create_sessions_for_periode` for active self-assessment periode `c772833d-d0dc-4006-a05c-39ce3b8f008f`.
  - Created 32 new sessions.
  - `GET /api/v1/assessment/sessions?...` returned 66 sessions with all new stream codes visible.

## Notes

- Bobot is intentionally `0.00` for newly seeded placeholder indikator. Final contribution weights and full formula normalization are handled in Plan 06-03.
- The current master stream UI already renders nested `ml_stream.structure`, so no new tree editor was required in this slice.
