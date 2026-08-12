"""UI test — Remote MCP "Test Settings" panel: select a tool and run it.

TMS: ELITEA-1937 (test-specs/mcp/l3_remote-mcp-test-settings-select-and-run-tool_ELITEA-1937.md)

Creates a Remote MCP pointed at a public, auth-free MCP server
(``https://mcp.deepwiki.com/mcp``, the same stable 3-tool fixture ELITEA-1933/1934
use), selects "Read wiki structure" from the empty-state Test Settings selector,
fills its ``repoName`` parameter, runs it, and verifies a real (non-canned)
result renders in the shared chat-message-list result view.

Fixture substitution (AFS § Preconditions): the case's own example tool
("tavily_search") needs an API-key credential not provisioned here — the
DeepWiki fixture's ``read_wiki_structure`` tool exercises the identical
select -> run -> see-result mechanism this case tests.
"""

import logging
import uuid

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage
from pages.toolkit_test_settings_page import ToolkitTestSettingsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p3, pytest.mark.regression, pytest.mark.new]

MCP_URL = "https://mcp.deepwiki.com/mcp"
TOOL_KEY = "read_wiki_structure"
REPO_NAME = "AsyncFuncAI/deepwiki-open"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1937_remote-mcp-test-settings-select-and-run-tool.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_test_settings_select_and_run_tool(page, toolkit_api: ToolkitAPI):
    """Selecting a discovered tool in the Test Settings panel and running it shows a real result."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    test_settings = ToolkitTestSettingsPage(page)
    # Toolkit Name input carries MAX_NAME_LENGTH=32 (EliteaUI src/common/constants.js).
    toolkit_name = f"autotest_mcp_run_tool_{uuid.uuid4().hex[:6]}"
    created_id: int | None = None

    try:
        with allure.step("Step 1 — Create a Remote MCP and Load Tools; wait for the 3-tool fixture"):
            form.navigate_to_create()
            form.select_remote_mcp_type()
            form.fill_name(toolkit_name)
            form.fill_url(MCP_URL)
            save_response = form.save_and_wait_for_created(project_id)
            created_id = save_response["id"]
            assert isinstance(created_id, int), f"Save response should include a numeric id: {save_response!r}"

            sync_response = form.click_load_tools(project_id)
            assert sync_response, "mcp_sync_tools response body should be non-empty"
            discovered_names = set(form.get_discovered_tool_names())
            assert TOOL_KEY in discovered_names, (
                f"Expected {TOOL_KEY!r} among the discovered tool pills, got: {discovered_names!r}"
            )

        with allure.step(
            "Step 2 — Verify the empty-state 'Select Tool' entry point is shown before any tool "
            "is selected (EL-5947 gating — the literal 'Test Settings' panel only mounts AFTER "
            "a tool is chosen, see AFS CLARIFICATION #1086)"
        ):
            select_tool_button = test_settings.empty_state_tool_select
            select_tool_button.wait_for(state="visible", timeout=10_000)
            assert select_tool_button.is_visible(), (
                "The empty-state 'Select Tool' button should be visible before any tool is selected"
            )

        with allure.step(
            "Step 3 — Click 'Select Tool'; verify the popover lists all 3 discovered tools"
        ):
            test_settings.open_empty_state_tool_select()
            tool_options = test_settings.get_tool_options()
            expect(tool_options).to_have_count(3, timeout=10_000)
            target_option = test_settings.get_tool_option(TOOL_KEY)
            assert target_option.is_visible(), (
                f"Expected a {TOOL_KEY!r} option in the Tool-selection popover"
            )

        with allure.step(f"Step 4 — Select {TOOL_KEY!r}; verify the Test Settings panel mounts"):
            target_option.click()
            test_settings.wait_for_panel()
            assert test_settings.tool_select.is_visible(), (
                "Test Settings panel's Tool select should be visible after choosing a tool"
            )
            expect(test_settings.model_selector_name).to_be_visible(timeout=10_000)
            model_name = test_settings.model_selector_name.text_content() or ""
            assert model_name.strip(), (
                f"Model selector should show a non-empty default model name, got: {model_name!r}"
            )
            assert test_settings.is_param_field_visible("repoName"), (
                f"{TOOL_KEY!r}'s 'repoName' parameter field should render after tool selection"
            )

        with allure.step(
            "Step 5 — Verify the pre-run panel shows only the settings form (no separate chat/"
            "welcome region — AFS CLARIFICATION #1086: no such state exists on this surface between "
            "tool-selection and Run)"
        ):
            expect(test_settings.get_result_items()).to_have_count(0, timeout=3_000)

        with allure.step(
            f"Step 6 — Fill repoName={REPO_NAME!r}; verify Run is disabled until filled, then click Run"
        ):
            run_button = test_settings.run_tool_button
            assert run_button.is_disabled(), (
                "Run button should stay disabled until the required 'repoName' parameter is filled"
            )
            test_settings.fill_param_field("repoName", REPO_NAME)
            expect(run_button).to_be_enabled(timeout=10_000)
            test_settings.run_tool()

        with allure.step(
            "Step 7 — Verify a real (non-canned) response from the selected tool appears in the "
            "Run Results view"
        ):
            result_text = test_settings.wait_for_tool_result()
            assert TOOL_KEY in result_text, (
                f"Result should name the executed tool {TOOL_KEY!r}, got: {result_text[:200]!r}"
            )
            assert "AsyncFuncAI/deepwiki-open" in result_text, (
                f"Result should contain real DeepWiki content for the requested repo, "
                f"got: {result_text[:200]!r}"
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
