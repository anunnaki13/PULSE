---
status: complete
phase: 04-compliance-tracker-reports
plan: 03
completed_at: "2026-05-12T03:25:00.000+07:00"
requirements_addressed:
  - REQ-report-nko-semester
  - REQ-report-assessment-sheet
  - REQ-report-compliance-detail
  - REQ-report-recommendation-tracker
---

# Summary 04-03 - Report Export Endpoints

## Delivered

- Added `/api/v1/reports/*` routes:
  - `GET /reports/nko-semester?periode_id=&format=pdf|excel|word`
  - `GET /reports/assessment-sheet?periode_id=&format=pdf|excel|word`
  - `GET /reports/compliance-detail?periode_id=&format=pdf|excel|word`
  - `GET /reports/recommendation-tracker?periode_id=&format=pdf|excel|word`
- Added role gates for `super_admin`, `admin_unit`, `manajer_unit`, and `viewer`.
- Added deterministic renderers:
  - CSV with UTF-8 BOM for Excel-compatible exports,
  - HTML `.doc` for Word-compatible exports,
  - minimal valid PDF for early NKO/report artifacts.
- Report data pulls from persisted periode, NKO snapshot, compliance summary, assessment sessions, and recommendation tracker.

## Verification

- `python3 -m compileall -q app` passed.
- `pytest -q tests/test_report_exports.py tests/test_compliance_summary.py tests/test_nko_calculator.py` passed: 12/12.
- Rebuilt `pulse-backend` and waited for Docker health.
- API smoke for active periode `d152b998-48e4-4d41-99fa-e1f901c7e2fe` passed:
  - `nko-semester` PDF returned 1377 bytes and valid `%PDF-1.4` header.
  - `nko-semester` CSV returned 567 bytes.
  - `nko-semester` Word-compatible doc returned 1302 bytes.
  - `assessment-sheet` CSV returned 90 bytes.
  - `compliance-detail` CSV returned 208 bytes.
  - `recommendation-tracker` CSV returned 96 bytes.
  - Download header confirmed: `content-disposition: attachment`.
