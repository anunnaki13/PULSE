# Constraints

> Tech-stack and contract constraints extracted from SPECs.
> Type taxonomy: `api-contract | schema | nfr | protocol`.
> Naming/identifier constraints reflect the post-rebrand state per ADR DEC-001/DEC-002.

---

## CONSTR-stack-frontend (nfr)
- source: `05_FRONTEND_ARCHITECTURE.md` §1
- type: nfr
- statement: Frontend is React 18 + Vite + TypeScript. State: TanStack Query v5 (server) + Zustand (client). Forms: React Hook Form + Zod. Routing: React Router v6. Styling: Tailwind CSS + custom skeuomorphic tokens. UI: custom + shadcn/ui forked. Icons: Lucide React + Heroicons. Charts: Recharts or Apache ECharts. Date: date-fns + dayjs. HTTP: Axios. Real-time: native WebSocket / Socket.IO client. Animation: Motion (framer-motion). Toast: Sonner.

## CONSTR-stack-backend (nfr)
- source: `04_API_SPEC.md`; `08_DEPLOYMENT.md` §5
- type: nfr
- statement: Backend is FastAPI on Python 3.11 (slim). Process: `gunicorn` with `uvicorn.workers.UvicornWorker`, 4 workers, bind `0.0.0.0:8000`. Validation via Pydantic. Migrations via Alembic. SQLAlchemy + asyncpg.

## CONSTR-stack-data (nfr)
- source: `03_DATA_MODEL.md` §1; `08_DEPLOYMENT.md` §1, §4 (db service)
- type: nfr
- statement: PostgreSQL 16+ with pgvector extension (`pgvector/pgvector:pg16` image). Use UUID primary keys. JSONB for dynamic schemas (ml_stream.structure, self_assessment payload, asesor_review, audit before/after). Audit columns on every table: `created_at, updated_at, created_by, updated_by`. Soft delete (`deleted_at`) on critical entities. Versioning via `konkin_template` + `ml_stream.version`.

## CONSTR-stack-cache (nfr)
- source: `08_DEPLOYMENT.md` §4
- type: nfr
- statement: Redis 7 (alpine), `maxmemory 256mb`, `maxmemory-policy allkeys-lru`. Used for cache and queue.

## CONSTR-postgres-extensions (schema)
- source: `03_DATA_MODEL.md` §3.1, §3.9
- type: schema
- statement: Required extensions: `uuid-ossp`, `pgcrypto`, `vector` (pgvector). pgvector index type: `ivfflat` with `vector_cosine_ops` on `pedoman_chunk.embedding`.

## CONSTR-jsonb-indexes (schema)
- source: `03_DATA_MODEL.md` §3.3, §3.5
- type: schema
- statement: GIN indexes on hot JSONB columns:
  - `idx_ml_stream_structure ON ml_stream USING GIN(structure)`
  - `idx_assessment_self_data ON assessment_session USING GIN(self_assessment)`

## CONSTR-id-uuid (schema)
- source: `03_DATA_MODEL.md` §1, §3
- type: schema
- statement: All primary keys are `UUID PRIMARY KEY DEFAULT uuid_generate_v4()`. No sequential int IDs in URL-exposed entities.

## CONSTR-data-model-core-tables (schema)
- source: `03_DATA_MODEL.md` §3
- type: schema
- statement: Required tables (DDL canonical in source):
  - User/auth: `bidang`, `roles`, `users`, `user_roles`.
  - Konkin master: `konkin_template`, `perspektif`, `indikator`, `indikator_owners`, `ml_stream`.
  - Periode/assessment: `periode`, `assessment_session`.
  - Recommendation: `recommendation`, `recommendation_progress`.
  - Compliance: `compliance_laporan_definisi`, `compliance_laporan_submission` (with `keterlambatan_hari` GENERATED column), `compliance_komponen`, `compliance_komponen_realisasi`.
  - NKO/audit: `nko_snapshot`, `audit_log`.
  - AI: `ai_conversation`, `ai_message`, `pedoman_chunk` (vector(768)), `ai_suggestion_log`.
  - Plus ADR-introduced: `ai_inline_help` (DEC-006).
  - Notification: `notification`.

## CONSTR-api-versioning (api-contract)
- source: `04_API_SPEC.md` §1
- type: api-contract
- statement: All REST endpoints under `/api/v1`. Base URL post-rebrand: `https://pulse.tenayan.local/api/v1` (DEC-002 supersedes the `siskonkin.tenayan.local` host shown in source).

## CONSTR-api-conventions (api-contract)
- source: `04_API_SPEC.md` §1
- type: api-contract
- statement: JSON UTF-8. Auth via `Authorization: Bearer <jwt>` or httpOnly cookie. Pagination `?page=&page_size=` with `{data, meta:{total, page, ...}}`. Sorting `?sort=-created_at`. Error envelope `{error: {code, message, details}}`. Status codes per spec (200/201/204/400/401/403/404/409/422/500).

## CONSTR-openapi (api-contract)
- source: `04_API_SPEC.md` §17
- type: api-contract
- statement: FastAPI auto-generates Swagger UI at `/api/v1/docs` and ReDoc at `/api/v1/redoc`. In production these may be auth-gated or disabled.

## CONSTR-websocket-endpoints (protocol)
- source: `04_API_SPEC.md` §15
- type: protocol
- statement: WebSocket endpoints:
  - `WS /ws/dashboard?token=...` — push NKO updates `{type, periode_id, nko_total, changed_indikator}`.
  - `WS /ws/notifications?token=...` — push notifications.
- Nginx must set Upgrade/Connection headers on `/ws/` location with `proxy_read_timeout 3600s`.

## CONSTR-rate-limits (nfr)
- source: `04_API_SPEC.md` §16; `08_DEPLOYMENT.md` §7
- type: nfr
- statement: Per-user rate limits — default 100 req/min mutating; 1000 req/min dashboard read; 20 req/min AI endpoints. Nginx zones: `api 60r/s burst=20`, `ai 20r/m burst=5`.

## CONSTR-security-headers (nfr)
- source: `08_DEPLOYMENT.md` §7
- type: nfr
- statement: Nginx adds `X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `X-XSS-Protection "1; mode=block"`, `Strict-Transport-Security "max-age=31536000; includeSubDomains"`, `Referrer-Policy strict-origin-when-cross-origin`. CSRF protection on cookie-based endpoints. SQL injection prevented via parameterized queries (SQLAlchemy default).

## CONSTR-no-file-upload (api-contract)
- source: `04_API_SPEC.md` §16; `UPDATE-001-pulse-rebrand-ai-features.md` §3.2
- type: api-contract
- statement: System does NOT expose evidence-file upload endpoints. Only external URL fields (`link_eviden`) are accepted. The single multipart endpoint is admin-only Excel import: `POST /konkin/templates/{id}/import-from-excel`.

## CONSTR-llm-routing (protocol)
- source: `07_AI_INTEGRATION.md` §2; `08_DEPLOYMENT.md` §3 (.env); ADR DEC-010
- type: protocol
- statement: LLM access via OpenRouter only. Model routing:
  - Routine (draft justification, draft recommendation, anomaly LLM, inline-help, comparative-analysis): `google/gemini-2.5-flash`.
  - Complex (chat RAG, summary periode, action plan SMART): `anthropic/claude-sonnet-4`.
  - Embeddings: `openai/text-embedding-3-small` (or `voyage-2`).
- Required headers: `Authorization: Bearer ${OPENROUTER_API_KEY}`, `HTTP-Referer: https://pulse.tenayan.local` (post-rebrand), `X-Title: PULSE` (post-rebrand from "SISKONKIN").
- Default sampling: temperature 0.3, max_tokens 400 for short responses, 1000 for default.

## CONSTR-llm-pii-policy (nfr)
- source: `07_AI_INTEGRATION.md` §6
- type: nfr
- statement: PII masking layer must run before any LLM call. Forbidden in payload: NIP, personal email, audit-in-progress data, exact vendor names. Allowed: KPI values, formulas, ML criteria, NKO snapshot agregat, anonymised PIC label.

## CONSTR-rag-pipeline (protocol)
- source: `07_AI_INTEGRATION.md` §4
- type: protocol
- statement: RAG chunking via `RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120, separators=["\\n\\n","\\n",". "," "])`. Top-k retrieval k=5 via pgvector cosine. Chunks tagged with section/page metadata. Optional hybrid BM25 keyword search for technical terms.

## CONSTR-ai-cost-budget (nfr)
- source: `07_AI_INTEGRATION.md` §1, §2; ADR DEC-009
- type: nfr
- statement: AI spend budget for MVP at UP Tenayan scale: ~$3.15/month (~Rp 50.000) post-update. Spend must be tracked per use-case category and per user.

## CONSTR-domain-pulse (nfr)
- source: `08_DEPLOYMENT.md`; ADR DEC-001/DEC-002
- type: nfr
- statement: Domain placeholder `pulse.tenayan.local` (DEC-002 supersedes `siskonkin.tenayan.local` shown in `08_DEPLOYMENT.md` source).

## CONSTR-network-naming (nfr)
- source: `08_DEPLOYMENT.md` §4; ADR DEC-002
- type: nfr
- statement: Docker network: `pulse-net`. Container names: `pulse-db`, `pulse-redis`, `pulse-backend`, `pulse-frontend`, `pulse-nginx`. (Source uses `siskonkin-*`; ADR DEC-002 supersedes.)

## CONSTR-host-port (nfr)
- source: `08_DEPLOYMENT.md` §4
- type: nfr
- statement: Nginx publishes on host port `3399` (HTTP) or `443` (HTTPS) only. PostgreSQL never exposed publicly.

## CONSTR-env-secrets (nfr)
- source: `08_DEPLOYMENT.md` §3
- type: nfr
- statement: Secrets in `.env`, never committed. Required keys: `APP_SECRET_KEY`, `POSTGRES_PASSWORD`, `JWT_SECRET_KEY`, `OPENROUTER_API_KEY`, `SMTP_PASSWORD`. JWT TTLs: access 60min, refresh 14 days. Post-rebrand env values: `POSTGRES_DB=pulse`, `POSTGRES_USER=pulse`, `BACKUP_DIR=/var/backups/pulse`, `APP_BASE_URL=https://pulse.tenayan.local` (DEC-002).

## CONSTR-backup (nfr)
- source: `08_DEPLOYMENT.md` §9
- type: nfr
- statement: Daily `pg_dump | gzip` at 02:00 to `${BACKUP_DIR}`. Retention default 30 days. Weekly rsync to NAS at 03:00 Sunday. Restore script must accept a backup filename and pipe into `psql`.

## CONSTR-design-tokens (schema)
- source: `06_DESIGN_SYSTEM_SKEUOMORPHIC.md` §2
- type: schema
- statement: Design tokens (CSS custom properties under `:root`):
  - Surfaces: `--sk-surface-base #1a1f2e`, `--sk-surface-raised #232938`, `--sk-surface-deep #0f1218`, `--sk-surface-lcd #0a1410`, `--sk-surface-light #f4f1ea`, `--sk-surface-light-deep #e5e0d4`.
  - Brand: `--sk-pln-blue #1e3a8a`, `--sk-pln-blue-bright #3b82f6`, `--sk-pln-yellow #fbbf24`, `--sk-pln-yellow-glow #fde047`.
  - Level palette: L0 `#ef4444`, L1 `#f97316`, L2 `#eab308`, L3 `#22c55e`, L4 `#10b981`.
  - LCD text `#4ade80`; LCD glow `0 0 8px rgba(74,222,128,0.55)`.
  - Typography stack: display/heading `Bebas Neue` + `Oswald`; body `Barlow`; mono `JetBrains Mono`; LCD `Share Tech Mono` / DSEG7.
  - Type scale `--text-xs..--text-6xl` per source.

## CONSTR-design-philosophy (nfr)
- source: `06_DESIGN_SYSTEM_SKEUOMORPHIC.md` §1; ADR DEC-010 (dark theme locked)
- type: nfr
- statement: Three pillars — Tactile, Industrial Refinement, Information First. Default theme is dark (control-room digital); light theme exists as variant only (DEC-010). Pulse Heartbeat signature animation layered on top per DEC-003.

## CONSTR-i18n-default (nfr)
- source: `05_FRONTEND_ARCHITECTURE.md` §8
- type: nfr
- statement: Default UI copy is Bahasa Indonesia. Structure ready for English support later (`react-intl` or simple lookup). All blueprint and AI prompt outputs are BI formal unless explicitly opt-in.

## CONSTR-accessibility (nfr)
- source: `05_FRONTEND_ARCHITECTURE.md` §7
- type: nfr
- statement: Semantic HTML + ARIA. Keyboard navigation for all skeuomorphic primitives (e.g. SkDial responds to arrow keys). Visible focus indicator. Color contrast WCAG AA minimum despite tactile depth. Screen-reader friendly via `aria-describedby` for level criteria.

## CONSTR-ai-suggestion-audit (api-contract)
- source: `07_AI_INTEGRATION.md` §6; `03_DATA_MODEL.md` §3.9
- type: api-contract
- statement: Every LLM request must persist a row in `ai_suggestion_log` with `user_id, suggestion_type, context_entity_type, context_entity_id, prompt, suggestion_text, accepted, user_edited_version, model_used, created_at`. Acceptance flag updated after user accept/reject.

## CONSTR-fallback-graceful (nfr)
- source: `07_AI_INTEGRATION.md` §10
- type: nfr
- statement: If OpenRouter is unavailable: AI buttons disabled with tooltip; forms remain fully functional; errors logged with exponential backoff; admin alerted (email/Slack).

## CONSTR-monitoring (nfr)
- source: `07_AI_INTEGRATION.md` §9; `08_DEPLOYMENT.md` §10
- type: nfr
- statement: Track per-AI-suggestion-type: acceptance rate (target draft > 60%, anomaly > 40%), p50/p95/p99 latency (target < 5s), per-user/month cost, thumbs up/down. Backend logs structured JSON to stdout + volume. Slow-query log threshold 500ms on PostgreSQL.

## CONSTR-pulse-rebrand-find-replace (nfr)
- source: `UPDATE-001-pulse-rebrand-ai-features.md` §1.3 (locked DEC-001/DEC-002)
- type: nfr
- statement: All occurrences of `SISKONKIN`/`Siskonkin`/`siskonkin` and identifier variants must be replaced with `PULSE`/`pulse` per the case-sensitive table in ADR §1.3. SPEC source files not yet updated; downstream consumers MUST treat the rebrand as authoritative.
