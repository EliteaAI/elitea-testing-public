"""UI test — deselect and re-select a specific tool via the Raw Json editor.

TMS: ELITEA-1935 (test-specs/mcp/l1_remote-mcp-deselect-select-specific-tools_ELITEA-1935.md)

Seeds a Remote MCP against the public DeepWiki MCP server, discovers its
tools, then drives the case: read ``settings.selected_tools`` in Raw Json,
delete one tool's line, save, confirm the Form view's chip flips to
``data-selected="false"`` (the chip is NOT removed), re-add the name, save
again, and confirm the round-trip persisted server-side after a reload.

Fixture substitution (transit only, declared): the case's precondition names a
Tavily-based MCP ("Web Search" with ``tavily_crawl``), which needs an API-key
credential that is not provisioned in this environment. The project's standard
public fixture ``https://mcp.deepwiki.com/mcp`` is used instead (same precedent
as ELITEA-1933/1934), and the case's "tool to deselect" maps to
``ask_question``. Every asserted value — the ``selected_tools`` payload, each
chip's ``data-selected`` attribute, the PUT status — is produced by the real
system against a real MCP server. Nothing is stubbed, injected or fabricated.
"""

import logging
import uuid

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p0, pytest.mark.regression]

# Public, auth-free MCP server used across the MCP suite (test-specs/mcp/_surface.md
# § Fixtures) — must be a REAL reachable server here, since this case's whole
# precondition is a toolkit with genuinely discovered tools.
DEEPWIKI_MCP_URL = "https://mcp.deepwiki.com/mcp"
DEEPWIKI_TOOLS = {"ask_question", "read_wiki_contents", "read_wiki_structure"}

# The tool this case deselects. Load-bearing, not arbitrary: `selected_tools`
# renders one array element per line and `ask_question` sorts FIRST, so it is a
# non-last element. Deleting the LAST element would strand the preceding line's
# trailing comma and make the document invalid JSON, so Save would be refused.
TOOL_TO_DESELECT = "ask_question"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1935_remote-mcp-deselect-select-specific-tools.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_toggle_selected_tools_via_raw_json(page, toolkit_api: ToolkitAPI):
    """A tool can be removed from and re-added to `selected_tools` via Raw Json, and the Form view follows."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)

    # ---- Setup (transit, NOT a case step) -------------------------------
    # Create a dedicated Remote MCP against the DeepWiki fixture and discover
    # its tools, so the test starts from the case's stated precondition
    # ("a Remote MCP that has discovered tools"). A dedicated, disposable
    # toolkit rather than a shared leftover: this case SAVES edits, which is
    # inherently destructive to whatever toolkit it runs against
    # (test-automation-implementation Hard Rule 10).
    form.navigate_to_create()
    form.select_remote_mcp_type()
    # MAX_NAME_LENGTH=32 is enforced as inputProps.maxLength and silently
    # truncates — "autotest_conn_tools_" is 20 chars, +4 hex = 24. Safe.
    toolkit_name = f"autotest_conn_tools_{uuid.uuid4().hex[:4]}"
    form.fill_name(toolkit_name)
    form.fill_url(DEEPWIKI_MCP_URL)
    toolkit_id = form.save_and_wait_for_created(project_id)["id"]
    form.click_load_tools(project_id)
    form.save_and_wait_for_updated(project_id, toolkit_id)

    try:
        with allure.step("Step 1 — Open the Remote MCP detail page (toolkit with discovered tools)"):
            form.navigate_to_detail(toolkit_id, project_id)
            assert form.get_detail_heading_text() == toolkit_name, (
                "Detail title should show the toolkit's own name, not the 'Edit MCP' "
                f"placeholder, got: {form.get_detail_heading_text()!r}"
            )
            assert form.form_view_toggle.get_attribute("aria-pressed") == "true", (
                "Detail page should open in Form view"
            )

        with allure.step("Step 2 — Switch to Raw Json view; verify the JSON editor is visible"):
            form.switch_to_raw_json_view()
            assert form.raw_json_editor_content.is_visible(), (
                "Raw Json editor should be visible after switching view"
            )

        with allure.step(
            "Step 3 — Locate 'selected_tools' and note all tool names present"
        ):
            # get_raw_json_full(), never get_raw_json(): with tools discovered the
            # document carries the args_schema blocks (~120 lines) and CodeMirror
            # virtualizes, so a single text_content() read returns a truncated,
            # unparseable payload (AFS step 3 warning).
            raw_json = form.get_raw_json_full()
            mcp_settings = raw_json["settings"]
            selected_tools = mcp_settings["selected_tools"]
            assert set(selected_tools) == DEEPWIKI_TOOLS, (
                f"All three discovered tools should start selected, got: {selected_tools!r}"
            )
            assert len(selected_tools) == 3, (
                f"selected_tools should hold exactly 3 entries with no duplicates, got: {selected_tools!r}"
            )
            # Analyst addition (AFS Axis 2): available_mcp_tools is the companion
            # field that drives the chip list. A regression that populated
            # selected_tools but dropped available_mcp_tools would render zero
            # chips while the assertion above still passed. (This also corrects
            # issue #574's blanket "the product never renders it" — it is
            # CONDITIONAL on tools having been discovered.)
            available = mcp_settings.get("available_mcp_tools")
            assert available is not None, (
                "settings.available_mcp_tools should be present once tools are discovered "
                f"(settings keys: {sorted(mcp_settings)})"
            )
            assert {t["value"] for t in available} == DEEPWIKI_TOOLS, (
                f"available_mcp_tools should hold one entry per discovered tool, got: {available!r}"
            )

        with allure.step(
            f"Step 4 — Remove {TOOL_TO_DESELECT!r} from the 'selected_tools' array"
        ):
            # get_raw_json_full() leaves the editor scrolled to the BOTTOM; the
            # target line would then be virtualized out of the DOM and the click
            # below would time out (documented trap, test-specs/mcp/_surface.md).
            form.scroll_raw_json_to_top()
            form.delete_raw_json_line(f'"{TOOL_TO_DESELECT}",')

            edited_json = form.get_raw_json_full()
            edited_tools = edited_json["settings"]["selected_tools"]
            assert TOOL_TO_DESELECT not in edited_tools, (
                f"Editor's selected_tools should no longer contain {TOOL_TO_DESELECT!r}, "
                f"got: {edited_tools!r}"
            )
            assert set(edited_tools) == DEEPWIKI_TOOLS - {TOOL_TO_DESELECT}, (
                f"The other two tool names should be untouched, got: {edited_tools!r}"
            )

        with allure.step("Step 5 — Click Save; the update completes successfully"):
            # There is NO success toast on the MCP detail Save (confirmed live,
            # test-specs/mcp/_surface.md) — the PUT 200 is the honest,
            # system-produced completion signal.
            save_response = form.save_and_wait_for_updated(project_id, toolkit_id)
            saved_tools = save_response["settings"]["selected_tools"]
            assert set(saved_tools) == DEEPWIKI_TOOLS - {TOOL_TO_DESELECT}, (
                f"Save response should carry the reduced selected_tools, got: {saved_tools!r}"
            )
            assert form.detail_save_button.is_disabled(), (
                "Save should be disabled again once the form is no longer dirty"
            )

        with allure.step(
            f"Step 6 — Form view: {TOOL_TO_DESELECT!r} is no longer selected in the Tools section"
        ):
            form.switch_to_form_view()
            assert not form.is_tool_chip_selected(TOOL_TO_DESELECT), (
                f"{TOOL_TO_DESELECT!r}'s chip should carry data-selected='false' after the edit"
            )
            for still_selected in sorted(DEEPWIKI_TOOLS - {TOOL_TO_DESELECT}):
                assert form.is_tool_chip_selected(still_selected), (
                    f"{still_selected!r} should still be selected"
                )
            # Analyst addition (AFS Axis 2): the chip list is driven by
            # available_mcp_tools, the selection by selected_tools — deselecting
            # does NOT remove the chip. Asserting chip ABSENCE here would fail,
            # and without this count a regression that wiped the whole chip list
            # would still satisfy "the removed tool is no longer selected".
            assert sorted(form.get_discovered_tool_names()) == sorted(DEEPWIKI_TOOLS), (
                "All 3 tool chips should still be rendered — deselecting removes the tool "
                f"from selected_tools, not the chip, got: {form.get_discovered_tool_names()!r}"
            )

        with allure.step(
            f"Step 7 — Switch back to Raw Json and add {TOOL_TO_DESELECT!r} back to 'selected_tools'"
        ):
            form.switch_to_raw_json_view()
            form.scroll_raw_json_to_top()
            # Re-add as a single-line replacement: JSON is whitespace-insensitive,
            # so two names on one line is valid and the server normalises the
            # formatting on save (verified live, AFS step 7).
            form.fill_raw_json_line(
                '"read_wiki_contents",',
                f'"{TOOL_TO_DESELECT}", "read_wiki_contents",',
            )
            readded_tools = form.get_raw_json_full()["settings"]["selected_tools"]
            assert set(readded_tools) == DEEPWIKI_TOOLS, (
                f"Editor's selected_tools should hold all three names again, got: {readded_tools!r}"
            )

        with allure.step("Step 8 — Save; the tool is selected again in Form view and persists"):
            resave_response = form.save_and_wait_for_updated(project_id, toolkit_id)
            assert set(resave_response["settings"]["selected_tools"]) == DEEPWIKI_TOOLS, (
                "Save response should carry all three tool names again, got: "
                f"{resave_response['settings']['selected_tools']!r}"
            )

            form.switch_to_form_view()
            for tool_name in sorted(DEEPWIKI_TOOLS):
                assert form.is_tool_chip_selected(tool_name), (
                    f"{tool_name!r}'s chip should be selected again after the re-add"
                )

            # Analyst addition (AFS Axis 2): the Form view reads client-side
            # Formik state, so without a reload the test cannot distinguish
            # "saved" from "optimistically rendered" — and reaching the server is
            # the whole point of the case.
            form.reload_and_wait()
            form.switch_to_raw_json_view()
            persisted_tools = form.get_raw_json_full()["settings"]["selected_tools"]
            assert sorted(persisted_tools) == sorted(DEEPWIKI_TOOLS), (
                "selected_tools should still hold all three names after a full reload "
                f"(server-side persistence), got: {persisted_tools!r}"
            )
    finally:
        # Not a case step — teardown for the toolkit seeded above (AFS § Cleanup).
        try:
            toolkit_api.delete_toolkit(toolkit_id)
        except Exception:
            logger.warning(
                "Failed to delete seeded MCP toolkit id=%s during cleanup", toolkit_id, exc_info=True
            )
