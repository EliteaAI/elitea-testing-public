"""UI test — Remote MCP "Load Tools" against an invalid/unreachable URL.

TMS: ELITEA-1934 (test-specs/mcp/l1_remote-mcp-load-tools-invalid-url_ELITEA-1934.md)

Creates a Remote MCP pointed at an IANA-reserved, deterministically-unreachable
``.invalid`` hostname, clicks "Load Tools", and verifies the failure is
communicated via a `200` response body (not a 4xx/5xx), the exact error toast
text specified by the case, the Tools section keeping its pre-existing
empty-state (no phantom tool list), the "Load Tools" button reverting to its
idle label, and the connection status widget staying "Not Connected"/"Login"
(never "Connected!"/"Logout").
"""

import logging
import uuid

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p1, pytest.mark.regression]

INVALID_URL = "https://nonexistent.invalid/mcp"
EXPECTED_EMPTY_STATE_TEXT = 'No tools to display for now. To get tools from MCP press button “Load Tools”'
EXPECTED_ERROR_MESSAGE = (
    "Failed to sync MCP tools: DNS resolution failed. Please check the server hostname in the URL."
)


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1934_remote-mcp-load-tools-invalid-url.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_load_tools_invalid_url(page, toolkit_api: ToolkitAPI):
    """Loading tools from an invalid URL surfaces the exact DNS-failure toast and stays 'Not Connected'."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    # Toolkit Name input carries MAX_NAME_LENGTH=32 (EliteaUI src/common/constants.js) —
    # silently truncates anything longer (see .agents/memory/test-automation-engineer/
    # mcp_toolkit_create_form_implementer_quirks.md). Keep the generated name under it.
    toolkit_name = f"autotest_inv_url_{uuid.uuid4().hex[:8]}"
    created_id: int | None = None

    try:
        with allure.step("Step 1 — Navigate to MCP creation; select Remote MCP type"):
            form.navigate_to_create()
            form.select_remote_mcp_type()
            assert "/mcps/create/mcp" in page.url, f"Expected the Remote MCP form URL, got: {page.url}"
            assert form.name_input.is_visible(), "Toolkit Name field should be visible on the Remote MCP form"
            assert form.url_input.is_visible(), "Url field should be visible on the Remote MCP form"

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
            assert toolkit_name in form.get_detail_heading_text()
            # The invalid URL round-trips through save unchanged — no server-side
            # rejection either, validation only happens at Load-Tools/sync time.
            assert form.url_input.input_value() == INVALID_URL, (
                "Detail page Url field should still show the invalid URL unchanged after save"
            )

        with allure.step("Step 5 — Click 'Load Tools'; verify mcp_sync_tools resolves 200 with a failure body"):
            sync_response = form.click_load_tools(project_id)
            result = sync_response.get("result", {})
            # Axis 2: the actual HTTP-level contract the UI's useGetRemoteMcpTools
            # hook branches on — never a 4xx/5xx, the failure lives in the 200 body.
            assert result.get("success") is False, (
                f"mcp_sync_tools result.success should be False for an invalid URL, got: {sync_response!r}"
            )
            assert result.get("error") == EXPECTED_ERROR_MESSAGE, (
                f"Expected the exact DNS-failure error message, got: {result.get('error')!r}"
            )
            assert result.get("server_url") == INVALID_URL, (
                f"result.server_url should echo back the invalid URL, got: {result.get('server_url')!r}"
            )

        with allure.step("Step 6 — Verify the error toast shows the exact DNS-failure message"):
            form.sync_error_toast_message.wait_for(state="visible", timeout=10_000)
            toast_text = form.sync_error_toast_message.text_content()
            assert toast_text == EXPECTED_ERROR_MESSAGE, (
                f"Expected the exact DNS-failure toast text, got: {toast_text!r}"
            )

        with allure.step(
            "Step 7 — Verify the connection status stays 'Not Connected'/'Login' "
            "(never 'Connected!'/'Logout')"
        ):
            assert not form.is_mcp_connected(), (
                "Connection status should report disconnected (data-connected='false') "
                "after a failed Load Tools attempt"
            )
            assert form.get_connection_auth_button_label() == "Login", (
                "Auth button should still read 'Login', never 'Logout', after a failed sync"
            )

        with allure.step(
            "Step 8 — Verify the Tools section still shows its pre-existing empty-state "
            "(no phantom/partial tool list) and 'Load Tools' reverted to its idle label"
        ):
            # Axis 2: guards against a regression that renders a phantom/partial
            # tool list on a sync failure instead of leaving the empty state intact.
            assert form.get_tools_empty_state_text() == EXPECTED_EMPTY_STATE_TEXT, (
                f"Tools empty-state text should be unchanged after a failed Load Tools, "
                f"got: {form.get_tools_empty_state_text()!r}"
            )
            # Axis 2: guards against a regression that leaves the button permanently
            # stuck on "Loading...", which would silently block every retry.
            assert form.load_tools_button.text_content() == "Load Tools", (
                "'Load Tools' button should revert to its idle label after the failed sync resolves"
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
