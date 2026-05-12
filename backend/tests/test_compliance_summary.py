"""Unit-mode checks for Phase 4 compliance summary primitives."""

from decimal import Decimal
from pathlib import Path

from app.services.compliance_summary import calculate_laporan_pengurang


def test_laporan_pengurang_counts_late_days():
    assert calculate_laporan_pengurang(2, True, Decimal("0.039"), Decimal("0.039")) == Decimal("0.0780")


def test_laporan_pengurang_adds_invalidity_deduction():
    assert calculate_laporan_pengurang(2, False, Decimal("0.039"), Decimal("0.039")) == Decimal("0.1170")


def test_phase4_compliance_routes_registered():
    from app.routers import api_router

    paths = {getattr(route, "path", None) for route in api_router.routes}
    assert "/api/v1/compliance/summary" in paths
    assert "/api/v1/compliance/laporan-definisi" in paths
    assert "/api/v1/compliance/component-realizations" in paths


def test_compliance_migration_seeds_blueprint_report_names():
    migration = Path(__file__).resolve().parents[1] / "alembic/versions/20260513_140000_0008_compliance_tracker.py"
    text = migration.read_text(encoding="utf-8")
    for code in ["PENGUSAHAAN", "BA_TRANSFER_ENERGI", "KEUANGAN", "NAVITAS", "PACA", "ICOFR"]:
        assert code in text
    assert "sa.Computed" in text
