"""Read-only service for application statuses and transition validation."""

from typing import List, Optional, Union

from job_tracker.models.application_status import ApplicationStatus
from job_tracker.services.base_service import BaseService


ALLOWED_TRANSITIONS = {
    "Applied": {"Interview Scheduled", "Rejected", "Withdrawn"},
    "Interview Scheduled": {"Interviewed", "Rejected"},
    "Interviewed": {"Offer", "Rejected"},
    "Offer": {"Accepted", "Rejected", "Withdrawn"},
    "Accepted": set(),
    "Rejected": set(),
    "Withdrawn": set(),
}


class StatusService(BaseService):
    """Status lookup and transition validation operations."""

    def get_all_statuses(self) -> List[ApplicationStatus]:
        query = """
            SELECT id, status_name, description, is_terminal
            FROM application_statuses
            ORDER BY id ASC
        """

        with self._executor() as (_, executor):
            rows = executor.execute_query(query)
            return [ApplicationStatus.from_dict(row) for row in rows]

    def get_status(self, status_id: int) -> Optional[ApplicationStatus]:
        query = """
            SELECT id, status_name, description, is_terminal
            FROM application_statuses
            WHERE id = %s
        """

        with self._executor() as (_, executor):
            row = executor.execute_query_single(query, (status_id,))
            return ApplicationStatus.from_dict(row) if row else None

    def validate_transition(self, current_status: Union[int, str], new_status: Union[int, str]) -> bool:
        current_name = self._resolve_status_name(current_status)
        new_name = self._resolve_status_name(new_status)

        if current_name not in ALLOWED_TRANSITIONS:
            raise ValueError(f"Unknown current status: {current_name}")

        allowed = ALLOWED_TRANSITIONS[current_name]
        return new_name in allowed

    def _resolve_status_name(self, status: Union[int, str]) -> str:
        if isinstance(status, str):
            return status

        if isinstance(status, int):
            status_model = self.get_status(status)
            if not status_model:
                raise ValueError(f"Status id not found: {status}")
            return status_model.status_name

        raise ValueError("Status must be an int (id) or str (status name)")

    def get_status_id_by_name(self, status_name: str) -> Optional[int]:
        query = "SELECT id FROM application_statuses WHERE status_name = %s"
        with self._executor() as (_, executor):
            row = executor.execute_query_single(query, (status_name,))
            return row["id"] if row else None

