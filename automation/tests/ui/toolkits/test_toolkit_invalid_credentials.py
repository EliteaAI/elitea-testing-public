"""Tests for toolkit behavior with invalid/expired credentials.

Verifies that:
1. Warning message "Authentication failed: Invalid bearer token" appears
2. Save button remains disabled when credentials are invalid

Bug reference: https://github.com/EliteaAI/elitea_issues/issues/4906
Before fix: Save button was disabled but no explanation why
After fix: Warning message shows "Authentication failed: Invalid bearer token"
           explaining why Save is disabled

Usage:
    pytest test_toolkit_invalid_credentials.py -v
    pytest test_toolkit_invalid_credentials.py -v -k "jira"
"""

import logging

import pytest

from pages.toolkit_detail_page import ToolkitDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits]


class TestToolkitInvalidCredentials:
    """Tests for toolkit behavior with invalid/expired credentials.

    Bug #4906: When toolkit had expired/invalid credentials, Save button
    was disabled but user had no idea why. After the fix, a warning message
    "Authentication failed: Invalid bearer token" is shown to explain
    why Save is disabled.
    TC-1778

    Parameterized to test both Jira (P1) and GitHub (P2) toolkits.
    """

    @pytest.mark.parametrize(
        ("fixture_name", "toolkit_type"),
        [
            pytest.param(
                "jira_toolkit_with_invalid_credential",
                "Jira",
                marks=pytest.mark.p1,
            ),
            pytest.param(
                "github_toolkit_with_invalid_credential",
                "GitHub",
                marks=pytest.mark.p2,
            ),
        ],
        ids=["jira", "github"],
    )
    def test_invalid_credentials_warning_and_save_disabled(
        self,
        page,
        request,
        fixture_name: str,
        toolkit_type: str,
    ):
        """Verify warning message and disabled Save button for invalid credentials.

        Steps:
        1. Open toolkit detail page with invalid credentials
        2. Verify warning message starting with "Authentication failed:" appears
        3. Verify Save button is disabled
        """
        toolkit_data = request.getfixturevalue(fixture_name)

        toolkit_page = ToolkitDetailPage(page)
        toolkit_page.navigate_to_toolkit(toolkit_data["id"])

        warning = toolkit_page.get_authentication_warning(timeout=15000)

        assert warning is not None, (
            f"Expected authentication warning for {toolkit_type} toolkit with invalid credentials. "
            "This indicates the bug #4906 fix may have regressed - "
            "user should see why Save is disabled."
        )

        assert warning.startswith("Authentication failed:"), (
            f"Warning should start with 'Authentication failed:', "
            f"but got: '{warning}'"
        )
        logger.info("%s authentication warning displayed correctly: %s", toolkit_type, warning)

        assert toolkit_page.is_save_button_disabled(), (
            f"Save button should be disabled when {toolkit_type} credentials are invalid"
        )
        logger.info("Save button is correctly disabled for invalid %s credentials", toolkit_type)
