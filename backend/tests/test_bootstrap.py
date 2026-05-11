"""Wave-0 bootstrap tests — fail fast on circular imports, missing settings,
or broken router auto-discovery before the container even tries to boot.
"""


def test_app_imports():
    # Catches circular imports, missing settings, syntax errors before the container builds.
    from app.main import app

    assert app.title.startswith("PULSE")


def test_router_auto_include():
    from app.routers import api_router

    prefixed = {r.path for r in api_router.routes}
    assert "/api/v1/health" in prefixed, f"got {prefixed}"
    assert "/api/v1/health/detail" in prefixed
    assert "/api/v1/metrics" in prefixed
