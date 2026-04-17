"""CRUD service for positions."""

from typing import List, Optional

from job_tracker.models.position import Position
from job_tracker.services.crud_service import CRUDService


class PositionService(CRUDService[Position]):
    """Business logic and CRUD operations for positions."""

    _model = Position
    _table = "positions"
    _select_columns = "id, title, level, created_at"

    def create(self, title: str, level: str) -> Position:
        """Insert a new position and return the created record."""
        position = Position(title=title, level=level)

        with self._transaction() as executor:
            row = executor.execute_insert_returning(
                f"""
                INSERT INTO positions (title, level)
                VALUES (%s, %s)
                RETURNING {self._select_columns}
                """,
                (position.title, position.level),
            )
            return Position.from_dict(row)

    def get_all(self) -> List[Position]:
        """Fetch all positions ordered by creation date descending."""
        query = f"SELECT {self._select_columns} FROM {self._table} ORDER BY created_at DESC"
        with self._executor() as executor:
            rows = executor.execute_query(query)
            return [Position.from_dict(row) for row in rows]
