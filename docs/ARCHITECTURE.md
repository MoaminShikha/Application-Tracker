# Architecture Documentation

## Overview

This application follows a **layered architecture** pattern, separating concerns across distinct layers with clear responsibilities and dependencies.

## Layered Architecture

### 1. CLI Layer (`job_tracker/cli/`)

**Responsibility**: User interaction and command parsing

**Components**:
- `main.py`: Click-based command definitions
- `menu.py`: Interactive menu interface with tabulated output
- `interactive.py`: Guided prompt workflows

**Key Design Decisions**:
- Chose **Click** over argparse for better composability and cleaner syntax
- Implemented both menu and command modes to accommodate different user preferences
- Used **tabulate** for table formatting to improve readability over raw text output
- Added optional `job_id` capture in both guided and direct command flows for external posting references

### 2. Service Layer (`job_tracker/services/`)

**Responsibility**: Business logic and transaction management

**Components**:
- `base_service.py`: Shared database executor access pattern
- Entity services: `company_service.py`, `position_service.py`, etc.
- `status_service.py`: State machine transition validation
- `application_service.py`: Application lifecycle management

**Key Design Decisions**:
- Services own transaction boundaries (commit/rollback)
- State machine pattern enforces valid status transitions
- Services compose multiple database operations atomically
- No business logic leaks into CLI or database layers
- `ApplicationService` treats `job_id` as optional but validates/sanitizes when provided

**Status Transition Matrix**:
```
Applied → {Interview Scheduled, Rejected, Withdrawn}
Interview Scheduled → {Interviewed, Rejected}
Interviewed → {Offer, Rejected}
Offer → {Accepted, Rejected, Withdrawn}
Accepted, Rejected, Withdrawn → {terminal states}
```

### 3. Model Layer (`job_tracker/models/`)

**Responsibility**: Data validation and type safety

**Components**:
- `base.py`: Base model with validation interface
- Entity models: `company.py`, `position.py`, `application.py`, etc.
- Custom validation per model (email format, date constraints, etc.)

**Key Design Decisions**:
- Used **dataclasses** for clean syntax and automatic `__init__`, `__repr__`
- Validation happens at model creation, not database layer
- Models are immutable after validation (no setters)
- `from_dict()` factory pattern for database row mapping

**Validation Examples**:
- Email: Regex pattern matching
- Dates: Not in future, within 365-day window
- Required fields: Explicit checks with descriptive errors
- Optional IDs: `job_id` allows NULL, but rejects empty strings when present

### 4. Database Layer (`job_tracker/database/`)

**Responsibility**: Connection management and query execution

**Components**:
- `connection.py`: Context manager for PostgreSQL connections
- `query_executor.py`: Safe parameterized query execution
- `transaction.py`: Transaction helper utilities
- `exceptions.py`: Custom exception hierarchy
- `logger.py`: Database operation logging

**Key Design Decisions**:
- **Context managers** ensure connections are always closed
- Parameterized queries prevent SQL injection
- Custom exception mapping from psycopg2 to application-specific errors
- Logging with execution time tracking for performance monitoring
- Connection timeout and statement timeout configurations

### 5. Analytics Layer (`job_tracker/analytics/`)

**Responsibility**: Metrics calculation and reporting

**Components**:
- `analytics_service.py`: Query-based metrics (conversion rates, distributions)
- `reporting.py`: Export to JSON/CSV formats

**Key Design Decisions**:
- Read-only operations (no writes)
- Aggregations done in SQL for performance
- Lightweight export formats for portability
- Recent application exports include `job_id` for reconciliation with external systems

## Data Flow

### Creating an Application (Happy Path)

```
1. CLI (menu.py)
   ↓ collects user input
2. Service (application_service.py)
   ↓ validates business rules
   ↓ starts transaction
3. Model (application.py)
   ↓ validates data (`job_id` optional + sanitized)
4. Database (query_executor.py)
   ↓ executes INSERT
   ↓ logs event
   ↓ commits transaction
5. Returns created application
   ↓
6. CLI displays success
```

### Error Handling Flow

```
1. CLI captures user input
2. Service validates business rules
   └─> If invalid: raise ValueError
3. Model validates data
   └─> If invalid: raise ValidationError
4. Database executes query
   └─> If error: raise DatabaseError
5. Service catches exception
   └─> Rollback transaction
   └─> Propagate to CLI
6. CLI displays user-friendly error
```

## Technology Choices

### PostgreSQL over SQLite

**Why PostgreSQL?**
- Demonstrates production-ready database interactions
- Stronger type system and constraints
- Better concurrency handling
- More realistic for portfolio (most companies use Postgres/MySQL)

**Trade-offs**:
- Requires separate installation (not embedded like SQLite)
- More complex setup for users
- Justified by portfolio value and learning objectives

### Click over Argparse

**Why Click?**
- Cleaner decorator-based syntax
- Better composability (command groups)
- Built-in prompts and validation
- Industry standard for Python CLIs

### Dataclasses over ORMs (SQLAlchemy, Django ORM)

**Why Dataclasses?**
- Lightweight and explicit
- No magic/hidden behavior
- Forces understanding of SQL
- Demonstrates low-level database programming

**Trade-offs**:
- More boilerplate code
- Manual relationship management
- Justified by learning objectives and project scope

## Design Patterns Used

1. **Layered Architecture**: Separation of concerns across layers
2. **Service Layer**: Centralized business logic
3. **Repository Pattern**: Database access abstraction (query_executor)
4. **Context Manager**: Resource management (connections, transactions)
5. **Factory Pattern**: Model creation from database rows
6. **State Machine**: Status transition validation
7. **Dependency Injection**: Services receive database connection via context

## Testing Strategy

```
tests/
├── unit/              # Model validation, service logic
├── integration/       # Multi-layer flows
├── database/          # Schema constraints, DB layer
└── cli/              # Command smoke tests
```

**Philosophy**:
- Test business logic in services (isolated from DB)
- Test database constraints with actual Postgres
- Test integration flows for critical paths
- CLI smoke tests ensure commands execute

## Future Improvements

### Potential Enhancements
1. **Caching Layer**: Redis for analytics queries
2. **Message Queue**: Async processing for notifications
3. **API Layer**: RESTful API with FastAPI
4. **Frontend**: Web UI with React or htmx
5. **Authentication**: Multi-user support

### Scalability Considerations
- Current design supports read replicas (analytics on replica)
- Service layer enables horizontal scaling (stateless)
- Connection pooling could be added (pgbouncer)

## Lessons Learned

### 1. Transaction Boundaries Matter
**Initial mistake**: I placed `commit()` calls in the database layer, thinking "this is where the database lives, so this is where commits should go."

**Problem**: Services that needed to perform multiple operations atomically had no way to manage the transaction boundary. If operation A succeeded but operation B failed, A was already committed.

**Solution**: Moved transaction control to the service layer. Services now explicitly commit on success and rollback on exceptions. The database layer is purely for query execution.

**Code example**: `application_service.py` creates an application AND logs an initial event, both in one transaction.

### 2. Validation at Model Layer Saves Round-Trips
**Realization**: Why hit the database only to have it reject invalid data?

**Implementation**: Models validate on creation using the `validate()` method. Email regex, date constraints, and required field checks happen before any SQL executes.

**Impact**: Better error messages, faster feedback, and reduced database load. A malformed email fails in 10μs locally instead of waiting for a network round-trip.

### 3. Context Managers Saved Me from Connection Leaks
**Problem I avoided**: Early prototypes had manual `connection.close()` calls. Easy to forget in error paths.

**Solution**: Python's `with` statement guarantees cleanup. Even if an exception occurs, `__exit__` runs.

**Best practice adopted**: Every database interaction wrapped in `with self._executor()` pattern.

### 4. State Machine Design - Harder to Retrofit
**Decision point**: Should I implement status transition validation now or later?

**Choice**: Built the state machine upfront in `status_service.py` with an `ALLOWED_TRANSITIONS` matrix.

**Validation**: This prevented impossible transitions (e.g., Applied → Offer without Interview) from day one. Retrofitting this after users had bad data would have been painful.

### 5. Database Constraints Caught Logic Bugs
**Surprise**: Writing tests that intentionally violate foreign key constraints found bugs in my cascade deletion logic.

**Example**: Deleting a company should cascade to applications, but I initially forgot to handle recruiter relationships. The database rejected my delete, forcing me to fix the schema.

**Lesson**: Database constraints are executable documentation. They encode business rules that tests verify.

### 6. Click vs Argparse - The Right Choice
**Trade-off**: Click has a learning curve, but the decorator syntax is significantly cleaner for complex CLIs.

**Validation**: Built-in prompts (`click.prompt`) and type coercion reduced boilerplate. Menu mode would have been 2x the code with argparse.

### 7. Manual SQL > ORM for Learning
**Temptation**: SQLAlchemy would have saved lines of code.

**Reasoning**: For a portfolio project, explicitly writing SQL demonstrates understanding of:
- JOIN queries
- Parameterized queries (SQL injection prevention)
- Transaction isolation
- Query optimization

**Result**: Recruiters can see I understand databases, not just ORMs.

### 8. Analytics Queries Taught Me Aggregation Patterns
**Challenge**: Calculating conversion rates required GROUP BY and window functions.

**Solution**: Learned PostgreSQL's `COUNT(*) FILTER (WHERE ...)` syntax for conditional aggregation.

**Realization**: Moving aggregation to the database is faster than fetching all rows and processing in Python.

### What I'd Do Differently

1. **Add database migrations sooner**: Currently using a single `schema.sql`. Would adopt Alembic for version-controlled schema changes.
2. **Connection pooling**: Using `pgbouncer` or SQLAlchemy's pool would improve performance under load.
3. **More integration tests**: Unit tests are comprehensive, but real multi-layer flows have fewer tests than I'd like.
4. **Logging strategy**: Currently logging to file, but structured logging (JSON) would enable better monitoring.
5. **Configuration management**: Environment variables work, but a hierarchical config (dev/test/prod) would be more robust.

## References

- [12-Factor App](https://12factor.net/) - Configuration and dependency management
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) - Layer separation
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Don%27t_Do_This) - Database design patterns

