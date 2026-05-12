---
status: planned
phase: 04-compliance-tracker-reports
plan: 02
requirements_addressed:
  - REQ-compliance-laporan-tracker
  - REQ-compliance-komponen
  - REQ-compliance-summary
---

# Plan 04-02 - Compliance Frontend Dashboard

## Objective

Add a usable compliance tracker screen for BID CPF/admin users and surface persisted compliance deduction on the executive dashboard.

## Scope

- Add frontend API hooks for compliance definitions, submissions, components, and summary.
- Add `/compliance` route with report tracker form/table and component realization form/table.
- Add navigation entry for admins/super admins.
- Show summary cards: total pengurang, cap, late reports, invalid reports, and component deduction.
- Keep Bahasa Indonesia labels and control-room visual style.

## Verification

- TypeScript, Vitest, Vite build.
- Browser smoke for `/compliance`.
- Confirm dashboard NKO reflects persisted compliance summary after a submission.
