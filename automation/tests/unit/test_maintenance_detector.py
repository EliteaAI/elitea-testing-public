"""Unit tests for maintenance detection utilities.

Tests the maintenance detection logic without requiring a live browser/server.
"""

import pytest
from unittest.mock import Mock

from utils.maintenance_detector import (
    MaintenanceError,
    MaintenanceState,
    MaintenanceTimeoutError,
    detect_maintenance_ui,
    is_maintenance_response,
)


class TestMaintenanceState:
    """Test MaintenanceState data class."""

    def test_no_maintenance_is_falsy(self):
        """MaintenanceState with is_maintenance=False evaluates to False."""
        state = MaintenanceState(is_maintenance=False)

        assert not state
        assert not state.is_maintenance
        assert state.message is None

    def test_maintenance_is_truthy(self):
        """MaintenanceState with is_maintenance=True evaluates to True."""
        state = MaintenanceState(
            is_maintenance=True, message="Under maintenance", banner_present=True
        )

        assert state
        assert state.is_maintenance
        assert state.message == "Under maintenance"
        assert state.banner_present

    def test_repr(self):
        """MaintenanceState has meaningful repr."""
        state = MaintenanceState(
            is_maintenance=True, message="Test", banner_present=True, full_page=False
        )

        repr_str = repr(state)
        assert "MaintenanceState" in repr_str
        assert "is_maintenance=True" in repr_str
        assert "banner=True" in repr_str


class TestDetectMaintenanceUI:
    """Test UI maintenance detection."""

    def test_no_maintenance_when_normal_app(self):
        """No maintenance detected when normal app structure present."""
        page = Mock()
        page.evaluate.side_effect = [
            {"present": False, "message": None},  # No banner
            {"is_maintenance": False},  # Normal app structure
        ]

        state = detect_maintenance_ui(page)

        assert not state
        assert not state.is_maintenance
        assert not state.banner_present
        assert not state.full_page

    def test_detect_banner_maintenance(self):
        """Detect maintenance banner overlay."""
        page = Mock()
        page.evaluate.side_effect = [
            {"present": True, "message": "System under maintenance until 3pm"},
            # Second evaluate not called (short-circuit)
        ]

        state = detect_maintenance_ui(page)

        assert state
        assert state.is_maintenance
        assert state.banner_present
        assert not state.full_page
        assert "maintenance" in state.message.lower()

    def test_detect_full_page_maintenance(self):
        """Detect full-page maintenance message."""
        page = Mock()
        page.evaluate.side_effect = [
            {"present": False, "message": None},  # No banner
            {
                "is_maintenance": True,
                "message": "Scheduled maintenance in progress. Back soon.",
            },
        ]

        state = detect_maintenance_ui(page)

        assert state
        assert state.is_maintenance
        assert not state.banner_present
        assert state.full_page
        assert "maintenance" in state.message.lower()

    def test_detect_deployment_banner(self):
        """Detect deployment banner as maintenance."""
        page = Mock()
        page.evaluate.side_effect = [
            {"present": True, "message": "Release 2.0.6 - Deployment in progress"},
        ]

        state = detect_maintenance_ui(page)

        assert state
        assert state.is_maintenance
        assert state.banner_present
        assert "deployment" in state.message.lower()


class TestIsMaintenanceResponse:
    """Test API maintenance response detection."""

    def test_503_with_html_maintenance_page(self):
        """503 with HTML maintenance page is detected."""
        is_maint, msg = is_maintenance_response(
            503,
            "text/html; charset=utf-8",
            "<html><body><h1>Service Under Maintenance</h1></body></html>",
        )

        assert is_maint
        assert "503" in msg
        assert "maintenance" in msg.lower()

    def test_503_with_json_error_not_maintenance(self):
        """503 with JSON error response is NOT maintenance (legitimate error)."""
        is_maint, msg = is_maintenance_response(
            503, "application/json", '{"error": "Database connection failed"}'
        )

        assert not is_maint
        assert msg is None

    def test_502_with_html_maintenance_keywords(self):
        """502 with HTML containing maintenance keywords is detected."""
        is_maint, msg = is_maintenance_response(
            502,
            "text/html",
            "<html><body>Service temporarily unavailable due to scheduled maintenance</body></html>",
        )

        assert is_maint
        assert "502" in msg

    def test_200_with_maintenance_html_instead_of_json(self):
        """200 OK with HTML maintenance page (when JSON expected) is detected."""
        is_maint, msg = is_maintenance_response(
            200,
            "text/html",
            "<html><head><title>Maintenance</title></head><body>Under construction</body></html>",
        )

        assert is_maint
        assert "200 OK" in msg
        assert "maintenance HTML" in msg

    def test_200_with_json_not_maintenance(self):
        """200 with valid JSON is NOT maintenance."""
        is_maint, msg = is_maintenance_response(
            200, "application/json", '{"id": 123, "name": "test"}'
        )

        assert not is_maint
        assert msg is None

    def test_404_not_maintenance(self):
        """404 errors are NOT maintenance."""
        is_maint, msg = is_maintenance_response(
            404, "application/json", '{"error": "Not found"}'
        )

        assert not is_maint

    def test_various_maintenance_keywords(self):
        """Test detection of various maintenance keywords."""
        keywords = [
            "maintenance",
            "under construction",
            "temporarily unavailable",
            "scheduled downtime",
            "service unavailable",
        ]

        for keyword in keywords:
            is_maint, msg = is_maintenance_response(
                503, "text/html", f"<html><body>{keyword}</body></html>"
            )
            assert is_maint, f"Failed to detect keyword: {keyword}"

    def test_case_insensitive_detection(self):
        """Maintenance detection is case insensitive."""
        is_maint, msg = is_maintenance_response(
            503, "text/html", "<html><body>UNDER MAINTENANCE</body></html>"
        )

        assert is_maint

    def test_partial_keyword_match(self):
        """Partial keyword matches are detected (exact match required for 'unavailable')."""
        is_maint, msg = is_maintenance_response(
            503,
            "text/html",
            "<html><body>System is temporarily unavailable</body></html>",
        )

        assert is_maint  # "temporarily unavailable" matches keyword


class TestMaintenanceExceptions:
    """Test maintenance exception classes."""

    def test_maintenance_error_is_exception(self):
        """MaintenanceError is an Exception subclass."""
        exc = MaintenanceError("Test maintenance error")

        assert isinstance(exc, Exception)
        assert str(exc) == "Test maintenance error"

    def test_maintenance_timeout_error_is_exception(self):
        """MaintenanceTimeoutError is an Exception subclass."""
        exc = MaintenanceTimeoutError("Timeout waiting for maintenance to clear")

        assert isinstance(exc, Exception)
        assert "Timeout" in str(exc)


@pytest.mark.skip(reason="Integration test requiring live browser")
class TestWaitForMaintenanceClear:
    """Integration tests for wait_for_maintenance_clear.

    These require a live Playwright browser and are skipped in unit test runs.
    Run manually with: pytest -v tests/unit/test_maintenance_detector.py::TestWaitForMaintenanceClear -s
    """

    def test_wait_clears_when_maintenance_ends(self, page):
        """wait_for_maintenance_clear returns True when maintenance ends."""
        # This would need a way to simulate maintenance clearing
        # Leave as integration test placeholder
        pass
