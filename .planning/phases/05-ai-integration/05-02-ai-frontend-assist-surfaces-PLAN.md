---
status: planned
phase: 05-ai-integration
plan: 02
requirements_addressed:
  - REQ-ai-draft-justification
  - REQ-ai-draft-recommendation
  - REQ-ai-anomaly-detection
  - REQ-ai-inline-help
  - REQ-ai-comparative-analysis
  - REQ-ai-fallback
---

# Plan 05-02 - AI Frontend Assist Surfaces

## Objective

Light up AI Assist buttons in the assessment workflow without making AI mandatory for form completion.

## Scope

- Add frontend AI API hooks.
- Show AI status badge.
- Add PIC actions:
  - Draft Justifikasi -> fills `catatan_pic`.
  - Inline Help -> opens contextual help panel.
  - Comparative Analysis -> shows cross-period narrative.
  - Anomaly Check -> shows classification/warning.
- Add asesor action:
  - Draft Rekomendasi -> fills inline recommendation draft.
- Disable AI controls with tooltip when AI is unavailable.

## Verification

- TypeScript/Vite build.
- Focused frontend tests.
- Browser smoke for AI mock path.
