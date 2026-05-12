---
status: complete
phase: 04-compliance-tracker-reports
plan: 02
completed_at: "2026-05-12T03:10:00.000+07:00"
requirements_addressed:
  - REQ-compliance-laporan-tracker
  - REQ-compliance-komponen
  - REQ-compliance-summary
---

# Summary 04-02 - Compliance Frontend Dashboard

## Delivered

- Added frontend compliance API hooks for definitions, submissions, components, summary, and upsert mutations.
- Added `/compliance` route for `super_admin` and `admin_unit`.
- Added admin navigation entry for Compliance.
- Built a Compliance Control Desk UI with:
  - active periode context,
  - summary cards for total pengurang, cap, late reports, invalid reports, report deduction, and component deduction,
  - routine report form for the 9 seeded report definitions,
  - component realization form for PACA/ICOFR/NAC/Critical Event,
  - detail pengurang and laporan tersimpan tables.
- Kept the dashboard linked to the same compliance-backed NKO snapshot through existing dashboard invalidation.

## Verification

- `pnpm build` passed.
- `pnpm test -- --run src/lib/dashboard-calculations.test.ts src/routes/ProtectedRoute.test.tsx` passed: 12/12.
- Rebuilt `pulse-frontend` and ran the stack with `docker-compose.yml` only.
- API smoke for active periode `d152b998-48e4-4d41-99fa-e1f901c7e2fe` passed:
  - dummy Pengusahaan late 2 days saved,
  - compliance summary returned `0.0780`,
  - dashboard snapshot returned `compliance_deduction = 0.0780` and `nko_total = 106.0420`.
- Chrome CDP smoke passed after login:
  - `/compliance` rendered `Compliance Control Desk`,
  - `PENGUSAHAAN` visible,
  - `0,0780` visible,
  - JavaScript exception count: 0.
