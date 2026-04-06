"""Shared helpers for CRUD service classes."""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

import psycopg2
import psycopg2.pool
from psycopg2 import extensions

from job_tracker.database.query_executor import QueryExecutor
from job_tracker.utils.config import Config

logger = logging.getLogger(__name__)


class BaseService:
    """
    Base class that provides DB connection pool + query executor wiring.

    A single SimpleConnectionPool is shared across all BaseService instances
    within a process (class-level). Connections are borrowed for the duration
    of each _executor() / _transaction() block and returned to the pool
    immediately after, instead of being opened and closed on every call.
    """

    _pool: Optional[psycopg2.pool.SimpleConnectionPool] = None

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config()
        if BaseService._pool is None:
            BaseService._pool = psycopg2.pool.SimpleConnectionPool(
                1,  # minconn
                5,  # maxconn
                self.config.get_connection_string(),
                options=f"-c statement_timeout=30000",
            )
            logger.debug("Connection pool created (minconn=1, maxconn=5)")

    @contextmanager
    def _executor(self) -> Generator[QueryExecutor, None, None]:
        """Yield a query executor using a pooled connection (read-only operations)."""
        conn = self._pool.getconn()
        discard = False
        try:
            yield QueryExecutor(conn)
        except Exception:
            # Clear failed transaction state before returning pooled connection.
            if not self._safe_rollback(conn):
                discard = True
            raise
        finally:
            if not self._is_connection_usable(conn):
                discard = True
            self._pool.putconn(conn, close=discard)

    @contextmanager
    def _transaction(self) -> Generator[QueryExecutor, None, None]:
        """Yield a query executor inside a transaction; commits on success, rolls back on error."""
        conn = self._pool.getconn()
        discard = False
        try:
            executor = QueryExecutor(conn)
            yield executor
            conn.commit()
        except Exception:
            if not self._safe_rollback(conn):
                discard = True
            raise
        finally:
            if not self._is_connection_usable(conn):
                discard = True
            self._pool.putconn(conn, close=discard)

    def _safe_rollback(self, conn) -> bool:
        """Best-effort rollback; returns False if connection should be discarded."""
        try:
            if conn is None or getattr(conn, "closed", 1) != 0:
                return False
            conn.rollback()
            return True
        except Exception:
            return False

    def _is_connection_usable(self, conn) -> bool:
        """Check if pooled connection is valid for reuse."""
        try:
            if conn is None or getattr(conn, "closed", 1) != 0:
                return False
            return conn.get_transaction_status() != extensions.TRANSACTION_STATUS_UNKNOWN
        except Exception:
            return False
