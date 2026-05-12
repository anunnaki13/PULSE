---
status: ready-for-planning
phase: 04-compliance-tracker-reports
created: "2026-05-12T02:25:00+07:00"
source:
  - .planning/ROADMAP.md
  - .planning/REQUIREMENTS.md
  - .planning/phases/03-nko-calculator-dashboard/03-UAT.md
---

# Phase 04 Context - Compliance Tracker + Reports

## Phase Boundary

Phase 04 replaces the Phase 03 dummy compliance deduction with persisted compliance tracking. BID CPF/admin users must be able to record routine report submissions and non-report compliance components, see the capped compliance deduction summary, and export operational report artifacts.

## Decisions

### D-01 - Routine Report Definitions

Seed the nine routine reports required by the blueprint: Pengusahaan, BA Transfer Energi, Keuangan, Monev BPP, Kinerja Investasi, Manajemen Risiko, Self Assessment, Manajemen Material, and Navitas.

### D-02 - Deduction Formula

Routine report deduction is `keterlambatan_hari * pengurang_per_keterlambatan` plus invalidity deduction when applicable. Default factor is `0.039`. Total compliance deduction must be capped at `10`.

### D-03 - Generated Delay Column

`keterlambatan_hari` must be a database generated column so reporting/export cannot drift from stored submission dates.

### D-04 - NKO Integration

Phase 03 NKO snapshots must use persisted compliance summary when available. If the dashboard is still using fallback gross pilar data, the final NKO is fallback gross minus persisted compliance deduction.

### D-05 - Report Exports

Exports can start with deterministic generated artifacts that open cleanly. Exact visual mirroring of the official PDF can be iterated after the data contracts are stable.

## Canonical References

- `.planning/ROADMAP.md` - Phase 04 success criteria.
- `.planning/REQUIREMENTS.md` - `REQ-compliance-laporan-tracker`, `REQ-compliance-komponen`, `REQ-compliance-summary`, and report export requirements.
- `backend/app/services/nko_calculator.py` - NKO snapshot integration point.
- `frontend/src/routes/Dashboard.tsx` - dashboard surface that must reflect compliance deduction.

## Deferred

- Pixel-perfect official PDF styling can be refined after export payloads are verified.
- External Navitas/SAP synchronization remains out of scope.
