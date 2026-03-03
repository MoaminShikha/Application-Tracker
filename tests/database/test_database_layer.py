"""
Comprehensive test suite for database layer (Phase 2.8).

Tests connection management, query execution, transactions, and error handling.
Run with: pytest tests/test_database_layer.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import psycopg2
from psycopg2 import OperationalError, ProgrammingError, IntegrityError

from job_tracker.database.connection import DatabaseConnection
from job_tracker.database.query_executor import QueryExecutor
from job_tracker.database.transaction import TransactionManager
from job_tracker.database.exceptions import (
    DatabaseConnectionError,
    ConnectionFailedError,
    ConnectionTimeoutError,
    QueryExecutionError,
    InvalidQueryError,
    TransactionError,
    NoActiveTransactionError,
)


# ============================================================================
# TESTS FOR DATABASE CONNECTION
# ============================================================================

class TestDatabaseConnection:
    """Test suite for DatabaseConnection context manager."""

    @pytest.fixture
    def connection_string(self):
        """Valid test connection string."""
        return "host=localhost port=5432 dbname=test_job_tracker user=postgres password=test"

    @pytest.fixture
    def db_connection(self, connection_string):
        """Create DatabaseConnection instance."""
        return DatabaseConnection(connection_string, connect_timeout=5, statement_timeout=30000)

    def test_connection_initialization(self, db_connection, connection_string):
        """Test that DatabaseConnection initializes with correct parameters."""
        assert db_connection.connection_string == connection_string
        assert db_connection.connect_timeout == 5
        assert db_connection.statement_timeout == 30000
        assert db_connection._is_connected is False
        assert db_connection.connection is None

    def test_is_connected_property(self, db_connection):
        """Test is_connected property reflects connection state."""
        assert db_connection.is_connected is False

    @patch('psycopg2.connect')
    def test_connect_success(self, mock_connect, db_connection):
        """Test successful database connection."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        db_connection.connect()

        assert db_connection._is_connected is True
        assert db_connection.connection == mock_connection
        mock_connect.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()

    @patch('psycopg2.connect')
    def test_connect_timeout_error(self, mock_connect, db_connection):
        """Test connection timeout raises ConnectionTimeoutError."""
        mock_connect.side_effect = OperationalError("timeout")

        with pytest.raises(ConnectionTimeoutError):
            db_connection.connect()

        assert db_connection._is_connected is False

    @patch('psycopg2.connect')
    def test_connect_operational_error(self, mock_connect, db_connection):
        """Test operational error (wrong credentials) raises ConnectionFailedError."""
        mock_connect.side_effect = OperationalError("FATAL: password authentication failed")

        with pytest.raises(ConnectionFailedError):
            db_connection.connect()

        assert db_connection._is_connected is False

    @patch('psycopg2.connect')
    def test_connect_programming_error(self, mock_connect, db_connection):
        """Test programming error (permission denied) raises ConnectionFailedError."""
        mock_connect.side_effect = ProgrammingError("permission denied")

        with pytest.raises(ConnectionFailedError):
            db_connection.connect()

        assert db_connection._is_connected is False

    @patch('psycopg2.connect')
    def test_connect_unexpected_error(self, mock_connect, db_connection):
        """Test unexpected error raises DatabaseConnectionError."""
        mock_connect.side_effect = Exception("Unexpected error")

        with pytest.raises(DatabaseConnectionError):
            db_connection.connect()

        assert db_connection._is_connected is False

    @patch('psycopg2.connect')
    def test_disconnect_success(self, mock_connect, db_connection):
        """Test successful disconnection."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        db_connection.connect()
        db_connection.disconnect()

        assert db_connection._is_connected is False
        mock_connection.close.assert_called_once()

    def test_disconnect_when_not_connected(self, db_connection):
        """Test disconnecting when not connected doesn't raise error."""
        db_connection.disconnect()
        assert db_connection._is_connected is False

    @patch('psycopg2.connect')
    def test_context_manager_success(self, mock_connect, db_connection):
        """Test context manager enters and exits correctly."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        with db_connection:
            assert db_connection._is_connected is True

        assert db_connection._is_connected is False
        mock_connection.close.assert_called_once()

    @patch('psycopg2.connect')
    def test_context_manager_exception_still_disconnects(self, mock_connect, db_connection):
        """Test context manager disconnects even if exception occurs."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        try:
            with db_connection:
                raise ValueError("Test error")
        except ValueError:
            pass

        assert db_connection._is_connected is False
        mock_connection.close.assert_called_once()


# ============================================================================
# TESTS FOR QUERY EXECUTOR
# ============================================================================

class TestQueryExecutor:
    """Test suite for QueryExecutor."""

    @pytest.fixture
    def mock_connection(self):
        """Create a mock psycopg2 connection."""
        return MagicMock()

    @pytest.fixture
    def query_executor(self, mock_connection):
        """Create QueryExecutor instance with mock connection."""
        return QueryExecutor(mock_connection)

    def test_executor_initialization(self, mock_connection, query_executor):
        """Test QueryExecutor initializes with connection."""
        assert query_executor.connection == mock_connection

    def test_executor_initialization_without_connection(self):
        """Test QueryExecutor raises error if no connection."""
        with pytest.raises(ValueError):
            QueryExecutor(None)

    def test_execute_query_empty_raises_error(self, query_executor):
        """Test execute_query raises error on empty query."""
        with pytest.raises(InvalidQueryError):
            query_executor.execute_query("")

    def test_execute_query_success(self, mock_connection, query_executor):
        """Test successful SELECT query."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'Apple'},
            {'id': 2, 'name': 'Google'}
        ]
        mock_connection.cursor.return_value = mock_cursor

        results = query_executor.execute_query("SELECT * FROM companies")

        assert len(results) == 2
        assert results[0]['name'] == 'Apple'
        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_execute_query_with_params(self, mock_connection, query_executor):
        """Test execute_query with parameters (SQL injection prevention)."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'Apple'}]
        mock_connection.cursor.return_value = mock_cursor

        results = query_executor.execute_query(
            "SELECT * FROM companies WHERE id = %s",
            params=(1,)
        )

        assert len(results) == 1
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM companies WHERE id = %s",
            (1,)
        )

    def test_execute_query_single_with_results(self, mock_connection, query_executor):
        """Test execute_query_single returns first row."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'Apple'}]
        mock_connection.cursor.return_value = mock_cursor

        result = query_executor.execute_query_single("SELECT * FROM companies LIMIT 1")

        assert result['id'] == 1
        assert result['name'] == 'Apple'

    def test_execute_query_single_no_results(self, mock_connection, query_executor):
        """Test execute_query_single returns None if no results."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor

        result = query_executor.execute_query_single("SELECT * FROM companies WHERE id = 999")

        assert result is None

    def test_execute_update_insert_success(self, mock_connection, query_executor):
        """Test successful INSERT query."""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_connection.cursor.return_value = mock_cursor

        rows_affected = query_executor.execute_update(
            "INSERT INTO companies (name, location) VALUES (%s, %s)",
            params=('Apple', 'Cupertino')
        )

        assert rows_affected == 1
        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_execute_update_delete_success(self, mock_connection, query_executor):
        """Test successful DELETE query."""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 3
        mock_connection.cursor.return_value = mock_cursor

        rows_affected = query_executor.execute_update(
            "DELETE FROM companies WHERE id = %s",
            params=(1,)
        )

        assert rows_affected == 3

    def test_execute_update_empty_query_raises_error(self, query_executor):
        """Test execute_update raises error on empty query."""
        with pytest.raises(InvalidQueryError):
            query_executor.execute_update("")

    def test_execute_query_postgres_error(self, mock_connection, query_executor):
        """Test execute_query handles PostgreSQL errors."""
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = ProgrammingError("column does not exist")
        mock_connection.cursor.return_value = mock_cursor

        with pytest.raises(QueryExecutionError):
            query_executor.execute_query("SELECT invalid_column FROM companies")


# ============================================================================
# TESTS FOR TRANSACTION MANAGER
# ============================================================================

class TestTransactionManager:
    """Test suite for TransactionManager."""

    @pytest.fixture
    def mock_db_connection(self):
        """Create a mock DatabaseConnection."""
        mock = MagicMock(spec=DatabaseConnection)
        mock.is_connected = True
        return mock

    @pytest.fixture
    def transaction_manager(self, mock_db_connection):
        """Create TransactionManager instance."""
        return TransactionManager(mock_db_connection, timeout_seconds=10)

    def test_transaction_manager_initialization(self, mock_db_connection, transaction_manager):
        """Test TransactionManager initializes correctly."""
        assert transaction_manager.connection == mock_db_connection
        assert transaction_manager.timeout_seconds == 10
        assert transaction_manager._transaction_depth == 0

    def test_transaction_manager_requires_connected_connection(self):
        """Test TransactionManager raises error if connection not active."""
        mock = MagicMock(spec=DatabaseConnection)
        mock.is_connected = False

        with pytest.raises(ValueError):
            TransactionManager(mock)

    def test_begin_transaction(self, mock_db_connection, transaction_manager):
        """Test begin_transaction executes BEGIN."""
        transaction_manager.begin_transaction()

        assert transaction_manager._transaction_depth == 1
        mock_db_connection.execute_query.assert_called_once_with("BEGIN", fetch=False)

    def test_commit_simple_transaction(self, mock_db_connection, transaction_manager):
        """Test commit_transaction executes COMMIT."""
        transaction_manager.begin_transaction()
        transaction_manager.commit()

        assert transaction_manager._transaction_depth == 0
        calls = mock_db_connection.execute_query.call_args_list
        assert calls[1][0][0] == "COMMIT"

    def test_commit_without_transaction_raises_error(self, transaction_manager):
        """Test commit without active transaction raises error."""
        with pytest.raises(NoActiveTransactionError):
            transaction_manager.commit()

    def test_rollback_simple_transaction(self, mock_db_connection, transaction_manager):
        """Test rollback_transaction executes ROLLBACK."""
        transaction_manager.begin_transaction()
        transaction_manager.rollback()

        assert transaction_manager._transaction_depth == 0
        calls = mock_db_connection.execute_query.call_args_list
        assert calls[1][0][0] == "ROLLBACK"

    def test_rollback_without_transaction_raises_error(self, transaction_manager):
        """Test rollback without active transaction raises error."""
        with pytest.raises(NoActiveTransactionError):
            transaction_manager.rollback()

    def test_nested_transaction_uses_savepoint(self, mock_db_connection, transaction_manager):
        """Test nested transaction creates savepoint."""
        transaction_manager.begin_transaction()
        transaction_manager.begin_transaction()

        assert transaction_manager._transaction_depth == 2
        calls = mock_db_connection.execute_query.call_args_list
        assert "SAVEPOINT" in calls[1][0][0]

    def test_nested_transaction_commit_releases_savepoint(self, mock_db_connection, transaction_manager):
        """Test committing nested transaction releases savepoint."""
        transaction_manager.begin_transaction()
        transaction_manager.begin_transaction()
        transaction_manager.commit()

        assert transaction_manager._transaction_depth == 1
        calls = mock_db_connection.execute_query.call_args_list
        assert "RELEASE SAVEPOINT" in calls[2][0][0]

    def test_context_manager_commits_on_success(self, mock_db_connection):
        """Test context manager commits on successful exit."""
        mock_db_connection.is_connected = True
        tm = TransactionManager(mock_db_connection)

        with tm:
            pass

        assert tm._transaction_depth == 0
        calls = mock_db_connection.execute_query.call_args_list
        assert calls[1][0][0] == "COMMIT"

    def test_context_manager_rollback_on_exception(self, mock_db_connection):
        """Test context manager rolls back on exception."""
        mock_db_connection.is_connected = True
        tm = TransactionManager(mock_db_connection)

        try:
            with tm:
                raise ValueError("Test error")
        except ValueError:
            pass

        assert tm._transaction_depth == 0
        calls = mock_db_connection.execute_query.call_args_list
        assert calls[1][0][0] == "ROLLBACK"

    def test_is_in_transaction_property(self, transaction_manager):
        """Test is_in_transaction property."""
        assert transaction_manager.is_in_transaction is False
        transaction_manager.begin_transaction()
        assert transaction_manager.is_in_transaction is True
        transaction_manager.commit()
        assert transaction_manager.is_in_transaction is False


# ============================================================================
# INTEGRATION TEST SCENARIOS
# ============================================================================

class TestIntegrationScenarios:
    """Test realistic scenarios combining multiple components."""

    @pytest.fixture
    def mock_connection(self):
        """Create a mock psycopg2 connection for integration tests."""
        return MagicMock()

    def test_insert_and_select_flow(self, mock_connection):
        """Test INSERT followed by SELECT."""
        # Mock cursor for INSERT
        insert_cursor = MagicMock()
        insert_cursor.rowcount = 1
        insert_cursor.fetchone.return_value = {'id': 1, 'name': 'Apple', 'location': 'Cupertino'}

        # Mock cursor for SELECT
        select_cursor = MagicMock()
        select_cursor.fetchall.return_value = [{'id': 1, 'name': 'Apple', 'location': 'Cupertino'}]

        mock_connection.cursor.side_effect = [insert_cursor, select_cursor]

        executor = QueryExecutor(mock_connection)

        # INSERT
        rows = executor.execute_update(
            "INSERT INTO companies (name, location) VALUES (%s, %s)",
            params=('Apple', 'Cupertino')
        )
        assert rows == 1

        # SELECT
        results = executor.execute_query("SELECT * FROM companies WHERE name = %s", params=('Apple',))
        assert len(results) == 1
        assert results[0]['name'] == 'Apple'

    def test_transaction_with_inserts(self, mock_connection):
        """Test transaction with multiple inserts."""
        mock_db_conn = MagicMock(spec=DatabaseConnection)
        mock_db_conn.is_connected = True
        mock_db_conn.execute_query = MagicMock()

        tm = TransactionManager(mock_db_conn)

        with tm:
            # Simulate multiple operations
            pass

        assert tm._transaction_depth == 0
        assert mock_db_conn.execute_query.call_count >= 2  # BEGIN + COMMIT


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

