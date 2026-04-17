"""Phase 2 Textual app with read-only dashboard and applications table."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, Static

from job_tracker.analytics import AnalyticsService
from job_tracker.services import ApplicationService, CompanyService, PositionService, StatusService


def build_dashboard_text(overview: dict, conversions: dict) -> str:
    """Build compact dashboard text lines from analytics payloads."""
    return "\n".join(
        [
            f"Applications: {overview.get('total_applications', 0)}",
            f"Active: {overview.get('active_applications', 0)}",
            f"Offers: {overview.get('offers', 0)}",
            f"Accepted: {overview.get('accepted', 0)}",
            f"Rejected: {overview.get('rejected', 0)}",
            "",
            f"App -> Interview: {conversions.get('application_to_interview_pct', 0)}%",
            f"App -> Offer: {conversions.get('application_to_offer_pct', 0)}%",
            f"App -> Accept: {conversions.get('application_to_accept_pct', 0)}%",
        ]
    )


class TrackerApp(App[None]):
    """Read-only Textual interface for dashboard and applications."""

    TITLE = "Application Tracker"
    SUB_TITLE = "Phase 2 - Read-only dashboard"

    BINDINGS = [
        Binding("d", "show_dashboard", "Dashboard"),
        Binding("a", "show_applications", "Applications"),
        Binding("r", "refresh_data", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="main"):
            yield Static("[b]Application Tracker[/b] - [d] Dashboard | [a] Applications | [r] Refresh | [q] Quit", id="top-help")
            yield Static("", id="dashboard-body")
            yield DataTable(id="applications-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#applications-table", DataTable)
        table.add_columns("ID", "Company", "Position", "Job ID", "Status", "Applied")
        self.action_refresh_data()
        self.action_show_dashboard()

    def action_show_dashboard(self) -> None:
        dashboard = self.query_one("#dashboard-body", Static)
        table = self.query_one("#applications-table", DataTable)
        dashboard.styles.display = "block"
        table.styles.display = "none"

    def action_show_applications(self) -> None:
        dashboard = self.query_one("#dashboard-body", Static)
        table = self.query_one("#applications-table", DataTable)
        dashboard.styles.display = "none"
        table.styles.display = "block"

    def action_refresh_data(self) -> None:
        self._load_dashboard()
        self._load_applications()

    def _load_dashboard(self) -> None:
        dashboard = self.query_one("#dashboard-body", Static)
        try:
            analytics = AnalyticsService()
            overview = analytics.get_overview_counts()
            conversions = analytics.get_conversion_rates()
            dashboard.update(build_dashboard_text(overview, conversions))
        except Exception as exc:
            dashboard.update(f"Unable to load dashboard data.\n{exc}")

    def _load_applications(self) -> None:
        table = self.query_one("#applications-table", DataTable)

        try:
            table.clear()
        except TypeError:
            table.clear(columns=False)

        try:
            app_svc = ApplicationService()
            company_svc = CompanyService()
            position_svc = PositionService()
            status_svc = StatusService()

            apps = app_svc.get_all()
            if not apps:
                table.add_row("-", "No applications", "-", "-", "-", "-")
                return

            for app in apps:
                company = company_svc.get(app.company_id)
                position = position_svc.get(app.position_id)
                status = status_svc.get_status(app.current_status)

                company_name = company.name if company else f"ID {app.company_id}"
                position_name = f"{position.title} ({position.level})" if position else f"ID {app.position_id}"
                status_name = status.status_name if status else str(app.current_status)

                table.add_row(
                    str(app.id),
                    company_name,
                    position_name,
                    app.job_id or "-",
                    status_name,
                    str(app.applied_date),
                )
        except Exception as exc:
            table.add_row("-", "Unable to load applications", "-", "-", str(exc), "-")


def run() -> None:
    """Run the Textual app."""
    TrackerApp().run()

