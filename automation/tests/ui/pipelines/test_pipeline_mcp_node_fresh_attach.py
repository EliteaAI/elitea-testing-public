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
(Interrupt before/after, Structured output) that neither sibling covers.
"""

import logging

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

# The two Input-mapping parameters "ask_question" requires (raw schema keys —
# NOT the capitalized display labels the case text uses ("RepoName"/"Question");
# see McpNode/InputMapping.jsx: variableName is a display-only capitalization
# of these exact keys — same precedent as the sibling ELITEA-1954/1955 tests).
_REPO_NAME_VALUE = "EliteaAI/elitea-testing-public"
_QUESTION_VALUE = "What is this repository about?"


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
        assert pipeline_page.get_node_ids() == ["END"], (
            "A fresh pipeline's canvas should show only the END node before any node is added"
        )

    with allure.step('Step 2 — Click TOOLS "+ MCP"; verify the MCP-picker popup opens'):
        popper = pipeline_page.open_mcp_popper(timeout=UI_ELEMENT_TIMEOUT)
        assert popper.is_visible(), "'+ MCP' popper should open"
        assert pipeline_page.get_mcp_popper_search_input_count(popper) > 0, (
            "'+ MCP' popper should render a toolkit-search-input search field"
        )
        assert pipeline_page.get_mcp_popper_menu_item_count(popper) > 0, (
            "'+ MCP' popper should list at least one toolkit-menu-item result row "
            "(the project's available MCPs, including the freshly-provisioned fixture MCP)"
        )

    with allure.step("Step 3 — Select the fixture MCP from the popup"):
        # Regression check for a fix-round finding (2026-08-04): this AFS
        # originally claimed pipeline-level MCP-attach fires "no persistence
        # request ... only GET calls" (contradicted by ELITEA-1955's sibling
        # test using this same page-object method) — corrected in the AFS's
        # Test Steps step 4 / § Network Behavior. `select_mcp_in_popper()`
        # hard-blocks on `page.expect_response(... PATCH ... status == 201
        # ...)` before returning, so it is itself the regression guard: if a
        # future product change ever stops persisting on attach (reverting to
        # the originally-claimed GET-only behavior, or vice versa breaking
        # the immediate PATCH), this call times out and the step fails
        # loudly instead of silently passing on a stale assumption.
        attach_response = pipeline_page.select_mcp_in_popper(
            popper, mcp_display_name, project_id, timeout=UI_ELEMENT_TIMEOUT
        )
        assert attach_response is not None, (
            "MCP attach should return the persisted toolkit payload from the "
            "immediate PATCH .../tool/prompt_lib/{project}/ 201 response — the "
            "pipeline Tools-section attach auto-persists on selection, same as "
            "the agent-level Tools section (#530), not deferred to pipeline Save"
        )

    with allure.step(
        "Step 4 — Verify the MCP appears attached in TOOLS as a flat-list card (no MCP sub-tab — "
        "CLARIFICATION EliteaAI/elitea-testing-public#1149, sibling of #530)"
    ):
        assert pipeline_page.is_toolkit_attached(mcp_display_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"TOOLS section should show a card for the attached MCP {mcp_display_name!r}"
        )
        assert not console_errors, f"Attaching the MCP should not introduce console errors: {console_errors}"

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
        assert pipeline_page.mcp_node_toolkit_select.is_visible(), (
            "MCP node's Toolkit select should be visible inline on the canvas card"
        )
        assert pipeline_page.mcp_node_input_select.is_visible(), "Input select should be visible inline"
        assert pipeline_page.mcp_node_output_select.is_visible(), "Output select should be visible inline"
        assert pipeline_page.is_node_interrupt_before_toggle_visible(mcp_node_id), (
            "Interrupt before toggle should be visible inline"
        )
        assert pipeline_page.mcp_node_interrupt_after_toggle.is_visible(), (
            "Interrupt after toggle should be visible inline"
        )
        assert pipeline_page.mcp_node_structured_output_toggle.is_visible(), (
            "Structured output toggle should be visible inline"
        )
        # Disabled-state assertions (AFS step 6 — confirmed live): Interrupt
        # before is disabled because this node is the entry point
        # (CommonInterruptSettings.jsx entry_point === id gating); Interrupt
        # after is disabled because the node's default transition is END;
        # Structured output has no such gating and stays enabled.
        assert pipeline_page.is_node_interrupt_before_toggle_disabled(mcp_node_id), (
            "Interrupt before should be disabled — this node is the pipeline's entry point"
        )
        assert pipeline_page.mcp_node_interrupt_after_toggle.is_disabled(), (
            "Interrupt after should be disabled — the node's default transition is END"
        )
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
        assert not pipeline_page.is_input_mapping_section_visible(2, timeout=2000), (
            "INPUT MAPPING (required N) should NOT be rendered before a Toolkit is selected"
        )

    with allure.step("Step 7 — Select the attached MCP from the Toolkit dropdown"):
        pipeline_page.select_mcp_node_toolkit(mcp_toolkit_name, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_toolkit_value() == mcp_toolkit_name, (
            f"Toolkit select should show {mcp_toolkit_name!r} after selection"
        )
        assert pipeline_page.mcp_node_tool_select.is_visible(), (
            "A Tool combobox should render on the node once a Toolkit with tools is selected"
        )

    with allure.step(
        "Step 8 — Select 'ask_question' Tool; Input mapping (required 2) appears with repoName/question"
    ):
        pipeline_page.select_mcp_node_tool("ask_question", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_tool_value() == "ask_question", (
            "Tool select should show 'ask_question' after selection"
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

    with allure.step("Step 9 — Fill the required Input-mapping Value fields (Type left at default Fixed)"):
        pipeline_page.fill_mcp_node_input_mapping_value("repoName", _REPO_NAME_VALUE)
        pipeline_page.fill_mcp_node_input_mapping_value("question", _QUESTION_VALUE)

        assert pipeline_page.get_mcp_node_input_mapping_value("repoName") == _REPO_NAME_VALUE
        assert pipeline_page.get_mcp_node_input_mapping_value("question") == _QUESTION_VALUE

    with allure.step("Step 10 — Set Input combobox to 'input' and Output combobox to 'messages'"):
        pipeline_page.select_mcp_node_input_variable("input", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_input_value() == "input", (
            "Input select should show 'input' after selection"
        )
        pipeline_page.select_mcp_node_output_variable("messages", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_mcp_node_output_value() == "messages", (
            "Output select should show 'messages' after selection"
        )

    with allure.step("Step 11 — Save; verify 201 + no console errors across the whole flow"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
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
        assert pipeline_page.get_mcp_node_toolkit_value() == mcp_toolkit_name, (
            f"Toolkit should persist as {mcp_toolkit_name!r} after reload"
        )
        assert pipeline_page.get_mcp_node_tool_value() == "ask_question", (
            "Tool should persist as 'ask_question' after reload"
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
        assert pipeline_page.get_mcp_node_input_value() == "input", (
            "Input should persist as 'input' after reload"
        )
        assert pipeline_page.get_mcp_node_output_value() == "messages", (
            "Output should persist as 'messages' after reload"
        )
