"""UI test — MCP Integration in Pipeline: select an MCP directly in the node (auto-attach).

TMS: ELITEA-1955
(test-specs/pipelines/l3_mcp-node-without-toolkit-attached-first_ELITEA-1955.md)

Adds an MCP node to a pipeline with nothing attached in TOOLS, opens the node's
project MCP picker (EL-7159) and verifies its search box, "Create new" and a
non-empty MCP list, searches for and picks the fixture MCP, verifies it is the
node's value and that it auto-appears in the TOOLS section (no "+ MCP" click),
then configures a Tool + Input-mapping, saves, and confirms persistence after reload.
"""

import logging

import pytest
import allure

from pages.pipeline_detail_page import PipelineDetailPage
from config import settings

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p3, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

# The two Input-mapping parameters "ask_wiki_question" requires (raw schema keys,
# same tool + fixture the sibling ELITEA-1954 test uses — see
# pipeline_detail_page.fill_mcp_node_input_mapping_value docstring for why
# these are the raw schema keys, not the capitalized display labels).
_REPO_NAME_VALUE = "EliteaAI/elitea-testing-public"
_QUESTION_VALUE = "What is this repository about?"


@pytest.mark.tms("ELITEA-1955")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/"
    "ELITEA-1955_mcp-integration-in-pipeline-mcp-node-without-tool-first.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_node_empty_toolkit_before_attach(page, pipeline_id, mcp_toolkit_with_tools):
    """Picking an MCP directly in the node picker auto-attaches it to TOOLS (EL-7159)."""
    fixture = mcp_toolkit_with_tools
    mcp_display_name = fixture["name"]  # exact popper row text, not space-stripped
    mcp_toolkit_name = fixture["toolkit_name"]  # cleaned select-option value
    project_id = str(settings.elitea_project_id)

    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from every step (node
    # creation, empty-dropdown open, MCP attach, tool configuration, save,
    # reload) are captured — not just from a later step. AFS Expected
    # Results require "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Navigate to the fresh pipeline; verify configuration panel + canvas load"):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step (already carries ?viewMode=owner)
        assert pipeline_page.configuration_tab.is_visible(), (
            "Configuration panel (General section) should be visible after navigating"
        )

    with allure.step("Step 2 — Confirm the TOOLS section has no MCP/Toolkit attached yet"):
        pipeline_page.ensure_toolkits_section_visible(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.toolkit_card.count() == 0, (
            "TOOLS section should show no toolkit/MCP card before any attach — "
            "this pipeline was created fresh via the plain create_pipeline API"
        )

    with allure.step('Step 3 — Click "Add node" and select "MCP"; config fields render inline'):
        pipeline_page.add_node("MCP", timeout=UI_ELEMENT_TIMEOUT)
        mcp_node_id = pipeline_page.wait_for_node_on_canvas("mcp", timeout=UI_ELEMENT_TIMEOUT)
        assert mcp_node_id, "MCP node should be present on the canvas with a non-empty data-id"
        # Canvas cards are view-only summaries (EL-7157): the Toolkit/Tool selects
        # live in the node side panel — open it by selecting the node.
        pipeline_page.ensure_mcp_node_panel_open(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.mcp_node_toolkit_select.is_visible(), (
            "MCP node's Toolkit select should be visible in the node configuration panel "
            "after the node is selected"
        )

    with allure.step("Step 4 — Open the node's MCP picker; search box, \"Create new\" and a non-empty MCP list render"):
        pipeline_page.open_mcp_node_picker(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_picker_search_count() == 1, "MCP picker should render a search textbox"
        assert pipeline_page.get_mcp_node_picker_create_new_count() == 1, (
            "MCP picker should render a 'Create new' action"
        )
        assert pipeline_page.get_mcp_node_picker_option_count() > 0, (
            "MCP picker should list the project's MCPs (non-empty) even though nothing is attached in TOOLS"
        )

    with allure.step("Step 5 — Type the fixture MCP name into the picker search"):
        pipeline_page.search_mcp_node_picker(mcp_toolkit_name, timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 6 — Select the fixture MCP from the filtered results"):
        pipeline_page.select_mcp_node_picker_result(mcp_toolkit_name, timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 7 — The MCP is now the node's selected value"):
        selected_toolkit = pipeline_page.get_mcp_node_toolkit_value()
        assert selected_toolkit == mcp_toolkit_name, (
            f"Node MCP picker should show {mcp_toolkit_name!r} after selection, got {selected_toolkit!r}"
        )
        assert pipeline_page.mcp_node_tool_select.is_visible(), (
            "A Tool combobox should render on the node once an MCP with tools is selected"
        )

    with allure.step("Step 8 — The same MCP appears in the left TOOLS section automatically (no '+ MCP' click)"):
        pipeline_page.close_node_panel(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.ensure_toolkits_section_visible(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.is_toolkit_attached(mcp_display_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"TOOLS section should show a card for {mcp_display_name!r} auto-attached by picking it in the node"
        )
        assert not console_errors, f"Picking the MCP should not introduce console errors: {console_errors}"
        pipeline_page.ensure_mcp_node_panel_open(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 9 — Select a tool; Input mapping (required 2) renders with the tool's own params"):
        pipeline_page.select_mcp_node_tool("ask_wiki_question", timeout=UI_ELEMENT_TIMEOUT)
        selected_tool = pipeline_page.get_mcp_node_tool_value()
        assert selected_tool == "ask_wiki_question", (
            f"Tool select should show 'ask_wiki_question' after selection, got {selected_tool!r}"
        )
        assert pipeline_page.has_mcp_node_required_input_mapping_count(2, timeout=UI_ELEMENT_TIMEOUT), (
            "Exactly 2 required Input-mapping fields should be listed in the panel for ask_wiki_question's "
            "2 required parameters (repoName, question)"
        )
        assert pipeline_page.is_mcp_node_input_mapping_value_visible(
            "repoName", timeout=UI_ELEMENT_TIMEOUT
        ), "repoName Value field should be visible"
        assert pipeline_page.is_mcp_node_input_mapping_value_visible(
            "question", timeout=UI_ELEMENT_TIMEOUT
        ), "question Value field should be visible"

    with allure.step("Step 9 (cont.) — Fill Input-mapping fields; Save; reload; verify full configuration persists"):
        pipeline_page.fill_mcp_node_input_mapping_value("repoName", _REPO_NAME_VALUE)
        pipeline_page.fill_mcp_node_input_mapping_value("question", _QUESTION_VALUE)

        assert pipeline_page.get_mcp_node_input_mapping_value("repoName") == _REPO_NAME_VALUE
        assert pipeline_page.get_mcp_node_input_mapping_value("question") == _QUESTION_VALUE

        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

        # Reload via the canonical URL (carries ?viewMode=owner) — a bare
        # /pipelines/all/{id} 404s, per the already-filed
        # EliteaAI/elitea-testing-public#512 clarification.
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("mcp", timeout=UI_ELEMENT_TIMEOUT)
        # The node panel is closed after a reload — reopen it to read the fields.
        pipeline_page.ensure_mcp_node_panel_open(timeout=UI_ELEMENT_TIMEOUT)

        persisted_toolkit = pipeline_page.get_mcp_node_toolkit_value()
        persisted_tool = pipeline_page.get_mcp_node_tool_value()
        assert persisted_toolkit == mcp_toolkit_name, (
            f"Toolkit should persist as {mcp_toolkit_name!r} after reload, got {persisted_toolkit!r}"
        )
        assert persisted_tool == "ask_wiki_question", (
            f"Tool should persist as 'ask_wiki_question' after reload, got {persisted_tool!r}"
        )
        assert pipeline_page.has_mcp_node_required_input_mapping_count(2, timeout=UI_ELEMENT_TIMEOUT), (
            "The 2 required Input-mapping fields should still be present after reload"
        )
        assert pipeline_page.get_mcp_node_input_mapping_value("repoName") == _REPO_NAME_VALUE, (
            "repoName Input-mapping value should persist through reload"
        )
        assert pipeline_page.get_mcp_node_input_mapping_value("question") == _QUESTION_VALUE, (
            "question Input-mapping value should persist through reload"
        )
