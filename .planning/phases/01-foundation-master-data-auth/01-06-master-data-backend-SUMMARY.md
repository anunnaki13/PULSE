---
phase: 01-foundation-master-data-auth
plan: 06
subsystem: backend
tags: [master-data, alembic, csrf, rbac, jsonb, excel-import, B-01, B-02, B-04, B-07, W-07]
dependency_graph:
  requires:
    - 01-03-backend-skeleton-health   # auto-discovery routers/models + Alembic + tests
    - 01-05-auth-backend-jwt-rbac     # require_role, require_csrf, six-role seed
  provides:
    - master-data backend (bidang + konkin templates + perspektif + indikator + ml_stream)
    - Excel import (admin-only, CSRF-protected, idempotent)
    - users.bidang_id FK (B-04 deferred FK closed)
    - W-07-aware lock validator (excludes is_pengurang from bobot sum)
    - locked single-multipart contract (test_no_upload_policy)
  affects:
    - backend/app/models/user.py (amended with bidang_id)
    - backend/alembic chain (0001 → 0002 → 0003)
    - OpenAPI surface (12 new routes, 1 multipart endpoint)
tech_stack:
  added:
    - openpyxl 3.1.5 (streaming Excel parser, read_only=True / data_only=True)
  patterns:
    - per-sheet SAVEPOINT via `async with db.begin_nested()` (Pitfall #10)
    - Idempotency-Key header → konkin_import_log.idempotency_key UNIQUE gate
    - pic_bidang scoped reads via WHERE Bidang.id == user.bidang_id (Phase-1 scope)
    - W-07 lock validator: SUM(bobot) WHERE is_pengurang = FALSE == 100.00 ± 0.01
    - Pydantic v2 HttpUrl → anyOf:[{format:uri,...},{type:null}] for nullable URL fields
key_files:
  created:
    - backend/app/models/bidang.py
    - backend/app/models/konkin_template.py
    - backend/app/models/perspektif.py
    - backend/app/models/indikator.py
    - backend/app/models/ml_stream.py
    - backend/app/models/konkin_import_log.py
    - backend/app/schemas/master.py
    - backend/app/routers/master_bidang.py
    - backend/app/routers/master_konkin.py
    - backend/app/services/excel_import.py
    - backend/alembic/versions/20260512_140000_0003_master_data.py
    - backend/tests/test_bidang.py
    - backend/tests/test_master_konkin.py
    - backend/tests/test_ml_stream.py
  modified:
    - backend/app/models/user.py (B-04: add `bidang_id: Mapped[uuid.UUID | None]`)
    - backend/tests/test_no_upload_policy.py (locked allow-list + anyOf-aware HttpUrl check)
decisions:
  - W-07 fix: perspektif carries is_pengurang + pengurang_cap; lock validator filters non-pengurang rows
  - B-04 fix: users.bidang_id + fk_users_bidang_id added in 0003 (FK target now exists)
  - B-07 fix: import-from-excel uses Depends(require_csrf) — same CSRF rule as every mutating cookie-reachable route
  - B-01/B-02: all require_role calls use spec names verbatim (super_admin, admin_unit, pic_bidang, asesor, manajer_unit, viewer)
  - Phase-1 _import_sheet placeholder: counts non-empty rows; perspektif/indikator materialisation deferred to Phase 2
metrics:
  duration_seconds: 740
  completed_date: 2026-05-11
  task_count: 3
  files_changed: 16
  lines_inserted: 2950
  lines_deleted: 33
---

# Phase 1 Plan 6: Master Data Backend Summary

Master-data backend delivered: five domain models (bidang, konkin_template, perspektif, indikator, ml_stream) plus `konkin_import_log`, all on Alembic revision `0003_master_data` chained off Plan 05's `0002_auth_users_roles`. Twelve OpenAPI routes mounted under `/api/v1/{bidang,konkin/templates,konkin/perspektif,konkin/indikator,ml-stream}` with strict RBAC (B-01/B-02 spec naming) and a single CSRF-protected multipart endpoint for Excel template imports (B-07).

---

## Endpoint Contract Table

| Path                                                                | Method | Role gate                              | CSRF?       | Request body                          | Success response                  |
| ------------------------------------------------------------------- | ------ | -------------------------------------- | ----------- | ------------------------------------- | --------------------------------- |
| `/api/v1/bidang`                                                    | GET    | `current_user` (pic_bidang scoped)     | n/a         | `?page&page_size`                     | 200 `{data:[BidangPublic], meta}` |
| `/api/v1/bidang/{id}`                                               | GET    | `current_user` (pic_bidang scoped)     | n/a         | —                                     | 200 `BidangPublic` \| 404         |
| `/api/v1/bidang`                                                    | POST   | `super_admin` \| `admin_unit`          | **yes**     | `BidangCreate`                        | 201 `BidangPublic`                |
| `/api/v1/bidang/{id}`                                               | PATCH  | `super_admin` \| `admin_unit`          | **yes**     | `BidangUpdate`                        | 200 `BidangPublic`                |
| `/api/v1/bidang/{id}`                                               | DELETE | `super_admin` \| `admin_unit`          | **yes**     | —                                     | 204 (soft delete)                 |
| `/api/v1/konkin/templates`                                          | GET    | `current_user`                         | n/a         | `?page&page_size`                     | 200 list                          |
| `/api/v1/konkin/templates/{id}`                                     | GET    | `current_user`                         | n/a         | —                                     | 200 `TemplatePublic`              |
| `/api/v1/konkin/templates`                                          | POST   | `super_admin` \| `admin_unit`          | **yes**     | `TemplateCreate` (`clone_from_id?`)   | 201 `TemplatePublic`              |
| `/api/v1/konkin/templates/{id}`                                     | PATCH  | `super_admin` \| `admin_unit`          | **yes**     | `TemplateUpdate`                      | 200 \| 409 if locked              |
| `/api/v1/konkin/templates/{id}/lock`                                | POST   | `super_admin` \| `admin_unit`          | **yes**     | —                                     | 200 \| 422 W-07                   |
| `/api/v1/konkin/templates/{template_id}/import-from-excel`          | POST   | `super_admin` \| `admin_unit` (**B-07**) | **yes**   | multipart/.xlsx + `Idempotency-Key`   | 201 \| 200 `already_applied`      |
| `/api/v1/konkin/templates/{id}/perspektif`                          | GET    | `current_user`                         | n/a         | —                                     | 200 list                          |
| `/api/v1/konkin/templates/{id}/perspektif`                          | POST   | `super_admin` \| `admin_unit`          | **yes**     | `PerspektifCreate`                    | 201                               |
| `/api/v1/konkin/perspektif/{id}`                                    | PATCH  | `super_admin` \| `admin_unit`          | **yes**     | `PerspektifUpdate`                    | 200 \| 409 if locked              |
| `/api/v1/konkin/perspektif/{id}`                                    | DELETE | `super_admin` \| `admin_unit`          | **yes**     | —                                     | 204                               |
| `/api/v1/konkin/perspektif/{id}/indikator`                          | GET    | `current_user`                         | n/a         | —                                     | 200 list                          |
| `/api/v1/konkin/perspektif/{id}/indikator`                          | POST   | `super_admin` \| `admin_unit`          | **yes**     | `IndikatorCreate`                     | 201                               |
| `/api/v1/konkin/indikator/{id}`                                     | PATCH  | `super_admin` \| `admin_unit`          | **yes**     | `IndikatorUpdate`                     | 200 \| 409 if locked              |
| `/api/v1/konkin/indikator/{id}`                                     | DELETE | `super_admin` \| `admin_unit`          | **yes**     | —                                     | 204 (soft delete)                 |
| `/api/v1/ml-stream`                                                 | GET    | `current_user`                         | n/a         | `?page&page_size`                     | 200 list                          |
| `/api/v1/ml-stream/{id}`                                            | GET    | `current_user`                         | n/a         | —                                     | 200 `MlStreamDetail` (JSONB tree) |
| `/api/v1/ml-stream`                                                 | POST   | `super_admin` \| `admin_unit`          | **yes**     | `MlStreamCreate`                      | 201                               |
| `/api/v1/ml-stream/{id}`                                            | PATCH  | `super_admin` \| `admin_unit`          | **yes**     | `MlStreamUpdate`                      | 200                               |
| `/api/v1/ml-stream/{id}`                                            | DELETE | `super_admin` \| `admin_unit`          | **yes**     | —                                     | 204 (soft delete)                 |

**Anonymous → every protected route returns 401.** **viewer / manajer_unit / asesor / pic_bidang on a write → 403** (no role match in `require_role("super_admin","admin_unit")`).

---

## W-07 Lock Validator Details

Server-side function: `app.routers.master_konkin._validate_template_for_lock`.

Two rules — both filter pengurang rows out:

1. **Perspektif-sum rule.** `SUM(perspektif.bobot) WHERE template_id = ? AND is_pengurang = FALSE` must equal **100.00 ± 0.01**. Reject 422 otherwise with structured detail:
   ```json
   {
     "error": "bobot_perspektif_invalid",
     "expected": "100.00",
     "actual": "<sum>",
     "tolerance": "0.01",
     "offending": [{"id": "...", "kode": "...", "bobot": "...", "is_pengurang": true|false}, ...],
     "rule": "SUM(bobot) WHERE is_pengurang = FALSE must equal 100.00 (W-07)"
   }
   ```
   Pengurang perspektif rows are surfaced in `offending` for UI debug, but they don't count toward the sum.

2. **Indikator-sum-per-non-pengurang-perspektif rule.** For each `perspektif WHERE is_pengurang = FALSE`, `SUM(indikator.bobot)` for the non-deleted children must equal **100.00 ± 0.01**. Pengurang perspektif (e.g. VI Compliance) are **excluded** from this check too — their indikator are computed differently per the Phase-3 NKO calc (`NKO = Σ(Pilar I..V) − Pengurang Compliance` with `pengurang_cap` as the upper bound).

**Tolerance:** `Decimal("0.01")` — chosen so a sum of `99.99` or `100.01` rounds in, but `99.98` is rejected.

**Idempotency:** locking an already-locked template returns 200 with the unchanged row (no re-validation).

---

## Excel Import Flow (`POST /konkin/templates/{id}/import-from-excel`)

1. **Auth gate** (router-level `dependencies`): `Depends(require_role("super_admin","admin_unit"))` → 403 if the user is not admin. **B-07 fix:** `Depends(require_csrf)` is on the same list. Bearer-mode callers are skipped by `require_csrf`'s standard rule (no CSRF surface). Cookie-mode callers MUST echo the `csrf_token` cookie back via the `X-CSRF-Token` header.

2. **Content-type filter** (`excel_import.ALLOWED_CT`):
   - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
   - `application/vnd.ms-excel`
   Anything else → 415 Unsupported Media Type.

3. **Lock check.** If `template.locked == True` → 409 (can't import into a locked template; clone it first).

4. **Idempotency gate** (when `Idempotency-Key` header present). Look up `konkin_import_log.idempotency_key = <key>`. If a row exists → return `200 {"data": {"status": "already_applied", "log_id": "<uuid>", "summary": {...}}}` WITHOUT re-parsing.

5. **Streaming parse.** `openpyxl.load_workbook(BytesIO(raw), read_only=True, data_only=True)` — constant memory, no formula evaluation, no path traversal (BytesIO → never on disk).

6. **SAVEPOINT per sheet.** `async with db.begin_nested():` so a malformed sheet rolls back ONLY that sheet. Outer transaction commits atomically on full success.

7. **Phase-1 scope.** `_import_sheet` counts non-empty rows but DOES NOT create perspektif/indikator rows. The test suite asserts the surface (status codes, idempotency semantics, log row, CSRF) — Phase-2 / Plan 07 seed work materialises rows.

8. **Idempotency log write.** Only when `Idempotency-Key` is present. `konkin_import_log` row contains `template_id`, `idempotency_key` (UNIQUE), `summary` (JSONB per-sheet counts), `imported_by` (FK users.id ON DELETE SET NULL).

---

## Updated No-Upload Test Allow-List

```python
# backend/tests/test_no_upload_policy.py
ALLOWED_MULTIPART_PATHS: set[str] = {
    "/api/v1/konkin/templates/{template_id}/import-from-excel",
}
```

Exactly one multipart endpoint — locked. The companion `test_link_eviden_is_url_only` was updated (Rule 1 fix) to walk into `anyOf` branches because Pydantic v2 renders `HttpUrl | None` as:
```json
{"anyOf": [{"format": "uri", "type": "string", ...}, {"type": "null"}], ...}
```
The earlier check only inspected top-level `format` and reported false positives on nullable URLs.

---

## B-04 Audit: Post-Migration `users` Table

After `alembic upgrade head` (0001 → 0002 → 0003):

| Column          | Type                          | Nullable | Notes                                        |
| --------------- | ----------------------------- | -------- | -------------------------------------------- |
| `id`            | UUID                          | NOT NULL | PK, `uuid_generate_v4()` default             |
| `email`         | VARCHAR(255)                  | NOT NULL | UNIQUE, indexed                              |
| `full_name`     | VARCHAR(255)                  | NOT NULL |                                              |
| `password_hash` | VARCHAR(255)                  | NOT NULL | bcrypt hash                                  |
| `is_active`     | BOOLEAN                       | NOT NULL | default `true`                               |
| **`bidang_id`** | **UUID**                      | **NULL** | **added by 0003; FK `fk_users_bidang_id`**   |
| `created_at`    | TIMESTAMP WITH TIME ZONE      | NOT NULL | default `now()`                              |
| `updated_at`    | TIMESTAMP WITH TIME ZONE      | NOT NULL | default `now()`                              |
| `deleted_at`    | TIMESTAMP WITH TIME ZONE      | NULL     | soft-delete sentinel                         |

**FK constraint added in 0003:** `fk_users_bidang_id` → `bidang(id)` ON DELETE SET NULL.

Plan 05's 0002 migration deliberately did NOT touch `bidang_id` — the FK target table didn't exist yet (CONTEXT.md "Migration FK ordering"). Plan 06 is the place where both the column and the FK are introduced, and the `User` model file is amended in-place.

---

## Threat-Model Disposition (post-implementation)

| Threat ID | Disposition | Implementation                                                              |
| --------- | ----------- | --------------------------------------------------------------------------- |
| T-06-T-01 | MITIGATED   | Pydantic `BidangCreate` / `IndikatorCreate` / etc. enumerate exact fields; ORM never binds raw body. |
| T-06-T-02 | MITIGATED   | `excel_import` reads from `BytesIO`; no disk writes; filename never touched. |
| T-06-T-03 | MITIGATED   | `_ensure_unlocked(template)` raises 409 on every mutating route.            |
| T-06-T-04 | MITIGATED   | `import-from-excel` carries `Depends(require_csrf)` — B-07 contract.        |
| T-06-D-01 | MITIGATED   | openpyxl `read_only=True, data_only=True` + per-sheet SAVEPOINT; Plan 02 Nginx `client_max_body_size 25M` upstream. |
| T-06-I-01 | MITIGATED   | Bidang router applies `WHERE Bidang.id == user.bidang_id` when caller is `pic_bidang` and not super_admin/admin_unit. |
| T-06-E-01 | MITIGATED   | Every write route carries `Depends(require_role("super_admin","admin_unit"))` in `dependencies`. |
| T-06-E-02 | MITIGATED   | `test_no_upload_policy::test_only_allowed_multipart_endpoints` asserts allow-list exactly. |

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Test logic bug] Nullable HttpUrl mis-detected as non-URI by `test_link_eviden_is_url_only`**
- **Found during:** Task 2 (right after the routers + schemas committed and OpenAPI got the new components)
- **Issue:** Pydantic v2 renders `HttpUrl | None` as `{"anyOf": [{"format": "uri", ...}, {"type": "null"}], ...}` — `spec.get("format")` returns `None`, not `"uri"`. The Wave-2 contract test only checked the top-level `format` key, so the very first nullable `link_eviden` field would have tripped it. Without this fix, the entire Wave 4 test suite would fail the moment the master-data schemas were introduced — a real regression.
- **Fix:** Added `_is_uri_spec(spec)` helper that walks into `anyOf` / `oneOf` / `allOf` branches and returns True if any branch declares `format=uri`. Top-level non-nullable `HttpUrl` and nullable `HttpUrl | None` both satisfy the contract.
- **Files modified:** `backend/tests/test_no_upload_policy.py`
- **Commit:** `09ce3bf` (Task 3 — bundled with the allow-list update because both touch the same file)

**2. [Rule 1 — Cosmetic] Removed "Bearer auth assumed" *phrases* from new docstrings**
- **Found during:** Task 2 verifier run
- **Issue:** My initial draft of `master_konkin.py`'s module docstring + the import-from-excel comment explained the B-07 fix by *quoting* the misleading earlier-draft phrase "Bearer auth assumed" — but the plan's static grep is `grep 'Bearer auth assumed'` (no escape), so my quoted explanation tripped it. Function correctness was unaffected; the regex was just too eager.
- **Fix:** Rewrote both comments to describe the misleading earlier-draft idea without naming the exact phrase. CSRF behaviour is unchanged; the grep now returns 0.
- **Files modified:** `backend/app/routers/master_konkin.py`
- **Commit:** `e5a7bf8` (Task 2 — fixed before commit)

**3. [Procedural] Single-line `op.add_column` for static grep compatibility**
- **Found during:** Task 1 string-content check
- **Issue:** My initial `op.add_column` was multi-line (Black-style) — the plan's regex `add_column.+users.+bidang_id` is non-multiline and missed it.
- **Fix:** Collapsed to one line. Functionally identical.
- **Files modified:** `backend/alembic/versions/20260512_140000_0003_master_data.py`
- **Commit:** `59163a6` (Task 1 — fixed before commit)

No architectural deviations (no Rule 4 escalations).

---

## Authentication Gates

None encountered. Every test layer that needs auth uses the in-process httpx `AsyncClient` + the fixture-seeded users; no external credentials required.

---

## Verification Status

| Verification step                                                            | Status        | Notes                                                                   |
| ---------------------------------------------------------------------------- | ------------- | ----------------------------------------------------------------------- |
| All model files load via SQLAlchemy `inspect`                                | PASS          | bidang_id present on User; is_pengurang+pengurang_cap on Perspektif     |
| Alembic chain 0001 → 0002 → 0003 intact                                      | PASS (static) | revision/down_revision strings verified; live `upgrade head` deferred to Plan 07 docker e2e |
| `users.bidang_id` + `fk_users_bidang_id` declared in 0003                    | PASS          | single-line `op.add_column` + `op.create_foreign_key`                   |
| `idx_ml_stream_structure` GIN index declared in 0003                         | PASS          | `op.execute("CREATE INDEX ... USING GIN (structure)")`                  |
| OpenAPI surface = exactly one multipart endpoint                             | PASS          | `/api/v1/konkin/templates/{template_id}/import-from-excel`              |
| All `require_role(...)` calls use spec names (B-01/B-02)                     | PASS          | Both routers use only `super_admin`, `admin_unit`, `pic_bidang`         |
| `import-from-excel` has `Depends(require_csrf)` (B-07)                       | PASS          | static regex AND OpenAPI dependency-tree confirm                        |
| No "Bearer auth assumed" comment anywhere in router/services/tests           | PASS          | `grep -c 'Bearer auth assumed' = 0`                                     |
| `test_no_upload_policy.py` passes (host-side, no DB needed)                  | PASS          | 2/2                                                                     |
| `test_bootstrap.py` passes                                                    | PASS          | 2/2                                                                     |
| `tests/test_bidang.py`, `test_master_konkin.py`, `test_ml_stream.py` collect | PASS (20/20)  | DB-dependent run deferred to Plan 07 container e2e (per plan B-06 fallback rule; docker stack not running in this worktree). |
| Host-side import smoke for all new modules                                   | PASS          | `from app.services.excel_import import import_workbook; from tests import …` |

The "live pytest inside `pulse-backend`" gate in the plan's `<verification>` block is a Plan 07 responsibility — Plan 07 brings the docker stack up (deps `01-02 + 01-04 + 01-05 + 01-06`), runs `alembic upgrade head`, and exercises the full pytest suite end-to-end. This plan ships the code at static + import-smoke confidence as the plan's B-06 fallback explicitly allows.

---

## Known Stubs

**`app.services.excel_import._import_sheet`** — Phase-1 placeholder. It iterates `sheet.iter_rows(values_only=True)` and returns the count of non-empty rows, but does NOT create `Perspektif` or `Indikator` ORM rows. This is documented in the function's own docstring AND in the plan ("Phase 1 scope: accept perspektif + indikator rows from a single workbook" → "returns 0 rows for now"). Plan 07's seed module materialises the real Konkin 2026 rows; a future Phase-2 plan will replace `_import_sheet` with the real sheet-by-sheet parser. **Resolution slot:** Phase 2 / Plan 07 seed. No additional work is required from Plan 06 because the test suite intentionally asserts the surface (idempotency, status codes, log row), not the row counts.

No other stubs.

---

## Threat Flags

None — the threat model in the plan covered every new surface introduced.

## TDD Gate Compliance

Plan is `type: execute`, not `type: tdd` — no RED/GREEN gates required. The test files in Task 3 are written after their target code (Task 1 + Task 2) per the plan's explicit task order.

---

## Self-Check: PASSED

**Files verified to exist:**

- FOUND: `backend/app/models/bidang.py`
- FOUND: `backend/app/models/konkin_template.py`
- FOUND: `backend/app/models/perspektif.py`
- FOUND: `backend/app/models/indikator.py`
- FOUND: `backend/app/models/ml_stream.py`
- FOUND: `backend/app/models/konkin_import_log.py`
- FOUND: `backend/app/models/user.py` (amended with `bidang_id`)
- FOUND: `backend/app/schemas/master.py`
- FOUND: `backend/app/routers/master_bidang.py`
- FOUND: `backend/app/routers/master_konkin.py`
- FOUND: `backend/app/services/excel_import.py`
- FOUND: `backend/alembic/versions/20260512_140000_0003_master_data.py`
- FOUND: `backend/tests/test_bidang.py`
- FOUND: `backend/tests/test_master_konkin.py`
- FOUND: `backend/tests/test_ml_stream.py`
- FOUND: `backend/tests/test_no_upload_policy.py` (updated)

**Commits verified in `git log`:**

- FOUND: `59163a6` — feat(01-06): master-data models + alembic 0003 (W-07 + B-04)
- FOUND: `e5a7bf8` — feat(01-06): Pydantic schemas + bidang/konkin routers (B-01/B-02 + B-07 + W-07)
- FOUND: `09ce3bf` — feat(01-06): excel_import service + master-data tests + locked allow-list
