---
status: planned
phase: 05-ai-integration
plan: 01
requirements_addressed:
  - REQ-ai-draft-justification
  - REQ-ai-draft-recommendation
  - REQ-ai-anomaly-detection
  - REQ-ai-inline-help
  - REQ-ai-comparative-analysis
  - REQ-ai-rate-limiting
  - REQ-ai-pii-masking
  - REQ-ai-fallback
  - REQ-ai-audit-trail
---

# Plan 05-01 - AI Backend Foundation

## Objective

Add AI persistence, PII masking, OpenRouter/mock client, and role-gated AI endpoints.

## Scope

- Add `ai_suggestion_log` and `ai_inline_help` models/migration.
- Add AI settings and OpenRouter client wrapper.
- Add deterministic mock mode when `OPENROUTER_API_KEY` is absent.
- Add PII masking service and tests.
- Add `/api/v1/ai/status`.
- Add endpoints:
  - `POST /ai/draft-justification`
  - `POST /ai/draft-recommendation`
  - `POST /ai/anomaly-check`
  - `GET /ai/inline-help/{indikator_id}`
  - `POST /ai/inline-help/{indikator_id}/regenerate`
  - `POST /ai/comparative-analysis`
  - `PATCH /ai/suggestions/{id}/feedback`

## Verification

- Unit tests for PII masking and schema validation.
- Router registration tests.
- API smoke in mock mode.
