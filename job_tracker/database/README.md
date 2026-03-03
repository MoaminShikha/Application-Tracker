# Database Layer Documentation

## Overview

The database layer provides a robust, production-ready interface for PostgreSQL database operations with comprehensive error handling, transaction management, and performance logging. This layer follows enterprise patterns with separation of concerns, ACID compliance, and structured monitoring.

---

## Architecture

```
database/
├── connection.py         # Connection management & query execution
├── transaction.py        # Transaction control & savepoints
├── exceptions.py         # Custom exception hierarchy
├── logger.py            # Performance logging & monitoring
├── init_db.py           # Database initialization
└── query_executor.py    # Query execution utilities
```

---

## Core Components

### 1. DatabaseConnection

**Purpose:** Manages PostgreSQL connections using the context manager pattern for automatic resource cleanup.

**Basic Usage:**

```python
from job_tracker.database.connection import DatabaseConnection

# Simple query
with DatabaseConnection(connection_string) as db:
    results = db.execute_query("SELECT * FROM companies WHERE id = 1")
    print(results)
```

**Advanced Usage:**

```python
# Custom timeout
with DatabaseConnection(connection_string, connect_timeout=10) as db:
    # Execute with custom statement timeout
    results = db.execute_query(
        "SELECT * FROM applications WHERE applied_date > NOW() - INTERVAL '30 days'",
        timeout=60000  # 60 seconds
    )
```

**Key Features:**
- Automatic connection cleanup via `__exit__`
- Configurable connection and statement timeouts
- Comprehensive error handling with custom exceptions
- Performance logging with execution time tracking
- Connection state management

**Configuration:**

```python
# Initialize with custom timeouts
db = DatabaseConnection(
    connection_string="postgresql://user:pass@localhost/dbname",
    connect_timeout=5,        # Max seconds to establish connection
    statement_timeout=30000   # Max milliseconds per query
)
```

---

### 2. Transaction Management

**Purpose:** Ensures ACID properties for multi-step database operations with support for nested transactions via savepoints.

**Basic Usage:**

```python
from job_tracker.database.transaction import TransactionManager

with DatabaseConnection(connection_string) as db:
    with TransactionManager(db) as txn:
        db.execute_query("INSERT INTO companies (name) VALUES ('TechCorp')", fetch=False)
        db.execute_query("INSERT INTO applications (company_id) VALUES (1)", fetch=False)
        # Automatic commit if no errors
```

**Rollback on Error:**

```python
with DatabaseConnection(connection_string) as db:
    try:
        with TransactionManager(db) as txn:
            db.execute_query("INSERT INTO companies (name) VALUES ('TechCorp')", fetch=False)
            # Simulate error
            raise ValueError("Business rule violated")
    except ValueError:
        # Transaction automatically rolled back
        print("Changes rolled back")
```

**Nested Transactions (Savepoints):**

```python
with DatabaseConnection(connection_string) as db:
    with TransactionManager(db) as txn:
        # Outer transaction
        db.execute_query("INSERT INTO companies (name) VALUES ('Company A')", fetch=False)
        
        try:
            with TransactionManager(db) as nested_txn:
                # Nested transaction creates savepoint
                db.execute_query("INSERT INTO companies (name) VALUES ('Company B')", fetch=False)
                raise Exception("Nested transaction fails")
        except:
            # Only nested transaction rolled back
            pass
        
        # Outer transaction still commits Company A
```

**Key Features:**
- Explicit transaction control (BEGIN, COMMIT, ROLLBACK)
- Automatic rollback on exception
- Savepoint support for nested transactions
- Transaction timeout enforcement
- Transaction event logging
- Depth tracking for nested transactions

---

### 3. Error Handling

**Exception Hierarchy:**

```
DatabaseError (base exception)
├── DatabaseConnectionError
│   ├── ConnectionFailedError
│   └── ConnectionTimeoutError
├── QueryExecutionError
├── TransactionError
│   ├── TransactionTimeoutError
│   ├── NoActiveTransactionError
│   ├── NestedTransactionError
│   └── TransactionAbortedError
├── IntegrityConstraintError
└── DataValidationError
```

**Usage Examples:**

```python
from job_tracker.database.exceptions import (
    ConnectionFailedError,
    IntegrityConstraintError,
    QueryExecutionError
)

# Handle connection failures
try:
    with DatabaseConnection(connection_string) as db:
        results = db.execute_query("SELECT * FROM companies")
except ConnectionFailedError as e:
    print(f"Cannot connect: {e}")
    # Implement retry logic or fallback

# Handle constraint violations
try:
    db.execute_query("INSERT INTO applications (company_id) VALUES (999)", fetch=False)
except IntegrityConstraintError as e:
    print(f"Foreign key violation: {e}")
    # Invalid company_id

# Handle query errors
try:
    db.execute_query("SELECT * FROM nonexistent_table")
except QueryExecutionError as e:
    print(f"Query failed: {e}")
```

**Error Mapping:**

The layer automatically maps PostgreSQL error codes to custom exceptions:
- `23503` (foreign key violation) → `IntegrityConstraintError`
- `23505` (unique violation) → `IntegrityConstraintError`
- `23514` (check constraint violation) → `DataValidationError`

---

### 4. Configuration

**Purpose:** Centralized environment variable management for database credentials and settings.

**Setup:**

Create `.env` file in project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=job_tracker
DB_USER=postgres
DB_PASSWORD=your_secure_password
```

**Usage:**

```python
from job_tracker.utils.config import Config

config = Config()
connection_string = config.get_db_connection_string()

# Access individual settings
host = config.db_host
port = config.db_port
database = config.db_name
```

**Validation:**

The configuration module validates all required environment variables on initialization and raises descriptive errors if any are missing.

---

### 5. Logging & Monitoring

**Purpose:** Track all database operations with performance metrics for monitoring, debugging, and optimization.

**Log Levels:**

- **DEBUG**: All queries with parameters, execution times, function calls
- **INFO**: Connection events, transaction events, row counts
- **WARNING**: Slow queries exceeding threshold
- **ERROR**: All failures with context

**Log Output:**

**Console (INFO and above):**
```
INFO: Connection established | timeout=5s
INFO: Transaction started | timeout=10s
INFO: Transaction committed
WARNING: SLOW QUERY (0.1523s > 0.1000s) | SELECT * FROM applications WHERE...
ERROR: Query execution failed: SELECT * FROM... | IntegrityError: duplicate key
```

**File `logs/database.log` (DEBUG and above):**
```
2025-02-27 14:30:22 | DEBUG    | job_tracker.database | Query executed in 0.0023s | SELECT * FROM companies
2025-02-27 14:30:22 | DEBUG    | job_tracker.database | Parameters: None
2025-02-27 14:30:22 | INFO     | job_tracker.database | Connection established | timeout=5s
2025-02-27 14:30:23 | ERROR    | job_tracker.database | Query execution failed | IntegrityError: duplicate key
```

**Performance Metrics:**

```python
from job_tracker.database.logger import db_logger

# Get current metrics
metrics = db_logger.get_metrics()
print(metrics)
# {
#     "total_queries": 150,
#     "total_errors": 2,
#     "total_execution_time": 3.4521,
#     "average_execution_time": 0.0230
# }

# Reset metrics
db_logger.reset_metrics()
```

**Slow Query Detection:**

Queries exceeding 100ms threshold are automatically logged as warnings:

```python
# In connection.py, automatically called
db_logger.log_slow_query(query, execution_time, threshold=0.1)
```

**Custom Logging:**

```python
from job_tracker.database.logger import db_logger

# Log custom events
db_logger.log_connection("pool exhausted", "waiting for available connection")
db_logger.log_transaction("savepoint created", "depth=2")
db_logger.log_error(exception, "Custom operation failed")
```

---

### 6. Database Initialization

**Purpose:** Set up database schema and reference data from SQL files.

**Usage:**

```python
from job_tracker.database.init_db import init_database

# Initialize database (idempotent - safe to run multiple times)
init_database(connection_string)
```

**Process:**
1. Reads `schema.sql` from `database_setup/`
2. Executes CREATE TABLE statements
3. Creates all indexes and constraints
4. Inserts reference data (statuses, etc.)
5. Verifies all tables created successfully
6. Logs initialization results

**Features:**
- Idempotent (safe to run multiple times)
- Transaction-wrapped (all-or-nothing)
- Comprehensive error handling
- Detailed logging

---

## Best Practices

### ✅ DO

**Always use context managers:**
```python
with DatabaseConnection(connection_string) as db:
    # Connection automatically closed
    results = db.execute_query("SELECT * FROM companies")
```

**Always use transactions for multi-step operations:**
```python
with DatabaseConnection(connection_string) as db:
    with TransactionManager(db) as txn:
        db.execute_query("INSERT INTO companies ...", fetch=False)
        db.execute_query("INSERT INTO applications ...", fetch=False)
```

**Always catch specific exceptions:**
```python
try:
    db.execute_query("INSERT ...")
except IntegrityConstraintError:
    # Handle constraint violation
    pass
except QueryExecutionError:
    # Handle query error
    pass
```

**Always validate input before queries:**
```python
def get_company(company_id: int):
    if not isinstance(company_id, int) or company_id <= 0:
        raise ValueError("Invalid company_id")
    
    with DatabaseConnection(connection_string) as db:
        results = db.execute_query(
            "SELECT * FROM companies WHERE id = %s",
            params=(company_id,)
        )
```

### ❌ DON'T

**Never concatenate user input into SQL:**
```python
# WRONG - SQL injection vulnerability
user_input = "'; DROP TABLE companies; --"
query = f"SELECT * FROM companies WHERE name = '{user_input}'"

# CORRECT - use parameterized queries
query = "SELECT * FROM companies WHERE name = %s"
results = db.execute_query(query, params=(user_input,))
```

**Never ignore transaction failures:**
```python
# WRONG
try:
    with TransactionManager(db) as txn:
        db.execute_query("INSERT ...")
except:
    pass  # Silently ignoring error

# CORRECT
try:
    with TransactionManager(db) as txn:
        db.execute_query("INSERT ...")
except TransactionError as e:
    logger.error(f"Transaction failed: {e}")
    # Implement retry logic or alert
```

**Never expose raw SQL errors to users:**
```python
# WRONG
try:
    db.execute_query("INSERT ...")
except Exception as e:
    return str(e)  # Exposes internal details

# CORRECT
try:
    db.execute_query("INSERT ...")
except IntegrityConstraintError:
    return "Invalid data - company does not exist"
except QueryExecutionError:
    return "Operation failed - please try again"
```

**Never commit sensitive data to version control:**
```python
# Add to .gitignore:
.env
logs/
*.log
```

---

## Common Patterns

### Pattern 1: Safe CRUD Operation

```python
def create_company(name: str, industry: str) -> int:
    """
    Create a new company.
    
    :param name: Company name
    :param industry: Company industry
    :return: New company ID
    :raises IntegrityConstraintError: If duplicate name
    :raises QueryExecutionError: If insert fails
    """
    query = """
        INSERT INTO companies (name, industry, created_at)
        VALUES (%s, %s, NOW())
        RETURNING id
    """
    
    with DatabaseConnection(get_connection_string()) as db:
        results = db.execute_query(query, params=(name, industry))
        return results[0][0]
```

### Pattern 2: Transaction with Multiple Operations

```python
def apply_to_job(company_id: int, position_id: int, recruiter_email: str) -> int:
    """
    Create application with related recruiter contact.
    
    :param company_id: Company ID
    :param position_id: Position ID
    :param recruiter_email: Recruiter email
    :return: New application ID
    """
    with DatabaseConnection(get_connection_string()) as db:
        with TransactionManager(db) as txn:
            # Create recruiter
            recruiter_query = """
                INSERT INTO recruiters (email, company_id)
                VALUES (%s, %s)
                RETURNING id
            """
            recruiter_result = db.execute_query(
                recruiter_query,
                params=(recruiter_email, company_id)
            )
            recruiter_id = recruiter_result[0][0]
            
            # Create application
            app_query = """
                INSERT INTO applications (company_id, position_id, recruiter_id, status_id)
                VALUES (%s, %s, %s, 1)
                RETURNING id
            """
            app_result = db.execute_query(
                app_query,
                params=(company_id, position_id, recruiter_id)
            )
            
            return app_result[0][0]
```

### Pattern 3: Graceful Error Handling

```python
def get_application_safe(application_id: int) -> Optional[dict]:
    """
    Get application by ID with graceful error handling.
    
    :param application_id: Application ID
    :return: Application dict or None if not found/error
    """
    try:
        with DatabaseConnection(get_connection_string()) as db:
            query = "SELECT * FROM applications WHERE id = %s"
            results = db.execute_query(query, params=(application_id,))
            
            if results:
                return {
                    "id": results[0][0],
                    "company_id": results[0][1],
                    # ... map columns to dict
                }
            return None
            
    except ConnectionFailedError as e:
        logger.error(f"Database connection failed: {e}")
        return None
    except QueryExecutionError as e:
        logger.error(f"Query failed: {e}")
        return None
```

---

## Performance Considerations

### Connection Management

**Current:** Single connection per operation
**Future:** Implement connection pooling for high-concurrency:

```python
from psycopg2 import pool

connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=connection_string
)
```

### Query Optimization

**Use indexes for analytics:**
- `applied_date` for temporal queries
- `company_id` for grouping
- `status_id` for filtering

**Check execution plans:**
```sql
EXPLAIN ANALYZE
SELECT * FROM applications WHERE applied_date > '2025-01-01';
```

### Batch Operations

For bulk inserts, use `executemany()`:

```python
cursor.executemany(
    "INSERT INTO companies (name) VALUES (%s)",
    [("Company A",), ("Company B",), ("Company C",)]
)
```

### Monitoring

**Check logs for slow queries:**
```bash
grep "SLOW QUERY" logs/database.log
```

**Review metrics periodically:**
```python
metrics = db_logger.get_metrics()
if metrics["average_execution_time"] > 0.1:
    print("WARNING: Average query time exceeding 100ms")
```

---

## Testing

**Test Suite Location:** `tests/database/test_database_layer.py`

**Coverage:**
- Connection establishment and cleanup
- Query execution (SELECT, INSERT, UPDATE, DELETE)
- Transaction commit and rollback
- Savepoints (nested transactions)
- Error handling for all exception types
- Timeout enforcement
- Edge cases (empty results, invalid SQL, etc.)

**Run Tests:**

```bash
# All database tests
pytest tests/database/

# Specific test file
pytest tests/database/test_database_layer.py

# With coverage
pytest tests/database/ --cov=job_tracker.database

# Verbose output
pytest tests/database/ -v
```

---

## Troubleshooting

### Issue: ModuleNotFoundError: No module named 'job_tracker'

**Cause:** Project root not in Python path

**Solution:**

```bash
# Option 1: Set PYTHONPATH (temporary)
export PYTHONPATH="${PYTHONPATH}:/path/to/Application Tracker"

# Option 2: Add to .env file
echo 'PYTHONPATH=/path/to/Application Tracker' >> .env

# Option 3: Install as editable package
pip install -e .
```

### Issue: Connection timeout

**Cause:** PostgreSQL not running or incorrect credentials

**Solution:**

1. Check PostgreSQL is running:
```bash
# Windows
Get-Service postgresql*

# Linux/Mac
sudo systemctl status postgresql
```

2. Verify credentials in `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=job_tracker
DB_USER=postgres
DB_PASSWORD=correct_password
```

3. Test connection manually:
```bash
psql -h localhost -U postgres -d job_tracker
```

### Issue: Permission denied on log directory

**Cause:** `logs/` directory not writable

**Solution:**

```bash
# Create directory with proper permissions
mkdir -p logs
chmod 755 logs

# Or specify different log directory
db_logger = DatabaseLogger(log_dir="/tmp/job_tracker_logs")
```

### Issue: Transaction deadlock

**Cause:** Multiple transactions waiting on each other

**Solution:**

1. Reduce transaction timeout
2. Implement retry logic with exponential backoff
3. Ensure consistent lock ordering

```python
import time

max_retries = 3
for attempt in range(max_retries):
    try:
        with TransactionManager(db) as txn:
            # Transaction operations
            break
    except TransactionError:
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
        else:
            raise
```

---

## Advanced Topics

### Custom Query Executor

For specialized query patterns, create custom executors:

```python
class AnalyticsQueryExecutor:
    """Specialized executor for analytics queries."""
    
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
    
    def execute_aggregation(self, query: str) -> dict:
        """Execute aggregation query and return single result."""
        results = self.connection.execute_query(query)
        if results:
            return {"count": results[0][0]}
        return {"count": 0}
```

### Connection Pooling (Future)

```python
class PooledDatabaseConnection:
    """Connection manager using connection pool."""
    
    def __init__(self, pool):
        self.pool = pool
        self.connection = None
    
    def __enter__(self):
        self.connection = self.pool.getconn()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pool.putconn(self.connection)
```

---

## API Reference

### DatabaseConnection

**Methods:**
- `connect()`: Establish connection
- `disconnect()`: Close connection
- `execute_query(query, fetch=True, timeout=None)`: Execute SQL

**Properties:**
- `is_connected`: Connection state (bool)

### TransactionManager

**Methods:**
- `begin_transaction()`: Start transaction or create savepoint
- `commit()`: Commit transaction or release savepoint
- `rollback()`: Rollback transaction or savepoint

**Properties:**
- `is_in_transaction`: Transaction state (bool)

### DatabaseLogger

**Methods:**
- `log_query(query, params, execution_time)`: Log query execution
- `log_connection(event, details)`: Log connection event
- `log_transaction(event, details)`: Log transaction event
- `log_error(error, context)`: Log error with context
- `log_slow_query(query, execution_time, threshold)`: Log slow query
- `get_metrics()`: Get performance metrics (dict)
- `reset_metrics()`: Reset all metrics

---

## Changelog

**v1.0.0 (Phase 2 Complete)**
- Initial database layer implementation
- Connection management with context managers
- Transaction support with savepoints
- Comprehensive error handling
- Performance logging and monitoring
- Database initialization utilities

---

## Contributing

When extending the database layer:

1. Follow existing patterns (context managers, error handling)
2. Add comprehensive docstrings (`:param:`, `:return:`, `:raises:`)
3. Log all significant operations
4. Write tests for new functionality
5. Update this documentation

---

## License

This is a learning/portfolio project. See project README for details.

