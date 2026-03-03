"""Analytics service for pipeline and performance metrics."""

from typing import Dict, List

from job_tracker.services.base_service import BaseService


class AnalyticsService(BaseService):
    """Provides aggregate metrics and analytics queries."""

    def get_overview_counts(self) -> Dict[str, int]:
        query = """
            SELECT
                COUNT(*)::int AS total_applications,
                COUNT(*) FILTER (WHERE s.is_terminal = FALSE)::int AS active_applications,
                COUNT(*) FILTER (WHERE s.status_name = 'Offer')::int AS offers,
                COUNT(*) FILTER (WHERE s.status_name = 'Accepted')::int AS accepted,
                COUNT(*) FILTER (WHERE s.status_name = 'Rejected')::int AS rejected
            FROM applications a
            JOIN application_statuses s ON s.id = a.current_status
        """
        with self._executor() as (_, executor):
            row = executor.execute_query_single(query)
            return row or {
                "total_applications": 0,
                "active_applications": 0,
                "offers": 0,
                "accepted": 0,
                "rejected": 0,
            }

    def get_status_distribution(self) -> List[Dict[str, int]]:
        query = """
            SELECT s.status_name, COUNT(*)::int AS count
            FROM applications a
            JOIN application_statuses s ON s.id = a.current_status
            GROUP BY s.status_name
            ORDER BY count DESC, s.status_name ASC
        """
        with self._executor() as (_, executor):
            return executor.execute_query(query)

    def get_conversion_rates(self) -> Dict[str, float]:
        query = """
            SELECT
                COUNT(*)::float AS total,
                COUNT(*) FILTER (WHERE s.status_name IN ('Interview Scheduled', 'Interviewed', 'Offer', 'Accepted'))::float AS reached_interview,
                COUNT(*) FILTER (WHERE s.status_name IN ('Offer', 'Accepted'))::float AS reached_offer,
                COUNT(*) FILTER (WHERE s.status_name = 'Accepted')::float AS accepted
            FROM applications a
            JOIN application_statuses s ON s.id = a.current_status
        """
        with self._executor() as (_, executor):
            row = executor.execute_query_single(query) or {}

        total = row.get("total", 0.0) or 0.0
        interview = row.get("reached_interview", 0.0) or 0.0
        offer = row.get("reached_offer", 0.0) or 0.0
        accepted = row.get("accepted", 0.0) or 0.0

        if total == 0:
            return {
                "application_to_interview_pct": 0.0,
                "application_to_offer_pct": 0.0,
                "application_to_accept_pct": 0.0,
            }

        return {
            "application_to_interview_pct": round((interview / total) * 100, 2),
            "application_to_offer_pct": round((offer / total) * 100, 2),
            "application_to_accept_pct": round((accepted / total) * 100, 2),
        }

    def get_response_time_by_company(self) -> List[Dict[str, float]]:
        query = """
            SELECT
                c.name AS company,
                ROUND(AVG(EXTRACT(EPOCH FROM (e.event_date - a.created_at)) / 86400.0)::numeric, 2)::float AS avg_days_to_first_event
            FROM applications a
            JOIN companies c ON c.id = a.company_id
            JOIN LATERAL (
                SELECT event_date
                FROM application_events e
                WHERE e.application_id = a.id
                ORDER BY e.event_date ASC
                LIMIT 1
            ) e ON TRUE
            GROUP BY c.name
            ORDER BY avg_days_to_first_event ASC NULLS LAST
        """
        with self._executor() as (_, executor):
            return executor.execute_query(query)

    def get_recent_applications(self, days: int = 30) -> List[Dict[str, str]]:
        query = """
            SELECT
                a.id,
                c.name AS company,
                p.title AS position,
                s.status_name AS status,
                a.applied_date
            FROM applications a
            JOIN companies c ON c.id = a.company_id
            JOIN positions p ON p.id = a.position_id
            JOIN application_statuses s ON s.id = a.current_status
            WHERE a.applied_date >= CURRENT_DATE - (%s * INTERVAL '1 day')
            ORDER BY a.applied_date DESC
        """
        with self._executor() as (_, executor):
            return executor.execute_query(query, (days,))

