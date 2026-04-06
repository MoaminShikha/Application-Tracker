"""Tests for typed query options integration in services."""

from contextlib import contextmanager

from job_tracker.services.application_service import ApplicationService
from job_tracker.services.company_service import CompanyService
from job_tracker.services.query_options import ApplicationQueryOptions, ListQueryOptions


class _CaptureExecutor:
    def __init__(self, rows):
        self.rows = rows
        self.last_query = None
        self.last_params = None

    def execute_query(self, query, params=None):
        self.last_query = query
        self.last_params = params
        return self.rows


def test_application_service_uses_default_sort_without_options():
    capture = _CaptureExecutor([])

    @contextmanager
    def fake_executor():
        yield capture

    svc = ApplicationService.__new__(ApplicationService)
    svc._executor = fake_executor

    svc.get_all_applications()

    assert "ORDER BY created_at DESC" in capture.last_query


def test_application_service_applies_filters_sort_and_pagination():
    capture = _CaptureExecutor([])

    @contextmanager
    def fake_executor():
        yield capture

    svc = ApplicationService.__new__(ApplicationService)
    svc._executor = fake_executor

    options = ApplicationQueryOptions(
        sort_by="applied_date",
        sort_dir="asc",
        company_id=5,
        status_id=2,
        limit=10,
        offset=20,
    )
    svc.get_all_applications(options=options)

    assert "ORDER BY applied_date ASC" in capture.last_query
    assert "LIMIT %s" in capture.last_query
    assert "OFFSET %s" in capture.last_query
    assert capture.last_params == (5, 5, 2, 2, 10, 20)


def test_company_service_default_and_custom_sort():
    capture = _CaptureExecutor([])

    @contextmanager
    def fake_executor():
        yield capture

    svc = CompanyService.__new__(CompanyService)
    svc._executor = fake_executor

    svc.get_all_companies()
    assert "ORDER BY created_at DESC" in capture.last_query

    svc.get_all_companies(options=ListQueryOptions(sort_by="name", sort_dir="asc", limit=5))
    assert "ORDER BY name ASC" in capture.last_query
    assert capture.last_params == (5,)

