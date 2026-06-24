from policypulse_api.demo import build_demo_result
from policypulse_api.reports import build_markdown, build_pdf


def test_markdown_report_contains_core_sections() -> None:
    report = build_markdown(build_demo_result())
    assert "# PolicyPulse AI Consultation Report" in report
    assert "## Public concerns" in report
    assert "## Executive memo" in report
    assert "COM-001" in report


def test_pdf_report_is_generated() -> None:
    report = build_pdf(build_demo_result())
    assert report.startswith(b"%PDF")
    assert len(report) > 2_000
