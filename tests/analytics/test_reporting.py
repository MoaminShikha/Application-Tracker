"""Tests for reporting helpers."""

from job_tracker.analytics.reporting import build_dashboard_rows, to_csv_report, to_json_report


def test_to_json_report_contains_keys():
    payload = {"overview": {"total_applications": 3}}
    out = to_json_report(payload)
    assert "overview" in out
    assert "total_applications" in out


def test_to_csv_report_writes_header_and_rows():
    rows = [{"id": 1, "company": "A"}, {"id": 2, "company": "B"}]
    out = to_csv_report(rows)
    assert "id,company" in out
    assert "1,A" in out
    assert "2,B" in out


def test_build_dashboard_rows_has_summary_lines():
    lines = build_dashboard_rows(
        {"total_applications": 5, "active_applications": 2, "offers": 1, "accepted": 1, "rejected": 2},
        [{"status_name": "Applied", "count": 2}],
        {"application_to_interview_pct": 40.0, "application_to_offer_pct": 20.0, "application_to_accept_pct": 20.0},
    )
    assert any("Total applications" in line for line in lines)
    assert any("Status distribution" in line for line in lines)

