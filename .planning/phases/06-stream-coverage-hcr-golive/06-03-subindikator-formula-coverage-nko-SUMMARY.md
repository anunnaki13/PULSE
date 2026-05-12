---
status: complete
phase: 06-stream-coverage-hcr-golive
plan: 03
completed_at: "2026-05-12T14:05:00.000+07:00"
---

# Plan 06-03 Summary - Subindikator Formula Coverage NKO

## Outcome

Pilar I, II, IV, and V now have normalized indicator weighting coverage for the seeded Konkin 2026 structure. KPI formula families include positive, negative, range-based, maturity average, and weighted maturity average.

## Implemented

- Added `backend/app/seed/subindikator_coverage.py`.
- Seeded Pilar I coverage:
  - EAF, EFOR
  - BPP components: Biaya Har, Fisik Har, Biaya Adm, Biaya Kimia & Pelumas, Penghapusan ATTB
  - SDGs components: TJSL, Proper, ERM, Intensitas Emisi, Kepuasan Pelanggan, Umur Persediaan Batubara, Digitalisasi Pembayaran
- Normalized Pilar II seeded maturity stream weights to `100.00` total.
- Seeded Pilar IV coverage:
  - Disburse Investasi UP Tenayan
  - Disburse Investasi PLTU Tembilahan
  - PRK UP Tenayan
  - PRK Tembilahan
- Seeded Pilar V coverage:
  - HCR, OCR, SPKI, Budaya, Diseminasi, Biaya Kesehatan, LTIFR, Project Korporat
- Added range-based score handling in `backend/app/services/nko_calculator.py`.

## Verification

- Backend compile passed.
- `pytest -q tests/test_nko_calculator.py` passed: 6/6.
- Backend rebuild and stack health passed.
- Live seed passed:
  - `subindikator_coverage: ensured 39 indicators/weights and 48 mappings`
- Live DB checks:
  - Pilar I: 14 indicators, `bobot_sum=100.00`
  - Pilar II: 13 indicators, `bobot_sum=100.00`
  - Pilar IV: 4 indicators, `bobot_sum=100.00`
  - Pilar V: 8 indicators, `bobot_sum=100.00`
  - `indikator_applicable_bidang` mappings: 118
- Active self-assessment periode `c772833d-d0dc-4006-a05c-39ce3b8f008f` received 38 new sessions and now returns 108 sessions.
- Dashboard API remained healthy for the active periode.
- NKO semester PDF export returned 200 with `application/pdf`.

## Notes

- The seeded domain values are formula/weight placeholders where final Pedoman line-item detail is not yet available. They are structured so each stream/component can be refined without schema changes.
- NKO still falls back to demo snapshot until enough approved/overridden live sessions exist for a full live recomputation.
