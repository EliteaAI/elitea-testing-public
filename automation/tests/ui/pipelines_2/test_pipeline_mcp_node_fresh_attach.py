"""UI test — Pipeline MCP node integration: fresh attach -> add node -> configure -> persist.

TMS: ELITEA-2037
(test-specs/pipelines/l2_pipeline-mcp-node-integration-fresh-attach_ELITEA-2037.md)

On a fresh, empty pipeline (no nodes/edges pre-seeded): attaches an MCP
toolkit via the TOOLS section's "+ MCP" button, adds a fresh MCP node via
the canvas "Add node" menu, verifies the node's static config fields render
immediately while the Tool select + Input-mapping accordions stay absent
until a Toolkit is chosen, selects the Toolkit then a Tool with required
parameters, fills the Input-mapping values, sets the tool-agnostic
Input/Output state-variable selects, saves, and confirms everything
persists through a full page reload.

Distinct from the sibling MCP-node cases already automated on this suite:
- ELITEA-1954 (test_pipeline_mcp_node_change_toolkit_and_tool.py) starts from
  an ALREADY-CONFIGURED node and switches Toolkit/Tool.
- ELITEA-1955 (test_pipeline_mcp_node_empty_toolkit_before_attach.py) adds the
  node BEFORE any MCP is attached to TOOLS (inverse ordering).
This case is the "happy path from scratch": attach-to-Tools, then add-node,
in the case's own step order, with full static-field-presence assertions
(Structured output) that neither sibling covers.
"""

import logging

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

# The two Input-mapping parameters "ask_wiki_question" requires (raw schema keys —
# NOT the capitalized display labels the case text uses ("RepoName"/"Question");
# see McpNode/InputMapping.jsx: variableName is a display-only capitalization
# of these exact keys — same precedent as the sibling ELITEA-1954/1955 tests).
_REPO_NAME_VALUE = "EliteaAI/elitea-testing-public"
_QUESTION_VALUE = "What is this repository about?"


@pytest.mark.tms("ELITEA-2037")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2037_pipeline-mcp-node-integration.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_node_fresh_attach(page, pipeline_id, mcp_toolkit_with_tools):
    """Fresh-attach an MCP, add + configure an MCP node, save, verify reload persistence."""
    fixture = mcp_toolkit_with_tools
    mcp_display_name = fixture["name"]  # exact popper row text, not space-stripped
    mcp_toolkit_name = fixture["toolkit_name"]  # cleaned select-option value
    project_id = str(settings.elitea_project_id)

    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from every step (attach,
    # node add, dropdown opens, tool selection, save, reload) are captured —
    # AFS Expected Results require "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step(
        "Step 1 — Navigate to the fresh, empty pipeline; verify configuration panel + canvas load"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step — a bare
        # /pipelines/all/{id} URL (no query params) 404s (ELITEA-1954 AFS
        # Known Defects); reloading THIS captured URL avoids that.
        assert pipeline_page.configuration_tab.is_visible(), (
            "Configuration panel (General section) should be visible after navigating"
        )
        # Adjusted (#2702, EL-7154): DEV no longer renders the terminal END node on an
        # empty canvas — it is created together with the first node added. A fresh
        # pipeline's canvas must therefore hold NO nodes at all (still exact, not weaker).
        assert pipeline_page.get_node_ids() == [], (
            "A fresh pipeline's canvas should be empty (no nodes, END included) before any node is added"
        )

    with allure.step(
        'Step 5 — Click "Add node" -> "MCP"; a fresh MCP node appears with no auto-created edge'
    ):
        pipeline_page.add_node("MCP", timeout=UI_ELEMENT_TIMEOUT)
        mcp_node_id = pipeline_page.wait_for_node_on_canvas("mcp", timeout=UI_ELEMENT_TIMEOUT)
        assert mcp_node_id, "MCP node should be present on the canvas with a non-empty data-id"

    with allure.step(
        "Step 6 — Static config fields present immediately (before any Toolkit is selected); "
        "Tool select + Input-mapping accordions are absent"
    ):
        assert pipeline_page.entry_point_trigger_select.is_visible(), (
            "Entry-point Trigger select ('Chat Message') should be visible — the fresh MCP node "
            "is the pipeline's only node, so it auto-becomes the entry point"
        )
        pipeline_page.ensure_mcp_node_panel_open(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.mcp_node_toolkit_select.is_visible(), (
            "MCP node's Toolkit select should be visible in the node config panel"
        )
        pipeline_page.expand_mcp_node_advanced_section(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.mcp_node_input_select.is_visible(), "Input select should be visible inline"
        assert pipeline_page.mcp_node_output_select.is_visible(), "Output select should be visible inline"
        assert pipeline_page.mcp_node_structured_output_toggle.is_visible(), (
            "Structured output toggle should be visible inline"
        )
        # Disabled-state assertion (AFS step 6): Structured output has no
        # entry/transition gating and stays enabled. (Interrupt before/after
        # toggles were removed from node cards — EL-3872, sign-off #2541.)
        assert not pipeline_page.mcp_node_structured_output_toggle.is_disabled(), (
            "Structured output should be enabled (no entry/transition gating)"
        )
        # Negative/absence assertions (AFS Axis 2) — a naive implementation
        # might only assert presence-after-configuration and silently skip
        # the pre-Toolkit-select empty state, which is exactly the state a
        # future regression (Tool select rendering stale/wrong options
        # before a Toolkit is chosen) would need to be caught by.
        assert pipeline_page.get_mcp_node_tool_value(timeout=2000) == "", (
            "Tool select should NOT be rendered (or should read empty) before a Toolkit is selected"
        )
        assert pipeline_page.has_mcp_node_required_input_mapping_count(0, timeout=2000), (
            "No required Input-mapping fields should be rendered before a Toolkit is selected"
        )

    with allure.step('Step 2 — Open the MCP picker; verify the MCP-picker popup opens'):
        # EL-7159 (class A, UI drift): TOOLS has no "+ MCP" button any more; MCPs are picked in
        # the MCP node's own picker (node config panel), so the node from Step 5 is added first.
        pipeline_page.open_mcp_node_picker(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_picker_search_count() > 0, (
            "MCP picker should render a search field"
        )
        assert pipeline_page.get_mcp_node_picker_option_count() > 0, (
            "MCP picker should list at least one result row "
            "(the project's available MCPs, including the freshly-provisioned fixture MCP)"
        )

    with allure.step("Step 3 — Select the fixture MCP from the picker"):
        # EL-7159: the pick attaches the MCP to the pipeline in the form; the attach PATCH
        # (/tool/prompt_lib/ 201) fires on Save (Step 11) — guarded there.
        pipeline_page.select_mcp_node_toolkit(mcp_toolkit_name, timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        "Step 4 — Verify the MCP appears attached in TOOLS as a flat-list card (no MCP sub-tab — "
        "CLARIFICATION EliteaAI/elitea-testing-public#1149, sibling of #530)"
    ):
        pipeline_page.close_node_panel(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.ensure_toolkits_section_visible(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.is_toolkit_attached(mcp_display_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"TOOLS section should show a card for the attached MCP {mcp_display_name!r}"
        )
        assert not console_errors, f"Attaching the MCP should not introduce console errors: {console_errors}"

    with allure.step("Step 7 — Select the attached MCP from the Toolkit dropdown"):
        pipeline_page.select_mcp_node_toolkit(mcp_toolkit_name, timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.ensure_mcp_node_panel_open(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_toolkit_value() == mcp_toolkit_name, (
            f"Toolkit select should show {mcp_toolkit_name!r} after selection"
        )
        assert pipeline_page.mcp_node_tool_select.is_visible(), (
            "A Tool combobox should render on the node once a Toolkit with tools is selected"
        )

    with allure.step(
        "Step 8 — Select 'ask_wiki_question' Tool; Input mapping (required 2) appears with repoName/question"
    ):
        pipeline_page.select_mcp_node_tool("ask_wiki_question", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_tool_value() == "ask_wiki_question", (
            "Tool select should show 'ask_wiki_question' after selection"
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

    with allure.step("Step 9 — Fill the required Input-mapping Value fields (Type left at default Fixed)"):
        pipeline_page.fill_mcp_node_input_mapping_value("repoName", _REPO_NAME_VALUE)
        pipeline_page.fill_mcp_node_input_mapping_value("question", _QUESTION_VALUE)

        assert pipeline_page.get_mcp_node_input_mapping_value("repoName") == _REPO_NAME_VALUE
        assert pipeline_page.get_mcp_node_input_mapping_value("question") == _QUESTION_VALUE

    with allure.step("Step 10 — Set Input combobox to 'input' and Output combobox to 'messages'"):
        pipeline_page.expand_mcp_node_advanced_section(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.select_mcp_node_input_variable("input", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_input_value() == "input", (
            "Input select should show 'input' after selection"
        )
        pipeline_page.select_mcp_node_output_variable("messages", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_output_value() == "messages", (
            "Output select should show 'messages' after selection"
        )

    with allure.step("Step 11 — Save; verify 201 + no console errors across the whole flow"):
        # EL-7159: Save also persists the MCP attachment (deferred from the Step 3 pick) — guard that
        # PATCH (/tool/prompt_lib/ 201) so a regression in the attach persistence fails here.
        attach_response = pipeline_page.save_and_wait_for_attach(
            "/tool/prompt_lib/", project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert attach_response is not None, (
            "Save should persist the MCP attachment via PATCH .../tool/prompt_lib/{project}/ 201"
        )
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 12 — Reload via the canonical URL; Tools attachment + full node config persist byte-for-byte"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("mcp", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.is_toolkit_attached(mcp_display_name, timeout=UI_ELEMENT_TIMEOUT), (
            "TOOLS section should still show the attached MCP card after reload"
        )
        # The node panel is closed after a reload — reopen it to read the node fields.
        pipeline_page.ensure_mcp_node_panel_open(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_toolkit_value() == mcp_toolkit_name, (
            f"Toolkit should persist as {mcp_toolkit_name!r} after reload"
        )
        assert pipeline_page.get_mcp_node_tool_value() == "ask_wiki_question", (
            "Tool should persist as 'ask_wiki_question' after reload"
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
        pipeline_page.expand_mcp_node_advanced_section(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_input_value() == "input", (
            "Input should persist as 'input' after reload"
        )
        assert pipeline_page.get_mcp_node_output_value() == "messages", (
            "Output should persist as 'messages' after reload"
        )
