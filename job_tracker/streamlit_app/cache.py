"""
Cached service-call wrappers.

All reads go through @st.cache_data (TTL = 30 s) so re-runs don't hammer the
DB.  Write helpers call st.cache_data.clear() after mutating state so the next
render fetches fresh data.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

import streamlit as st

from job_tracker.analytics.analytics_service import AnalyticsService
from job_tracker.services import (
    ApplicationService,
    CompanyService,
    EventService,
    PositionService,
    RecruiterService,
    StatusService,
)
from job_tracker.services.query_options import ApplicationQueryOptions, ListQueryOptions


# ── Read helpers (cached) ────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_companies():
    return CompanyService().get_all()


@st.cache_data(ttl=30)
def get_positions():
    return PositionService().get_all()


@st.cache_data(ttl=30)
def get_recruiters():
    return RecruiterService().get_all()


@st.cache_data(ttl=30)
def get_statuses():
    return StatusService().get_all_statuses()


@st.cache_data(ttl=30)
def get_status_id(name: str) -> Optional[int]:
    return StatusService().get_status_id_by_name(name)


@st.cache_data(ttl=30)
def get_applications(
    company_id: Optional[int] = None,
    status_id: Optional[int] = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
):
    return ApplicationService().get_all(
        options=ApplicationQueryOptions(
            company_id=company_id,
            status_id=status_id,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    )


@st.cache_data(ttl=30)
def get_application(app_id: int):
    return ApplicationService().get(app_id)


@st.cache_data(ttl=30)
def get_events(app_id: int):
    return EventService().get_for_application(app_id)


@st.cache_data(ttl=30)
def get_recent_applications(days: int = 7):
    """Return applications created in the last N days (client-side filter)."""
    from datetime import datetime, timedelta
    apps = ApplicationService().get_all()
    cutoff = datetime.now() - timedelta(days=days)
    return [a for a in apps if a.created_at and a.created_at >= cutoff]


# ── Write helpers (clear cache after mutation) ───────────────────────────────

def _clear():
    st.cache_data.clear()


def create_company(name: str, industry: Optional[str], location: Optional[str], notes: Optional[str]):
    result = CompanyService().create(name=name, industry=industry, location=location, notes=notes)
    _clear()
    return result


def create_position(title: str, level: str):
    result = PositionService().create(title=title, level=level)
    _clear()
    return result


def create_recruiter(name: str, email: Optional[str], phone: Optional[str], company_id: Optional[int]):
    result = RecruiterService().create(name=name, email=email, phone=phone, company_id=company_id)
    _clear()
    return result


def create_application(
    company_id: int,
    position_id: int,
    applied_date: Optional[date],
    recruiter_id: Optional[int],
    job_id: Optional[str],
    notes: Optional[str],
):
    result = ApplicationService().create(
        company_id=company_id,
        position_id=position_id,
        applied_date=applied_date,
        recruiter_id=recruiter_id,
        job_id=job_id,
        notes=notes,
    )
    _clear()
    return result


def update_application_status(app_id: int, new_status_id: int):
    result = ApplicationService().update_status(app_id, new_status_id)
    _clear()
    return result


def delete_application(app_id: int) -> bool:
    result = ApplicationService().delete(app_id)
    _clear()
    return result


def delete_company(company_id: int) -> bool:
    result = CompanyService().delete(company_id)
    _clear()
    return result


def delete_position(position_id: int) -> bool:
    result = PositionService().delete(position_id)
    _clear()
    return result


def delete_recruiter(recruiter_id: int) -> bool:
    result = RecruiterService().delete(recruiter_id)
    _clear()
    return result


def log_event(app_id: int, event_type: str, notes: Optional[str]):
    result = EventService().log(application_id=app_id, event_type=event_type, notes=notes)
    _clear()
    return result


def update_application(app_id: int, **fields):
    result = ApplicationService().update(app_id, **fields)
    _clear()
    return result


def refresh() -> None:
    """Explicitly clear all cached reads (e.g. after a manual refresh button)."""
    st.cache_data.clear()


# ── Analytics (cached reads) ─────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_analytics_overview() -> dict:
    return AnalyticsService().get_overview_counts()


@st.cache_data(ttl=30)
def get_status_distribution() -> list:
    return AnalyticsService().get_status_distribution()


@st.cache_data(ttl=30)
def get_conversion_rates() -> dict:
    return AnalyticsService().get_conversion_rates()


@st.cache_data(ttl=30)
def get_response_time_by_company() -> list:
    return AnalyticsService().get_response_time_by_company()
