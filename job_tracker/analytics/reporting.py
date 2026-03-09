"""Reporting helpers for dashboard rendering and exports."""

import csv
import json
from io import StringIO
from typing import Any, Dict, Iterable, List

from job_tracker.utils.colors import colorize_status


def build_dashboard_rows(
    overview: Dict[str, Any],
    distribution: List[Dict[str, Any]],
    conversions: Dict[str, Any],
) -> List[str]:
    """Build a compact text dashboard from analytics payloads."""
    rows = [
        "=== Application Tracker Dashboard ===",
        f"Total applications: {overview.get('total_applications', 0)}",
        f"Active applications: {overview.get('active_applications', 0)}",
        f"Offers: {overview.get('offers', 0)} | Accepted: {overview.get('accepted', 0)} | Rejected: {overview.get('rejected', 0)}",
        "",
        "Conversion rates:",
        f"- App -> Interview: {conversions.get('application_to_interview_pct', 0)}%",
        f"- App -> Offer: {conversions.get('application_to_offer_pct', 0)}%",
        f"- App -> Accept: {conversions.get('application_to_accept_pct', 0)}%",
        "",
        "Status distribution:",
    ]
    for item in distribution:
        status_name = item.get('status_name', 'Unknown')
        count = item.get('count', 0)
        colored_status = colorize_status(status_name)
        rows.append(f"- {colored_status}: {count}")
    return rows


def to_json_report(data: Dict[str, Any]) -> str:
    """Serialize report payload to pretty JSON."""
    return json.dumps(data, indent=2, default=str)


def to_csv_report(rows: Iterable[Dict[str, Any]]) -> str:
    """Serialize an iterable of dictionaries to CSV text."""
    rows_list = list(rows)
    if not rows_list:
        return ""

    output = StringIO()
    fieldnames = list(rows_list[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows_list)
    return output.getvalue()

