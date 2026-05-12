---
status: planned
phase: 04-compliance-tracker-reports
plan: 03
requirements_addressed:
  - REQ-report-nko-semester
  - REQ-report-assessment-sheet
  - REQ-report-compliance-detail
  - REQ-report-recommendation-tracker
---

# Plan 04-03 - Report Export Endpoints

## Objective

Provide deterministic report export endpoints for NKO semester, assessment sheet, compliance detail, and recommendation tracker.

## Scope

- Add `/reports/*` routes with role-gated downloads.
- Generate clean CSV/HTML-compatible artifacts first, with Excel-friendly content types where needed.
- Include NKO snapshot, compliance summary, assessment session, and recommendation data.
- Keep endpoint format parameters compatible with roadmap (`pdf|excel|word`) even if early artifacts are simple generated documents.

## Verification

- API smoke each endpoint returns non-empty downloadable artifact.
- Generated Excel-targeted files open as spreadsheet-compatible CSV.
- Generated PDF/Word early artifacts contain the expected headings and numbers.
