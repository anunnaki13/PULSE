---
status: complete
phase: 03-nko-calculator-dashboard
started: "2026-05-12T02:08:00+07:00"
updated: "2026-05-12T02:18:00+07:00"
source:
  - 03-01-nko-snapshot-engine-dashboard-api-SUMMARY.md
  - 03-02-executive-dashboard-live-integration-SUMMARY.md
---

# Phase 03 UAT - NKO Calculator + Dashboard

## Current Test

[testing complete]

## Tests

### 1. Backend NKO Snapshot Contract

expected: Dashboard API returns persisted or fallback NKO snapshot with gross pilar, compliance deduction, final NKO, and pilot stream breakdown.
result: pass
observed: |
  GET /api/v1/dashboard/executive?periode_id=c772833d-d0dc-4006-a05c-39ce3b8f008f returned:
  source=fallback, gross=106.1200, compliance_deduction=2.7600, nko_total=103.3600.
  Streams present: EAF, EFOR, OUTAGE, SMAP.

### 2. Formula Semantics

expected: EAF, EFOR, OUTAGE, and SMAP keep distinct formula semantics and unit labels.
result: pass
observed: |
  Unit tests cover positive KPI, negative KPI, maturity payload average, and fallback reconciliation anchor.
  Dashboard stream cards render percent/unit/level treatment separately.

### 3. Browser Login And Deep Link

expected: Super admin can log in and open /dashboard/executive without being bounced back to login after cookie hydration.
result: pass
observed: |
  Chrome headless operator flow logged in as super@pulse.tenayan.local and landed on http://127.0.0.1:3399/dashboard/executive.
  A hydration race found during UAT was fixed by adding hasHydrated to auth store and making ProtectedRoute wait for auth hydration.

### 4. Executive Dashboard Visual Contract

expected: Dashboard renders NKO gauge, data source label, scenario simulator, formula ledger, and pilot stream cards without obvious layout overflow.
result: pass
observed: |
  Chrome headless full-page verification found:
  hasNko=true, hasDataSource=true, hasStreams=true, hasScenario=true, hasFormulaLedger=true.
  streamCards=[EAF, EFOR, OUTAGE, SMAP].
  suspiciousLayoutCount=0 at 1424x1105 viewport.

### 5. Regression Checks

expected: Frontend and backend focused tests/builds remain green after Phase 3 fixes.
result: pass
observed: |
  Backend: pytest -q tests/test_phase2_services_and_routes.py tests/test_nko_calculator.py -> 9 passed.
  Frontend: pnpm exec tsc -b --pretty false -> passed.
  Frontend: pnpm exec vitest run --passWithNoTests -> 49 passed.
  Frontend: pnpm exec vite build -> passed.
  Docker: backend/frontend/nginx rebuilt and reported healthy.

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0
blocked: 0

## Defects Found And Fixed During UAT

- Direct dashboard/deep-link access after cookie login could redirect to `/login` before auth hydration finished. Fixed by tracking `hasHydrated` in `auth-store` and making `ProtectedRoute` wait before redirecting.

## Gaps

- Full compliance persistence remains Phase 04.
- Full stream inventory and HCR/OCR remain Phase 06.
