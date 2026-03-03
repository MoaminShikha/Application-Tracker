"""CRUD service for recruiters."""

from typing import List, Optional

from job_tracker.models.recruiter import Recruiter
from job_tracker.services.base_service import BaseService


class RecruiterService(BaseService):
    """Business logic and CRUD operations for recruiters."""

    def create_recruiter(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> Recruiter:
        recruiter = Recruiter(name=name, email=email, phone=phone, company_id=company_id)
        recruiter.validate()

        query = """
            INSERT INTO recruiters (name, email, phone, company_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, email, phone, company_id, created_at
        """

        with self._executor() as (db, executor):
            try:
                row = executor.execute_insert_returning(
                    query,
                    (recruiter.name, recruiter.email, recruiter.phone, recruiter.company_id),
                )
                db.connection.commit()
                return Recruiter.from_dict(row)
            except Exception:
                db.connection.rollback()
                raise

    def get_recruiter(self, recruiter_id: int) -> Optional[Recruiter]:
        query = """
            SELECT id, name, email, phone, company_id, created_at
            FROM recruiters
            WHERE id = %s
        """

        with self._executor() as (_, executor):
            row = executor.execute_query_single(query, (recruiter_id,))
            return Recruiter.from_dict(row) if row else None

    def get_all_recruiters(self) -> List[Recruiter]:
        query = """
            SELECT id, name, email, phone, company_id, created_at
            FROM recruiters
            ORDER BY created_at DESC
        """

        with self._executor() as (_, executor):
            rows = executor.execute_query(query)
            return [Recruiter.from_dict(row) for row in rows]

    def update_recruiter(self, recruiter_id: int, **fields) -> Optional[Recruiter]:
        allowed_fields = {"name", "email", "phone", "company_id"}
        updates = {k: v for k, v in fields.items() if k in allowed_fields}
        if not updates:
            raise ValueError("No valid fields provided for update")

        set_clauses = []
        params = []
        for field, value in updates.items():
            set_clauses.append(f"{field} = %s")
            params.append(value)
        params.append(recruiter_id)

        query = f"""
            UPDATE recruiters
            SET {', '.join(set_clauses)}
            WHERE id = %s
            RETURNING id, name, email, phone, company_id, created_at
        """

        with self._executor() as (db, executor):
            try:
                row = executor.execute_query_single(query, tuple(params))
                db.connection.commit()
                return Recruiter.from_dict(row) if row else None
            except Exception:
                db.connection.rollback()
                raise

    def delete_recruiter(self, recruiter_id: int) -> bool:
        query = "DELETE FROM recruiters WHERE id = %s"

        with self._executor() as (db, executor):
            try:
                affected = executor.execute_update(query, (recruiter_id,))
                db.connection.commit()
                return affected > 0
            except Exception:
                db.connection.rollback()
                raise

