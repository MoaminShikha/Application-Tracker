"""CRUD service for companies."""

from typing import List, Optional

from job_tracker.models.company import Company
from job_tracker.services.base_service import BaseService
from job_tracker.services.query_options import ListQueryOptions


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

        with self._transaction() as executor:
            row = executor.execute_insert_returning(
                query,
                (company.name, company.industry, company.location, company.notes),
            )
            return Company.from_dict(row)

    def get_company(self, company_id: int) -> Optional[Company]:
        query = """
            SELECT id, name, industry, location, notes, created_at, updated_at
            FROM companies
            WHERE id = %s
        """

        with self._executor() as executor:
            row = executor.execute_query_single(query, (company_id,))
            return Company.from_dict(row) if row else None

    def get_all_companies(self, options: Optional[ListQueryOptions] = None) -> List[Company]:
        options = options or ListQueryOptions(sort_by="created_at", sort_dir="desc")
        sort_columns = {"id", "name", "created_at", "updated_at"}
        sort_by = options.sort_by if options.sort_by in sort_columns else "created_at"
        sort_dir = "ASC" if str(options.sort_dir).lower() == "asc" else "DESC"

        query = f"""
            SELECT id, name, industry, location, notes, created_at, updated_at
            FROM companies
            ORDER BY {sort_by} {sort_dir}
        """

        params = []
        if options.limit is not None:
            query += "\n LIMIT %s"
            params.append(options.limit)
        if options.offset is not None:
            query += "\n OFFSET %s"
            params.append(options.offset)

        with self._executor() as executor:
            rows = executor.execute_query(query, tuple(params) if params else None)
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

        with self._transaction() as executor:
            current = executor.execute_query_single(
                """
                SELECT id, name, industry, location, notes, created_at, updated_at
                FROM companies
                WHERE id = %s
                """,
                (company_id,),
            )
            if not current:
                return None

            merged = {**current, **updates}
            Company.from_dict(merged)

            row = executor.execute_query_single(query, tuple(params))
            return Company.from_dict(row) if row else None

    def delete_company(self, company_id: int) -> bool:
        query = "DELETE FROM companies WHERE id = %s"

        with self._transaction() as executor:
            affected = executor.execute_update(query, (company_id,))
            return affected > 0

