"""Smoke tests for Textual shell wiring."""

import importlib

import pytest


textual = pytest.importorskip("textual")


def test_tui_app_import_and_class_exists():
    mod = importlib.import_module("job_tracker.tui.app")
    assert hasattr(mod, "TrackerApp")
    assert hasattr(mod, "run")


def test_tui_dashboard_formatter_has_expected_lines():
    mod = importlib.import_module("job_tracker.tui.app")
    out = mod.build_dashboard_text(
        {
            "total_applications": 10,
            "active_applications": 4,
            "offers": 2,
            "accepted": 1,
            "rejected": 3,
        },
        {
            "application_to_interview_pct": 50.0,
            "application_to_offer_pct": 20.0,
            "application_to_accept_pct": 10.0,
        },
    )
    assert "Applications: 10" in out
    assert "App -> Interview: 50.0%" in out


def test_tui_has_phase2_bindings():
    mod = importlib.import_module("job_tracker.tui.app")
    keys = {binding.key for binding in mod.TrackerApp.BINDINGS}
    assert {"q", "d", "a", "r"}.issubset(keys)


def test_tui_module_entrypoint_exposes_main():
    mod = importlib.import_module("job_tracker.tui.__main__")
    assert hasattr(mod, "main")

