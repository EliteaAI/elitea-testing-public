"""UI test — Pipeline with Toolkit Node: config + Input mapping.

TMS: ELITEA-2010
(test-specs/pipelines/l2_toolkit-node-config-and-input-mapping_ELITEA-2010.md)

Attaches a GitHub toolkit (with settings.selected_tools explicitly set —
see the AFS Preconditions/Test Data CLARIFICATION on why the case's named
"SDConfluence" toolkit isn't used) to a fresh pipeline, adds a Toolkit node,
verifies the Tool select + INPUT MAPPING sections are absent until a Toolkit
is chosen (a real two-stage progressive-disclosure precondition, not a
rendering defect), selects a Tool, fills its required Input-mapping
parameter, sets the tool-agnostic Input/Output state-variable selects, saves,
and confirms everything persists through a full page reload.
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
    pytest.mark.p1,
    pytest.mark.regression,
]

UI_ELEMENT_TIMEOUT = 10_000
TOOLKIT_POPPER_TIMEOUT = 20_000  # the popper's toolkit list can take several
# seconds to resolve past "Loading..." on this environment (~30 pre-existing
# toolkits) — a 15s explicit wait was needed this session per the AFS timing
# note; 20s gives headroom.
SAVE_RESPONSE_TIMEOUT = 15_000

_SEARCH_QUERY_PARAM = "search_query"  # raw schema key behind the "SEARCH
# QUERY" display label (confirmed via GET .../elitea_core/toolkits/
# prompt_lib/{project}: github.properties.selected_tools.args_schemas.
# search_issues.properties — required: ["search_query"], display title
# "Search Query"; optional siblings are "repo_name"/"max_count", matching
# the AFS's MAX COUNT / REPO NAME).
_SEARCH_QUERY_VALUE = "{input} error"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2010_toolkit-node-config-and-input-mapping.md",
    "onetest-ai Test Case link",
)
def test_toolkit_node_config_and_input_mapping(page, pipeline_id, github_toolkit_with_selected_tools):
    """Attach a toolkit, configure a Toolkit node's Tool + Input mapping; verify persistence."""
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

    with allure.step('Step 2 — Attach the toolkit via TOOLS "+ Toolkit"; verify it appears'):
        popper = pipeline_page.open_toolkit_popper(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.select_toolkit_in_popper(popper, toolkit_name, timeout=TOOLKIT_POPPER_TIMEOUT)
        assert pipeline_page.is_toolkit_attached(toolkit_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"Toolkit {toolkit_name!r} should appear as a card in the TOOLS section"
        )

    with allure.step('Step 3 — Add a Toolkit node via the canvas "+" menu; verify it appears'):
        pipeline_page.add_node("Toolkit")
        node_id = pipeline_page.wait_for_node_on_canvas("toolkit", timeout=UI_ELEMENT_TIMEOUT)
        assert node_id, "Toolkit node should be present on the canvas with a non-empty data-id"

    with allure.step(
        "Step 4 — Base fields render inline; Tool select + INPUT MAPPING are absent before a Toolkit is chosen"
    ):
        assert pipeline_page.toolkit_node_toolkit_select.is_visible(), (
            "Toolkit node's Toolkit select should be visible inline on the canvas card — "
            "no separate click-to-open action needed (live product simplification, "
            "see AFS Coverage Map row 3)"
        )
        assert pipeline_page.toolkit_node_input_select.is_visible(), "Input select should be visible inline"
        assert pipeline_page.toolkit_node_output_select.is_visible(), "Output select should be visible inline"
        # Interrupt before/after + Structured output — added to close a gap
        # the first implementation left unasserted despite the case's own
        # step 3 naming them and the AFS Coverage Map claiming full coverage
        # (fix-round finding). Both are unconditional on the Toolkit node
        # (ToolkitNode.jsx passes showStructuredOutput; CommonInterruptSettings.jsx).
        assert pipeline_page.is_node_interrupt_before_toggle_visible(node_id), (
            "Interrupt before toggle should be visible inline"
        )
        assert pipeline_page.toolkit_node_interrupt_after_toggle.is_visible(), (
            "Interrupt after toggle should be visible inline"
        )
        assert pipeline_page.toolkit_node_structured_output_toggle.is_visible(), (
            "Structured output toggle should be visible inline"
        )
        # Negative/absence assertions (AFS Axis 2) — the case's literal
        # step-3 wording implies Tool/INPUT MAPPING are part of the initial
        # reveal; live product only renders them once a Toolkit (then Tool)
        # is actually selected. Asserting absence here turns the two-stage
        # reveal into a test-enforced contract instead of a documented
        # assumption (.agents/testing.md § canon #277 discipline).
        assert not pipeline_page.is_toolkit_node_tool_select_visible(timeout=2000), (
            "Tool select should NOT be rendered before a Toolkit is selected"
        )
        assert not pipeline_page.is_toolkit_node_input_mapping_section_visible(1, timeout=2000), (
            "INPUT MAPPING (required N) should NOT be rendered before a Toolkit is selected"
        )

    with allure.step("Step 5 — Select the attached toolkit; Toolkit combobox shows its name"):
        pipeline_page.select_toolkit_node_toolkit(toolkit_name, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_toolkit_node_toolkit_value() == toolkit_name, (
            f"Toolkit select should show {toolkit_name!r} after selection"
        )

    with allure.step(
        "Step 6 — Select 'search_issues' Tool; INPUT MAPPING (required 1) appears with SEARCH QUERY"
    ):
        pipeline_page.select_toolkit_node_tool("search_issues", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_toolkit_node_tool_value() == "search_issues", (
            "Tool select should show 'search_issues' after selection"
        )
        assert pipeline_page.is_toolkit_node_input_mapping_section_visible(1, timeout=UI_ELEMENT_TIMEOUT), (
            "'Input mapping (required 1)' section should appear for search_issues's "
            "1 required parameter (search_query)"
        )
        # The now-expanded node's INPUT MAPPING row can land directly under
        # ReactFlow's own pinned bottom-left canvas controls (live-confirmed:
        # a coordinate-based click on the SEARCH QUERY Type select silently
        # landed on the canvas's "Fit View" button instead). Fit View clears
        # the overlap before Step 7 touches that row.
        pipeline_page.fit_canvas_view(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 7 — INPUT MAPPING (required): set SEARCH QUERY Type to F-String, fill Value"):
        pipeline_page.select_toolkit_node_input_mapping_type(
            _SEARCH_QUERY_PARAM, "F-String", timeout=UI_ELEMENT_TIMEOUT
        )
        assert pipeline_page.get_toolkit_node_input_mapping_type(_SEARCH_QUERY_PARAM) == "F-String", (
            "SEARCH QUERY Type select should show 'F-String' after selection"
        )
        pipeline_page.fill_toolkit_node_input_mapping_value(_SEARCH_QUERY_PARAM, _SEARCH_QUERY_VALUE)
        assert pipeline_page.get_toolkit_node_input_mapping_value(_SEARCH_QUERY_PARAM) == _SEARCH_QUERY_VALUE, (
            "SEARCH QUERY Value field should reflect the typed f-string text"
        )

    with allure.step("Step 8 — Set Input combobox to 'input' and Output combobox to 'messages'"):
        pipeline_page.select_toolkit_node_input_variable("input", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_toolkit_node_input_value() == "input", (
            "Input select should show 'input' after selection"
        )
        pipeline_page.select_toolkit_node_output_variable("messages", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_toolkit_node_output_value() == "messages", (
            "Output select should show 'messages' after selection"
        )

    with allure.step("Step 9 — Save; verify 201 + no console errors + no failed requests"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"No console errors expected at any step: {console_errors}"
        assert not failed_requests, f"No failed network requests expected at any step: {failed_requests}"

    with allure.step(
        "Step 10 — Reload via the canonical URL; Toolkit/Tool/SEARCH QUERY mapping/Input/Output persisted"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("toolkit", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_toolkit_node_toolkit_value() == toolkit_name, (
            f"Toolkit should persist as {toolkit_name!r} after reload"
        )
        assert pipeline_page.get_toolkit_node_tool_value() == "search_issues", (
            "Tool should persist as 'search_issues' after reload"
        )
        assert pipeline_page.is_toolkit_node_input_mapping_section_visible(1, timeout=UI_ELEMENT_TIMEOUT), (
            "Input mapping (required 1) section should still be present after reload"
        )
        assert pipeline_page.get_toolkit_node_input_mapping_value(_SEARCH_QUERY_PARAM) == _SEARCH_QUERY_VALUE, (
            "SEARCH QUERY Input-mapping value should persist through reload"
        )
        # Axis 2 addition (AFS): the case only names Toolkit/Tool/QUERY
        # mapping in its Expected Final State — also assert Input/Output
        # survive, matching the same regression class already flagged for
        # the sibling LLM-node case (ELITEA-2004 AFS).
        assert pipeline_page.get_toolkit_node_input_value() == "input", (
            "Input should persist as 'input' after reload"
        )
        assert pipeline_page.get_toolkit_node_output_value() == "messages", (
            "Output should persist as 'messages' after reload"
        )
