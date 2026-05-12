---
status: complete
phase: 06-stream-coverage-hcr-golive
plan: 02
completed_at: "2026-05-12T13:50:00.000+07:00"
---

# Plan 06-02 Summary - HCR OCR Assessment Coverage

## Outcome

HCR and OCR now have dynamic maturity stream coverage through the same JSONB rubric workflow as other maturity streams. OCR includes explicit OWM weighting metadata.

## Implemented

- Added `backend/app/seed/hcr_ocr.py`.
- Added `HCR` stream under Perspektif V with 7 HCR areas:
  - Strategic Workforce Planning
  - Talent Acquisition
  - Talent Management & Development
  - Performance Management
  - Reward & Recognition
  - Industrial Relation
  - HC Operations
- Added `OCR` stream under Perspektif V with 6 OCR areas.
- Added OWM sub-area weights in OCR:
  - `OCR-OWM-01`: `0.55`
  - `OCR-OWM-02`: `0.45`
- Added zero-weight placeholder indikator rows for HCR/OCR pending final weighting in Plan 06-03.
- Added HCR/OCR applicability mappings for `BID_HTD` and `BID_HSC`.
- Extended maturity calculation to use weighted average when payload items include `weight`.
- Extended frontend assessment payload generation to preserve optional `weight` metadata from `ml_stream.structure`.

## Verification

- Backend compile passed.
- `pytest -q tests/test_nko_calculator.py` passed: 6/6.
- Frontend `pnpm build` passed.
- Frontend focused tests passed: 12/12.
- Rebuilt `pulse-backend` and `pulse-frontend`; stack health passed.
- Live seed passed:
  - `hcr_ocr: ensured 2 streams and 4 applicability mappings`
  - `HCR` has 7 areas.
  - `OCR` has 6 areas.
  - OCR OWM weights are `[0.55, 0.45]`.
- Existing self-assessment periode `c772833d-d0dc-4006-a05c-39ce3b8f008f` received 4 new HCR/OCR sessions.
- Assessment API smoke returned `total=70`, `hasHCR=True`, `hasOCR=True`.

## Notes

- HCR/OCR criteria are placeholder/dummy rubric text and are explicitly marked through the stream structure. Final domain-specific rubric refinement remains part of Phase 6 data completion.
- Bobot remains `0.00` until Plan 06-03 assigns final sub-indikator and pilar contribution coverage.
