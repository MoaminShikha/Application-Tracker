"""Application management service with status validation."""

from datetime import date
from typing import List, Optional

from job_tracker.models.application import Application
from job_tracker.services.crud_service import CRUDService
from job_tracker.services.query_options import ApplicationQueryOptions
from job_tracker.services.status_service import ALLOWED_TRANSITIONS


_INSERT_EVENT_SQL = """
    INSERT INTO application_events (application_id, event_type, notes)
    VALUES (%s, %s, %s)
"""


class ApplicationService(CRUDService[Application]):
    """Business logic and CRUD operations for applications."""

    _model = Application
    _table = "applications"
    _select_columns = (
        "id, company_id, position_id, recruiter_id, job_id, "
        "current_status, applied_date, notes, created_at, updated_at"
    )

    def create(
        self,
        company_id: int,
        position_id: int,
        applied_date: Optional[date] = None,
        recruiter_id: Optional[int] = None,
        job_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Application:
        """Create a new application, set status to 'Applied', and log the initial event."""
        with self._transaction() as executor:
            status_row = executor.execute_query_single(
                "SELECT id FROM application_statuses WHERE status_name = 'Applied'"
            )
            if not status_row:
                raise ValueError("Required status 'Applied' is missing from application_statuses")

            application = Application(
                company_id=company_id,
                position_id=position_id,
                recruiter_id=recruiter_id,
                job_id=job_id,
                current_status=status_row["id"],
                applied_date=applied_date or date.today(),
                notes=notes,
            )

            row = executor.execute_insert_returning(
                f"""
                INSERT INTO applications
                    (company_id, position_id, recruiter_id, job_id, current_status, applied_date, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING {self._select_columns}
                """,
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
            executor.execute_update(_INSERT_EVENT_SQL, (row["id"], "Applied", "Application created"))
            return Application.from_dict(row)

    def get_all(self, options: Optional[ApplicationQueryOptions] = None) -> List[Application]:
        """Fetch applications with optional filtering, sorting, and pagination."""
        options = options or ApplicationQueryOptions(sort_by="created_at", sort_dir="desc")
        sort_columns = {"id", "created_at", "updated_at", "applied_date", "current_status"}
        sort_by = options.sort_by if options.sort_by in sort_columns else "created_at"
        sort_dir = "ASC" if str(options.sort_dir).lower() == "asc" else "DESC"

        query = f"""
            SELECT {self._select_columns}
            FROM {self._table}
            WHERE (%s IS NULL OR company_id = %s)
              AND (%s IS NULL OR current_status = %s)
            ORDER BY {sort_by} {sort_dir}
        """

        params = [options.company_id, options.company_id, options.status_id, options.status_id]
        if options.limit is not None:
            query += "\n LIMIT %s"
            params.append(options.limit)
        if options.offset is not None:
            query += "\n OFFSET %s"
            params.append(options.offset)

        with self._executor() as executor:
            rows = executor.execute_query(query, tuple(params))
            return [Application.from_dict(row) for row in rows]

    def update_status(self, application_id: int, new_status: int) -> Optional[Application]:
        """Transition application to a new status, validating the state machine."""
        with self._transaction() as executor:
            app_row = executor.execute_query_single(
                "SELECT current_status FROM applications WHERE id = %s",
                (application_id,),
            )
            if not app_row:
                return None

            status_rows = executor.execute_query(
                "SELECT id, status_name FROM application_statuses WHERE id = ANY(%s)",
                ([app_row["current_status"], new_status],),
            )
            statuses = {r["id"]: r["status_name"] for r in status_rows}

            current_name = statuses.get(app_row["current_status"])
            new_name = statuses.get(new_status)
            if not current_name or not new_name:
                raise ValueError("Current or new status does not exist")

            if new_name not in ALLOWED_TRANSITIONS.get(current_name, set()):
                raise ValueError(f"Invalid transition: {current_name} -> {new_name}")

            row = executor.execute_query_single(
                f"""
                UPDATE {self._table}
                SET current_status = %s, updated_at = NOW()
                WHERE id = %s
                RETURNING {self._select_columns}
                """,
                (new_status, application_id),
            )
            if not row:
                return None

            executor.execute_update(
                _INSERT_EVENT_SQL,
                (application_id, f"Status changed to {new_name}", None),
            )
            return Application.from_dict(row)

    def update(self, application_id: int, **fields) -> Optional[Application]:
        """Update editable fields on an application. Validates merged state before writing."""
        allowed = {"company_id", "position_id", "recruiter_id", "job_id", "applied_date", "notes"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            raise ValueError("No valid fields provided for update")

        set_clauses = [f"{field} = %s" for field in updates]
        set_clauses.append("updated_at = NOW()")
        params = list(updates.values()) + [application_id]

        query = f"""
            UPDATE {self._table}
            SET {', '.join(set_clauses)}
            WHERE id = %s
            RETURNING {self._select_columns}
        """

        with self._transaction() as executor:
            current = executor.execute_query_single(
                f"SELECT {self._select_columns} FROM {self._table} WHERE id = %s",
                (application_id,),
            )
            if not current:
                return None
            Application.from_dict({**current, **updates})  # validate merged state
            row = executor.execute_query_single(query, tuple(params))
            return Application.from_dict(row) if row else None
