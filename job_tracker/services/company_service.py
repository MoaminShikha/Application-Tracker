"""CRUD service for companies."""

from typing import List, Optional

from job_tracker.models.company import Company
from job_tracker.services.crud_service import CRUDService
from job_tracker.services.query_options import ListQueryOptions


class CompanyService(CRUDService[Company]):
    """Business logic and CRUD operations for companies."""

    _model = Company
    _table = "companies"
    _select_columns = "id, name, industry, location, notes, created_at, updated_at"

    def create(
        self,
        name: str,
        industry: Optional[str] = None,
        location: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Company:
        """Insert a new company and return the created record."""
        company = Company(name=name, industry=industry, location=location, notes=notes)

        with self._transaction() as executor:
            row = executor.execute_insert_returning(
                f"""
                INSERT INTO companies (name, industry, location, notes)
                VALUES (%s, %s, %s, %s)
                RETURNING {self._select_columns}
                """,
                (company.name, company.industry, company.location, company.notes),
            )
            return Company.from_dict(row)

    def get_all(self, options: Optional[ListQueryOptions] = None) -> List[Company]:
        """Fetch all companies with optional sort/limit/offset."""
        options = options or ListQueryOptions(sort_by="created_at", sort_dir="desc")
        sort_columns = {"id", "name", "created_at", "updated_at"}
        sort_by = options.sort_by if options.sort_by in sort_columns else "created_at"
        sort_dir = "ASC" if str(options.sort_dir).lower() == "asc" else "DESC"

        query = f"""
            SELECT {self._select_columns}
            FROM {self._table}
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

    def update(self, company_id: int, **fields) -> Optional[Company]:
        """Update allowed fields on a company. Validates merged state before writing."""
        allowed = {"name", "industry", "location", "notes"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            raise ValueError("No valid fields provided for update")

        set_clauses = [f"{field} = %s" for field in updates]
        set_clauses.append("updated_at = NOW()")
        params = list(updates.values()) + [company_id]

        query = f"""
            UPDATE {self._table}
            SET {', '.join(set_clauses)}
            WHERE id = %s
            RETURNING {self._select_columns}
        """

        with self._transaction() as executor:
            current = executor.execute_query_single(
                f"SELECT {self._select_columns} FROM {self._table} WHERE id = %s",
                (company_id,),
            )
            if not current:
                return None
            Company.from_dict({**current, **updates})  # validate merged state
            row = executor.execute_query_single(query, tuple(params))
            return Company.from_dict(row) if row else None
