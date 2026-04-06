import logging

import psycopg2
from psycopg2 import OperationalError, ProgrammingError

from job_tracker.database.exceptions import (
    DatabaseConnectionError,
    ConnectionFailedError,
    ConnectionTimeoutError,
    QueryExecutionError,
    map_postgres_error,
)
from job_tracker.database.logger import log_execution_time

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Context manager for PostgreSQL database connections.

    Handles connection lifecycle, error handling, and timeout configuration.
    Used directly by init_db.py; services go through BaseService's connection pool.
    """

    def __init__(self, connection_string: str, connect_timeout: int = 5, statement_timeout: int = 30000):
        self.connection_string = connection_string
        self.connect_timeout = connect_timeout
        self.statement_timeout = statement_timeout
        self._is_connected = False
        self.connection = None

    def __enter__(self) -> "DatabaseConnection":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.disconnect()
        return False

    @log_execution_time
    def connect(self) -> None:
        try:
            logger.info("Connecting to database...")
            self.connection = psycopg2.connect(
                self.connection_string, connect_timeout=self.connect_timeout
            )
            with self.connection.cursor() as cur:
                cur.execute(f"SET statement_timeout TO {self.statement_timeout}")
            self._is_connected = True
            logger.info("Connected to database successfully")
        except OperationalError as e:
            self._is_connected = False
            if "timeout" in str(e).lower():
                raise ConnectionTimeoutError(f"Connection timed out: {e}")
            raise ConnectionFailedError(f"Failed to connect to database: {e}")
        except ProgrammingError as e:
            self._is_connected = False
            raise ConnectionFailedError(f"Database connection error: {e}")
        except Exception as e:
            self._is_connected = False
            raise DatabaseConnectionError(f"Unexpected connection error: {e}")

    def disconnect(self) -> None:
        try:
            if self.connection:
                self.connection.close()
            self._is_connected = False
            logger.info("Disconnected from database")
        except Exception as e:
            logger.error("Error during disconnection: %s", e)
            self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected
