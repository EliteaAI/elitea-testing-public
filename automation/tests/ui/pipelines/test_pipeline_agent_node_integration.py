"""UI test — Pipeline Agent node integration: attach -> add node -> configure -> persist.

TMS: ELITEA-2038
(test-specs/pipelines/l2_pipeline-agent-node-integration_ELITEA-2038.md)

On a fresh, empty pipeline (no nodes/edges pre-seeded): attaches an agent via
the TOOLS section's "+ Agent" button, adds a fresh Agent node via the canvas
"Add node" menu, verifies the node's static config fields render immediately
(and that no "Structured output" toggle ever renders for this node type)
while the INPUT MAPPING accordion stays absent until an Agent is chosen,
selects the Agent, fills the TASK Input-mapping value, sets the
tool-agnostic Input/Output state-variable selects, saves, and confirms
everything persists through a full page reload.

Step 0 is added ahead of the case's own step 1 (AFS Preconditions
clarification, same pattern as the sibling Code/State-modifier/Custom/MCP
node cases in this family): the case's Test Data table implies the Input/
Output variables "normalized_issue"/"kb_results"/"triage_summary" are
directly selectable, but live behavior requires them to exist as custom
pipeline state variables first.

Step 10's "set Type to F-String" is also a case-text CLARIFICATION:
live-confirmed the TASK field's Type default is already "F-String" (unlike
every sibling node's Fixed-by-default tool parameters) — this test asserts
the value rather than performing a state-changing selection.
"""

import logging

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.agents, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

_INPUT_VARIABLE_1 = "normalized_issue"
_INPUT_VARIABLE_2 = "kb_results"
_OUTPUT_VARIABLE = "triage_summary"
_TASK_VALUE = "Triage this critical GitHub issue. Issue: {normalized_issue}"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2038_pipeline-agent-node-integration.md",
    "onetest-ai Test Case link",
)
def test_agent_node_fresh_attach(page, pipeline_id, agent_id, agent_api):
    """Fresh-attach an Agent, add + configure an Agent node, save, verify reload persistence."""
    agent_name = agent_api.get_agent(agent_id)["name"]
    project_id = str(settings.elitea_project_id)

    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 0 so console errors from every step (state
    # setup, attach, node add, dropdown opens, save, reload) are captured —
    # AFS Expected Results require "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step(
        "Step 0 (setup) — create the 'normalized_issue'/'kb_results'/'triage_summary' custom state "
        "variables via the STATE panel, so they're selectable in the Agent node's Input/Output combos later"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step — a bare /pipelines/all/{id}
        # URL (no query params) 404s (ELITEA-1954 AFS Known Defects)

        pipeline_page.open_state_panel(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.add_state_variable(_INPUT_VARIABLE_1, timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.add_state_variable(_INPUT_VARIABLE_2, timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.add_state_variable(_OUTPUT_VARIABLE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_state_variable_name_text(_INPUT_VARIABLE_1, timeout=UI_ELEMENT_TIMEOUT) == (
            _INPUT_VARIABLE_1
        ), "STATE panel should list 'normalized_issue' as a custom state variable after it's added"
        assert pipeline_page.get_state_variable_name_text(_INPUT_VARIABLE_2, timeout=UI_ELEMENT_TIMEOUT) == (
            _INPUT_VARIABLE_2
        ), "STATE panel should list 'kb_results' as a custom state variable after it's added"
        assert pipeline_page.get_state_variable_name_text(_OUTPUT_VARIABLE, timeout=UI_ELEMENT_TIMEOUT) == (
            _OUTPUT_VARIABLE
        ), "STATE panel should list 'triage_summary' as a custom state variable after it's added"
        # Close the drawer — it overlaps the canvas and would intercept the
        # Agent node's own inline field clicks in later steps (same gotcha
        # documented for the sibling Decision/Router/Code/State-modifier node AFSes).
        pipeline_page.close_state_panel(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_node_ids() == ["END"], (
            "A fresh pipeline's canvas should show only the END node before any node is added"
        )

    with allure.step('Step 2 — Click TOOLS "+ Agent"; select the fixture agent from the popper'):
        popper = pipeline_page.open_agent_popper(timeout=UI_ELEMENT_TIMEOUT)
        assert popper.is_visible(), "'+ Agent' popper should open"

        # Regression guard: the Agent picker auto-persists via a DIFFERENT
        # endpoint from the sibling Toolkit/MCP pickers
        # (/application_relation/prompt_lib/, not /tool/prompt_lib/) —
        # select_agent_in_popper() hard-blocks on that specific PATCH-201
        # response before returning, so a future regression that reverts to
        # the wrong endpoint (or stops persisting on select) times out this
        # step instead of silently passing.
        attach_response = pipeline_page.select_agent_in_popper(
            popper, agent_name, project_id, timeout=UI_ELEMENT_TIMEOUT
        )
        assert attach_response is not None, (
            "Agent attach should return the persisted relation payload from the immediate "
            "PATCH .../application_relation/prompt_lib/{project}/{agent_id}/{version_id} 201 response"
        )
        page.keyboard.press("Escape")

    with allure.step(
        "Step 4 — Verify the agent appears attached in TOOLS as a flat-list card (no 'sub-tab' — "
        "same root cause as EliteaAI/elitea-testing-public#1149/#530)"
    ):
        assert pipeline_page.is_toolkit_attached(agent_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"TOOLS section should show a card for the attached agent {agent_name!r}"
        )
        assert not console_errors, f"Attaching the agent should not introduce console errors: {console_errors}"

    with allure.step('Step 5 — Click "Add node" -> "Agent"; a fresh Agent node appears'):
        pipeline_page.add_node("Agent", timeout=UI_ELEMENT_TIMEOUT)
        agent_node_id = pipeline_page.wait_for_node_on_canvas("agent", timeout=UI_ELEMENT_TIMEOUT)
        assert agent_node_id, "Agent node should be present on the canvas with a non-empty data-id"

    with allure.step(
        "Step 6 — Static config fields present immediately (before any Agent is selected); "
        "INPUT MAPPING is absent, and NO Structured output toggle exists for this node type"
    ):
        assert pipeline_page.entry_point_trigger_select.is_visible(), (
            "Entry-point Trigger select ('Chat Message') should be visible — the fresh Agent node "
            "is the pipeline's only node, so it auto-becomes the entry point"
        )
        assert pipeline_page.agent_node_agent_select.is_visible(), (
            "Agent node's Agent select should be visible inline on the canvas card"
        )
        assert pipeline_page.agent_node_input_select.is_visible(), "Input select should be visible inline"
        assert pipeline_page.agent_node_output_select.is_visible(), "Output select should be visible inline"
        assert pipeline_page.is_node_interrupt_before_toggle_visible(agent_node_id), (
            "Interrupt before toggle should be visible inline"
        )
        assert pipeline_page.agent_node_interrupt_after_toggle.is_visible(), (
            "Interrupt after toggle should be visible inline"
        )
        # Disabled-state assertions (AFS step 6 — confirmed live): Interrupt
        # before is disabled because this node is the entry point
        # (CommonInterruptSettings.jsx entry_point === id gating); Interrupt
        # after is disabled because the node's default transition is END.
        assert pipeline_page.is_node_interrupt_before_toggle_disabled(agent_node_id), (
            "Interrupt before should be disabled — this node is the pipeline's entry point"
        )
        assert pipeline_page.agent_node_interrupt_after_toggle.is_disabled(), (
            "Interrupt after should be disabled — the node's default transition is END"
        )
        # Negative/absence assertions (AFS Axis 2) — a naive implementation
        # might only assert presence-after-configuration and silently skip
        # the pre-Agent-select empty state.
        assert not pipeline_page.is_agent_node_input_mapping_section_visible(1, timeout=2000), (
            "INPUT MAPPING (required 1) should NOT be rendered before an Agent is selected"
        )
        # Note: AgentNode.jsx never renders a "Structured output" toggle at
        # all (showStructuredOutput=false, confirmed via source + live DOM,
        # AFS step 6) — there is deliberately no testid for it (wiring one
        # would be an unreferenced, unrenderable field), so this is
        # documented rather than asserted in-test: no compliant testid-only
        # locator exists to check its absence against.

    with allure.step("Step 7 — Select the attached agent from the Agent dropdown"):
        pipeline_page.select_agent_node_agent(agent_name, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_agent_node_agent_value(timeout=UI_ELEMENT_TIMEOUT) == agent_name, (
            f"Agent select should show {agent_name!r} after selection"
        )
        assert pipeline_page.is_agent_node_input_mapping_section_visible(1, timeout=UI_ELEMENT_TIMEOUT), (
            "'Input mapping (required 1)' section should appear once an Agent is selected"
        )

    with allure.step("Step 8 — Set Input combobox — add 'normalized_issue', 'kb_results'"):
        pipeline_page.select_agent_node_input_variable(_INPUT_VARIABLE_1, timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.select_agent_node_input_variable(_INPUT_VARIABLE_2, timeout=UI_ELEMENT_TIMEOUT)
        input_value = pipeline_page.get_agent_node_input_value()
        assert _INPUT_VARIABLE_1 in input_value and _INPUT_VARIABLE_2 in input_value, (
            f"Input select should show both {_INPUT_VARIABLE_1!r} and {_INPUT_VARIABLE_2!r}, got {input_value!r}"
        )

    with allure.step("Step 9 — Set Output combobox — add 'triage_summary'"):
        pipeline_page.select_agent_node_output_variable(_OUTPUT_VARIABLE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_agent_node_output_value() == _OUTPUT_VARIABLE, (
            f"Output select should show {_OUTPUT_VARIABLE!r} after selection"
        )

    with allure.step(
        "Step 10 — TASK: verify Type is 'F-String' (already the default — CLARIFICATION, not an "
        "action), fill Value"
    ):
        assert pipeline_page.get_agent_node_input_mapping_type() == "F-String", (
            "TASK Input-mapping Type should be 'F-String' — this is the field's live DEFAULT "
            "(unlike sibling nodes' tool parameters, which default to 'Fixed'), not a value the "
            "test has to select"
        )
        pipeline_page.fill_agent_node_input_mapping_value(_TASK_VALUE)
        assert pipeline_page.get_agent_node_input_mapping_value() == _TASK_VALUE, (
            "TASK Value field should reflect the typed text"
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
        pipeline_page.wait_for_node_on_canvas("agent", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.is_toolkit_attached(agent_name, timeout=UI_ELEMENT_TIMEOUT), (
            "TOOLS section should still show the attached agent card after reload"
        )
        assert pipeline_page.get_agent_node_agent_value(timeout=UI_ELEMENT_TIMEOUT) == agent_name, (
            f"Agent should persist as {agent_name!r} after reload"
        )
        input_value_after_reload = pipeline_page.get_agent_node_input_value()
        assert _INPUT_VARIABLE_1 in input_value_after_reload and _INPUT_VARIABLE_2 in input_value_after_reload, (
            f"Input should persist as both {_INPUT_VARIABLE_1!r} and {_INPUT_VARIABLE_2!r} after reload, "
            f"got {input_value_after_reload!r}"
        )
        assert pipeline_page.get_agent_node_output_value() == _OUTPUT_VARIABLE, (
            f"Output should persist as {_OUTPUT_VARIABLE!r} after reload"
        )
        assert pipeline_page.is_agent_node_input_mapping_section_visible(1, timeout=UI_ELEMENT_TIMEOUT), (
            "Input mapping (required 1) section should still be present after reload"
        )
        assert pipeline_page.get_agent_node_input_mapping_type() == "F-String", (
            "TASK Type should persist as 'F-String' after reload"
        )
        assert pipeline_page.get_agent_node_input_mapping_value() == _TASK_VALUE, (
            "TASK Value should persist after reload"
        )
        # The console listener registered before Step 0 stays attached across
        # page.goto() (same Page object, navigation doesn't unsubscribe
        # listeners) — but the test previously never re-checked the list
        # after the reload, so an error introduced only by the reload/
        # hydration path (e.g. a rehydration crash reading the persisted
        # node config) would silently escape detection. Re-assert here.
        assert not console_errors, f"Reload should not introduce console errors: {console_errors}"
