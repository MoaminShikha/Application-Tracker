"""Executable model tests for validation boundaries and serialization behavior."""

from datetime import date, datetime, timedelta

import pytest

from job_tracker.models import (
    Application,
    ApplicationEvent,
    ApplicationStatus,
    Company,
    Position,
    Recruiter,
    ValidationError,
)


def test_company_validates_required_and_optional_constraints():
    Company(name="Acme", industry="Tech", location="Remote", notes="x").validate()
    with pytest.raises(ValidationError):
        Company(name="   ").validate()
    with pytest.raises(ValidationError):
        Company(name="Acme", location=" ").validate()


def test_position_rejects_invalid_level_and_long_title():
    Position(title="Backend Engineer", level="Senior").validate()
    Position(title="Student Intern", level="Student").validate()
    with pytest.raises(ValidationError):
        Position(title="A" * 51, level="Senior").validate()
    with pytest.raises(ValidationError):
        Position(title="Backend Engineer", level="Staff").validate()


def test_recruiter_email_validation_and_optional_fields():
    Recruiter(name="Alex", email="alex@example.com").validate()
    Recruiter(name="Alex", email=None, phone=None).validate()
    with pytest.raises(ValidationError):
        Recruiter(name="Alex", email="bad-email").validate()


def test_application_date_and_job_id_rules():
    Application(
        company_id=1,
        position_id=1,
        current_status=1,
        applied_date=date.today(),
        job_id=" GH-123 ",
    ).validate()

    with pytest.raises(ValidationError):
        Application(company_id=1, position_id=1, current_status=1, applied_date=date.today() + timedelta(days=1)).validate()
    with pytest.raises(ValidationError):
        Application(company_id=1, position_id=1, current_status=1, applied_date=date.today() - timedelta(days=366)).validate()
    with pytest.raises(ValidationError):
        Application(company_id=1, position_id=1, current_status=1, applied_date=date.today(), job_id="   ").validate()


def test_application_string_date_parsing_and_days_in_status():
    app = Application(company_id=1, position_id=1, current_status=1, applied_date=str(date.today()))
    app.validate()
    assert isinstance(app.applied_date, date)

    app.created_at = datetime.now() - timedelta(days=3)
    assert app.days_in_current_status() >= 3


def test_application_event_validation_and_string_datetime():
    event = ApplicationEvent(application_id=1, event_type="Phone Screen", event_date=datetime.now().isoformat())
    event.validate()
    assert isinstance(event.event_date, datetime)

    with pytest.raises(ValidationError):
        ApplicationEvent(application_id=0, event_type="Phone Screen", event_date=datetime.now()).validate()
    with pytest.raises(ValidationError):
        ApplicationEvent(application_id=1, event_type="", event_date=datetime.now()).validate()


def test_application_status_validation_and_helpers():
    status = ApplicationStatus(status_name="Applied", description="submitted", is_terminal=False)
    status.validate()
    assert status.is_final_state() is False
    assert str(status) == "Applied"

    with pytest.raises(ValidationError):
        ApplicationStatus(status_name="Invalid", is_terminal=False).validate()
    with pytest.raises(ValidationError):
        ApplicationStatus(status_name="Rejected", is_terminal=False).validate()


def test_model_round_trip_and_equality():
    company = Company(id=1, name="Acme", industry="Tech", location="Remote")
    company.validate()
    payload = company.to_dict()
    clone = Company.from_dict(payload)

    assert clone == company
    assert "Acme" in repr(company)

