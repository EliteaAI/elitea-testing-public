"""UI test — Remote MCP: view run history and inspect a past execution's details.

TMS: ELITEA-1940 (test-specs/mcp/l3_remote-mcp-test-settings-view-run-history_ELITEA-1940.md)

Creates a Remote MCP pointed at the public, auth-free DeepWiki MCP server
(``https://mcp.deepwiki.com/mcp`` — the same stable 3-tool fixture
ELITEA-1933/1934/1937 use), runs one of its tools TWICE with different
parameters, then opens Run History and verifies the past executions are listed
with timestamps and that selecting an entry renders that execution's input and
output.

Two live divergences from the case text, filed as clarification #1727 (location
only — the case's observable is fully intact, so this asserts the LIVE contract
per the reverse-masking guard):

* the "view run history" control is in the MCP **detail action bar**
  (``pipeline-history-tab``), not in the test-panel header — EL-6277 moved the
  Test surface to its own route and relocated this button;
* it navigates to a full **page**, ``/toolkits/all/{id}/history?isMCP=true``,
  not a panel/drawer (MCPs deliberately reuse the toolkit route with an
  ``isMCP`` flag).

Fixture substitution (AFS § Preconditions, transit only): the case's
precondition "an MCP with at least one previous tool execution" is satisfied by
the test performing the runs itself against a real remote MCP server — every
asserted value (run rows, timestamps, input JSON, output) is produced by the
system, nothing is fabricated or injected.

Two runs (not one) are required by the observable: ``RunHistoryContainer``
auto-selects row 0 on mount, so a "click an entry -> details show" assertion
that clicks row 0 would pass even if the click did nothing. The runs use
DIFFERENT ``repoName`` values so the detail pane's content is provably
row-specific.
"""

import logging
import re
import uuid

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage
from pages.toolkit_run_history_page import ToolkitRunHistoryPage
from pages.toolkit_test_settings_page import ToolkitTestSettingsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p3, pytest.mark.regression, pytest.mark.new]

MCP_URL = "https://mcp.deepwiki.com/mcp"
TOOL_KEY = "read_wiki_structure"
REPO_FIRST_RUN = "AsyncFuncAI/deepwiki-open"
REPO_SECOND_RUN = "facebook/react"

# Run History's Date column, confirmed live: "24-08-2026, 06:17 AM".
# Asserted by SHAPE, never by exact text — the value is generated per run, and
# an "is non-empty" check would pass on any garbage string.
TIMESTAMP_PATTERN = re.compile(r"\d{2}-\d{2}-\d{4},\s*\d{2}:\d{2}\s*(?:AM|PM)")
# Duration column, confirmed live: "1.19 s" (also rendered in ms for fast runs).
DURATION_PATTERN = re.compile(r"\d+(?:\.\d+)?\s*(?:ms|s)(?!\w)")

RUN_RESULT_TIMEOUT = 30_000


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1940_remote-mcp-test-settings-view-run-history.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_view_run_history_and_entry_details(page, toolkit_api: ToolkitAPI):
    """Run History lists past MCP tool executions with timestamps; selecting one shows its details."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    test_settings = ToolkitTestSettingsPage(page)
    run_history = ToolkitRunHistoryPage(page)
    # Toolkit Name input carries MAX_NAME_LENGTH=32 (EliteaUI src/common/constants.js).
    toolkit_name = f"autotest_mcp_run_history_{uuid.uuid4().hex[:6]}"
    created_id: int | None = None

    try:
        with allure.step("Step 1 — Create a Remote MCP and open its detail page"):
            form.navigate_to_create()
            form.select_remote_mcp_type()
            form.fill_name(toolkit_name)
            form.fill_url(MCP_URL)
            save_response = form.save_and_wait_for_created(project_id)
            created_id = save_response["id"]
            assert isinstance(created_id, int), f"Save response should include a numeric id: {save_response!r}"

            form.navigate_to_detail(created_id, project_id)
            assert form.get_detail_heading_text() == toolkit_name, (
                f"Detail page title should show the MCP's name, got: "
                f"{form.get_detail_heading_text()!r}"
            )

        with allure.step("Step 2 — Load Tools; verify the 3-tool fixture is discovered"):
            sync_response = form.click_load_tools(project_id)
            assert sync_response, "mcp_sync_tools response body should be non-empty"
            discovered_names = form.get_discovered_tool_names()
            assert len(discovered_names) == 3, (
                f"DeepWiki exposes 3 tools; discovered pills were: {discovered_names!r}"
            )
            assert TOOL_KEY in discovered_names, (
                f"Expected {TOOL_KEY!r} among the discovered tool pills, got: {discovered_names!r}"
            )

        with allure.step(
            "Step 3 — Save the dirtied form; verify the action bar's Test button goes "
            "disabled -> enabled (ToolkitForm.jsx: isTestDisabled={dirty}, AFS Axis 2)"
        ):
            assert form.is_test_button_disabled(), (
                "Test button should be disabled while the form is dirty (Load Tools dirties it)"
            )
            form.save_and_wait_for_updated(project_id, created_id)
            expect(form.test_button).to_be_enabled(timeout=10_000)

        with allure.step("Step 4 — Click Test; verify the Test route opens on its tool-select empty state"):
            form.open_test_route(created_id)
            assert f"/mcps/all/{created_id}/test" in page.url, (
                f"Test button should navigate to the MCP Test route, got: {page.url!r}"
            )
            expect(test_settings.empty_state_tool_select).to_be_visible(timeout=10_000)

        with allure.step(
            f"Step 5a — Select {TOOL_KEY!r}, run it with repoName={REPO_FIRST_RUN!r}, "
            "and verify a real (non-canned) result"
        ):
            test_settings.select_tool_from_empty_state(TOOL_KEY)
            test_settings.wait_for_panel()
            test_settings.fill_param_field("repoName", REPO_FIRST_RUN)
            expect(test_settings.run_tool_button).to_be_enabled(timeout=10_000)
            test_settings.run_tool()
            first_result = test_settings.wait_for_tool_result(timeout=RUN_RESULT_TIMEOUT)
            assert TOOL_KEY in first_result, (
                f"Result should name the executed tool {TOOL_KEY!r}, got: {first_result[:200]!r}"
            )

        with allure.step(
            f"Step 5b — Run the same tool a second time with repoName={REPO_SECOND_RUN!r} "
            "so Run History holds two DISTINGUISHABLE executions"
        ):
            result_items = test_settings.get_result_items()
            items_before_second_run = result_items.count()
            test_settings.set_param_field("repoName", REPO_SECOND_RUN)
            test_settings.run_tool()
            # The results list APPENDS (useToolkitChat: setChatHistory(prev => [...prev, ...])),
            # so wait for a NEW item before reading the last one — otherwise the previous
            # run's already-completed result would satisfy the ✅/❌ wait immediately.
            expect(result_items.nth(items_before_second_run)).to_be_visible(timeout=RUN_RESULT_TIMEOUT)
            second_result = test_settings.wait_for_tool_result(timeout=RUN_RESULT_TIMEOUT)
            assert TOOL_KEY in second_result, (
                f"Second result should name the executed tool {TOOL_KEY!r}, got: {second_result[:200]!r}"
            )

        with allure.step(
            "Step 6 — Return to the MCP detail page and click Run History; verify it navigates "
            "to /toolkits/all/{id}/history?isMCP=true (clarification #1727: an action-bar "
            "button and a full page, not a test-panel-header button opening a drawer)"
        ):
            form.navigate_to_detail(created_id, project_id)
            form.open_run_history(created_id)
            assert f"/toolkits/all/{created_id}/history" in page.url, (
                f"Run History should open the toolkit history route, got: {page.url!r}"
            )
            assert "isMCP=true" in page.url, (
                f"An MCP's Run History route should carry the isMCP flag, got: {page.url!r}"
            )
            run_history.wait_for_loaded()

        with allure.step(
            "Step 7 — Verify both executions are listed, each with a timestamp and a duration"
        ):
            expect(run_history.get_items()).to_have_count(2, timeout=10_000)
            row_texts = run_history.get_item_texts()
            for index, row_text in enumerate(row_texts):
                assert TIMESTAMP_PATTERN.search(row_text), (
                    f"Run History row {index} should show a DD-MM-YYYY, hh:mm AM/PM timestamp, "
                    f"got: {row_text!r}"
                )
                assert DURATION_PATTERN.search(row_text), (
                    f"Run History row {index} should show a duration, got: {row_text!r}"
                )

        with allure.step(
            "Step 8 — Verify the auto-selected top row shows the most recent run's details, "
            "then click the OTHER row and verify both the selection and the details change"
        ):
            # Default sort is Date-descending, so row 0 is the second (most recent) run;
            # RunHistoryContainer auto-selects it on mount.
            assert run_history.is_item_selected(0), (
                "Run History should auto-select the most recent row on mount"
            )
            expect(run_history.detail_message_list).to_contain_text(
                REPO_SECOND_RUN, timeout=10_000
            )

            run_history.select_item(1)
            assert run_history.is_item_selected(1), "The clicked row should become the selected one"
            assert not run_history.is_item_selected(0), (
                "The previously auto-selected row should no longer be marked selected"
            )
            # The detail pane now has to show the FIRST run — proving the click changed
            # the rendered execution, not merely that 'some detail is visible'.
            expect(run_history.detail_message_list).to_contain_text(
                REPO_FIRST_RUN, timeout=10_000
            )
            expect(run_history.detail_message_list).to_contain_text(TOOL_KEY, timeout=10_000)
            expect(run_history.get_detail_message_items()).to_have_count(2, timeout=10_000)

    finally:
        # Not a case step — cleanup for the persistent server-side toolkit this
        # test creates (AFS § Cleanup). Deleting the MCP disposes of its run
        # history with it (history is keyed on entityId).
        if created_id is not None:
            try:
                toolkit_api.delete_toolkit(created_id)
            except Exception:
                logger.warning(
                    "Failed to delete seeded MCP toolkit id=%s during cleanup", created_id, exc_info=True
                )
