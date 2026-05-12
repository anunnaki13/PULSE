---
status: complete
phase: 05-ai-integration
system_type: LLM-assisted workflow features
framework: Direct OpenRouter HTTP client with Pydantic schemas
alternative_considered: LangGraph
---

# AI-SPEC - Phase 05 AI Integration

## 1. System Classification

PULSE Phase 05 is not an autonomous agent. It is a set of bounded, opt-in LLM assists inside existing assessment and recommendation workflows.

Primary tasks:
- generate Bahasa Indonesia draft justifications,
- generate structured SMART recommendation JSON,
- classify anomaly suspicion,
- generate cached inline help per indikator,
- generate short cross-period comparison narrative.

## 1b. Domain Context

Good output for PLTU Tenayan Konkin work is formal, concise, auditable, and tied to measurable operating context. It should mention KPI/ML stream semantics, not invent evidence, and should distinguish operational risk from compliance risk.

Bad output fabricates root causes, cites unavailable documents, includes personal identifiers, gives generic motivation, or recommends actions that are not assignable, measurable, or time-bound.

Stakes:
- wrong recommendations can misdirect unit performance actions,
- unmasked PII can violate internal policy,
- hallucinated evidence can weaken audit readiness,
- AI downtime must never block assessment submission or asesor review.

## 2. Framework Selection

Selected: Direct OpenRouter HTTP client with Pydantic schemas.

Rationale:
- The use cases are bounded single-call generations/classifications.
- Existing FastAPI app already has routing, RBAC, audit middleware, and Pydantic validation.
- A full agent framework would add state and tracing overhead without meaningful benefit.
- OpenRouter is OpenAI-compatible and can be called directly at `/api/v1/chat/completions`.

Alternative: LangGraph. Rejected for Phase 05 because there is no multi-step autonomous state machine yet. Reconsider if Phase 5b RAG chat becomes long-running with tool calls.

## 3. Implementation Guidance

Entry point pattern:

```python
masked = mask_pii(prompt_payload)
result = await openrouter.complete(
    use_case="draft_justification",
    messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": masked.text}],
    response_format={"type": "json_object"},
)
log = AiSuggestionLog(..., prompt=masked.text, suggestion_text=result.text, model_used=result.model)
```

Rules:
- Never send raw user text before PII masking.
- Use strict response schemas for structured outputs.
- Log both success and fallback failures.
- Keep mock mode deterministic and visibly labeled.
- Use low temperature for formal reports and JSON tasks.

## 4. Prompt Contracts

Draft justification:
- 3-5 sentences,
- Bahasa Indonesia formal,
- no invented evidence,
- mention indicator code/name and target/realisasi if available.

Draft recommendation:
- JSON fields: `severity`, `deskripsi`, `action_items`, `target_outcome`,
- action items must be concrete and assignable,
- deadline may be null in draft.

Inline help:
- `apa_itu`,
- `formula_explanation`,
- `best_practice`,
- `common_pitfalls`,
- `related_indikator`.

## 4b. Pydantic Output Example

```python
class AiDraftRecommendation(BaseModel):
    severity: Literal["low", "medium", "high", "critical"]
    deskripsi: str
    action_items: list[ActionItem]
    target_outcome: str
```

## 5. Evaluation Strategy

| Dimension | Method | Pass Criteria |
|---|---|---|
| PII masking | code-based tests | emails, NIP-like numbers, and vendor markers replaced before client call |
| JSON validity | Pydantic validation | draft recommendation always validates |
| Domain grounding | fixture review | mentions stream and provided values, no invented evidence |
| Fallback behavior | integration smoke | no key/downstream failure returns unavailable status or deterministic mock |
| Cost tracking | DB assertion | every AI request logs use case, model, latency, and estimated cost |

Reference dataset starts with 10 fixtures: EAF good, EAF bad, EFOR high, OUTAGE low maturity, SMAP weak WBS, missing evidence, invalid PII, submitted session, prior-period comparison, and OpenRouter unavailable.

## 6. Guardrails

- PII masking is online and mandatory.
- AI endpoints are role-gated and CSRF protected for mutations.
- AI responses are suggestions only; user must accept/edit/reject.
- No AI output mutates assessment or recommendation rows directly.
- OpenRouter unavailable state disables frontend buttons and keeps forms usable.

## 7. Monitoring

Track:
- requests by use case/user/model,
- latency,
- fallback/mock count,
- estimated cost,
- accept/reject/edit rate.

Tracing default: DB-backed `ai_suggestion_log` for MVP. External tracing can be added later with Langfuse or Arize Phoenix.

## Checklist

- [x] Framework selected.
- [x] Domain-specific failure modes defined.
- [x] PII masking required.
- [x] Structured outputs use Pydantic.
- [x] Eval dimensions defined.
- [x] Fallback behavior defined.
