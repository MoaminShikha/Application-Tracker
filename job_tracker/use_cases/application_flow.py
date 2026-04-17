"""Application-related use-case orchestration for interface layers."""

from datetime import date
from typing import List, Optional, Protocol, runtime_checkable

from job_tracker.domain.exceptions import NotFoundError, map_to_domain_error
from job_tracker.models.application import Application
from job_tracker.services import ApplicationService, StatusService
from job_tracker.services.query_options import ApplicationQueryOptions


@runtime_checkable
class _ApplicationServicePort(Protocol):
    def create(
        self,
        company_id: int,
        position_id: int,
        applied_date: Optional[date] = None,
        recruiter_id: Optional[int] = None,
        job_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Application: ...

    def get_all(self, options: Optional[ApplicationQueryOptions] = None) -> List[Application]: ...

    def update_status(self, application_id: int, new_status: int) -> Optional[Application]: ...


@runtime_checkable
class _StatusServicePort(Protocol):
    def get_status_id_by_name(self, status_name: str) -> Optional[int]: ...


class ApplicationFlow:
    """Orchestrates application commands so interfaces stay thin."""

    def __init__(
        self,
        application_service: Optional[_ApplicationServicePort] = None,
        status_service: Optional[_StatusServicePort] = None,
    ) -> None:
        self.application_service = application_service or ApplicationService()
        self.status_service = status_service or StatusService()

    def _resolve_status_id(self, new_status_input: str) -> int:
        if str(new_status_input).isdigit():
            return int(new_status_input)

        status_id = self.status_service.get_status_id_by_name(new_status_input)
        if status_id is None:
            raise NotFoundError(f"Unknown status: {new_status_input}")
        return status_id

    def create_application(
        self,
        company_id: int,
        position_id: int,
        applied_date: Optional[date] = None,
        recruiter_id: Optional[int] = None,
        job_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Application:
        try:
            return self.application_service.create(
                company_id=company_id,
                position_id=position_id,
                applied_date=applied_date,
                recruiter_id=recruiter_id,
                job_id=job_id,
                notes=notes,
            )
        except Exception as exc:
            raise map_to_domain_error(exc)

    def list_applications(self, options: Optional[ApplicationQueryOptions] = None) -> List[Application]:
        try:
            return self.application_service.get_all(options=options)
        except Exception as exc:
            raise map_to_domain_error(exc)

    def update_status(self, application_id: int, new_status_input: str) -> Application:
        try:
            updated = self.application_service.update_status(
                application_id=application_id,
                new_status=self._resolve_status_id(new_status_input),
            )
            if not updated:
                raise NotFoundError(f"Application {application_id} not found")
            return updated
        except Exception as exc:
            raise map_to_domain_error(exc)
