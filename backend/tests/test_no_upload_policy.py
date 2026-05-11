"""Contract test for REQ-no-evidence-upload (DEC-010, CONSTR-no-file-upload).

Plan 06 (master data) introduces the ONLY allowed multipart endpoint
``POST /api/v1/konkin/templates/{template_id}/import-from-excel`` — the
admin-only Konkin Excel-template import (B-07: CSRF-protected). Every other
multipart endpoint in the OpenAPI surface is a regression.

The companion ``test_link_eviden_is_url_only`` walks the OpenAPI components
schemas and rejects any ``link_eviden`` property that is NOT declared as
``format=uri`` (i.e. Pydantic ``HttpUrl``). Nullable HttpUrl fields render
as ``{"anyOf": [{"format": "uri", ...}, {"type": "null"}]}`` in Pydantic
v2 — we walk into ``anyOf`` to find the URI branch.
"""

from app.main import app

# Plan 06 locked allow-list — exactly one multipart endpoint.
ALLOWED_MULTIPART_PATHS: set[str] = {
    "/api/v1/konkin/templates/{template_id}/import-from-excel",
}


def _multipart_paths() -> set[str]:
    schema = app.openapi()
    paths: set[str] = set()
    for path, methods in schema["paths"].items():
        for verb, op in methods.items():
            if verb.startswith("x-"):
                continue
            body = op.get("requestBody") or {}
            content = body.get("content") or {}
            if "multipart/form-data" in content:
                paths.add(path)
    return paths


def _is_uri_spec(spec: dict) -> bool:
    """True if `spec` (or any anyOf/oneOf branch of it) declares format=uri.

    Pydantic v2 renders ``HttpUrl | None`` as::

        {"anyOf": [{"format": "uri", "type": "string", ...},
                   {"type": "null"}], ...}

    and a non-nullable ``HttpUrl`` as::

        {"format": "uri", "type": "string", ...}

    Both shapes must satisfy the URI-only contract for ``link_eviden``.
    """
    if spec.get("format") == "uri":
        return True
    for key in ("anyOf", "oneOf", "allOf"):
        branches = spec.get(key) or []
        if isinstance(branches, list):
            for b in branches:
                if isinstance(b, dict) and _is_uri_spec(b):
                    return True
    return False


def test_only_allowed_multipart_endpoints():
    got = _multipart_paths()
    extras = got - ALLOWED_MULTIPART_PATHS
    missing = ALLOWED_MULTIPART_PATHS - got
    assert not extras, f"Unexpected multipart endpoints: {extras}"
    assert not missing, f"Expected multipart endpoints not present: {missing}"


def test_link_eviden_is_url_only():
    schema = app.openapi()
    offenders: list[str] = []
    for name, s in (schema.get("components", {}).get("schemas") or {}).items():
        for prop, spec in (s.get("properties") or {}).items():
            if prop == "link_eviden" and not _is_uri_spec(spec):
                offenders.append(f"{name}.{prop}")
    assert not offenders, (
        f"link_eviden must be format=uri (Pydantic HttpUrl): {offenders}"
    )
