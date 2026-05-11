"""Excel-template import service (REQ-no-evidence-upload final form).

This module is the *interface* that ``master_konkin.import_from_excel``
imports. Task 2 introduces it with a minimal interface so the router module
loads; Task 3 (same plan) replaces ``import_workbook`` with the full
openpyxl streaming + per-sheet SAVEPOINT + Idempotency-Key implementation.

Public surface:

- ``ALLOWED_CT`` — content-type allow-list, checked by the router before
  reading the body. Anything else returns 415.
- ``import_workbook(db, template, raw, idempotency_key, imported_by)`` —
  async function returning ``{"status": "imported"|"already_applied",
  "summary": {sheet_name: row_count, ...}}``. Idempotency-Key gate: when a
  matching ``konkin_import_log.idempotency_key`` row exists, the function
  short-circuits to ``already_applied`` without re-parsing.
"""

from __future__ import annotations

from uuid import UUID

# Plan 06 final allow-list — keep in sync with
# `backend/tests/test_no_upload_policy.py::ALLOWED_MULTIPART_PATHS`.
ALLOWED_CT: set[str] = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
}


async def import_workbook(
    db,
    template,
    raw: bytes,
    idempotency_key: str | None,
    imported_by: UUID,
) -> dict:
    """Placeholder implementation — replaced in Task 3 with the streaming
    openpyxl + SAVEPOINT-per-sheet + Idempotency-Key implementation.

    Keep this signature stable: the router calls it with these exact kwargs.
    """
    raise NotImplementedError(
        "excel_import.import_workbook is finalised in Task 3 of Plan 06"
    )
