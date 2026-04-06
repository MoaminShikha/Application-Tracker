"""Interactive CLI mode with guided prompts for user-friendly experience."""

import click
from datetime import datetime

from job_tracker.services import (
    ApplicationService,
    CompanyService,
    EventService,
    PositionService,
    RecruiterService,
    StatusService,
)
from job_tracker.models import VALID_LEVELS
from job_tracker.utils.colors import colorize_status


def prompt_company_details():
    """Interactive prompts to gather company information."""
    click.echo("\n📋 Add New Company")
    click.echo("=" * 50)

    name = click.prompt("Company name", type=str)
    location = click.prompt("Location (optional, press Enter to skip)", default="", show_default=False)
    industry = click.prompt("Industry (optional, press Enter to skip)", default="", show_default=False)
    notes = click.prompt("Notes (optional, press Enter to skip)", default="", show_default=False)

    return {
        "name": name,
        "location": location if location else None,
        "industry": industry if industry else None,
        "notes": notes if notes else None,
    }


def prompt_position_details():
    """Interactive prompts to gather position information."""
    click.echo("\n💼 Add New Position")
    click.echo("=" * 50)

    title = click.prompt("Job title (e.g., 'Software Engineer', 'Data Scientist')", type=str)

    click.echo("\nAvailable seniority levels:")
    levels = sorted(VALID_LEVELS)
    for idx, level in enumerate(levels, 1):
        click.echo(f"  {idx}. {level}")

    level_choice = click.prompt(f"Choose level (1-{len(levels)})", type=click.IntRange(1, len(levels)))
    level = levels[level_choice - 1]

    return {"title": title, "level": level}


def prompt_recruiter_details():
    """Interactive prompts to gather recruiter information."""
    click.echo("\n👤 Add New Recruiter")
    click.echo("=" * 50)

    name = click.prompt("Recruiter name", type=str)
    email = click.prompt("Email (optional, press Enter to skip)", default="", show_default=False)
    phone = click.prompt("Phone (optional, press Enter to skip)", default="", show_default=False)

    has_company = click.confirm("Associate with a company?", default=False)
    company_id = None
    if has_company:
        # Show companies
        svc = CompanyService()
        companies = svc.get_all_companies()
        if companies:
            click.echo("\nAvailable companies:")
            for c in companies:
                click.echo(f"  {c.id}. {c.name} ({c.location})")
            company_id = click.prompt("Company ID", type=int)
        else:
            click.echo("⚠️  No companies found. Add companies first with 'add-company'")

    return {
        "name": name,
        "email": email if email else None,
        "phone": phone if phone else None,
        "company_id": company_id,
    }


def prompt_application_details():
    """Interactive prompts to gather application information."""
    click.echo("\n📝 Add New Application")
    click.echo("=" * 50)

    # Show companies
    company_svc = CompanyService()
    companies = company_svc.get_all_companies()

    if not companies:
        click.echo("❌ No companies found! Please add companies first with 'add-company'")
        raise click.Abort()

    click.echo("\n📍 Available companies:")
    for c in companies:
        click.echo(f"  {c.id}. {c.name} ({c.location})")

    company_id = click.prompt("Select company ID", type=int)

    # Show positions
    position_svc = PositionService()
    positions = position_svc.get_all_positions()

    if not positions:
        click.echo("❌ No positions found! Please add positions first with 'add-position'")
        raise click.Abort()

    click.echo("\n💼 Available positions:")
    for p in positions:
        click.echo(f"  {p.id}. {p.title} ({p.level})")

    position_id = click.prompt("Select position ID", type=int)

    job_id = click.prompt("Job ID / Posting ID (optional, press Enter to skip)", default="", show_default=False)

    # Optional fields
    use_today = click.confirm("Applied today?", default=True)
    applied_date = None
    if not use_today:
        date_str = click.prompt("Applied date (YYYY-MM-DD)", type=str)
        applied_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Recruiter
    has_recruiter = click.confirm("Was there a recruiter involved?", default=False)
    recruiter_id = None
    if has_recruiter:
        recruiter_svc = RecruiterService()
        recruiters = recruiter_svc.get_all_recruiters()
        if recruiters:
            click.echo("\n👤 Available recruiters:")
            for r in recruiters:
                click.echo(f"  {r.id}. {r.name} ({r.email or 'no email'})")
            recruiter_id = click.prompt("Select recruiter ID (or 0 to skip)", type=int, default=0)
            if recruiter_id == 0:
                recruiter_id = None
        else:
            click.echo("⚠️  No recruiters found.")

    notes = click.prompt("Notes (optional, press Enter to skip)", default="", show_default=False)

    return {
        "company_id": company_id,
        "position_id": position_id,
        "job_id": job_id if job_id else None,
        "applied_date": applied_date,
        "recruiter_id": recruiter_id,
        "notes": notes if notes else None,
    }


def prompt_status_update():
    """Interactive prompts to update application status."""
    click.echo("\n🔄 Update Application Status")
    click.echo("=" * 50)

    # Show applications
    app_svc = ApplicationService()
    apps = app_svc.get_all_applications()

    if not apps:
        click.echo("❌ No applications found! Add applications first with 'add-application'")
        raise click.Abort()

    click.echo("\n📋 Your applications:")
    for a in apps[:10]:  # Show first 10
        status_svc_temp = StatusService()
        status_obj = status_svc_temp.get_status(a.current_status)
        status_display = colorize_status(status_obj.status_name) if status_obj else a.current_status
        click.echo(f"  {a.id}. Company ID {a.company_id}, Position ID {a.position_id}, Status {status_display}")

    application_id = click.prompt("Select application ID to update", type=int)

    # Get current status
    app = app_svc.get_application(application_id)
    if not app:
        click.echo(f"❌ Application {application_id} not found")
        raise click.Abort()

    status_svc = StatusService()
    current_status = status_svc.get_status(app.current_status)

    click.echo(f"\n📍 Current status: {colorize_status(current_status.status_name)}")

    # Show valid transitions
    from job_tracker.services.status_service import ALLOWED_TRANSITIONS
    current_name = current_status.status_name
    allowed = ALLOWED_TRANSITIONS.get(current_name, set())

    if not allowed:
        click.echo(f"⚠️  This application is in a terminal state ({colorize_status(current_name)}). No further updates allowed.")
        raise click.Abort()

    click.echo(f"\n✅ Valid next statuses:")
    allowed_list = sorted(allowed)
    for idx, status_name in enumerate(allowed_list, 1):
        click.echo(f"  {idx}. {colorize_status(status_name)}")

    choice = click.prompt("Choose new status (1-{})".format(len(allowed_list)), type=click.IntRange(1, len(allowed_list)))
    new_status_name = allowed_list[choice - 1]
    new_status_id = status_svc.get_status_id_by_name(new_status_name)

    return {"application_id": application_id, "new_status_id": new_status_id, "new_status_name": new_status_name}


def prompt_event_details():
    """Interactive prompts to log an event."""
    click.echo("\n📅 Log Application Event")
    click.echo("=" * 50)

    # Show applications
    app_svc = ApplicationService()
    apps = app_svc.get_all_applications()

    if not apps:
        click.echo("❌ No applications found!")
        raise click.Abort()

    click.echo("\n📋 Your applications:")
    for a in apps[:10]:
        click.echo(f"  {a.id}. Company ID {a.company_id}, Position ID {a.position_id}")

    application_id = click.prompt("Select application ID", type=int)

    event_type = click.prompt("Event type (e.g., 'Phone Screen', 'On-site Interview', 'Feedback Received')", type=str)

    use_now = click.confirm("Event happened now?", default=True)
    event_date = None
    if not use_now:
        date_str = click.prompt("Event date/time (YYYY-MM-DDTHH:MM:SS or press Enter for today)", default="", show_default=False)
        if date_str:
            event_date = datetime.fromisoformat(date_str)

    notes = click.prompt("Notes (optional, press Enter to skip)", default="", show_default=False)

    return {
        "application_id": application_id,
        "event_type": event_type,
        "event_date": event_date,
        "notes": notes if notes else None,
    }


@click.group()
def interactive():
    """Interactive mode with guided prompts."""
    pass


@interactive.command("add-company")
def interactive_add_company():
    """Add a company with interactive prompts."""
    try:
        details = prompt_company_details()
        svc = CompanyService()
        company = svc.create_company(**details)
        click.echo(f"\n✅ Created company #{company.id}: {company.name}")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)


@interactive.command("add-position")
def interactive_add_position():
    """Add a position with interactive prompts."""
    try:
        details = prompt_position_details()
        svc = PositionService()
        position = svc.create_position(**details)
        click.echo(f"\n✅ Created position #{position.id}: {position.title} ({position.level})")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)


@interactive.command("add-recruiter")
def interactive_add_recruiter():
    """Add a recruiter with interactive prompts."""
    try:
        details = prompt_recruiter_details()
        svc = RecruiterService()
        recruiter = svc.create_recruiter(**details)
        click.echo(f"\n✅ Created recruiter #{recruiter.id}: {recruiter.name}")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)


@interactive.command("add-application")
def interactive_add_application():
    """Add an application with interactive prompts."""
    try:
        details = prompt_application_details()
        svc = ApplicationService()
        app = svc.create_application(**details)
        message = f"\n✅ Created application #{app.id} for company ID {app.company_id}"
        if app.job_id:
            message += f" (Job ID: {app.job_id})"
        click.echo(message)
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)


@interactive.command("update-status")
def interactive_update_status():
    """Update application status with interactive prompts."""
    try:
        details = prompt_status_update()
        svc = ApplicationService()
        app = svc.update_application_status(details["application_id"], details["new_status_id"])
        click.echo(f"\n✅ Updated application #{app.id} to '{details['new_status_name']}'")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)


@interactive.command("log-event")
def interactive_log_event():
    """Log an event with interactive prompts."""
    try:
        details = prompt_event_details()
        svc = EventService()
        event = svc.log_event(**details)
        click.echo(f"\n✅ Logged event #{event.id} for application #{event.application_id}")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)


@interactive.command("show-history")
def interactive_show_history():
    """Show application history with interactive selection."""
    try:
        click.echo("\n📜 View Application History")
        click.echo("=" * 50)

        app_svc = ApplicationService()
        apps = app_svc.get_all_applications()

        if not apps:
            click.echo("❌ No applications found!")
            return

        click.echo("\n📋 Your applications:")
        for a in apps[:10]:
            click.echo(f"  {a.id}. Company ID {a.company_id}, Position ID {a.position_id}")

        application_id = click.prompt("Select application ID", type=int)

        event_svc = EventService()
        events = event_svc.get_events_for_application(application_id)

        if not events:
            click.echo("\n⚠️  No events found for this application.")
            return

        click.echo(f"\n📅 Timeline for application #{application_id}:")
        click.echo("=" * 50)
        for e in events:
            click.echo(f"{e.event_date}\t{e.event_type}\t{e.notes or ''}")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)


@interactive.command("delete-application")
def interactive_delete_application():
    """Delete an application with confirmation."""
    try:
        click.echo("\n🗑️  Delete Application")
        click.echo("=" * 50)

        app_svc = ApplicationService()
        apps = app_svc.get_all_applications()

        if not apps:
            click.echo("❌ No applications found!")
            return

        click.echo("\n📋 Your applications:")
        for a in apps[:20]:
            click.echo(f"  {a.id}. Company ID {a.company_id}, Position ID {a.position_id}")

        application_id = click.prompt("Enter application ID to delete", type=int)

        # Confirm deletion
        if not click.confirm(f"⚠️  Are you sure you want to delete application #{application_id}?", default=False):
            click.echo("Deletion cancelled.")
            return

        svc = ApplicationService()
        if svc.delete_application(application_id):
            click.echo(f"\n✅ Application #{application_id} deleted successfully.")
        else:
            click.echo(f"\n❌ Application #{application_id} not found or could not be deleted.")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)


@interactive.command("delete-company")
def interactive_delete_company():
    """Delete a company with confirmation."""
    try:
        click.echo("\n🗑️  Delete Company")
        click.echo("=" * 50)

        company_svc = CompanyService()
        companies = company_svc.get_all_companies()

        if not companies:
            click.echo("❌ No companies found!")
            return

        click.echo("\n📋 Available companies:")
        for c in companies:
            click.echo(f"  {c.id}. {c.name} ({c.location or 'No location'})")

        company_id = click.prompt("Enter company ID to delete", type=int)

        # Confirm deletion
        if not click.confirm(f"⚠️  Are you sure you want to delete company #{company_id}?", default=False):
            click.echo("Deletion cancelled.")
            return

        svc = CompanyService()
        if svc.delete_company(company_id):
            click.echo(f"\n✅ Company #{company_id} deleted successfully.")
        else:
            click.echo(f"\n❌ Company #{company_id} not found or could not be deleted.")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)


@interactive.command("delete-position")
def interactive_delete_position():
    """Delete a position with confirmation."""
    try:
        click.echo("\n🗑️  Delete Position")
        click.echo("=" * 50)

        position_svc = PositionService()
        positions = position_svc.get_all_positions()

        if not positions:
            click.echo("❌ No positions found!")
            return

        click.echo("\n📋 Available positions:")
        for p in positions:
            click.echo(f"  {p.id}. {p.title} ({p.level})")

        position_id = click.prompt("Enter position ID to delete", type=int)

        # Confirm deletion
        if not click.confirm(f"⚠️  Are you sure you want to delete position #{position_id}?", default=False):
            click.echo("Deletion cancelled.")
            return

        svc = PositionService()
        if svc.delete_position(position_id):
            click.echo(f"\n✅ Position #{position_id} deleted successfully.")
        else:
            click.echo(f"\n❌ Position #{position_id} not found or could not be deleted.")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)


@interactive.command("delete-recruiter")
def interactive_delete_recruiter():
    """Delete a recruiter with confirmation."""
    try:
        click.echo("\n🗑️  Delete Recruiter")
        click.echo("=" * 50)

        recruiter_svc = RecruiterService()
        recruiters = recruiter_svc.get_all_recruiters()

        if not recruiters:
            click.echo("❌ No recruiters found!")
            return

        click.echo("\n👤 Available recruiters:")
        for r in recruiters:
            click.echo(f"  {r.id}. {r.name} ({r.email or 'No email'})")

        recruiter_id = click.prompt("Enter recruiter ID to delete", type=int)

        # Confirm deletion
        if not click.confirm(f"⚠️  Are you sure you want to delete recruiter #{recruiter_id}?", default=False):
            click.echo("Deletion cancelled.")
            return

        svc = RecruiterService()
        if svc.delete_recruiter(recruiter_id):
            click.echo(f"\n✅ Recruiter #{recruiter_id} deleted successfully.")
        else:
            click.echo(f"\n❌ Recruiter #{recruiter_id} not found or could not be deleted.")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)


def main():
    interactive()


if __name__ == "__main__":
    main()

