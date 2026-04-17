"""Generic CRUD base for typed service layers."""

import logging
from typing import ClassVar, Generic, List, Optional, Type, TypeVar

from job_tracker.models.base import BaseModel
from job_tracker.services.base_service import BaseService

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class CRUDService(BaseService, Generic[T]):
    """
    Generic base service that provides get, get_all, and delete for any model T.

    Subclasses must define class variables:
        _model          – the Model class (e.g. Company)
        _table          – DB table name (e.g. "companies")
        _select_columns – comma-separated column list for SELECT queries

    Subclasses must implement:
        create(...)  – insert a new record and return the created model

    Subclasses may implement:
        update(...)  – modify a record and return the updated model

    Subclasses may override:
        get_all(...) – if filtering, sorting, or pagination options are needed
    """

    _model: ClassVar[Type]
    _table: ClassVar[str]
    _select_columns: ClassVar[str]

    def get(self, record_id: int) -> Optional[T]:
        """Fetch a single record by primary key. Returns None if not found."""
        query = f"SELECT {self._select_columns} FROM {self._table} WHERE id = %s"
        with self._executor() as executor:
            row = executor.execute_query_single(query, (record_id,))
            return self._model.from_dict(row) if row else None

    def get_all(self) -> List[T]:
        """Fetch all records ordered by id ascending."""
        query = f"SELECT {self._select_columns} FROM {self._table} ORDER BY id ASC"
        with self._executor() as executor:
            rows = executor.execute_query(query)
            return [self._model.from_dict(row) for row in rows]

    def delete(self, record_id: int) -> bool:
        """Delete a record by primary key. Returns True if a row was removed."""
        query = f"DELETE FROM {self._table} WHERE id = %s"
        with self._transaction() as executor:
            affected = executor.execute_update(query, (record_id,))
            return affected > 0
