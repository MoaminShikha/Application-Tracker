"""Tests for analytics service calculations with mocked executor."""

from contextlib import contextmanager

from job_tracker.analytics.analytics_service import AnalyticsService


class _FakeExecutor:
    def execute_query_single(self, query, params=None):
        if "COUNT(*)::float AS total" in query:
            return {
                "total": 10.0,
                "reached_interview": 6.0,
                "reached_offer": 3.0,
                "accepted": 2.0,
            }
        return {
            "total_applications": 4,
            "active_applications": 2,
            "offers": 1,
            "accepted": 1,
            "rejected": 1,
        }

    def execute_query(self, query, params=None):
        return [{"status_name": "Applied", "count": 2}]


@contextmanager
def _fake_executor_context():
    yield _FakeExecutor()


def test_get_conversion_rates_calculates_percentages():
    svc = AnalyticsService.__new__(AnalyticsService)
    svc._executor = _fake_executor_context

    out = svc.get_conversion_rates()
    assert out["application_to_interview_pct"] == 60.0
    assert out["application_to_offer_pct"] == 30.0
    assert out["application_to_accept_pct"] == 20.0


def test_get_overview_counts_returns_values():
    svc = AnalyticsService.__new__(AnalyticsService)
    svc._executor = _fake_executor_context

    out = svc.get_overview_counts()
    assert out["total_applications"] == 4
    assert out["active_applications"] == 2

