"""Tests for application use-case orchestration layer."""

from datetime import date

import pytest

from job_tracker.domain.exceptions import NotFoundError
from job_tracker.use_cases.application_flow import ApplicationFlow


class _FakeApp:
    def __init__(self, app_id=1, status=1):
        self.id = app_id
        self.current_status = status


class _FakeApplicationService:
    def __init__(self):
        self.created_payload = None
        self.updated_payload = None

    def create_application(self, **kwargs):
        self.created_payload = kwargs
        return _FakeApp(app_id=7)

    def get_all_applications(self, options=None):
        return [_FakeApp(app_id=1), _FakeApp(app_id=2)]

    def update_application_status(self, application_id, new_status):
        self.updated_payload = (application_id, new_status)
        return _FakeApp(app_id=application_id, status=new_status)


class _FakeStatusService:
    def __init__(self, mapping=None):
        self.mapping = mapping or {"Applied": 1, "Interview Scheduled": 2}

    def get_status_id_by_name(self, name):
        return self.mapping.get(name)


def test_create_application_delegates_to_service():
    app_svc = _FakeApplicationService()
    flow = ApplicationFlow(application_service=app_svc, status_service=_FakeStatusService())

    app = flow.create_application(company_id=1, position_id=2, applied_date=date.today(), job_id="GH-1")

    assert app.id == 7
    assert app_svc.created_payload["company_id"] == 1
    assert app_svc.created_payload["position_id"] == 2


def test_update_status_with_name_resolves_id_and_updates():
    app_svc = _FakeApplicationService()
    flow = ApplicationFlow(application_service=app_svc, status_service=_FakeStatusService())

    app = flow.update_status(10, "Interview Scheduled")

    assert app.id == 10
    assert app_svc.updated_payload == (10, 2)


def test_update_status_raises_not_found_for_unknown_status_name():
    app_svc = _FakeApplicationService()
    flow = ApplicationFlow(application_service=app_svc, status_service=_FakeStatusService(mapping={}))

    with pytest.raises(NotFoundError):
        flow.update_status(10, "Unknown")


def test_update_status_accepts_numeric_status_id_without_lookup():
    app_svc = _FakeApplicationService()
    flow = ApplicationFlow(application_service=app_svc, status_service=_FakeStatusService(mapping={}))

    app = flow.update_status(10, "2")

    assert app.id == 10
    assert app_svc.updated_payload == (10, 2)


