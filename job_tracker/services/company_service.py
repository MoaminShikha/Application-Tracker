"""CRUD service for companies."""

from typing import List, Optional

from job_tracker.models.company import Company
from job_tracker.services.base_service import BaseService


class CompanyService(BaseService):
    """Business logic and CRUD operations for companies."""

    def create_company(
        self,
        name: str,
        industry: Optional[str] = None,
        location: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Company:
        company = Company(name=name, industry=industry, location=location, notes=notes)
        company.validate()

        query = """
            INSERT INTO companies (name, industry, location, notes)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, industry, location, notes, created_at, updated_at
        """

        with self._executor() as (db, executor):
            try:
                row = executor.execute_insert_returning(
                    query,
                    (company.name, company.industry, company.location, company.notes),
                )
                db.connection.commit()
                return Company.from_dict(row)
            except Exception:
                db.connection.rollback()
                raise

    def get_company(self, company_id: int) -> Optional[Company]:
        query = """
            SELECT id, name, industry, location, notes, created_at, updated_at
            FROM companies
            WHERE id = %s
        """

        with self._executor() as (_, executor):
            row = executor.execute_query_single(query, (company_id,))
            return Company.from_dict(row) if row else None

    def get_all_companies(self) -> List[Company]:
        query = """
            SELECT id, name, industry, location, notes, created_at, updated_at
            FROM companies
            ORDER BY created_at DESC
        """

        with self._executor() as (_, executor):
            rows = executor.execute_query(query)
            return [Company.from_dict(row) for row in rows]

    def update_company(self, company_id: int, **fields) -> Optional[Company]:
        allowed_fields = {"name", "industry", "location", "notes"}
        updates = {k: v for k, v in fields.items() if k in allowed_fields}
        if not updates:
            raise ValueError("No valid fields provided for update")

        set_clauses = []
        params = []
        for field, value in updates.items():
            set_clauses.append(f"{field} = %s")
            params.append(value)

        set_clauses.append("updated_at = NOW()")
        params.append(company_id)

        query = f"""
            UPDATE companies
            SET {', '.join(set_clauses)}
            WHERE id = %s
            RETURNING id, name, industry, location, notes, created_at, updated_at
        """

        with self._executor() as (db, executor):
            try:
                row = executor.execute_query_single(query, tuple(params))
                db.connection.commit()
                return Company.from_dict(row) if row else None
            except Exception:
                db.connection.rollback()
                raise

    def delete_company(self, company_id: int) -> bool:
        query = "DELETE FROM companies WHERE id = %s"

        with self._executor() as (db, executor):
            try:
                affected = executor.execute_update(query, (company_id,))
                db.connection.commit()
                return affected > 0
            except Exception:
                db.connection.rollback()
                raise

