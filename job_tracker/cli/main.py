"""CLI entrypoint for Application Tracker."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from job_tracker.analytics import AnalyticsService, build_dashboard_rows, to_csv_report, to_json_report
from job_tracker.database.init_db import InitDB
from job_tracker.domain.exceptions import (
    ConstraintViolationError,
    InvalidTransitionError,
    NotFoundError,
    ValidationFailedError,
)
from job_tracker.services import (
    CompanyService,
    EventService,
    PositionService,
    RecruiterService,
    StatusService,
)
from job_tracker.services.query_options import ApplicationQueryOptions
from job_tracker.use_cases import ApplicationFlow
from job_tracker.utils.colors import colorize_status

# Import interactive mode and menu
from job_tracker.cli.interactive import interactive as interactive_mode
from job_tracker.cli.menu import menu as menu_mode


def _ensure_database_ready() -> None:
    """Ensure schema and additive migrations are applied before running CLI commands."""
    InitDB().initialize_database()


def build_cli() -> click.Group:
    @click.group(help="Application Tracker CLI - Track your job search pipeline\n\n💡 TIP: Run 'python -m job_tracker.cli menu' for guided menu interface!")
    def cli() -> None:
        try:
            _ensure_database_ready()
        except Exception as e:
            raise click.ClickException(f"Database initialization failed: {e}")

    # Add menu mode as primary entry point
    cli.add_command(menu_mode, name="menu")

    # Add interactive mode as a subcommand
    cli.add_command(interactive_mode, name="interactive")

    @cli.command("add-company")
    @click.option("--name", required=True, type=str, help="Company name (unique)")
    @click.option("--location", default=None, type=str, help="Location (optional, e.g., 'Seattle', 'Remote')")
    @click.option("--industry", default=None, type=str, help="Industry sector")
    @click.option("--notes", default=None, type=str, help="Additional notes")
    def add_company(name: str, location: Optional[str], industry: Optional[str], notes: Optional[str]) -> None:
        """Add a new company to track applications for."""
        try:
            svc = CompanyService()
            company = svc.create(name=name, location=location, industry=industry, notes=notes)
            click.echo(f"✅ Created company #{company.id}: {company.name}")
            if company.location:
                click.echo(f"   📍 Location: {company.location}")
            if company.industry:
                click.echo(f"   🏢 Industry: {company.industry}")
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)
            raise click.Abort()

    @cli.command("list-companies")
    def list_companies() -> None:
        """View all companies you're tracking."""
        try:
            svc = CompanyService()
            companies = svc.get_all()
            if not companies:
                click.echo("📭 No companies found. Add one with: add-company")
                return
            click.echo(f"\n📋 Companies ({len(companies)} total):")
            click.echo("=" * 60)
            for c in companies:
                click.echo(f"  {c.id:3d}  {c.name:30s}  📍 {c.location}")
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)

    @cli.command("add-position")
    @click.option("--title", required=True, type=str, help="Job title")
    @click.option("--level", required=True, type=str, help="Seniority: Entry/Intern/Junior/Mid/Senior/Student/Lead/Manager")
    def add_position(title: str, level: str) -> None:
        """Add a job position/title."""
        try:
            svc = PositionService()
            position = svc.create(title=title, level=level)
            click.echo(f"✅ Created position #{position.id}: {position.title} ({position.level})")
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)
            click.echo("💡 Valid levels: Entry, Intern, Junior, Mid, Senior, Student, Lead, Manager")
            raise click.Abort()

    @cli.command("add-recruiter")
    @click.option("--name", required=True, type=str, help="Recruiter name")
    @click.option("--email", default=None, type=str, help="Email address")
    @click.option("--phone", default=None, type=str, help="Phone number")
    @click.option("--company-id", default=None, type=int, help="Associated company ID")
    def add_recruiter(name: str, email: Optional[str], phone: Optional[str], company_id: Optional[int]) -> None:
        """Add a recruiter or point of contact."""
        try:
            svc = RecruiterService()
            recruiter = svc.create(name=name, email=email, phone=phone, company_id=company_id)
            click.echo(f"✅ Created recruiter #{recruiter.id}: {recruiter.name}")
            if recruiter.email:
                click.echo(f"   📧 {recruiter.email}")
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)
            raise click.Abort()

    @cli.command("list-recruiters")
    def list_recruiters() -> None:
        """View all recruiters you're tracking."""
        try:
            svc = RecruiterService()
            recruiters = svc.get_all()
            if not recruiters:
                click.echo("📭 No recruiters found. Add one with: add-recruiter")
                return
            click.echo(f"\n👤 Recruiters ({len(recruiters)} total):")
            click.echo("=" * 60)
            for r in recruiters:
                email_display = r.email or "no email"
                click.echo(f"  {r.id:3d}  {r.name:30s}  📧 {email_display}")
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)

    @cli.command("add-application")
    @click.option("--company-id", required=True, type=int, help="Company ID (from list-companies)")
    @click.option("--position-id", required=True, type=int, help="Position ID (from add-position output)")
    @click.option("--applied-date", default=None, type=str, help="Applied date YYYY-MM-DD (default: today)")
    @click.option("--recruiter-id", default=None, type=int, help="Recruiter ID (optional)")
    @click.option("--job-id", default=None, type=str, help="External job posting ID/reference (optional)")
    @click.option("--notes", default=None, type=str, help="Application notes")
    def add_application(
        company_id: int,
        position_id: int,
        applied_date: Optional[str],
        recruiter_id: Optional[int],
        job_id: Optional[str],
        notes: Optional[str],
    ) -> None:
        """Create a new job application record."""
        try:
            flow = ApplicationFlow()
            app = flow.create_application(
                company_id=company_id,
                position_id=position_id,
                applied_date=_parse_date(applied_date),
                recruiter_id=recruiter_id,
                job_id=job_id,
                notes=notes,
            )
            click.echo(f"✅ Created application #{app.id}")
            click.echo(f"   🏢 Company ID: {app.company_id}")
            click.echo(f"   💼 Position ID: {app.position_id}")
            if app.job_id:
                click.echo(f"   🆔 Job ID: {app.job_id}")
            click.echo(f"   📅 Applied: {app.applied_date}")
            click.echo(f"   ℹ️  Initial status set to 'Applied' and event logged automatically")
        except (ValidationFailedError, ConstraintViolationError, NotFoundError) as e:
            click.echo(f"❌ Error: {e}", err=True)
            click.echo("💡 Tip: Run 'list-companies' to see company IDs")
            raise click.Abort()
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)
            raise click.Abort()

    @cli.command("list-applications")
    @click.option("--sort-by", default="created_at", type=click.Choice(["id", "created_at", "updated_at", "applied_date", "current_status"], case_sensitive=False), show_default=True, help="Sort column")
    @click.option("--sort-dir", default="desc", type=click.Choice(["asc", "desc"], case_sensitive=False), show_default=True, help="Sort direction")
    @click.option("--limit", default=None, type=int, help="Optional max rows")
    @click.option("--offset", default=None, type=int, help="Optional row offset")
    @click.option("--company-id", default=None, type=int, help="Optional company filter")
    @click.option("--status-id", default=None, type=int, help="Optional status filter")
    def list_applications(
        sort_by: str,
        sort_dir: str,
        limit: Optional[int],
        offset: Optional[int],
        company_id: Optional[int],
        status_id: Optional[int],
    ) -> None:
        """View all your job applications."""
        try:
            flow = ApplicationFlow()
            apps = flow.list_applications(
                options=ApplicationQueryOptions(
                    sort_by=sort_by,
                    sort_dir=sort_dir,
                    limit=limit,
                    offset=offset,
                    company_id=company_id,
                    status_id=status_id,
                )
            )
            if not apps:
                click.echo("📭 No applications found. Add one with: add-application")
                return
            click.echo(f"\n📝 Applications ({len(apps)} total):")
            click.echo("=" * 110)
            for a in apps:
                job_id_display = a.job_id if a.job_id else "-"
                click.echo(
                    f"  ID {a.id:3d} | Company {a.company_id:3d} | Position {a.position_id:3d} | "
                    f"Job ID {job_id_display:15s} | Status {a.current_status} | {a.applied_date}"
                )
        except (ValidationFailedError, ConstraintViolationError) as e:
            click.echo(f"❌ Error: {e}", err=True)
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)

    @cli.command("update-status")
    @click.option("--application-id", required=True, type=int, help="Application ID to update")
    @click.option("--new-status", required=True, type=str, help="New status name or ID")
    def update_status(application_id: int, new_status: str) -> None:
        """Update an application's status (validates state transitions)."""
        try:
            flow = ApplicationFlow()
            status_svc = StatusService()
            updated = flow.update_status(application_id=application_id, new_status_input=new_status)
            status_name = status_svc.get_status(updated.current_status).status_name
            click.echo(f"✅ Updated application #{updated.id} to {colorize_status(status_name)}")
            click.echo(f"   ℹ️  Event logged automatically")
        except InvalidTransitionError as e:
            click.echo(f"❌ Invalid transition: {e}", err=True)
            click.echo("💡 Tip: Check valid transitions in the docs or use interactive mode")
            raise click.Abort()
        except NotFoundError as e:
            click.echo(f"❌ {e}", err=True)
            click.echo("💡 Valid statuses: Applied, Interview Scheduled, Interviewed, Offer, Accepted, Rejected, Withdrawn")
            raise click.Abort()
        except (ValidationFailedError, ConstraintViolationError) as e:
            click.echo(f"❌ Error: {e}", err=True)
            raise click.Abort()
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)
            raise click.Abort()

    @cli.command("log-event")
    @click.option("--application-id", required=True, type=int, help="Application ID")
    @click.option("--event-type", required=True, type=str, help="Event type (e.g., 'Phone Screen', 'On-site')")
    @click.option("--event-date", default=None, type=str, help="ISO datetime (default: now)")
    @click.option("--notes", default=None, type=str, help="Event details")
    def log_event(application_id: int, event_type: str, event_date: Optional[str], notes: Optional[str]) -> None:
        """Log an event for an application (e.g., interview, feedback)."""
        try:
            svc = EventService()
            event = svc.log(
                application_id=application_id,
                event_type=event_type,
                event_date=_parse_datetime(event_date),
                notes=notes,
            )
            click.echo(f"✅ Logged event #{event.id} for application #{event.application_id}")
            click.echo(f"   📅 {event.event_date}")
            click.echo(f"   📝 {event.event_type}")
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)
            raise click.Abort()

    @cli.command("show-history")
    @click.option("--application-id", required=True, type=int, help="Application ID")
    def show_history(application_id: int) -> None:
        """View timeline of events for an application."""
        try:
            svc = EventService()
            events = svc.get_for_application(application_id)
            if not events:
                click.echo(f"📭 No events found for application #{application_id}")
                return
            click.echo(f"\n📜 Timeline for application #{application_id}:")
            click.echo("=" * 80)
            for e in events:
                notes_display = f" - {e.notes}" if e.notes else ""
                click.echo(f"  {e.event_date}  |  {e.event_type}{notes_display}")
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)

    @cli.command("analytics")
    @click.option("--days", default=30, type=int, show_default=True, help="Recent applications window")
    def analytics(days: int) -> None:
        """Show analytics dashboard with metrics and conversion rates."""
        try:
            svc = AnalyticsService()
            overview = svc.get_overview_counts()
            distribution = svc.get_status_distribution()
            conversions = svc.get_conversion_rates()
            recent = svc.get_recent_applications(days=days)

            rows = build_dashboard_rows(overview, distribution, conversions)
            for line in rows:
                click.echo(line)

            click.echo("")
            click.echo(f"📊 Recent applications (last {days} days): {len(recent)}")
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)

    @cli.command("export-report")
    @click.option("--format", "fmt", type=click.Choice(["json", "csv"], case_sensitive=False), required=True, help="Export format")
    @click.option("--output", required=True, type=click.Path(path_type=Path), help="Output file path")
    def export_report(fmt: str, output: Path) -> None:
        """Export analytics report to JSON or CSV."""
        try:
            svc = AnalyticsService()
            payload = {
                "overview": svc.get_overview_counts(),
                "status_distribution": svc.get_status_distribution(),
                "conversion_rates": svc.get_conversion_rates(),
                "response_time_by_company": svc.get_response_time_by_company(),
                "recent_applications": svc.get_recent_applications(days=30),
            }

            output.parent.mkdir(parents=True, exist_ok=True)

            if fmt.lower() == "json":
                output.write_text(to_json_report(payload), encoding="utf-8")
            else:
                output.write_text(to_csv_report(payload["recent_applications"]), encoding="utf-8")

            click.echo(f"✅ Report written to: {output}")
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)
            raise click.Abort()

    return cli


cli = build_cli()


def main() -> None:
    cli()


if __name__ == "__main__":
    main()


def _parse_date(value: Optional[str]):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_datetime(value: Optional[str]):
    if not value:
        return None
    return datetime.fromisoformat(value)
