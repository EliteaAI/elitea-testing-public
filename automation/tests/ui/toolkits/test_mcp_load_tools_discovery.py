"""UI test — Remote MCP "Load Tools" tool discovery.

TMS: ELITEA-1933 (test-specs/mcp/l2_remote-mcp-load-tools-tools-discovery_ELITEA-1933.md)

Creates a Remote MCP pointed at a public, auth-free MCP server
(``https://mcp.deepwiki.com/mcp``, a stable 3-tool fixture), clicks "Load
Tools", and verifies the discovered tools are reflected in the Form view
(pills, all default-selected), the Test Settings "Tool" dropdown (schema
render on select), and the Raw Json view (``available_mcp_tools`` +
``selected_tools`` shapes).
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

MCP_URL = "https://mcp.deepwiki.com/mcp"
EXPECTED_EMPTY_STATE_TEXT = 'No tools to display for now. To get tools from MCP press button “Load Tools”'
EXPECTED_TOOL_NAMES = {"read_wiki_structure", "read_wiki_contents", "ask_question"}


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1933_remote-mcp-load-tools-tools-discovery.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_load_tools_discovery(page, toolkit_api: ToolkitAPI):
    """A Remote MCP discovers and loads tools, reflected in Form view, Test Settings, and Raw Json."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    # Toolkit Name input carries MAX_NAME_LENGTH=32 (EliteaUI src/common/constants.js) —
    # silently truncates anything longer (see .agents/memory/test-automation-engineer/
    # mcp_toolkit_create_form_implementer_quirks.md). Keep the generated name under it.
    toolkit_name = f"autotest_tools_disc_{uuid.uuid4().hex[:6]}"
    created_id: int | None = None

    try:
        with allure.step("Step 1 — Navigate to MCP creation; select Remote MCP type"):
            form.navigate_to_create()
            form.select_remote_mcp_type()
            assert "/mcps/create/mcp" in page.url, f"Expected the Remote MCP form URL, got: {page.url}"
            # Empty-state text is visible even before Name/URL are filled.
            assert form.get_tools_empty_state_text() == EXPECTED_EMPTY_STATE_TEXT, (
                f"Tools empty-state text should show before any tool is loaded, "
                f"got: {form.get_tools_empty_state_text()!r}"
            )

        with allure.step(f'Step 2 — Fill Toolkit Name "{toolkit_name}"'):
            form.fill_name(toolkit_name)
            assert form.name_input.input_value() == toolkit_name

        with allure.step(f'Step 3 — Fill Url "{MCP_URL}"'):
            form.fill_url(MCP_URL)
            assert form.url_input.input_value() == MCP_URL
            assert form.save_button.is_enabled(), "Save button should be enabled once Name+Url are filled"

        with allure.step("Step 4 — Click Save; verify 201 + navigation to detail page"):
            save_response = form.save_and_wait_for_created(project_id)
            created_id = save_response["id"]
            assert isinstance(created_id, int), f"Save response should include a numeric id: {save_response!r}"
            assert f"/mcps/all/{created_id}" in page.url, (
                f"Should navigate to the new MCP's detail page, got: {page.url}"
            )
            assert toolkit_name in form.get_detail_heading_text()

        with allure.step("Step 5 — Verify Tools section shows the empty-state message"):
            assert form.get_tools_empty_state_text() == EXPECTED_EMPTY_STATE_TEXT, (
                f"Tools empty-state text should show before any tool is loaded, "
                f"got: {form.get_tools_empty_state_text()!r}"
            )

        with allure.step('Step 6 — Click "Load Tools"; verify mcp_sync_tools resolves 200'):
            sync_response = form.click_load_tools(project_id)
            assert sync_response, "mcp_sync_tools response body should be non-empty"

        with allure.step(
            "Step 7 — Wait for tools to load (same network wait as Step 6); "
            'verify "Not Connected" flips to "Connected!"'
        ):
            # No separate wait needed — click_load_tools() already resolved the
            # mcp_sync_tools response before returning (AFS Step 7 note: the
            # tools list is populated synchronously with that response, not a
            # separate polling step). The "Connected!"/"Logout" indicator has no
            # testid in scope for this case (out of Concrete Handles) — the
            # discovered-pill and Raw Json assertions below are the case's own
            # proof that the connect+sync sequence completed successfully.
            discovered_names = set(form.get_discovered_tool_names())
            assert discovered_names == EXPECTED_TOOL_NAMES, (
                f"Discovered tool pills should match the fixture's 3 tools, got: {discovered_names!r}"
            )

        with allure.step("Step 8 — Verify discovered tools appear as pills, all default-selected"):
            discovered_names = form.get_discovered_tool_names()
            assert set(discovered_names) == EXPECTED_TOOL_NAMES, (
                f"Expected exactly the 3 fixture tools as pills, got: {discovered_names!r}"
            )
            assert len(discovered_names) == 3, (
                f"Expected exactly 3 pills (no duplicates), got: {discovered_names!r}"
            )
            # Axis 2 addition: all 3 tools are checkmarked (selected) immediately
            # after Load Tools, with no manual selection — guards against a
            # regression that populates available_mcp_tools but leaves
            # selected_tools empty (AFS Axis 2).
            for tool_name in EXPECTED_TOOL_NAMES:
                assert form.is_tool_chip_selected(tool_name), (
                    f"Tool pill {tool_name!r} should be checkmarked (selected) by default after Load Tools"
                )

        with allure.step(
            'Step 9 — Select "ask_question" in the Test Settings "Tool" dropdown; '
            "verify its parameter schema renders (CLARIFICATION issue #595, not a "
            "Tools-section pill click)"
        ):
            form.select_test_tool("ask_question")
            # ask_question's schema requires repoName (string or array-of-strings,
            # anyOf) and question (string) — assert the rendered fields, which are
            # the schema-on-select proof (AFS step 9). Located via the dynamic
            # toolkit-test-param-{fieldKey} testid (EliteaUI automation/testids
            # commit a3c58b93, CommonStringField.jsx / AnyOfPatternField.jsx) —
            # per-review fix: these are ordinary EliteaUI elements, not a
            # documented stop+flag exception, so a raw get_by_text() locator was
            # a testid-only policy violation (.agents/testing.md § Locator policy).
            assert form.is_test_param_field_visible("repoName"), (
                "ask_question's 'repoName' parameter field should render after selecting "
                "the tool in the Test Settings dropdown"
            )
            assert form.is_test_param_field_visible("question"), (
                "ask_question's 'question' parameter field should render after selecting "
                "the tool in the Test Settings dropdown"
            )

        with allure.step(
            "Step 10 — Switch to Raw Json; verify available_mcp_tools populated "
            "with label/value/args_schema/description per tool"
        ):
            form.switch_to_raw_json_view()
            # get_raw_json() truncates on this payload's size (CodeMirror
            # virtualization, ~30 of ~85 lines rendered at a time) —
            # get_raw_json_full() is required here (AFS § Automation Hints /
            # McpFormPage docstring).
            raw_json = form.get_raw_json_full()
            available_tools = raw_json["settings"]["available_mcp_tools"]
            assert len(available_tools) == 3, (
                f"available_mcp_tools should contain exactly 3 tool objects, got: {len(available_tools)}"
            )
            available_by_value = {t["value"]: t for t in available_tools}
            assert set(available_by_value.keys()) == EXPECTED_TOOL_NAMES, (
                f"available_mcp_tools values should match the fixture's 3 tools, "
                f"got: {set(available_by_value.keys())!r}"
            )
            for tool_name, tool_obj in available_by_value.items():
                assert tool_obj.get("label"), f"{tool_name} should have a non-empty 'label'"
                assert "args_schema" in tool_obj, f"{tool_name} should have an 'args_schema'"
                assert "description" in tool_obj, f"{tool_name} should have a 'description'"
                schema_properties = tool_obj["args_schema"].get("properties", {})
                assert "repoName" in schema_properties, (
                    f"{tool_name}'s args_schema should require 'repoName', got: {schema_properties!r}"
                )
            # Confirmed shapes (AFS step 10): ask_question also requires 'question'.
            ask_question_properties = available_by_value["ask_question"]["args_schema"]["properties"]
            assert "question" in ask_question_properties, (
                f"ask_question's args_schema should require 'question', got: {ask_question_properties!r}"
            )

        with allure.step(
            "Step 11 — Verify selected_tools contains all 3 discovered tool names"
        ):
            selected_tools = raw_json["settings"]["selected_tools"]
            assert set(selected_tools) == EXPECTED_TOOL_NAMES, (
                f"selected_tools should contain all 3 discovered tool names, got: {selected_tools!r}"
            )
            assert len(selected_tools) == 3, (
                f"selected_tools should have no duplicates, got: {selected_tools!r}"
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
