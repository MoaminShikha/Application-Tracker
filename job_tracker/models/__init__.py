"""
Data Models
Defines structured data classes for all entities.
"""

from job_tracker.models.base import BaseModel, ValidationError
from job_tracker.models.company import Company
from job_tracker.models.position import Position, VALID_LEVELS
from job_tracker.models.recruiter import Recruiter
from job_tracker.models.application import Application
from job_tracker.models.application_event import ApplicationEvent, VALID_EVENT_TYPES
from job_tracker.models.application_status import ApplicationStatus, VALID_STATUSES

__all__ = [
    "BaseModel",
    "ValidationError",
    "Company",
    "Position",
    "VALID_LEVELS",
    "Recruiter",
    "Application",
    "ApplicationEvent",
    "VALID_EVENT_TYPES",
    "ApplicationStatus",
    "VALID_STATUSES",
]
