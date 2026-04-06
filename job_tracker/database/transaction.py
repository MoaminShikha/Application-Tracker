from typing import Optional
import time
import logging

from job_tracker.database.connection import DatabaseConnection
from job_tracker.database.exceptions import (
    TransactionError,
    TransactionTimeoutError,
    NoActiveTransactionError,
    NestedTransactionError,
    TransactionAbortedError
)
logger = logging.getLogger(__name__)



class TransactionManager:
    def __init__(self, connection: DatabaseConnection, timeout_seconds: int = 10) -> None:
        """
        Initialize TransactionManager with connection and timeout.

        :param connection: Active DatabaseConnection instance
        :param timeout_seconds: Maximum seconds a transaction can run
        :raises ValueError: If connection is not active
        """
        if not connection.is_connected:
            raise ValueError("Connection must be active")

        self.connection = connection
        self.timeout_seconds = timeout_seconds
        self._transaction_depth: int = 0  # incremented on begin_transaction, decremented on commit or rollback
        self._transaction_start_time: Optional[
            float] = None  # set to time when transaction starts, used to check for timeouts

    def __enter__(self) -> 'TransactionManager':
        """
        Context manager entry: begin transaction.

        :return: self
        """
        self.begin_transaction()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Context manager exit: commit on success, rollback on error.

        :param exc_type: Exception type if error occurred, None otherwise
        :param exc_val: Exception value if error occurred
        :param exc_tb: Exception traceback if error occurred
        :return: False to propagate exceptions, True to suppress
        """
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        return False

    def begin_transaction(self) -> None:
        """
        Start transaction (BEGIN) or create savepoint if nested.

        :raises TransactionError: If BEGIN or SAVEPOINT fails
        """
        if self._transaction_depth > 0:
            self._execute_query("SAVEPOINT transaction_{}".format(self._transaction_depth))
            logger.debug("Savepoint created at depth=%d", self._transaction_depth)
        else:
            self._execute_query("BEGIN")
            self._transaction_start_time = time.time()
            logger.debug("Transaction started (timeout=%ds)", self.timeout_seconds)
        self._transaction_depth += 1

    def commit(self) -> None:
        """
        Commit transaction or release savepoint if nested.

        :raises NoActiveTransactionError: If not in transaction
        :raises TransactionTimeoutError: If transaction timed out
        :raises TransactionError: If COMMIT or RELEASE fails
        """
        self._check_timeout()
        try:
            if self._transaction_depth == 0:
                raise NoActiveTransactionError("No active transaction to commit.")
            elif self._transaction_depth == 1:
                self._execute_query("COMMIT")
                self._transaction_start_time = None
                logger.debug("Transaction committed")
            else:
                self._execute_query("RELEASE SAVEPOINT transaction_{}".format(self._transaction_depth - 1))
                logger.debug("Savepoint released at depth=%d", self._transaction_depth - 1)
            self._transaction_depth -= 1
        except NoActiveTransactionError:
            raise

    def rollback(self) -> None:
        """
        Rollback transaction or rollback to savepoint if nested.

        :raises NoActiveTransactionError: If not in transaction
        :raises TransactionError: If ROLLBACK fails
        """
        try:
            if self._transaction_depth == 0:
                raise NoActiveTransactionError("No active transaction to rollback.")
            elif self._transaction_depth == 1:
                self._execute_query("ROLLBACK")
                self._transaction_start_time = None
                logger.debug("Transaction rolled back")
            else:
                self._execute_query("ROLLBACK TO SAVEPOINT transaction_{}".format(self._transaction_depth - 1))
                logger.debug("Savepoint rolled back at depth=%d", self._transaction_depth - 1)
            self._transaction_depth -= 1
        except NoActiveTransactionError:
            raise

    def _check_timeout(self) -> None:
        """
        Check if transaction exceeded timeout and rollback if so.

        :raises TransactionTimeoutError: If timeout exceeded
        """
        if self._transaction_start_time is not None and time.time() - self._transaction_start_time > self.timeout_seconds:
            self.rollback()
            raise TransactionTimeoutError("Transaction timed out.")

    def _execute_query(self, query: str) -> None:
        """
        Execute a SQL command directly on the underlying psycopg2 connection.

        :param query: SQL command to execute
        :raises TransactionError: If execution fails
        """
        try:
            connection = getattr(self.connection, "connection", self.connection)
            with connection.cursor() as cur:
                cur.execute(query)
        except Exception as e:
            logger.error("Transaction error during query execution: %s", e)
            raise TransactionError(f"Failed to execute query: {e}")

    @property
    def is_in_transaction(self) -> bool:
        """
        Check if currently in a transaction.

        :return: True if transaction active, False otherwise
        """
        return self._transaction_depth > 0

    @property
    def depth(self) -> int:
        """
        Get current transaction nesting depth.

        :return: Nesting depth (0 = not in transaction)
        """
        return self._transaction_depth
