"""Immutable event logging service for applications."""

from datetime import datetime
from typing import List, Optional

from job_tracker.models.application_event import ApplicationEvent
from job_tracker.services.base_service import BaseService


class EventService(BaseService):
    """Log and read application events (insert-only design)."""

    _select_columns = "id, application_id, event_type, event_date, notes, created_at"

    def log(
        self,
        application_id: int,
        event_type: str,
        event_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> ApplicationEvent:
        """Validate and persist an application event."""
        # Validate via model construction (__post_init__ → validate)
        ApplicationEvent(
            application_id=application_id,
            event_type=event_type,
            event_date=event_date or datetime.now(),
            notes=notes,
        )

        # Use explicit event_date column only when the caller supplies one;
        # otherwise let the DB default (NOW()) fill it in.
        if event_date is not None:
            query = f"""
                INSERT INTO application_events (application_id, event_type, event_date, notes)
                VALUES (%s, %s, %s, %s)
                RETURNING {self._select_columns}
            """
            params = (application_id, event_type, event_date, notes)
        else:
            query = f"""
                INSERT INTO application_events (application_id, event_type, notes)
                VALUES (%s, %s, %s)
                RETURNING {self._select_columns}
            """
            params = (application_id, event_type, notes)

        with self._transaction() as executor:
            row = executor.execute_insert_returning(query, params)
            return ApplicationEvent.from_dict(row)

    def get(self, event_id: int) -> Optional[ApplicationEvent]:
        """Fetch a single event by primary key."""
        query = f"SELECT {self._select_columns} FROM application_events WHERE id = %s"
        with self._executor() as executor:
            row = executor.execute_query_single(query, (event_id,))
            return ApplicationEvent.from_dict(row) if row else None

    def get_for_application(self, application_id: int) -> List[ApplicationEvent]:
        """Fetch all events for an application ordered chronologically."""
        query = f"""
            SELECT {self._select_columns}
            FROM application_events
            WHERE application_id = %s
            ORDER BY event_date ASC
        """
        with self._executor() as executor:
            rows = executor.execute_query(query, (application_id,))
            return [ApplicationEvent.from_dict(row) for row in rows]
