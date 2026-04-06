"""Typed query option objects for list/read operations."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ListQueryOptions:
    """Generic list query options for sorting and pagination."""

    sort_by: Optional[str] = None
    sort_dir: str = "desc"
    limit: Optional[int] = None
    offset: Optional[int] = None


@dataclass(frozen=True)
class ApplicationQueryOptions(ListQueryOptions):
    """Application-specific query options."""

    status_id: Optional[int] = None
    company_id: Optional[int] = None

