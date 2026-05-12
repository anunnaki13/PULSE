---
status: active
phase: 07-operator-onboarding-guided-help
created_at: "2026-05-12T23:55:00.000+07:00"
---

# Phase 07 Context - Operator Onboarding Guided Help

## Purpose

Add an in-app guide so operators can understand what each PULSE menu does while the production go-live gates remain blocked by external VPS, SSL, monitoring, and OpenRouter tasks.

## Background

The user asked for menu explanations because the app was built from a large AI-generated blueprint and the current menu structure is not yet self-explanatory for a new operator. `docs/MENU-GUIDE.md` already explains the menus in Markdown; Phase 07 brings the same operational explanation into the authenticated application.

## Scope

- Add an authenticated `/guide` page.
- Add a top navigation entry named `Panduan`.
- Explain every major menu:
  - Dasbor
  - Assessment
  - Rekomendasi
  - Periode
  - Compliance
  - Audit
  - Master Data
  - Notifikasi
- Explain role ownership and the recommended end-to-end Konkin flow.
- Explain why each stream can use a different formula, unit, target direction, and aggregation behavior.

## Constraints

- No backend changes needed.
- Keep copy in Bahasa Indonesia.
- Keep UI consistent with the existing skeuomorphic/control-room dashboard style.
- Do not change current production-blocked status for Phase 06.

