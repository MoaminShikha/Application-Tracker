"""Smoke tests for CLI command wiring."""

from click.testing import CliRunner

import job_tracker.cli.main as cli_main
from job_tracker.models.company import Company


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

