"""CRUD service for positions."""

from typing import List, Optional

from job_tracker.models.position import Position
from job_tracker.services.base_service import BaseService


class PositionService(BaseService):
    """Business logic and CRUD operations for positions."""

    def create_position(self, title: str, level: str) -> Position:
        position = Position(title=title, level=level)
        position.validate()

        query = """
            INSERT INTO positions (title, level)
            VALUES (%s, %s)
            RETURNING id, title, level, created_at
        """

        with self._transaction() as executor:
            row = executor.execute_insert_returning(query, (position.title, position.level))
            return Position.from_dict(row)

    def get_position(self, position_id: int) -> Optional[Position]:
        query = """
            SELECT id, title, level, created_at
            FROM positions
            WHERE id = %s
        """

        with self._executor() as executor:
            row = executor.execute_query_single(query, (position_id,))
            return Position.from_dict(row) if row else None

    def get_all_positions(self) -> List[Position]:
        query = """
            SELECT id, title, level, created_at
            FROM positions
            ORDER BY created_at DESC
        """

        with self._executor() as executor:
            rows = executor.execute_query(query)
            return [Position.from_dict(row) for row in rows]

    def delete_position(self, position_id: int) -> bool:
        query = "DELETE FROM positions WHERE id = %s"

        with self._transaction() as executor:
            affected = executor.execute_update(query, (position_id,))
            return affected > 0

