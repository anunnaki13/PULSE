"""Contract test for REQ-no-evidence-upload (DEC-010, CONSTR-no-file-upload).

Phase 1 contract (Wave 2): ZERO multipart endpoints. Plan 06 (master data)
will add the only allowed multipart route —
`POST /api/v1/konkin/templates/{template_id}/import-from-excel` — and
amend `ALLOWED_MULTIPART_PATHS` below to `{that one path}`. Until then,
the allow-list is empty so the assertion fires the moment anyone (or any
Plan-04/05 mistake) introduces a multipart endpoint.

The companion `test_link_eviden_is_url_only` walks the OpenAPI components
schema and rejects any property named `link_eviden` that is not declared
as `format=uri` (i.e. Pydantic `HttpUrl`). Plan 06 introduces models with
`link_eviden`; this test guards the contract from the moment they land.
"""

from app.main import app

# Phase 1 contract: ZERO multipart endpoints in Wave 2.
# Plan 06 will add /api/v1/konkin/templates/{template_id}/import-from-excel AND update
# ALLOWED_MULTIPART_PATHS in this test to {that path}.
ALLOWED_MULTIPART_PATHS: set[str] = set()


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
            if prop == "link_eviden" and spec.get("format") != "uri":
                offenders.append(f"{name}.{prop}")
    assert not offenders, f"link_eviden must be format=uri (Pydantic HttpUrl): {offenders}"
