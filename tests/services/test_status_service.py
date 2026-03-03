"""Tests for status transition validation."""

from job_tracker.services.status_service import StatusService


def test_validate_transition_with_strings_allows_valid_path():
    svc = StatusService.__new__(StatusService)
    svc._resolve_status_name = lambda x: x
    assert svc.validate_transition("Applied", "Interview Scheduled") is True


def test_validate_transition_with_strings_blocks_invalid_path():
    svc = StatusService.__new__(StatusService)
    svc._resolve_status_name = lambda x: x
    assert svc.validate_transition("Rejected", "Offer") is False

