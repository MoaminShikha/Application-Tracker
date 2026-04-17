"""CRUD service for recruiters."""

from typing import List, Optional

from job_tracker.models.recruiter import Recruiter
from job_tracker.services.crud_service import CRUDService


class RecruiterService(CRUDService[Recruiter]):
    """Business logic and CRUD operations for recruiters."""

    _model = Recruiter
    _table = "recruiters"
    _select_columns = "id, name, email, phone, company_id, created_at"

    def create(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> Recruiter:
        """Insert a new recruiter and return the created record."""
        recruiter = Recruiter(name=name, email=email, phone=phone, company_id=company_id)

        with self._transaction() as executor:
            row = executor.execute_insert_returning(
                f"""
                INSERT INTO recruiters (name, email, phone, company_id)
                VALUES (%s, %s, %s, %s)
                RETURNING {self._select_columns}
                """,
                (recruiter.name, recruiter.email, recruiter.phone, recruiter.company_id),
            )
            return Recruiter.from_dict(row)

    def get_all(self) -> List[Recruiter]:
        """Fetch all recruiters ordered by creation date descending."""
        query = f"SELECT {self._select_columns} FROM {self._table} ORDER BY created_at DESC"
        with self._executor() as executor:
            rows = executor.execute_query(query)
            return [Recruiter.from_dict(row) for row in rows]

    def update(self, recruiter_id: int, **fields) -> Optional[Recruiter]:
        """Update allowed fields on a recruiter. Validates merged state before writing."""
        allowed = {"name", "email", "phone", "company_id"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            raise ValueError("No valid fields provided for update")

        set_clauses = [f"{field} = %s" for field in updates]
        params = list(updates.values()) + [recruiter_id]

        query = f"""
            UPDATE {self._table}
            SET {', '.join(set_clauses)}
            WHERE id = %s
            RETURNING {self._select_columns}
        """

        with self._transaction() as executor:
            current = executor.execute_query_single(
                f"SELECT {self._select_columns} FROM {self._table} WHERE id = %s",
                (recruiter_id,),
            )
            if not current:
                return None
            Recruiter.from_dict({**current, **updates})  # validate merged state
            row = executor.execute_query_single(query, tuple(params))
            return Recruiter.from_dict(row) if row else None
