---
status: planned
phase: 06-stream-coverage-hcr-golive
plan: 04
requirements_addressed:
  - REQ-ai-rag-chat
  - REQ-ai-summary-periode
  - REQ-ai-action-plan-generator
  - REQ-prod-checklist
---

# Plan 06-04 - Pedoman RAG Summary Action Plan

## Objective

Complete deferred Phase 5b AI features with Pedoman Konkin source grounding and production-grade auditability.

## Scope

- Add Pedoman Konkin chunk table and pgvector index.
- Add ingestion script for Pedoman chunks with metadata: section, page, title, and source hash.
- Add RAG chat endpoint using complex model routing and top-k=5 cosine retrieval.
- Add periode executive summary endpoint producing 400-600 Bahasa Indonesia words.
- Add SMART action-plan generator endpoint returning structured JSON.
- Log all requests to `ai_suggestion_log` with cost, model, fallback, and source metadata.

## Verification

- Unit test chunking metadata and retrieval ordering.
- API smoke for chat with cited sources.
- API smoke for summary and action-plan JSON schema.
- Rate-limit and fallback checks in mock mode.
