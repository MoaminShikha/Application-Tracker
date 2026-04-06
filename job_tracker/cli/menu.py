"""Main menu-driven interface for Application Tracker."""

import click
from tabulate import tabulate

from job_tracker.services import (
    ApplicationService,
    CompanyService,
    EventService,
    PositionService,
    RecruiterService,
    StatusService,
)
from job_tracker.analytics import AnalyticsService
from job_tracker.utils.colors import colorize_status


def _build_menu_snapshot() -> list[str]:
    """Build a compact runtime snapshot for the menu header."""
    try:
        analytics = AnalyticsService()
        company_svc = CompanyService()
        recruiter_svc = RecruiterService()

        overview = analytics.get_overview_counts()
        company_count = len(company_svc.get_all_companies())
        recruiter_count = len(recruiter_svc.get_all_recruiters())

        return [
            f"Applications: {overview.get('total_applications', 0)} total",
            f"Active: {overview.get('active_applications', 0)}",
            f"Offers: {overview.get('offers', 0)}",
            f"Accepted: {overview.get('accepted', 0)}",
            f"Companies: {company_count}",
            f"Recruiters: {recruiter_count}",
        ]
    except Exception:
        # Keep menu available even if snapshot queries fail.
        return ["Applications: unavailable", "Active: unavailable", "Offers: unavailable"]


def display_main_menu():
    """Display the main menu and return user choice."""
    click.clear()
    click.echo("=" * 70)
    click.echo("🎯 APPLICATION TRACKER")
    click.echo("   Track applications, interviews, and outcomes in one place")
    click.echo("=" * 70)
    click.echo("\nQuick snapshot:")
    click.echo("  • " + " | ".join(_build_menu_snapshot()))

    click.echo("📝 APPLICATIONS (Main Workflow)")
    click.echo("  1. Add a new job application")
    click.echo("  2. View all applications (table)")
    click.echo("  3. Update application status")
    click.echo("  4. View application timeline")
    click.echo("")

    click.echo("📊 ANALYTICS & REPORTS")
    click.echo("  5. View analytics dashboard")
    click.echo("  6. Export report (JSON/CSV)")
    click.echo("")

    click.echo("📋 VIEW DATA (Tables)")
    click.echo("  7. View all companies")
    click.echo("  8. View all positions")
    click.echo("  9. View all recruiters")
    click.echo("")

    click.echo("📅 EVENTS")
    click.echo("  10. Log a new event")
    click.echo("")

    click.echo("🗑️  DELETE/MANAGE DATA")
    click.echo("  12. Delete an application")
    click.echo("  13. Delete a company")
    click.echo("  14. Delete a position")
    click.echo("  15. Delete a recruiter")
    click.echo("")

    click.echo("❓ HELP & EXIT")
    click.echo("  11. Show help & tips")
    click.echo("  0. Exit")
    click.echo("")

    choice = click.prompt("Enter your choice (0-15)", type=click.IntRange(0, 15), default=0)
    return choice


def display_companies_table():
    """Display companies in a nice table format."""
    svc = CompanyService()
    companies = svc.get_all_companies()

    if not companies:
        click.echo("\n📭 No companies found.")
        click.echo("💡 Tip: Choose option 1 to add your first application (company is created/reused there).")
        return

    # Prepare table data
    headers = ["ID", "Company Name", "Location", "Industry", "Created"]
    rows = []
    for c in companies:
        rows.append([
            c.id,
            c.name,
            c.location,
            c.industry or "-",
            c.created_at.strftime("%Y-%m-%d") if c.created_at else "-"
        ])

    click.echo(f"\n📋 Companies ({len(companies)} total):")
    click.echo(tabulate(rows, headers=headers, tablefmt="grid"))


def display_applications_table():
    """Display applications in a formatted table."""
    app_svc = ApplicationService()
    company_svc = CompanyService()
    position_svc = PositionService()
    status_svc = StatusService()

    apps = app_svc.get_all_applications()

    if not apps:
        click.echo("\n📭 No applications found.")
        click.echo("💡 Tip: Choose option 1 to create your first application!")
        return

    # Build rich table with company/position names
    headers = ["App ID", "Company", "Position", "Job ID", "Status", "Applied Date", "Days Active", "Notes"]
    rows = []

    for a in apps:
        # Get company name
        company = company_svc.get_company(a.company_id)
        company_name = company.name if company else f"ID {a.company_id}"

        # Get position title
        position = position_svc.get_position(a.position_id)
        position_title = f"{position.title} ({position.level})" if position else f"ID {a.position_id}"

        # Get status name
        status = status_svc.get_status(a.current_status)
        status_name = status.status_name if status else f"ID {a.current_status}"

        # Colorize status for better visual feedback
        colored_status = colorize_status(status_name) if status else status_name

        # Calculate days since application
        days_active = a.days_in_current_status()
        notes_preview = a.notes[:40] + "..." if a.notes and len(a.notes) > 40 else (a.notes or "-")

        rows.append([
            a.id,
            company_name[:25],  # Truncate if too long
            position_title[:30],
            a.job_id or "-",
            colored_status,
            a.applied_date,
            f"{days_active} days",
            notes_preview,
        ])

    click.echo(f"\n📝 Applications ({len(apps)} total):")
    click.echo(tabulate(rows, headers=headers, tablefmt="grid"))


def display_recruiters_table():
    """Display recruiters in a table format."""
    svc = RecruiterService()
    recruiters = svc.get_all_recruiters()

    if not recruiters:
        click.echo("\n📭 No recruiters found.")
        click.echo("💡 Tip: Choose option 4 to add recruiters!")
        return

    headers = ["ID", "Name", "Email", "Phone", "Company ID"]
    rows = []
    for r in recruiters:
        rows.append([
            r.id,
            r.name,
            r.email or "-",
            r.phone or "-",
            r.company_id or "-"
        ])

    click.echo(f"\n👤 Recruiters ({len(recruiters)} total):")
    click.echo(tabulate(rows, headers=headers, tablefmt="grid"))


def add_company_interactive():
    """Add company with prompts."""
    click.echo("\n" + "=" * 70)
    click.echo("📋 Add New Company")
    click.echo("=" * 70)

    name = click.prompt("Company name", type=str)
    location = click.prompt("Location (e.g., 'Seattle', 'Remote')", type=str)
    industry = click.prompt("Industry (optional, press Enter to skip)", default="", show_default=False)
    notes = click.prompt("Notes (optional, press Enter to skip)", default="", show_default=False)

    try:
        svc = CompanyService()
        company = svc.create_company(
            name=name,
            location=location,
            industry=industry if industry else None,
            notes=notes if notes else None
        )
        click.echo(f"\n✅ Success! Created company #{company.id}: {company.name}")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


def add_position_interactive():
    """Add position with prompts."""
    click.echo("\n" + "=" * 70)
    click.echo("💼 Add New Position")
    click.echo("=" * 70)

    title = click.prompt("Job title (e.g., 'Software Engineer')", type=str)

    click.echo("\nAvailable seniority levels:")
    levels = ["Entry", "Intern", "Junior", "Mid", "Senior", "Student", "Lead", "Manager"]
    for idx, level in enumerate(levels, 1):
        click.echo(f"  {idx}. {level}")

    level_choice = click.prompt(f"Choose level (1-{len(levels)})", type=click.IntRange(1, len(levels)))
    level = levels[level_choice - 1]

    try:
        svc = PositionService()
        position = svc.create_position(title=title, level=level)
        click.echo(f"\n✅ Success! Created position #{position.id}: {position.title} ({position.level})")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


def add_recruiter_interactive():
    """Add recruiter with prompts."""
    click.echo("\n" + "=" * 70)
    click.echo("👤 Add New Recruiter")
    click.echo("=" * 70)

    name = click.prompt("Recruiter name", type=str)
    email = click.prompt("Email (optional)", default="", show_default=False)
    phone = click.prompt("Phone (optional)", default="", show_default=False)

    has_company = click.confirm("Associate with a company?", default=False)
    company_id = None

    if has_company:
        display_companies_table()
        company_id = click.prompt("\nCompany ID (or 0 to skip)", type=int, default=0)
        if company_id == 0:
            company_id = None

    try:
        svc = RecruiterService()
        recruiter = svc.create_recruiter(
            name=name,
            email=email if email else None,
            phone=phone if phone else None,
            company_id=company_id
        )
        click.echo(f"\n✅ Success! Created recruiter #{recruiter.id}: {recruiter.name}")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


def add_application_interactive():
    """Add a complete application with all details in one flow."""
    click.echo("\n" + "=" * 70)
    click.echo("📝 Add New Job Application")
    click.echo("=" * 70)
    click.echo("\nLet's add your job application. I'll guide you through each step.")

    # STEP 1: Company
    click.echo("\n" + "-" * 70)
    click.echo("STEP 1: Company Information")
    click.echo("-" * 70)

    company_name = click.prompt("\n📍 Company name", type=str)
    location = click.prompt("Location (optional, press Enter to skip)", default="", show_default=False)
    industry = click.prompt("Industry (optional, press Enter to skip)", default="", show_default=False)

    # Check if company exists
    company_svc = CompanyService()
    companies = company_svc.get_all_companies()
    existing_company = next((c for c in companies if c.name.lower() == company_name.lower()), None)

    if existing_company:
        click.echo(f"✓ Found existing company: {existing_company.name}")
        if click.confirm("Use this company?", default=True):
            company_id = existing_company.id
        else:
            click.echo("Creating new company entry...")
            company = company_svc.create_company(
                name=company_name,
                location=location if location else None,
                industry=industry if industry else None
            )
            company_id = company.id
            click.echo(f"✅ Created new company #{company_id}")
    else:
        company = company_svc.create_company(
            name=company_name,
            location=location if location else None,
            industry=industry if industry else None
        )
        company_id = company.id
        click.echo(f"✅ Created company #{company_id}: {company.name}")

    # STEP 2: Position
    click.echo("\n" + "-" * 70)
    click.echo("STEP 2: Position Details")
    click.echo("-" * 70)

    position_title = click.prompt("\n💼 Job title (e.g., 'Software Engineer')", type=str)

    click.echo("\nSeniority level:")
    levels = ["Entry", "Intern", "Junior", "Mid", "Senior", "Student", "Lead", "Manager"]
    for idx, level in enumerate(levels, 1):
        click.echo(f"  {idx}. {level}")

    level_choice = click.prompt(f"Choose level (1-{len(levels)})", type=click.IntRange(1, len(levels)))
    position_level = levels[level_choice - 1]

    # Check if position exists
    position_svc = PositionService()
    positions = position_svc.get_all_positions()
    existing_position = next(
        (p for p in positions if p.title.lower() == position_title.lower() and p.level == position_level),
        None
    )

    if existing_position:
        click.echo(f"✓ Found existing position: {existing_position.title} ({existing_position.level})")
        position_id = existing_position.id
    else:
        position = position_svc.create_position(title=position_title, level=position_level)
        position_id = position.id
        click.echo(f"✅ Created position #{position_id}: {position.title} ({position.level})")

    # STEP 3: Application Details
    click.echo("\n" + "-" * 70)
    click.echo("STEP 3: Application Details")
    click.echo("-" * 70)

    job_id = click.prompt("\nJob ID / Posting ID (optional, press Enter to skip)", default="", show_default=False)

    use_today = click.confirm("\nApplied today?", default=True)
    applied_date = None
    if not use_today:
        from datetime import datetime
        date_str = click.prompt("Applied date (YYYY-MM-DD)", type=str)
        applied_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    # STEP 4: Recruiter (optional)
    click.echo("\n" + "-" * 70)
    click.echo("STEP 4: Recruiter (Optional)")
    click.echo("-" * 70)

    has_recruiter = click.confirm("\nWas there a recruiter involved?", default=False)
    recruiter_id = None

    if has_recruiter:
        recruiter_name = click.prompt("Recruiter name", type=str)
        recruiter_email = click.prompt("Recruiter email (optional)", default="", show_default=False)

        # Check if recruiter exists
        recruiter_svc = RecruiterService()
        recruiters = recruiter_svc.get_all_recruiters()
        existing_recruiter = next(
            (r for r in recruiters if r.name.lower() == recruiter_name.lower()),
            None
        )

        if existing_recruiter:
            click.echo(f"✓ Found existing recruiter: {existing_recruiter.name}")
            recruiter_id = existing_recruiter.id
        else:
            recruiter = recruiter_svc.create_recruiter(
                name=recruiter_name,
                email=recruiter_email if recruiter_email else None,
                company_id=company_id
            )
            recruiter_id = recruiter.id
            click.echo(f"✅ Created recruiter #{recruiter_id}")

    # STEP 5: Notes
    notes = click.prompt("\nNotes (optional, press Enter to skip)", default="", show_default=False)

    # Create the application
    click.echo("\n" + "=" * 70)
    try:
        app_svc = ApplicationService()
        app = app_svc.create_application(
            company_id=company_id,
            position_id=position_id,
            applied_date=applied_date,
            recruiter_id=recruiter_id,
            job_id=job_id if job_id else None,
            notes=notes if notes else None
        )
        click.echo("✅ SUCCESS! Application created")
        click.echo("=" * 70)
        click.echo(f"Application ID: #{app.id}")
        click.echo(f"Company: {company_name}")
        click.echo(f"Position: {position_title} ({position_level})")
        click.echo(f"Status: Applied (automatically set)")
        if app.job_id:
            click.echo(f"Job ID: {app.job_id}")
        click.echo("Initial event logged automatically")
    except Exception as e:
        click.echo(f"\n❌ Error creating application: {e}")


def update_status_interactive():
    """Update application status with validation."""
    click.echo("\n" + "=" * 70)
    click.echo("🔄 Update Application Status")
    click.echo("=" * 70)

    display_applications_table()

    app_id = click.prompt("\nSelect application ID to update", type=int)

    # Get current status
    app_svc = ApplicationService()
    app = app_svc.get_application(app_id)

    if not app:
        click.echo(f"❌ Application #{app_id} not found")
        return

    status_svc = StatusService()
    current_status = status_svc.get_status(app.current_status)
    click.echo(f"\n📍 Current status: {colorize_status(current_status.status_name)}")

    # Show valid transitions
    from job_tracker.services.status_service import ALLOWED_TRANSITIONS
    allowed = ALLOWED_TRANSITIONS.get(current_status.status_name, set())

    if not allowed:
        click.echo(f"⚠️  This is a terminal state. No further updates allowed.")
        return

    click.echo("\n✅ Valid next statuses:")
    allowed_list = sorted(allowed)
    for idx, status_name in enumerate(allowed_list, 1):
        click.echo(f"  {idx}. {colorize_status(status_name)}")

    choice = click.prompt(f"Choose new status (1-{len(allowed_list)})", type=click.IntRange(1, len(allowed_list)))
    new_status_name = allowed_list[choice - 1]
    new_status_id = status_svc.get_status_id_by_name(new_status_name)

    try:
        updated = app_svc.update_application_status(app_id, new_status_id)
        click.echo(f"\n✅ Success! Updated application #{updated.id} to '{colorize_status(new_status_name)}'")
        click.echo("   ℹ️  Event logged automatically")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


def view_timeline_interactive():
    """View application timeline."""
    click.echo("\n" + "=" * 70)
    click.echo("📜 View Application Timeline")
    click.echo("=" * 70)

    display_applications_table()

    app_id = click.prompt("\nSelect application ID", type=int)

    event_svc = EventService()
    events = event_svc.get_events_for_application(app_id)

    if not events:
        click.echo("\n⚠️  No events found for this application")
        return

    click.echo(f"\n📅 Timeline for Application #{app_id}:")
    click.echo("=" * 70)

    headers = ["Date/Time", "Event Type", "Notes"]
    rows = []
    for e in events:
        rows.append([
            e.event_date.strftime("%Y-%m-%d %H:%M"),
            e.event_type,
            e.notes[:40] + "..." if e.notes and len(e.notes) > 40 else (e.notes or "-")
        ])

    click.echo(tabulate(rows, headers=headers, tablefmt="grid"))


def log_event_interactive():
    """Log event with prompts."""
    click.echo("\n" + "=" * 70)
    click.echo("📅 Log Application Event")
    click.echo("=" * 70)

    display_applications_table()

    app_id = click.prompt("\nSelect application ID", type=int)
    event_type = click.prompt("Event type (e.g., 'Phone Screen', 'On-site Interview')", type=str)

    use_now = click.confirm("Event happened now?", default=True)
    event_date = None
    if not use_now:
        from datetime import datetime
        date_str = click.prompt("Event date/time (YYYY-MM-DDTHH:MM:SS)", type=str)
        event_date = datetime.fromisoformat(date_str)

    notes = click.prompt("Notes (optional)", default="", show_default=False)

    try:
        svc = EventService()
        event = svc.log_event(
            application_id=app_id,
            event_type=event_type,
            event_date=event_date,
            notes=notes if notes else None
        )
        click.echo(f"\n✅ Success! Logged event #{event.id}")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


def view_analytics():
    """Show analytics dashboard."""
    click.echo("\n" + "=" * 70)
    click.echo("📊 Analytics Dashboard")
    click.echo("=" * 70)

    days = click.prompt("\nShow applications from last X days", type=int, default=30)

    from job_tracker.analytics import build_dashboard_rows

    svc = AnalyticsService()
    overview = svc.get_overview_counts()
    distribution = svc.get_status_distribution()
    conversions = svc.get_conversion_rates()
    recent = svc.get_recent_applications(days=days)

    click.echo("")
    rows = build_dashboard_rows(overview, distribution, conversions)
    for line in rows:
        click.echo(line)

    click.echo(f"\n📊 Recent applications (last {days} days): {len(recent)}")


def export_report_interactive():
    """Export report with prompts."""
    click.echo("\n" + "=" * 70)
    click.echo("📤 Export Report")
    click.echo("=" * 70)

    click.echo("\nChoose format:")
    click.echo("  1. JSON (full analytics)")
    click.echo("  2. CSV (recent applications)")

    choice = click.prompt("Select format (1-2)", type=click.IntRange(1, 2))
    fmt = "json" if choice == 1 else "csv"

    filename = click.prompt("Output filename", default=f"report.{fmt}")

    from pathlib import Path
    from job_tracker.analytics import to_json_report, to_csv_report

    try:
        svc = AnalyticsService()
        payload = {
            "overview": svc.get_overview_counts(),
            "status_distribution": svc.get_status_distribution(),
            "conversion_rates": svc.get_conversion_rates(),
            "response_time_by_company": svc.get_response_time_by_company(),
            "recent_applications": svc.get_recent_applications(days=30),
        }

        output = Path(filename)
        output.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "json":
            output.write_text(to_json_report(payload), encoding="utf-8")
        else:
            output.write_text(to_csv_report(payload["recent_applications"]), encoding="utf-8")

        click.echo(f"\n✅ Success! Report written to: {output}")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


def show_help():
    """Show help and tips."""
    click.echo("\n" + "=" * 70)
    click.echo("❓ Help & Tips")
    click.echo("=" * 70)

    click.echo("\n📖 Quick Start:")
    click.echo("  1. Choose option 1 to add a job application")
    click.echo("  2. Enter company name, position, and details")
    click.echo("  3. System automatically creates/reuses companies & positions")
    click.echo("  4. Track progress with option 3 (Update status)")
    click.echo("  5. View tables anytime (options 7-9)")
    click.echo("")

    click.echo("💡 Pro Tips:")
    click.echo("  • Everything is created in ONE flow (option 1)")
    click.echo("  • Company location is optional - just press Enter to skip")
    click.echo("  • System reuses existing companies/positions automatically")
    click.echo("  • Status updates validate transitions automatically")
    click.echo("  • Events are logged automatically on status changes")
    click.echo("  • Check analytics weekly (option 5)")
    click.echo("  • Export reports to share progress (option 6)")
    click.echo("")

    click.echo("📋 View Options:")
    click.echo("  • Option 2: View all applications (with company/position names!)")
    click.echo("  • Option 7: View all companies")
    click.echo("  • Option 8: View all positions")
    click.echo("  • Option 9: View all recruiters")
    click.echo("")

    click.echo("📚 Documentation:")
    click.echo("  • See docs/USER_FRIENDLY_GUIDE.md for detailed guide")
    click.echo("  • See docs/CLI_COMMANDS_REFERENCE.md for all commands")
    click.echo("  • See docs/ALL_INTERACTION_METHODS.md for workflows")


def delete_application_interactive():
    """Delete an application with confirmation."""
    click.echo("\n" + "=" * 70)
    click.echo("🗑️  Delete Application")
    click.echo("=" * 70)

    display_applications_table()

    app_id = click.prompt("\nEnter application ID to delete", type=int)

    # Confirm deletion
    if not click.confirm(f"⚠️  Are you sure you want to delete application #{app_id}?", default=False):
        click.echo("Deletion cancelled.")
        return

    try:
        svc = ApplicationService()
        if svc.delete_application(app_id):
            click.echo(f"\n✅ Application #{app_id} deleted successfully.")
        else:
            click.echo(f"\n❌ Application #{app_id} not found or could not be deleted.")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


def delete_company_interactive():
    """Delete a company with confirmation."""
    click.echo("\n" + "=" * 70)
    click.echo("🗑️  Delete Company")
    click.echo("=" * 70)

    display_companies_table()

    company_id = click.prompt("\nEnter company ID to delete", type=int)

    # Confirm deletion
    if not click.confirm(f"⚠️  Are you sure you want to delete company #{company_id}?", default=False):
        click.echo("Deletion cancelled.")
        return

    try:
        svc = CompanyService()
        if svc.delete_company(company_id):
            click.echo(f"\n✅ Company #{company_id} deleted successfully.")
        else:
            click.echo(f"\n❌ Company #{company_id} not found or could not be deleted.")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


def delete_position_interactive():
    """Delete a position with confirmation."""
    click.echo("\n" + "=" * 70)
    click.echo("🗑️  Delete Position")
    click.echo("=" * 70)

    position_svc = PositionService()
    positions = position_svc.get_all_positions()

    if not positions:
        click.echo("\n❌ No positions found!")
        return

    click.echo("\n📋 Available positions:")
    for p in positions:
        click.echo(f"  {p.id}. {p.title} ({p.level})")

    position_id = click.prompt("\nEnter position ID to delete", type=int)

    # Confirm deletion
    if not click.confirm(f"⚠️  Are you sure you want to delete position #{position_id}?", default=False):
        click.echo("Deletion cancelled.")
        return

    try:
        svc = PositionService()
        if svc.delete_position(position_id):
            click.echo(f"\n✅ Position #{position_id} deleted successfully.")
        else:
            click.echo(f"\n❌ Position #{position_id} not found or could not be deleted.")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


def delete_recruiter_interactive():
    """Delete a recruiter with confirmation."""
    click.echo("\n" + "=" * 70)
    click.echo("🗑️  Delete Recruiter")
    click.echo("=" * 70)

    display_recruiters_table()

    recruiter_id = click.prompt("\nEnter recruiter ID to delete", type=int)

    # Confirm deletion
    if not click.confirm(f"⚠️  Are you sure you want to delete recruiter #{recruiter_id}?", default=False):
        click.echo("Deletion cancelled.")
        return

    try:
        svc = RecruiterService()
        if svc.delete_recruiter(recruiter_id):
            click.echo(f"\n✅ Recruiter #{recruiter_id} deleted successfully.")
        else:
            click.echo(f"\n❌ Recruiter #{recruiter_id} not found or could not be deleted.")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")



@click.command()
def menu():
    """Launch interactive menu-driven interface."""
    while True:
        choice = display_main_menu()

        if choice == 0:
            click.echo("\n👋 Goodbye! Happy job hunting!")
            break
        elif choice == 1:
            add_application_interactive()
        elif choice == 2:
            display_applications_table()
        elif choice == 3:
            update_status_interactive()
        elif choice == 4:
            view_timeline_interactive()
        elif choice == 5:
            view_analytics()
        elif choice == 6:
            export_report_interactive()
        elif choice == 7:
            display_companies_table()
        elif choice == 8:
            click.echo("\n💼 Available positions:")
            position_svc = PositionService()
            positions = position_svc.get_all_positions()
            if not positions:
                click.echo("📭 No positions found yet.")
                click.echo("💡 Tip: Positions are created when you add applications (option 1)")
            else:
                for p in positions:
                    click.echo(f"  {p.id}. {p.title} ({p.level})")
        elif choice == 9:
            display_recruiters_table()
        elif choice == 10:
            log_event_interactive()
        elif choice == 11:
            show_help()
        elif choice == 12:
            delete_application_interactive()
        elif choice == 13:
            delete_company_interactive()
        elif choice == 14:
            delete_position_interactive()
        elif choice == 15:
            delete_recruiter_interactive()
        else:
            click.echo("\n❌ Invalid choice. Please try again.")

        if choice != 0:
            click.echo("\n" + "=" * 70)
            click.prompt("Press Enter to return to main menu", default="", show_default=False)


if __name__ == "__main__":
    menu()

