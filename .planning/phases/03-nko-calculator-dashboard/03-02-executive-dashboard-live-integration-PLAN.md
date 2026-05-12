---
status: planned
phase: 03-nko-calculator-dashboard
plan: 02
title: executive-dashboard-live-integration
requirements_addressed:
  - REQ-nko-realtime-ws
  - REQ-dashboard-executive
  - REQ-dashboard-heatmap
  - REQ-dashboard-trend
depends_on:
  - 03-01-nko-snapshot-engine-dashboard-api
---

# Plan 03-02 - Executive Dashboard Live Integration

## Objective

Connect the existing high-fidelity dashboard prototype to the Phase 03 backend contracts while preserving the "keren" control-room design, stream-specific formula explanations, unit labels, and fallback dummy data for not-yet-live parts.

## Scope

- Add frontend API helpers for executive dashboard, maturity heatmap, trend, and dashboard WebSocket.
- Replace hard-coded dashboard fixture as the primary source with live query data from `/dashboard/executive?periode_id=`.
- Keep `dashboard-fixtures.ts` as an explicit fallback for dev/demo empty states and scenario simulation.
- Add WebSocket subscription that updates the NKO gauge and affected stream/pilar cards without manual refresh.
- Make drilldown panels render formula trace from backend breakdown JSONB:
  - EAF: positive percent KPI.
  - EFOR: negative percent KPI.
  - Outage: maturity level area/sub-area average.
  - SMAP: compliance/maturity and pengurang-ready display.
- Preserve and refine the existing visual layout: NKO gauge, pilar cards, heatmap, trend, signal cards, recommendation pipeline, waterfall, formula ledger, and scenario simulator.
- Add route access consistency for `/dashboard/executive` using `manajer_unit`, `super_admin`, and `viewer`.

## Implementation Notes

- Use TanStack Query for dashboard payloads and invalidate/patch cache on `nko_updated`.
- Do not remove the scenario simulator; it is valuable for executive exploration while live data is still sparse.
- Use clear data-source labeling in development: live, fallback, or simulated scenario.
- Maintain responsive constraints so charts, gauge, and dense cards do not overlap on laptop/mobile widths.
- Keep text in Bahasa Indonesia for operator-facing labels.

## Verification

- `pnpm exec tsc -b --pretty false`
- `pnpm exec vitest run --passWithNoTests`
- `pnpm exec vite build`
- Browser smoke at `http://127.0.0.1:3399/dashboard/executive` after rebuilding frontend/nginx.
- Manual visual check for no overlap in desktop and mobile widths.

## Acceptance Checks

- Dashboard loads from live API when `periode_id` has a snapshot.
- Dashboard falls back to dummy demo payload when no snapshot exists and clearly treats it as demo data.
- NKO gauge updates after a `nko_updated` WebSocket event.
- Each pilot stream shows correct formula semantics and unit label instead of a generic percentage-only treatment.
- Existing worked example remains tested: gross pilar `106.12` - compliance `2.76` = NKO `103.36`.

## Deferred

- Report exports remain Phase 04.
- AI narratives, AI forecasting, and comparative analysis remain Phase 05.
