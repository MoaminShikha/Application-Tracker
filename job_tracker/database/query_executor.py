"""
Query Executor Module

Handles all database query operations:
- SELECT queries (retrieving data)
- INSERT/UPDATE/DELETE queries (modifying data)
- Cursor management
- Error handling and logging
- Parameterized queries for SQL injection prevention

:param: connection (DatabaseConnection) - Active database connection
:param: query (str) - SQL query with %s placeholders for parameters
:param: params (tuple) - Parameters to safely insert into query
:return:  results or affected row count
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from psycopg2 import Error as PostgresError
from psycopg2.extras import RealDictCursor

from job_tracker.database.exceptions import (
    QueryExecutionError,
    InvalidQueryError,
    map_postgres_error
)

logger = logging.getLogger(__name__)


class QueryExecutor:
    """
    Executes database queries safely with parameterization.

    Responsibilities:
    - Execute SELECT queries and return results as dictionaries
    - Execute INSERT/UPDATE/DELETE queries and return affected rows
    - Manage cursors properly (create and close)
    - Log query execution (especially in debug mode)
    - Handle query errors with meaningful messages
    - Prevent SQL injection through parameterized queries

    :param connection: Active database connection object
    """

    def __init__(self, connection):
        """
        Initialize QueryExecutor with a database connection.

        :param connection: psycopg2 connection object
        :raises: ValueError if connection is None
        """
        if not connection:
            raise ValueError("Connection is not active. Call connect() first.")
        self.connection = connection
        self._metrics: Dict[str, float] = {
            "query_count": 0,
            "error_count": 0,
            "total_exec_ms": 0.0
        }
        logger.debug("QueryExecutor initialized successfully.")

    def execute_query(self, query: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dictionaries.

        This method:
        1. Creates a cursor
        2. Executes the parameterized query
        3. Fetches all results
        4. Closes the cursor
        5. Returns results as list of dicts

        :param query: SQL SELECT query with %s placeholders for parameters
        :param params: Tuple of parameters to insert (optional)
        :return: List of dictionaries, each dict represents one row
                Example: [{'id': 1, 'name': 'Apple'}, {'id': 2, 'name': 'Google'}]
        :raises: QueryExecutionError if query fails
        :raises: ValueError if query is empty
        """
        if not query or query.strip() == "":
            raise InvalidQueryError("Query cannot be empty.")

        cursor = self._create_cursor(as_dict=True)

        try:
            self._metrics["query_count"] += 1
            self._log_query(query, params)
            start_time = time.perf_counter()
            cursor.execute(query, params)
            results = cursor.fetchall()
            execution_time = (time.perf_counter() - start_time) * 1000  # Convert to milliseconds
            self._metrics["total_exec_ms"] += execution_time
            logger.debug(f"Query executed successfully. Fetched {len(results)} row(s). Execution time: {execution_time:.2f}ms")
            return results
        except PostgresError as e:
            self._metrics["error_count"] += 1
            logger.error(f"Query execution failed: {str(e)}")
            exception_class = map_postgres_error(e)
            raise exception_class(f"Query execution failed: {str(e)}")
        finally:
            self._close_cursor(cursor)

    def execute_query_single(self, query: str, params: Tuple = None) -> Optional[Dict[str, Any]]:
        """
        Execute a SELECT query and return a single row as dictionary.

        Useful for queries that should return only one result.

        :param query: SQL SELECT query with %s placeholders
        :param params: Tuple of parameters to insert (optional)
        :return: Single dictionary row, or None if no results
        :raises: QueryExecutionError if query fails
        """
        results = self.execute_query(query, params)
        if results:
            return results[0]
        else:
            logger.debug("Query executed successfully. No results found.")
            return None

    def execute_update(self, query: str, params: Tuple = None) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.

        This method:
        1. Creates a cursor
        2. Executes the parameterized query
        3. Gets the number of affected rows
        4. Closes the cursor
        5. Returns affected row count

        :param query: SQL INSERT/UPDATE/DELETE query with %s placeholders
        :param params: Tuple of parameters to insert (optional)
        :return: Number of rows affected by the operation
        :raises: QueryExecutionError if query fails
        :raises: ValueError if query is empty
        """
        if not query or query.strip() == "":
            raise InvalidQueryError("Query cannot be empty.")

        cursor = self._create_cursor()

        try:
            self._metrics["query_count"] += 1
            self._log_query(query, params, "INFO")
            start_time = time.perf_counter()
            cursor.execute(query, params)
            row_count = cursor.rowcount
            execution_time = (time.perf_counter() - start_time) * 1000  # Convert to milliseconds
            self._metrics["total_exec_ms"] += execution_time
            logger.info(f"Query executed successfully. Affected {row_count} row(s). Execution time: {execution_time:.2f}ms")
            return row_count
        except PostgresError as e:
            self._metrics["error_count"] += 1
            logger.error(f"Query execution failed: {str(e)}")
            exception_class = map_postgres_error(e)
            raise exception_class(f"Query execution failed: {str(e)}")
        finally:
            self._close_cursor(cursor)

    def execute_insert_returning(self, query: str, params: Tuple = None) -> Dict[str, Any]:
        """
        Execute an INSERT query with RETURNING clause to get the inserted row.

        PostgreSQL's RETURNING clause allows us to get the newly inserted data
        (including auto-generated ID) without querying again.

        :param query: SQL INSERT query with RETURNING clause and %s placeholders
        :param params: Tuple of parameters to insert
        :return: Dictionary of the newly inserted row (including generated ID)
        :raises: QueryExecutionError if query fails
        """
        if not query or query.strip() == "":
            raise InvalidQueryError("Query cannot be empty.")

        cursor = self._create_cursor(as_dict=True)

        try:
            self._metrics["query_count"] += 1
            self._log_query(query, params, "INFO")
            start_time = time.perf_counter()
            cursor.execute(query, params)
            result = cursor.fetchone()
            execution_time = (time.perf_counter() - start_time) * 1000
            self._metrics["total_exec_ms"] += execution_time
            logger.info(f"INSERT query executed successfully. Returned row retrieved. Execution time: {execution_time:.2f}ms")
            return result
        except PostgresError as e:
            self._metrics["error_count"] += 1
            logger.error(f"Query execution failed: {str(e)}")
            exception_class = map_postgres_error(e)
            raise exception_class(f"Query execution failed: {str(e)}")
        finally:
            self._close_cursor(cursor)

    def execute_update_returning(self, query: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """
        Execute an UPDATE query with RETURNING clause to get updated rows.

        Useful when you want to verify the updated data without a separate query.

        :param query: SQL UPDATE query with RETURNING clause and %s placeholders
        :param params: Tuple of parameters
        :return: List of dictionaries representing updated rows
        :raises: QueryExecutionError if query fails
        """
        if not query or query.strip() == "":
            raise InvalidQueryError("Query cannot be empty.")

        cursor = self._create_cursor(as_dict=True)

        try:
            self._metrics["query_count"] += 1
            self._log_query(query, params, "INFO")
            start_time = time.perf_counter()
            cursor.execute(query, params)
            results = cursor.fetchall()
            execution_time = (time.perf_counter() - start_time) * 1000
            self._metrics["total_exec_ms"] += execution_time
            logger.info(f"UPDATE query executed successfully. Returned {len(results)} row(s). Execution time: {execution_time:.2f}ms")
            return results
        except PostgresError as e:
            self._metrics["error_count"] += 1
            logger.error(f"Query execution failed: {str(e)}")
            exception_class = map_postgres_error(e)
            raise exception_class(f"Query execution failed: {str(e)}")
        finally:
            self._close_cursor(cursor)

    def execute_batch(self, query: str, params_list: List[Tuple]) -> int:
        """
        Execute the same query multiple times with different parameters (batch operation).

        Useful for inserting multiple records at once.

        :param query: SQL query with %s placeholders
        :param params_list: List of parameter tuples, one per execution
        :return: Total number of rows affected
        :raises: QueryExecutionError if any query fails
        """
        if not params_list or len(params_list) == 0:
            raise InvalidQueryError("params_list cannot be empty.")

        if not query or query.strip() == "":
            raise InvalidQueryError("Query cannot be empty.")

        cursor = self._create_cursor()

        try:
            self._metrics["query_count"] += len(params_list)
            logger.info(f"Starting batch operation with {len(params_list)} executions.")
            start_time = time.perf_counter()
            total_affected = 0

            for idx, params in enumerate(params_list, start=1):
                self._log_query(query, params, "DEBUG")
                cursor.execute(query, params)
                total_affected += cursor.rowcount
                logger.debug(f"Batch execution {idx}/{len(params_list)} completed.")

            execution_time = (time.perf_counter() - start_time) * 1000
            self._metrics["total_exec_ms"] += execution_time
            logger.info(f"Batch operation completed successfully. Total rows affected: {total_affected}. Execution time: {execution_time:.2f}ms")
            return total_affected
        except PostgresError as e:
            self._metrics["error_count"] += 1
            logger.error(f"Batch operation failed: {str(e)}")
            exception_class = map_postgres_error(e)
            raise exception_class(f"Batch operation failed: {str(e)}")
        finally:
            self._close_cursor(cursor)

    def get_metrics(self) -> Dict[str, float]:
        """
        Get query execution metrics for this executor instance.

        :return: Dictionary with query_count, error_count, total_exec_ms
        """
        return dict(self._metrics)

    def _create_cursor(self, as_dict: bool = False):
        """
        Create a database cursor.

        Internal helper method for cursor creation.

        :param as_dict: If True, returns results as RealDictCursor (dicts),
                       else returns tuples
        :return: Database cursor object
        :raises: QueryExecutionError if cursor creation fails
        """
        try:
            if as_dict:
                cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            else:
                cursor = self.connection.cursor()
            logger.debug("Cursor created successfully.")
            return cursor
        except PostgresError as e:
            logger.error(f"Failed to create cursor: {str(e)}")
            raise QueryExecutionError(f"Failed to create cursor: {str(e)}")

    def _close_cursor(self, cursor):
        """
        Close a database cursor safely.

        Internal helper method for cursor cleanup.

        :param cursor: Cursor object to close
        :return: None
        """
        if cursor is not None:
            try:
                cursor.close()
                logger.debug("Cursor closed successfully.")
            except Exception as e:
                logger.warning(f"Error closing cursor: {str(e)}")

    def _log_query(self, query: str, params: Tuple = None, level: str = "DEBUG"):
        """
        Log query execution details.

        For security, this logs the query structure but NOT the parameter values.

        :param query: SQL query string
        :param params: Parameters (logged count only, not values)
        :param level: Logging level (DEBUG, INFO, WARNING, ERROR)
        :return: None
        """
        if logger.isEnabledFor(logging.DEBUG):
            query_preview = query[:200] + "..." if len(query) > 200 else query
            param_count = len(params) if params else 0
            log_func = getattr(logger, level.lower())
            log_func(f"Executing query: {query_preview} | Parameters: {param_count}")
