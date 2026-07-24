"""UI test — Remote MCP "Test Settings" panel: select a tool and run it.

TMS: ELITEA-1937 (test-specs/mcp/l2_test-settings-select-and-run-tool_ELITEA-1937.md)

Creates a Remote MCP with tools already discovered via the API (bypassing
the "Load Tools" UI flow — ELITEA-1933 already covers that surface, and this
case's own precondition is "a Remote MCP with discovered tools is
available", not "create one via the UI"), then drives the Test Settings
panel end-to-end: verify the default model + Tool dropdown + welcome
message, select a tool, fill its one required parameter, click RUN TOOL,
and verify a real result renders in the chat area — replacing the welcome
message in place (message count stays 1 both before and after).

Uses the ``read_wiki_structure`` tool (plain-text ``repoName`` field) rather
than the case's own literal "tavily_search" example — that tool needs a
credential this environment doesn't have (same substitution ELITEA-1933's
AFS already made) — and rather than ``ask_question`` (its ``repoName`` is an
``anyOf`` string/array rendered as a CodeMirror array editor, more fragile
automation surface for no benefit to this case, per the AFS).
"""

import logging
import re
import uuid

import allure
import pytest
from playwright.sync_api import expect

from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
RUN_TOOL_TIMEOUT = 30_000

MCP_URL = "https://mcp.deepwiki.com/mcp"
TOOL_NAME = "read_wiki_structure"
TOOL_LABEL = "Read wiki structure"
TEST_PARAM_KEY = "repoName"
TEST_PARAM_VALUE = "facebook/react"
EXPECTED_WELCOME_MESSAGE = (
    "Welcome! Select a tool from the Test Settings panel and click "
    "'RUN TOOL' to see the results here."
)


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1937_test-settings-select-and-run-tool.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_test_settings_select_and_run_tool(page, toolkit_api: ToolkitAPI):
    """Select a tool in the Test Settings panel, run it, verify the result in the chat area."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    toolkit_name = f"autotest_1937_{uuid.uuid4().hex[:8]}"
    created_id: int | None = None

    try:
        with allure.step(
            "Step 1 — Set up a Remote MCP with discovered tools via the API "
            "(not the UI) and open its detail page"
        ):
            tools = toolkit_api.sync_mcp_tools(MCP_URL)
            toolkit = toolkit_api.create_remote_mcp_toolkit(
                name=toolkit_name,
                description="ELITEA-1937 automation fixture",
                url=MCP_URL,
                tools=tools,
            )
            created_id = toolkit["id"]
            form.navigate_to_detail(created_id, project_id)
            assert f"/mcps/all/{created_id}" in page.url, (
                f"Expected the MCP detail page URL, got: {page.url}"
            )
            assert toolkit_name in form.get_detail_heading_text(), (
                f"Detail page heading should contain the toolkit name {toolkit_name!r}, "
                f"got: {form.get_detail_heading_text()!r}"
            )

        with allure.step('Step 2 — Verify the right-side "Test Settings" panel is visible'):
            expect(form.test_tool_select).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 3 — Verify the LLM model selector shows a default model"):
            expect(form.model_selector_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            model_name = form.model_selector_name.text_content() or ""
            assert model_name.strip(), (
                "Model selector should show a non-empty default model name "
                "(model-specific — not asserted on the exact value)"
            )

        with allure.step('Step 4 — Verify the "Tool" label and combobox dropdown are present'):
            assert form.test_tool_select.is_enabled(), "Tool dropdown should be present and enabled"

        with allure.step("Step 5 — Click the Tool combobox dropdown"):
            # `test_tool_select`'s testid resolves to the MUI wrapper <div>, which
            # carries no `aria-expanded` attribute (confirmed live: reads `null`).
            # The real, testid-backed signal that the dropdown opened is a known
            # option becoming visible — same handle step 6/7 use.
            form.test_tool_select.click()
            expect(form.get_test_tool_option(TOOL_NAME)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 6 — Verify the dropdown lists all 3 available tools for this MCP"):
            options = form.get_test_tool_options()
            expect(options).to_have_count(3, timeout=UI_ELEMENT_TIMEOUT)
            expect(form.get_test_tool_option(TOOL_NAME)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(f'Step 7 — Select the "{TOOL_NAME}" tool'):
            form.get_test_tool_option(TOOL_NAME).click()
            expect(form.test_tool_select).to_contain_text(TOOL_LABEL, timeout=UI_ELEMENT_TIMEOUT)
            assert form.is_test_param_field_visible(TEST_PARAM_KEY), (
                f"{TOOL_NAME}'s '{TEST_PARAM_KEY}' parameter field should render after selection"
            )

        with allure.step("Step 8 — Verify the welcome message in the chat area"):
            # get_welcome_message_text() reads the message-list CONTAINER's
            # text_content(), which (per .claude/rules/mui-patterns.md §
            # Extracting Message Text) prepends sender/timestamp header
            # metadata (confirmed live: "Elitealess than a minute ago...") —
            # same reason ToolkitTestSettingsPage's own consuming test
            # (test_toolkit_creation_create_bucket_verify_list_files.py)
            # asserts substring containment, not exact equality.
            welcome_text = form.get_welcome_message_text(timeout=UI_ELEMENT_TIMEOUT)
            assert EXPECTED_WELCOME_MESSAGE in welcome_text, (
                f"Expected the welcome message {EXPECTED_WELCOME_MESSAGE!r} in the chat area, "
                f"got: {welcome_text!r}"
            )
            assert form.get_result_message_count() == 1, (
                "Chat area should show exactly 1 message (the welcome message) before RUN TOOL"
            )

        with allure.step('Step 9 — Type a test query in the tool parameters and click "RUN TOOL"'):
            assert form.run_tool_button.is_disabled(), (
                "RUN TOOL should be disabled before the required parameter is filled"
            )
            form.fill_test_param(TEST_PARAM_KEY, TEST_PARAM_VALUE)
            expect(form.run_tool_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)
            form.run_tool()

        with allure.step("Step 10 — Verify the response appears in the chat area from the selected tool"):
            result_text = form.wait_for_tool_result(timeout=RUN_TOOL_TIMEOUT)
            # wait_for_tool_result() reads the message-list CONTAINER (same
            # header-metadata-prepended shape as get_welcome_message_text(),
            # confirmed live: "...Thought for 1 secautotest_1937_...: "
            # precedes the actual "✅ tool_name (N.NNNs)" result) — search
            # for the pattern rather than anchoring at the string start.
            assert re.search(rf"✅ {re.escape(TOOL_NAME)} \(\d", result_text), (
                f"Expected a success-prefixed result for {TOOL_NAME}, got: {result_text!r}"
            )
            assert "Available pages for facebook/react" in result_text, (
                f"Expected real tool output referencing the queried repo, got: {result_text!r}"
            )
            # Axis 2 addition (AFS) — the message list REPLACES in place, never
            # appends: count stays exactly 1 before and after RUN TOOL.
            assert form.get_result_message_count() == 1, (
                "Chat area should still show exactly 1 message after RUN TOOL "
                "(content replaces in place, does not append)"
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
