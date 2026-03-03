"""High-level happy path checks without DB dependency."""

from job_tracker.analytics.reporting import build_dashboard_rows


def test_happy_path_dashboard_rendering():
    lines = build_dashboard_rows(
        overview={"total_applications": 10, "active_applications": 4, "offers": 2, "accepted": 1, "rejected": 3},
        distribution=[{"status_name": "Applied", "count": 4}, {"status_name": "Rejected", "count": 3}],
        conversions={
            "application_to_interview_pct": 50.0,
            "application_to_offer_pct": 20.0,
            "application_to_accept_pct": 10.0,
        },
    )
    assert lines[0].startswith("=== Application Tracker Dashboard")
    assert any("App -> Interview" in line for line in lines)

