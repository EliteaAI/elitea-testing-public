"""UI test — Remote MCP "Load Tools" against an invalid/unreachable URL.

TMS: ELITEA-1934 (test-specs/mcp/l2_remote-mcp-load-tools-from-invalid-url_ELITEA-1934.md)

Creates a Remote MCP pointed at a real, guaranteed-unresolvable hostname
(``https://nonexistent.invalid/mcp``), clicks "Load Tools", and verifies the
sync failure surfaces as a toast with the exact DNS-failure message while the
connection-status indicator stays "Not Connected" both before and after the
failed attempt.
"""

import logging
import uuid

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p2, pytest.mark.regression]

INVALID_URL = "https://nonexistent.invalid/mcp"
EXPECTED_ERROR_MESSAGE = (
    "Failed to sync MCP tools: DNS resolution failed. Please check the server hostname in the URL."
)
NOT_CONNECTED_TEXT = "Not Connected"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1934_remote-mcp-load-tools-from-invalid-url.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_load_tools_invalid_url(page, toolkit_api: ToolkitAPI):
    """Loading tools from a Remote MCP with an unresolvable URL toasts the DNS failure, stays Not Connected."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    # Toolkit Name input carries MAX_NAME_LENGTH=32 (EliteaUI src/common/constants.js) —
    # keep the generated name under it (see .agents/memory/test-automation-engineer/
    # mcp_toolkit_create_form_implementer_quirks.md).
    toolkit_name = f"autotest_inv_url_{uuid.uuid4().hex[:6]}"
    created_id: int | None = None

    try:
        with allure.step("Step 1 — Navigate to MCP creation; select Remote MCP type"):
            form.navigate_to_create()
            form.select_remote_mcp_type()
            assert "/mcps/create/mcp" in page.url, f"Expected the Remote MCP form URL, got: {page.url}"

        with allure.step(f'Step 2 — Fill Toolkit Name "{toolkit_name}"'):
            form.fill_name(toolkit_name)
            assert form.name_input.input_value() == toolkit_name

        with allure.step(f'Step 3 — Fill Url "{INVALID_URL}"'):
            form.fill_url(INVALID_URL)
            assert form.url_input.input_value() == INVALID_URL
            assert form.save_button.is_enabled(), "Save button should be enabled once Name+Url are filled"

        with allure.step("Step 4 — Click Save; verify 201 + navigation to detail page"):
            save_response = form.save_and_wait_for_created(project_id)
            created_id = save_response["id"]
            assert isinstance(created_id, int), f"Save response should include a numeric id: {save_response!r}"
            assert f"/mcps/all/{created_id}" in page.url, (
                f"Should navigate to the new MCP's detail page, got: {page.url}"
            )

        with allure.step('Step 5 — Verify connection status shows "Not Connected" before Load Tools'):
            status_before = form.get_connection_status_text()
            assert status_before == NOT_CONNECTED_TEXT, (
                f"Connection status should be {NOT_CONNECTED_TEXT!r} before any Load Tools "
                f"attempt, got: {status_before!r}"
            )

        with allure.step(
            'Step 6 — Click "Load Tools"; verify mcp_sync_tools resolves 200 with a failure envelope'
        ):
            sync_response = form.click_load_tools(project_id)
            result = sync_response.get("result", {})
            assert result.get("success") is False, (
                f"mcp_sync_tools should report success=false for an unresolvable URL, got: {sync_response!r}"
            )
            assert result.get("error") == EXPECTED_ERROR_MESSAGE, (
                f"mcp_sync_tools error should be the DNS-failure message, got: {result.get('error')!r}"
            )

        with allure.step(
            "Step 7 — Verify the error toast shows the exact DNS-failure message "
            "(read immediately — the toast auto-dismisses within a few seconds)"
        ):
            toast_text = form.wait_for_sync_error_toast()
            assert toast_text == EXPECTED_ERROR_MESSAGE, (
                f"Error toast should read the exact DNS-failure message, got: {toast_text!r}"
            )

        with allure.step('Step 8 — Verify connection status still shows "Not Connected" after the failed attempt'):
            status_after = form.get_connection_status_text()
            assert status_after == NOT_CONNECTED_TEXT, (
                f"Connection status should still be {NOT_CONNECTED_TEXT!r} after a failed Load Tools "
                f"attempt (no false 'Connected!' flip), got: {status_after!r}"
            )

    finally:
        # Not a case step — cleanup for the persistent server-side toolkit this
        # test creates (AFS § Cleanup).
        if created_id is not None:
            try:
                toolkit_api.delete_toolkit(created_id)
            except Exception:
                logger.warning(
                    "Failed to delete seeded MCP toolkit id=%s during cleanup", created_id, exc_info=True
                )
