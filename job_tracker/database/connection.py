import psycopg2
from psycopg2 import OperationalError, ProgrammingError
import logging
import time

from job_tracker.database.exceptions import (
    DatabaseConnectionError,
    ConnectionFailedError,
    ConnectionTimeoutError,
    QueryExecutionError,
    map_postgres_error
)
from job_tracker.database.logger import db_logger, log_execution_time

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Context manager for PostgreSQL database connections.

    Handles connection lifecycle, error handling, and timeout configuration.
    """

    def __init__(self, connection_string, connect_timeout=5, statement_timeout=30000):
        """
        Initialize DatabaseConnection.

        :param connection_string: PostgreSQL connection string
        :param connect_timeout: Max seconds to wait for connection establishment
        :param statement_timeout: Max milliseconds for query execution
        """

        self.connection_string = connection_string
        self.connect_timeout = connect_timeout
        self.statement_timeout = statement_timeout
        self._is_connected = False
        self.connection = None

    def __enter__(self):
        """
        Context manager entry point.

        :return: The DatabaseConnection instance
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point.

        :param exc_type: Exception type if one occurred
        :param exc_val: Exception value if one occurred
        :param exc_tb: Exception traceback if one occurred
        :return: False to propagate exceptions, True to suppress
        """
        self.disconnect()
        return False

    @log_execution_time(db_logger)
    def connect(self):
        """
        Establish a connection to the PostgreSQL database.

        Sets up connection with timeout configuration.
        Updates a connection state flag on success.

        :raises ConnectionFailedError: If connection fails
        :raises ConnectionTimeoutError: If connection times out
        :raises DatabaseConnectionError: For other connection errors
        """

        try:
            logger.info("Connecting to database...")
            self.connection = psycopg2.connect(self.connection_string, connect_timeout=self.connect_timeout)

            cursor = self.connection.cursor()
            cursor.execute(f"SET statement_timeout TO {self.statement_timeout}")
            cursor.close()

            self._is_connected = True
            logger.info("Connected to database successfully!")
            db_logger.log_connection("established", f"timeout={self.connect_timeout}s")

        except OperationalError as e:
            logger.error(f"OperationalError during connection: {e}")
            db_logger.log_error(e, "Connection failed")
            self._is_connected = False
            if "timeout" in str(e).lower():
                raise ConnectionTimeoutError(f"Connection timed out: {e}")
            raise ConnectionFailedError(f"Failed to connect to database: {e}")

        except ProgrammingError as e:
            logger.error(f"ProgrammingError during connection: {e}")
            db_logger.log_error(e, "Connection failed")
            self._is_connected = False
            raise ConnectionFailedError(f"Database connection error (permission denied?): {e}")

        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            db_logger.log_error(e, "Connection failed")
            self._is_connected = False
            raise DatabaseConnectionError(f"Unexpected database connection error: {e}")


    def disconnect(self):
        """
        Close connection to PostgreSQL database.

        Releases database resources and updates state flag.
        Safe to call even if not connected.
        """

        try:
            logger.info("Disconnecting from database...")
            if self.connection:
                self.connection.close()
            self._is_connected = False
            logger.info("Disconnected from database successfully!")
            db_logger.log_connection("closed")

        except Exception as e:
            logger.error(f"Error during disconnection: {e}")
            db_logger.log_error(e, "Disconnection failed")
            self._is_connected = False


    def execute_query(self, query, fetch=True, timeout=None):
        """
        Execute a SQL query on the database.

        :param query: SQL query to execute
        :param fetch: Whether to fetch results (default True)
        :param timeout: Optional custom timeout in milliseconds
        :return: Query results if fetch=True, None otherwise
        :raises DatabaseConnectionError: If not connected
        :raises QueryExecutionError: If query fails
        """

        if not self._is_connected:
            raise DatabaseConnectionError("Not connected to database. Call connect() first.")

        cursor = None
        start_time = time.perf_counter()

        try:
            if timeout:
                cursor = self.connection.cursor()
                cursor.execute(f"SET statement_timeout TO {timeout}")
                cursor.close()

            cursor = self.connection.cursor()
            cursor.execute(query)

            if fetch:
                result = cursor.fetchall()
                execution_time = time.perf_counter() - start_time
                logger.info(f"Query executed successfully. Fetched {len(result)} rows.")
                db_logger.log_query(query, execution_time=execution_time)
                db_logger.log_slow_query(query, execution_time)
                return result
            else:
                self.connection.commit()
                execution_time = time.perf_counter() - start_time
                logger.info("Query executed and committed successfully.")
                db_logger.log_query(query, execution_time=execution_time)
                db_logger.log_slow_query(query, execution_time)
                return None

        except (OperationalError, ProgrammingError) as e:
            logger.error(f"PostgreSQL error during query execution: {e}")
            db_logger.log_error(e, f"Query execution failed: {query[:50]}...")

            exception_class = map_postgres_error(e)
            raise exception_class(f"Query execution failed: {e}")

        except Exception as e:
            logger.error(f"Unexpected error during query execution: {e}")
            db_logger.log_error(e, f"Query execution failed: {query[:50]}...")
            raise QueryExecutionError(f"Query execution failed: {e}")

        finally:
            if cursor:
                cursor.close()

    @property
    def is_connected(self):
        """
        Check if the connection is active.

        :return: True if connected, False otherwise
        """
        return self._is_connected
