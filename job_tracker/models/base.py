"""
Base Model - Abstract base class for all domain models.

Provides common functionality for serialization, validation, and representation.
"""

from abc import ABC
from dataclasses import asdict
from typing import Any, Dict


class ValidationError(Exception):
    """Raised when model validation fails."""
    pass


class BaseModel(ABC):
    """
    Abstract base class for all domain models.

    Provides common methods:
    - validate() - Validate model data
    - to_dict() - Serialize to dictionary
    - from_dict() - Deserialize from dictionary
    - __repr__() - String representation
    - __eq__() - Equality comparison
    """

    def validate(self) -> None:
        """
        Validate the model.

        Override in subclasses to implement specific validation rules.
        Should raise ValidationError if validation fails.
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize model to dictionary.

        Returns:
            Dictionary representation of the model
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """
        Deserialize model from dictionary.

        Args:
            data: Dictionary with model data

        Returns:
            Model instance

        Raises:
            ValidationError: If data is invalid
        """
        try:
            instance = cls(**data)
            instance.validate()
            return instance
        except TypeError as e:
            raise ValidationError(f"Invalid data for {cls.__name__}: {e}")
        except ValidationError:
            raise

    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return f"{self.__class__.__name__}({self.to_dict()})"

    def __eq__(self, other: Any) -> bool:
        """Compare two models by their data."""
        if not isinstance(other, self.__class__):
            return False
        return self.to_dict() == other.to_dict()

