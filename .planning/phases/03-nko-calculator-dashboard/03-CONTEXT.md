---
status: ready-for-planning
phase: 03-nko-calculator-dashboard
created: "2026-05-12T01:15:00+07:00"
source:
  - .planning/ROADMAP.md
  - .planning/REQUIREMENTS.md
  - .planning/STATE.md
  - user dashboard direction, 2026-05-12
---

# Phase 03 Context - NKO Calculator + Dashboard

## Phase Boundary

Phase 03 turns PULSE into the MVP-usable executive scoring product. The system must compute and persist NKO snapshots from approved assessment data, expose dashboard payloads and real-time update events, and wire the existing executive dashboard prototype to those live contracts.

This phase may use dummy data only for unavailable historical or non-implemented stream coverage. Dummy values must be explicit fallback data, not hidden as live facts.

## Decisions

### D-01 - Dashboard Visual Direction

The dashboard should feel like a polished control-room executive dashboard, not a plain CRUD page. The existing `/dashboard` and `/dashboard/executive` prototype is the visual baseline: NKO gauge, pilar cards, heatmap, trend, drilldown, recommendation pipeline, reconciliation waterfall, formula ledger, and scenario simulator.

### D-02 - Blueprint-Aware Streams

Each stream keeps its own calculation semantics and unit labels. Do not flatten all streams into one generic percentage card.

- EAF: positive KPI, percent unit, higher is better.
- EFOR: negative KPI, percent unit, lower is better.
- Outage Management: maturity level stream, level 0-4 with area/sub-area averages.
- SMAP: compliance/maturity stream, can affect compliance/pengurang display.

### D-03 - Persisted Snapshot Contract

The backend must persist `nko_snapshot` rows instead of calculating dashboard totals only in memory. Snapshot breakdown JSONB must be rich enough for pilar, indikator, stream, formula trace, compliance deduction, and drilldown views.

### D-04 - Live Update Contract

Approved/overridden assessment changes should trigger NKO recompute and dashboard broadcast over `WS /ws/dashboard?token=...` using payload shape `{type: "nko_updated", periode_id, nko_total, changed_indikator}`.

### D-05 - MVP Data Scope

The minimum live MVP scope is the four pilot indicators already seeded and used in Phase 2: EAF, EFOR, Outage Management, and SMAP. Phase 06 will expand stream coverage.

### D-06 - Demo Math Anchor

The dashboard must keep a clear worked example that reconciles gross pilar score `106.12` minus compliance deduction `2.76` to final NKO `103.36`, matching the existing prototype tests.

## Canonical References

- `.planning/ROADMAP.md` - Phase 03 goal and success criteria.
- `.planning/REQUIREMENTS.md` - `REQ-nko-calc-engine`, `REQ-nko-aggregation-rules`, `REQ-nko-realtime-ws`, `REQ-dashboard-executive`, `REQ-dashboard-heatmap`, `REQ-dashboard-trend`.
- `.planning/phases/02-assessment-workflow-pic-asesor/02-UAT.md` - verified Phase 2 data flow that triggers this phase.
- `frontend/src/lib/dashboard-calculations.ts` - existing prototype calculation semantics.
- `frontend/src/lib/dashboard-fixtures.ts` - existing dummy stream data and worked example.
- `frontend/src/routes/Dashboard.tsx` and `frontend/src/routes/Dashboard.css` - existing dashboard visual implementation.

## Deferred

- Full 14-stream maturity coverage is deferred to Phase 06.
- Compliance tracker persistence and official report exports are deferred to Phase 04.
- AI forecast/explanations are deferred to Phase 05. Phase 03 may implement deterministic linear forecast only.
