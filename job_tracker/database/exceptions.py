"""
Database Exception Module

Centralized exception hierarchy for all database-related errors.

Exception Hierarchy:
    DatabaseError (base)
    ├── DatabaseConnectionError
    │   ├── ConnectionFailedError
    │   └── ConnectionTimeoutError
    ├── QueryExecutionError
    │   ├── InvalidQueryError
    │   ├── QueryTimeoutError
    │   └── IntegrityConstraintError
    │       ├── ForeignKeyViolationError
    │       ├── UniqueViolationError
    │       └── NotNullViolationError
    ├── TransactionError
    │   ├── TransactionTimeoutError
    │   ├── NoActiveTransactionError
    │   ├── NestedTransactionError
    │   └── TransactionAbortedError
    └── DataValidationError
        ├── InvalidEmailError
        ├── InvalidDateError
        └── InvalidStatusTransitionError
"""


# ============================================================================
# BASE DATABASE ERROR
# ============================================================================

class DatabaseError(Exception):
    """
    Base exception for all database-related errors.

    All custom database exceptions inherit from this class.
    """
    pass


# ============================================================================
# CONNECTION ERRORS
# ============================================================================

class DatabaseConnectionError(DatabaseError):
    """
    Raised when database connection fails or encounters errors.

    Base class for all connection-related errors.
    """
    pass


class ConnectionFailedError(DatabaseConnectionError):
    """
    Raised when unable to establish connection to database.

    Common causes:
    - Wrong credentials
    - Database server offline
    - Network issues
    - Wrong host/port
    """
    pass


class ConnectionTimeoutError(DatabaseConnectionError):
    """
    Raised when connection attempt times out.

    Common causes:
    - Database server too slow to respond
    - Network latency
    - Firewall blocking connection
    """
    pass


# ============================================================================
# QUERY EXECUTION ERRORS
# ============================================================================

class QueryExecutionError(DatabaseError):
    """
    Raised when query execution fails.

    Base class for all query-related errors.
    """
    pass


class InvalidQueryError(QueryExecutionError):
    """
    Raised when SQL query syntax is invalid.

    Common causes:
    - Typos in SQL
    - Invalid table/column names
    - Missing keywords
    """
    pass


class QueryTimeoutError(QueryExecutionError):
    """
    Raised when query execution exceeds timeout limit.

    Common causes:
    - Query too complex
    - Large dataset
    - Missing indexes
    - Database under heavy load
    """
    pass


class IntegrityConstraintError(QueryExecutionError):
    """
    Raised when database integrity constraint is violated.

    Base class for constraint violation errors.
    """
    pass


class ForeignKeyViolationError(IntegrityConstraintError):
    """
    Raised when foreign key constraint is violated.

    Common causes:
    - Inserting record with non-existent foreign key
    - Deleting parent record with existing children (without CASCADE)
    """
    pass


class UniqueViolationError(IntegrityConstraintError):
    """
    Raised when unique constraint is violated.

    Common causes:
    - Inserting duplicate value in UNIQUE column
    - Inserting duplicate PRIMARY KEY
    """
    pass


class NotNullViolationError(IntegrityConstraintError):
    """
    Raised when NOT NULL constraint is violated.

    Common causes:
    - Inserting NULL into required field
    - Updating field to NULL when NOT NULL
    """
    pass


# ============================================================================
# TRANSACTION ERRORS
# ============================================================================

class TransactionError(DatabaseError):
    """
    Raised when transaction operation fails.

    Base class for all transaction-related errors.
    """
    pass


class TransactionTimeoutError(TransactionError):
    """
    Raised when transaction exceeds timeout limit.

    Transaction will be automatically rolled back.
    """
    pass


class NoActiveTransactionError(TransactionError):
    """
    Raised when attempting to commit/rollback without active transaction.

    Common causes:
    - Calling commit() without begin_transaction()
    - Calling rollback() without begin_transaction()
    - Already committed/rolled back
    """
    pass


class NestedTransactionError(TransactionError):
    """
    Raised when nested transaction operation fails.

    Related to savepoint creation or management.
    """
    pass


class TransactionAbortedError(TransactionError):
    """
    Raised when transaction is in aborted state.

    After an error, transaction must be rolled back before any new operations.
    """
    pass


# ============================================================================
# DATA VALIDATION ERRORS
# ============================================================================

class DataValidationError(DatabaseError):
    """
    Raised when data validation fails before database operation.

    Base class for all validation errors.
    """
    pass


class InvalidEmailError(DataValidationError):
    """
    Raised when email format is invalid.

    Email must match pattern: user@domain.com
    """
    pass


class InvalidDateError(DataValidationError):
    """
    Raised when date is invalid or out of acceptable range.

    Common causes:
    - Date in future when past date required
    - Invalid date format
    - Date before acceptable minimum
    """
    pass


class InvalidStatusTransitionError(DataValidationError):
    """
    Raised when status transition violates state machine rules.

    Example: Cannot transition from 'Applied' directly to 'Offer'
    Must go through 'Interview' first.
    """
    pass


# ============================================================================
# ERROR CODE MAPPING
# ============================================================================

POSTGRES_ERROR_MAP = {
    # Constraint violations (23xxx)
    '23503': ForeignKeyViolationError,
    '23505': UniqueViolationError,
    '23502': NotNullViolationError,

    # Syntax errors (42xxx)
    '42601': InvalidQueryError,  # Syntax error
    '42703': InvalidQueryError,  # Undefined column
    '42P01': InvalidQueryError,  # Undefined table

    # Connection errors (08xxx)
    '08000': ConnectionFailedError,  # Connection exception
    '08003': ConnectionFailedError,  # Connection does not exist
    '08006': ConnectionFailedError,  # Connection failure

    # Query cancellation (57xxx)
    '57014': QueryTimeoutError,  # Query canceled (timeout)
}


def map_postgres_error(pg_error):
    """
    Map PostgreSQL error code to custom exception class.

    :param pg_error: psycopg2 Error object
    :return: Custom exception class or QueryExecutionError if unmapped
    """
    if hasattr(pg_error, 'pgcode') and pg_error.pgcode in POSTGRES_ERROR_MAP:
        return POSTGRES_ERROR_MAP[pg_error.pgcode]
    return QueryExecutionError

