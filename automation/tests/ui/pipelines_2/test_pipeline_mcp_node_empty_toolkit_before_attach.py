"""UI test — MCP Integration in Pipeline: MCP node without a toolkit attached first.

TMS: ELITEA-1955
(test-specs/pipelines/l3_mcp-node-without-toolkit-attached-first_ELITEA-1955.md)

Adds an MCP node to a pipeline that has no MCP/Toolkit attached in TOOLS
yet, verifies the node's Toolkit dropdown shows zero real options (only
MUI's own empty-state placeholder), attaches a Remote MCP via the TOOLS
section's "+ MCP" button, verifies the same (already-rendered) node's
Toolkit dropdown immediately lists the newly-attached MCP with no reload
or node re-creation needed, configures a Tool + Input-mapping, saves, and
confirms everything persists through a full page reload.
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

# The two Input-mapping parameters "ask_question" requires (raw schema keys,
# same tool + fixture the sibling ELITEA-1954 test uses — see
# pipeline_detail_page.fill_mcp_node_input_mapping_value docstring for why
# these are the raw schema keys, not the capitalized display labels).
_REPO_NAME_VALUE = "EliteaAI/elitea-testing-public"
_QUESTION_VALUE = "What is this repository about?"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/"
    "ELITEA-1955_mcp-integration-in-pipeline-mcp-node-without-tool-first.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_node_empty_toolkit_before_attach(page, pipeline_id, mcp_toolkit_with_tools):
    """MCP node Toolkit dropdown is empty before attach, populates after."""
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
        assert pipeline_page.mcp_node_toolkit_select.is_visible(), (
            "MCP node's Toolkit select should be visible inline on the canvas card — "
            "no separate click-to-open action needed (live product simplification, "
            "see AFS Coverage Map row 4)"
        )

    with allure.step("Step 4 — Click the MCP node's Toolkit dropdown; verify it opens"):
        pipeline_page.open_mcp_node_toolkit_select_allow_empty(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.mcp_node_toolkit_select_combobox.get_attribute("aria-expanded") == "true", (
            "Toolkit combobox should report aria-expanded=true once the dropdown is open"
        )

    with allure.step("Step 5 — Inspect the open listbox; it has zero real (select-option-*) rows"):
        listed_toolkits = pipeline_page.get_open_listbox_option_names()
        assert listed_toolkits == [], (
            f"Toolkit dropdown should show zero real options before any MCP is attached "
            f"(only MUI's own empty-state placeholder, which carries no testid), "
            f"got {listed_toolkits!r}"
        )

    with allure.step("Step 6 — Close the dropdown without selecting anything"):
        pipeline_page.close_mcp_node_toolkit_select(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.mcp_node_toolkit_select_combobox.get_attribute("aria-expanded") == "false", (
            "Toolkit combobox should report aria-expanded=false after closing via Escape"
        )

    with allure.step('Step 7 — Go back to TOOLS section, click "+ MCP"; search popper opens'):
        popper = pipeline_page.open_mcp_popper(timeout=UI_ELEMENT_TIMEOUT)
        assert popper.is_visible(), "'+ MCP' popper should open"
        assert pipeline_page.get_mcp_popper_search_input_count(popper) > 0, (
            "'+ MCP' popper should render a toolkit-search-input search field"
        )
        assert pipeline_page.get_mcp_popper_menu_item_count(popper) > 0, (
            "'+ MCP' popper should list at least one toolkit-menu-item result row "
            "(the project's available MCPs, including the freshly-provisioned fixture MCP)"
        )

    with allure.step("Step 8 — Select the fixture MCP; verify 201 attach + card renders + no console errors"):
        attach_response = pipeline_page.select_mcp_in_popper(
            popper, mcp_display_name, project_id, timeout=UI_ELEMENT_TIMEOUT
        )
        assert attach_response is not None, "MCP attach should return the persisted toolkit payload"
        assert pipeline_page.is_toolkit_attached(mcp_display_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"TOOLS section should show a card for the attached MCP {mcp_display_name!r}"
        )
        assert not console_errors, f"Attaching the MCP should not introduce console errors: {console_errors}"

    with allure.step("Step 9 — Open the MCP node's Toolkit dropdown again; verify the new MCP is now listed"):
        pipeline_page.open_mcp_node_toolkit_select(timeout=UI_ELEMENT_TIMEOUT)
        listed_toolkits = pipeline_page.get_open_listbox_option_names()
        assert listed_toolkits == [mcp_toolkit_name], (
            f"Toolkit dropdown should list exactly the just-attached MCP {mcp_toolkit_name!r} "
            f"with no reload/re-creation needed, got {listed_toolkits!r}"
        )

    with allure.step("Step 10 — Select the newly-available toolkit; Toolkit combobox shows its name"):
        pipeline_page.select_open_listbox_option(mcp_toolkit_name, timeout=UI_ELEMENT_TIMEOUT)
        selected_toolkit = pipeline_page.get_mcp_node_toolkit_value()
        assert selected_toolkit == mcp_toolkit_name, (
            f"Toolkit select should show {mcp_toolkit_name!r} after selection, got {selected_toolkit!r}"
        )
        assert pipeline_page.mcp_node_tool_select.is_visible(), (
            "A Tool combobox should render on the node once a Toolkit with tools is selected"
        )

    with allure.step("Step 11 — Select a tool; Input mapping (required 2) renders with the tool's own params"):
        pipeline_page.select_mcp_node_tool("ask_question", timeout=UI_ELEMENT_TIMEOUT)
        selected_tool = pipeline_page.get_mcp_node_tool_value()
        assert selected_tool == "ask_question", (
            f"Tool select should show 'ask_question' after selection, got {selected_tool!r}"
        )
        assert pipeline_page.is_input_mapping_section_visible(2, timeout=UI_ELEMENT_TIMEOUT), (
            "'Input mapping (required 2)' section should appear for ask_question's "
            "2 required parameters (repoName, question)"
        )
        assert pipeline_page.is_mcp_node_input_mapping_value_visible(
            "repoName", timeout=UI_ELEMENT_TIMEOUT
        ), "repoName Value field should be visible"
        assert pipeline_page.is_mcp_node_input_mapping_value_visible(
            "question", timeout=UI_ELEMENT_TIMEOUT
        ), "question Value field should be visible"

    with allure.step("Step 12 — Fill Input-mapping fields; Save; reload; verify full configuration persists"):
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

        persisted_toolkit = pipeline_page.get_mcp_node_toolkit_value()
        persisted_tool = pipeline_page.get_mcp_node_tool_value()
        assert persisted_toolkit == mcp_toolkit_name, (
            f"Toolkit should persist as {mcp_toolkit_name!r} after reload, got {persisted_toolkit!r}"
        )
        assert persisted_tool == "ask_question", (
            f"Tool should persist as 'ask_question' after reload, got {persisted_tool!r}"
        )
        assert pipeline_page.is_input_mapping_section_visible(2, timeout=UI_ELEMENT_TIMEOUT), (
            "Input mapping (required 2) section should still be present after reload"
        )
        assert pipeline_page.get_mcp_node_input_mapping_value("repoName") == _REPO_NAME_VALUE, (
            "repoName Input-mapping value should persist through reload"
        )
        assert pipeline_page.get_mcp_node_input_mapping_value("question") == _QUESTION_VALUE, (
            "question Input-mapping value should persist through reload"
        )
