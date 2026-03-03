"""Shared helpers for CRUD service classes."""

from contextlib import contextmanager
from typing import Generator, Optional, Tuple

from job_tracker.database.connection import DatabaseConnection
from job_tracker.database.query_executor import QueryExecutor
from job_tracker.utils.config import Config


class BaseService:
    """Base class that provides DB connection + query executor wiring."""

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config()
        self.connection_string = self.config.get_connection_string()

    @contextmanager
    def _executor(self) -> Generator[Tuple[DatabaseConnection, QueryExecutor], None, None]:
        """Yield an active connection and query executor."""
        with DatabaseConnection(self.connection_string) as db:
            executor = QueryExecutor(db.connection)
            yield db, executor

