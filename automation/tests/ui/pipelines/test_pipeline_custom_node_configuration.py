"""UI test — Pipeline: Custom Node Configuration.

TMS: ELITEA-2036
(test-specs/pipelines/l2_pipeline-custom-node-configuration_ELITEA-2036.md)

Attaches a GitHub toolkit (with settings.selected_tools explicitly set —
same precondition the Toolkit-node case ELITEA-2010 already documents: a
toolkit with no selected_tools renders a Custom node with no Tool select
and no Input mapping at all) to a fresh pipeline, adds a Custom node,
verifies the Tool select + INPUT MAPPING sections are absent until a
Toolkit is chosen, selects a Tool, fills its required Input-mapping
parameter (Type + Value), sets the tool-agnostic Input/Output
state-variable selects, saves, and confirms everything persists through a
full page reload — including the node's raw-JSON editor view of its own
configuration.
"""

import logging

import pytest
import allure

from pages.pipeline_detail_page import PipelineDetailPage
from config import settings

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.pipelines,
    pytest.mark.toolkits,
    pytest.mark.p2,
    pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
TOOLKIT_POPPER_TIMEOUT = 20_000  # the popper's toolkit list can take several
# seconds to resolve past "Loading..." on this environment (same timing note
# already documented for the Toolkit-node case, ELITEA-2010 AFS).
SAVE_RESPONSE_TIMEOUT = 15_000

_SEARCH_QUERY_PARAM = "search_query"  # raw schema key behind the "SEARCH
# QUERY" display label (github's search_issues tool — same tool/param the
# sibling Toolkit-node case ELITEA-2010 uses).
_SEARCH_QUERY_VALUE = "{input} error"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2036_pipeline-custom-node-configuration.md",
    "onetest-ai Test Case link",
)
def test_custom_node_configuration(page, pipeline_id, github_toolkit_with_selected_tools):
    """Add a Custom node, configure Toolkit/Tool/Input-mapping/Input/Output; verify persistence."""
    toolkit_name = github_toolkit_with_selected_tools["name"]
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors / failed requests from every
    # step are captured — AFS Expected Results require "zero console errors,
    # zero failed network requests, at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
    failed_requests = []
    page.on("response", lambda resp: failed_requests.append(resp) if resp.status >= 400 else None)

    with allure.step("Step 1 — Navigate to the pipeline; verify configuration panel + canvas load"):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step — a bare
        # /pipelines/all/{id} URL (no query params) 404s (ELITEA-1954 AFS
        # Known Defects); reloading THIS captured URL avoids that.
        assert pipeline_page.configuration_tab.is_visible(), (
            "Configuration panel (General section) should be visible after navigating"
        )

    with allure.step('Step 1b — Attach the toolkit via TOOLS "+ Toolkit"; verify it appears'):
        # The case text doesn't spell out this precondition, but live
        # behavior requires it: a Custom node's Toolkit select only offers
        # toolkits already attached in TOOLS, and its Tool select / Input
        # mapping only render once a Toolkit with selected_tools is chosen
        # (same two-stage reveal already documented for the Toolkit node).
        popper = pipeline_page.open_toolkit_popper(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.select_toolkit_in_popper(popper, toolkit_name, timeout=TOOLKIT_POPPER_TIMEOUT)
        assert pipeline_page.is_toolkit_attached(toolkit_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"Toolkit {toolkit_name!r} should appear as a card in the TOOLS section"
        )

    with allure.step('Step 1 — Add a Custom node via the canvas "+" menu; verify it appears'):
        pipeline_page.add_node("Custom")
        node_id = pipeline_page.wait_for_node_on_canvas("custom", timeout=UI_ELEMENT_TIMEOUT)
        assert node_id, "Custom node should be present on the canvas with a non-empty data-id"

    with allure.step(
        "Step 2 — Examine config panel structure: base fields render inline; "
        "Tool select + INPUT MAPPING are absent before a Toolkit is chosen"
    ):
        assert pipeline_page.custom_node_toolkit_select.is_visible(), (
            "Custom node's Toolkit select should be visible inline on the canvas card — "
            "no separate click-to-open action needed (same always-expanded pattern as "
            "every other pipeline node type)"
        )
        assert pipeline_page.custom_node_input_select.is_visible(), "Input select should be visible inline"
        assert pipeline_page.custom_node_output_select.is_visible(), "Output select should be visible inline"
        assert pipeline_page.is_node_interrupt_before_toggle_visible(node_id), (
            "Interrupt before toggle should be visible inline"
        )
        assert pipeline_page.custom_node_interrupt_after_toggle.is_visible(), (
            "Interrupt after toggle should be visible inline"
        )
        assert pipeline_page.custom_node_structured_output_toggle.is_visible(), (
            "Structured output toggle should be visible inline"
        )
        assert pipeline_page.custom_node_json_editor_content.is_visible(), (
            "The node's raw-JSON editor view should be visible inline"
        )
        # Negative/absence assertions — the case's step 3 wording implies
        # Type+Value input-mapping fields are simply "configured"; live
        # product only renders them once a Toolkit (then Tool) is actually
        # selected — same two-stage reveal already test-enforced for the
        # Toolkit node (ELITEA-2010).
        assert not pipeline_page.is_custom_node_tool_select_visible(timeout=2000), (
            "Tool select should NOT be rendered before a Toolkit is selected"
        )
        assert not pipeline_page.is_custom_node_input_mapping_section_visible(1, timeout=2000), (
            "INPUT MAPPING (required N) should NOT be rendered before a Toolkit is selected"
        )

    with allure.step("Step 3a — Select the attached toolkit; Toolkit combobox shows its name"):
        pipeline_page.select_custom_node_toolkit(toolkit_name, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_custom_node_toolkit_value() == toolkit_name, (
            f"Toolkit select should show {toolkit_name!r} after selection"
        )

    with allure.step(
        "Step 3b — Select 'search_issues' Tool; INPUT MAPPING (required 1) appears with SEARCH QUERY"
    ):
        pipeline_page.select_custom_node_tool("search_issues", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_custom_node_tool_value() == "search_issues", (
            "Tool select should show 'search_issues' after selection"
        )
        assert pipeline_page.is_custom_node_input_mapping_section_visible(1, timeout=UI_ELEMENT_TIMEOUT), (
            "'Input mapping (required 1)' section should appear for search_issues's "
            "1 required parameter (search_query)"
        )
        assert pipeline_page.is_custom_node_input_mapping_optional_section_visible(2, timeout=UI_ELEMENT_TIMEOUT), (
            "'Input mapping (optional 2)' section should appear for search_issues's "
            "2 optional parameters (max_count, repo_name)"
        )
        # The now-expanded node's INPUT MAPPING row can land under ReactFlow's
        # own pinned canvas controls — same overlap already documented (and
        # worked around) for the Toolkit node's identical layout.
        pipeline_page.fit_canvas_view(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 3c — INPUT MAPPING (required): set SEARCH QUERY Type to F-String, fill Value"):
        pipeline_page.select_custom_node_input_mapping_type(
            _SEARCH_QUERY_PARAM, "F-String", timeout=UI_ELEMENT_TIMEOUT
        )
        assert pipeline_page.get_custom_node_input_mapping_type(_SEARCH_QUERY_PARAM) == "F-String", (
            "SEARCH QUERY Type select should show 'F-String' after selection"
        )
        pipeline_page.fill_custom_node_input_mapping_value(_SEARCH_QUERY_PARAM, _SEARCH_QUERY_VALUE)
        assert pipeline_page.get_custom_node_input_mapping_value(_SEARCH_QUERY_PARAM) == _SEARCH_QUERY_VALUE, (
            "SEARCH QUERY Value field should reflect the typed f-string text"
        )

    with allure.step("Step 4 — Set Input combobox to 'input' and Output combobox to 'messages'"):
        pipeline_page.select_custom_node_input_variable("input", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_custom_node_input_value() == "input", (
            "Input select should show 'input' after selection"
        )
        pipeline_page.select_custom_node_output_variable("messages", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_custom_node_output_value() == "messages", (
            "Output select should show 'messages' after selection"
        )

    with allure.step("Step 5 — Save; verify 201 + no console errors + no failed requests"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"No console errors expected at any step: {console_errors}"
        assert not failed_requests, f"No failed network requests expected at any step: {failed_requests}"

    with allure.step(
        "Step 6 — Reload via the canonical URL; Toolkit/Tool/SEARCH QUERY mapping/Input/Output/"
        "raw-JSON view all persisted"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("custom", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_custom_node_toolkit_value() == toolkit_name, (
            f"Toolkit should persist as {toolkit_name!r} after reload"
        )
        assert pipeline_page.get_custom_node_tool_value() == "search_issues", (
            "Tool should persist as 'search_issues' after reload"
        )
        assert pipeline_page.is_custom_node_input_mapping_section_visible(1, timeout=UI_ELEMENT_TIMEOUT), (
            "Input mapping (required 1) section should still be present after reload"
        )
        assert pipeline_page.get_custom_node_input_mapping_value(_SEARCH_QUERY_PARAM) == _SEARCH_QUERY_VALUE, (
            "SEARCH QUERY Input-mapping value should persist through reload"
        )
        assert pipeline_page.get_custom_node_input_value() == "input", (
            "Input should persist as 'input' after reload"
        )
        assert pipeline_page.get_custom_node_output_value() == "messages", (
            "Output should persist as 'messages' after reload"
        )
        # Axis 2 addition: the Custom node's own raw-JSON editor renders the
        # SAME persisted state as its structured fields above — a regression
        # where the two views drift (structured fields show one value, the
        # JSON view another) would otherwise go undetected. This is unique
        # to the Custom node among this suite's node types.
        json_text = pipeline_page.get_custom_node_json_editor_text(timeout=UI_ELEMENT_TIMEOUT)
        assert '"tool": "search_issues"' in json_text, (
            f"Raw-JSON editor should reflect the persisted tool selection, got: {json_text}"
        )
        assert _SEARCH_QUERY_VALUE in json_text, (
            f"Raw-JSON editor should reflect the persisted input_mapping value, got: {json_text}"
        )
