---
status: complete
phase: 07-operator-onboarding-guided-help
plan: 01
requirements_addressed:
  - REQ-operator-onboarding-guide
---

# Plan 07-01 - In-App Menu Guide

## Objective

Add an authenticated in-app guide page that explains PULSE menus, role ownership, Konkin workflow order, and the stream-specific formula/unit differences captured from the blueprint.

## Scope

- Create `frontend/src/routes/MenuGuide.tsx`.
- Register `/guide` in `frontend/src/App.tsx`.
- Add a `Panduan` navigation link in `frontend/src/routes/AppShell.tsx`.
- Add i18n key `nav.guide`.
- Update roadmap/state to track Phase 07 as a parallel onboarding enhancement.

## Verification

- `pnpm --dir frontend build` passes.
- `/guide` is available behind authentication.
- Navigation shows `Panduan` for authenticated users.
- Page content covers menus, roles, workflow, and stream/formula/satuan differences.
