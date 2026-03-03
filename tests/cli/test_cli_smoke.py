"""Smoke tests for CLI command wiring."""

import importlib
from datetime import date

from click.testing import CliRunner
from job_tracker.models.company import Company

cli_main = importlib.import_module("job_tracker.cli.main")


class _FakeCompanyService:
    def create_company(self, name, location, industry=None, notes=None):
        return Company(id=1, name=name, location=location, industry=industry, notes=notes)


class _FakeAnalyticsService:
    def get_overview_counts(self):
        return {"total_applications": 0, "active_applications": 0, "offers": 0, "accepted": 0, "rejected": 0}

    def get_status_distribution(self):
        return []

    def get_conversion_rates(self):
        return {
            "application_to_interview_pct": 0.0,
            "application_to_offer_pct": 0.0,
            "application_to_accept_pct": 0.0,
        }

    def get_recent_applications(self, days=30):
        return []

    def get_response_time_by_company(self):
        return []


class _FakeApplication:
    def __init__(self, app_id, company_id, position_id, applied_date, job_id=None):
        self.id = app_id
        self.company_id = company_id
        self.position_id = position_id
        self.current_status = 1
        self.applied_date = applied_date
        self.job_id = job_id


class _FakeApplicationService:
    def create_application(self, company_id, position_id, applied_date=None, recruiter_id=None, job_id=None, notes=None):
        return _FakeApplication(
            app_id=7,
            company_id=company_id,
            position_id=position_id,
            applied_date=applied_date or date.today(),
            job_id=job_id,
        )


def test_add_company_command(monkeypatch):
    monkeypatch.setattr(cli_main, "CompanyService", _FakeCompanyService)
    runner = CliRunner()
    result = runner.invoke(cli_main.cli, ["add-company", "--name", "Acme", "--location", "Remote"])
    assert result.exit_code == 0
    assert "Created company #1" in result.output


def test_analytics_command(monkeypatch):
    monkeypatch.setattr(cli_main, "AnalyticsService", _FakeAnalyticsService)
    runner = CliRunner()
    result = runner.invoke(cli_main.cli, ["analytics", "--days", "7"])
    assert result.exit_code == 0
    assert "Application Tracker Dashboard" in result.output


def test_add_application_accepts_optional_job_id(monkeypatch):
    monkeypatch.setattr(cli_main, "ApplicationService", _FakeApplicationService)
    runner = CliRunner()
    result = runner.invoke(
        cli_main.cli,
        [
            "add-application",
            "--company-id",
            "1",
            "--position-id",
            "2",
            "--job-id",
            "GH-12345",
        ],
    )
    assert result.exit_code == 0
    assert "Created application #7" in result.output
    assert "Job ID: GH-12345" in result.output
