---
status: complete
phase: 08-formula-stream-dictionary
plan: 01
requirements_addressed:
  - REQ-formula-stream-dictionary
---

# Plan 08-01 - Formula Stream Dictionary

## Objective

Create a formula dictionary page that lets authenticated users inspect stream-specific formula families, units, polarities, weights, and validation notes.

## Scope

- Create `frontend/src/routes/FormulaDictionary.tsx`.
- Register `/formula-dictionary` in `frontend/src/App.tsx`.
- Add `Kamus Formula` navigation link in `frontend/src/routes/AppShell.tsx`.
- Add i18n key `nav.formulaDictionary`.
- Update GSD requirements/roadmap/state.

## Verification

- `pnpm --dir frontend build` passes.
- `pnpm --dir frontend test --run` passes.
- `GET /formula-dictionary` returns the SPA from local Nginx.
- Main smoke remains green.
