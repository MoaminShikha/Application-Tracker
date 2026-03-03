"""Immutable event logging service for applications."""

from datetime import datetime
from typing import List, Optional

from job_tracker.models.application_event import ApplicationEvent
from job_tracker.services.base_service import BaseService


class EventService(BaseService):
    """Log and read application events (insert-only design)."""

    def log_event(
        self,
        application_id: int,
        event_type: str,
        event_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> ApplicationEvent:
        event = ApplicationEvent(
            application_id=application_id,
            event_type=event_type,
            event_date=event_date or datetime.now(),  # For validation only
            notes=notes,
        )
        event.validate()

        # If event_date is provided, use it; otherwise let DB use NOW()
        if event_date is not None:
            query = """
                INSERT INTO application_events (application_id, event_type, event_date, notes)
                VALUES (%s, %s, %s, %s)
                RETURNING id, application_id, event_type, event_date, notes, created_at
            """
            params = (application_id, event_type, event_date, notes)
        else:
            query = """
                INSERT INTO application_events (application_id, event_type, notes)
                VALUES (%s, %s, %s)
                RETURNING id, application_id, event_type, event_date, notes, created_at
            """
            params = (application_id, event_type, notes)

        with self._executor() as (db, executor):
            try:
                row = executor.execute_insert_returning(query, params)
                db.connection.commit()
                return ApplicationEvent.from_dict(row)
            except Exception:
                db.connection.rollback()
                raise

    def get_event(self, event_id: int) -> Optional[ApplicationEvent]:
        query = """
            SELECT id, application_id, event_type, event_date, notes, created_at
            FROM application_events
            WHERE id = %s
        """

        with self._executor() as (_, executor):
            row = executor.execute_query_single(query, (event_id,))
            return ApplicationEvent.from_dict(row) if row else None

    def get_events_for_application(self, application_id: int) -> List[ApplicationEvent]:
        query = """
            SELECT id, application_id, event_type, event_date, notes, created_at
            FROM application_events
            WHERE application_id = %s
            ORDER BY event_date ASC
        """

        with self._executor() as (_, executor):
            rows = executor.execute_query(query, (application_id,))
            return [ApplicationEvent.from_dict(row) for row in rows]

