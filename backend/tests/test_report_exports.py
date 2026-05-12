"""Unit-mode checks for Phase 4 report export routes and renderers."""

from app.services.report_exports import render_csv, render_pdf, render_word_html


def test_report_export_routes_registered():
    from app.routers import api_router

    paths = {getattr(route, "path", None) for route in api_router.routes}
    assert "/api/v1/reports/nko-semester" in paths
    assert "/api/v1/reports/assessment-sheet" in paths
    assert "/api/v1/reports/compliance-detail" in paths
    assert "/api/v1/reports/recommendation-tracker" in paths


def test_csv_renderer_is_excel_friendly_utf8_bom():
    content = render_csv(["A", "B"], [["NKO", "103.36"]])
    assert content.startswith(b"\xef\xbb\xbf")
    assert b"NKO" in content


def test_word_renderer_contains_expected_heading():
    content = render_word_html("Laporan NKO", [("Ringkasan", [["NKO Final", "103.36"]])])
    assert b"<h1>Laporan NKO</h1>" in content
    assert b"NKO Final" in content


def test_pdf_renderer_creates_pdf_header():
    content = render_pdf("Laporan NKO", ["NKO Final 103.36"])
    assert content.startswith(b"%PDF-1.4")
    assert b"%%EOF" in content
