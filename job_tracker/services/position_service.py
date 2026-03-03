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

        with self._executor() as (db, executor):
            try:
                row = executor.execute_insert_returning(query, (position.title, position.level))
                db.connection.commit()
                return Position.from_dict(row)
            except Exception:
                db.connection.rollback()
                raise

    def get_position(self, position_id: int) -> Optional[Position]:
        query = """
            SELECT id, title, level, created_at
            FROM positions
            WHERE id = %s
        """

        with self._executor() as (_, executor):
            row = executor.execute_query_single(query, (position_id,))
            return Position.from_dict(row) if row else None

    def get_all_positions(self) -> List[Position]:
        query = """
            SELECT id, title, level, created_at
            FROM positions
            ORDER BY created_at DESC
        """

        with self._executor() as (_, executor):
            rows = executor.execute_query(query)
            return [Position.from_dict(row) for row in rows]

    def delete_position(self, position_id: int) -> bool:
        query = "DELETE FROM positions WHERE id = %s"

        with self._executor() as (db, executor):
            try:
                affected = executor.execute_update(query, (position_id,))
                db.connection.commit()
                return affected > 0
            except Exception:
                db.connection.rollback()
                raise

