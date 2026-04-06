"""Domain exception types and mapper for user-facing flows."""

from job_tracker.database.exceptions import (
    DatabaseError,
    IntegrityConstraintError,
    ForeignKeyViolationError,
    UniqueViolationError,
)
from job_tracker.models.base import ValidationError


class DomainError(Exception):
    """Base class for domain/application-level errors."""


class NotFoundError(DomainError):
    """Raised when a requested entity is missing."""


class InvalidTransitionError(DomainError):
    """Raised when a state transition is not allowed."""


class ConstraintViolationError(DomainError):
    """Raised when data violates uniqueness or referential constraints."""


class ValidationFailedError(DomainError):
    """Raised when input/model validation fails."""


def map_to_domain_error(exc: Exception) -> DomainError:
    """Map lower-level errors into stable domain error types."""
    if isinstance(exc, DomainError):
        return exc
    if isinstance(exc, ValidationError):
        return ValidationFailedError(str(exc))
    if isinstance(exc, ValueError) and "transition" in str(exc).lower():
        return InvalidTransitionError(str(exc))
    if isinstance(exc, (ForeignKeyViolationError, UniqueViolationError, IntegrityConstraintError)):
        return ConstraintViolationError(str(exc))
    if isinstance(exc, DatabaseError):
        return ConstraintViolationError(str(exc))
    return DomainError(str(exc))

