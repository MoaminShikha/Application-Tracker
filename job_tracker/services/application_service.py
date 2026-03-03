"""Application management service with status validation."""

from datetime import date
from typing import List, Optional

from job_tracker.models.application import Application
from job_tracker.services.base_service import BaseService
from job_tracker.services.status_service import ALLOWED_TRANSITIONS


class ApplicationService(BaseService):
    """Business logic and CRUD operations for applications."""

    def create_application(
        self,
        company_id: int,
        position_id: int,
        applied_date: Optional[date] = None,
        recruiter_id: Optional[int] = None,
        job_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Application:
        status_id = self._get_status_id_by_name("Applied")
        if status_id is None:
            raise ValueError("Required status 'Applied' is missing from application_statuses")

        application = Application(
            company_id=company_id,
            position_id=position_id,
            recruiter_id=recruiter_id,
            job_id=job_id,
            current_status=status_id,
            applied_date=applied_date or date.today(),
            notes=notes,
        )
        application.validate()

        insert_app_query = """
            INSERT INTO applications (company_id, position_id, recruiter_id, job_id, current_status, applied_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, company_id, position_id, recruiter_id, job_id, current_status, applied_date, notes, created_at, updated_at
        """

        insert_event_query = """
            INSERT INTO application_events (application_id, event_type, notes)
            VALUES (%s, %s, %s)
        """

        with self._executor() as (db, executor):
            try:
                row = executor.execute_insert_returning(
                    insert_app_query,
                    (
                        application.company_id,
                        application.position_id,
                        application.recruiter_id,
                        application.job_id,
                        application.current_status,
                        application.applied_date,
                        application.notes,
                    ),
                )
                executor.execute_update(
                    insert_event_query,
                    (
                        row["id"],
                        "Applied",
                        "Application created",
                    ),
                )
                db.connection.commit()
                return Application.from_dict(row)
            except Exception:
                db.connection.rollback()
                raise

    def get_application(self, application_id: int) -> Optional[Application]:
        query = """
            SELECT id, company_id, position_id, recruiter_id, job_id, current_status, applied_date, notes, created_at, updated_at
            FROM applications
            WHERE id = %s
        """

        with self._executor() as (_, executor):
            row = executor.execute_query_single(query, (application_id,))
            return Application.from_dict(row) if row else None

    def get_all_applications(self) -> List[Application]:
        query = """
            SELECT id, company_id, position_id, recruiter_id, job_id, current_status, applied_date, notes, created_at, updated_at
            FROM applications
            ORDER BY created_at DESC
        """

        with self._executor() as (_, executor):
            rows = executor.execute_query(query)
            return [Application.from_dict(row) for row in rows]

    def update_application_status(self, application_id: int, new_status: int) -> Optional[Application]:
        current_app = self.get_application(application_id)
        if not current_app:
            return None

        current_name = self._get_status_name_by_id(current_app.current_status)
        new_name = self._get_status_name_by_id(new_status)
        if current_name is None or new_name is None:
            raise ValueError("Current or new status does not exist")

        allowed = ALLOWED_TRANSITIONS.get(current_name, set())
        if new_name not in allowed:
            raise ValueError(f"Invalid transition: {current_name} -> {new_name}")

        update_query = """
            UPDATE applications
            SET current_status = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id, company_id, position_id, recruiter_id, job_id, current_status, applied_date, notes, created_at, updated_at
        """

        insert_event_query = """
            INSERT INTO application_events (application_id, event_type, notes)
            VALUES (%s, %s, %s)
        """

        with self._executor() as (db, executor):
            try:
                row = executor.execute_query_single(update_query, (new_status, application_id))
                if not row:
                    db.connection.rollback()
                    return None
                executor.execute_update(
                    insert_event_query,
                    (application_id, f"Status changed to {new_name}", None),
                )
                db.connection.commit()
                return Application.from_dict(row)
            except Exception:
                db.connection.rollback()
                raise

    def update_application(self, application_id: int, **fields) -> Optional[Application]:
        allowed_fields = {"company_id", "position_id", "recruiter_id", "job_id", "applied_date", "notes"}
        updates = {k: v for k, v in fields.items() if k in allowed_fields}
        if not updates:
            raise ValueError("No valid fields provided for update")

        set_clauses = []
        params = []
        for field, value in updates.items():
            set_clauses.append(f"{field} = %s")
            params.append(value)

        set_clauses.append("updated_at = NOW()")
        params.append(application_id)

        query = f"""
            UPDATE applications
            SET {', '.join(set_clauses)}
            WHERE id = %s
            RETURNING id, company_id, position_id, recruiter_id, job_id, current_status, applied_date, notes, created_at, updated_at
        """

        with self._executor() as (db, executor):
            try:
                row = executor.execute_query_single(query, tuple(params))
                if not row:
                    db.connection.rollback()
                    return None
                updated = Application.from_dict(row)
                updated.validate()
                db.connection.commit()
                return updated
            except Exception:
                db.connection.rollback()
                raise

    def delete_application(self, application_id: int) -> bool:
        query = "DELETE FROM applications WHERE id = %s"

        with self._executor() as (db, executor):
            try:
                affected = executor.execute_update(query, (application_id,))
                db.connection.commit()
                return affected > 0
            except Exception:
                db.connection.rollback()
                raise

    def _get_status_id_by_name(self, status_name: str) -> Optional[int]:
        query = "SELECT id FROM application_statuses WHERE status_name = %s"
        with self._executor() as (_, executor):
            row = executor.execute_query_single(query, (status_name,))
            return row["id"] if row else None

    def _get_status_name_by_id(self, status_id: int) -> Optional[str]:
        query = "SELECT status_name FROM application_statuses WHERE id = %s"
        with self._executor() as (_, executor):
            row = executor.execute_query_single(query, (status_id,))
            return row["status_name"] if row else None

