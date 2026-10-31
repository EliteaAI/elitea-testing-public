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

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.agents, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

_INPUT_VARIABLE_1 = "normalized_issue"
_INPUT_VARIABLE_2 = "kb_results"
_OUTPUT_VARIABLE = "triage_summary"
_TASK_VALUE = "Triage this critical GitHub issue. Issue: {normalized_issue}"


@pytest.mark.tms("ELITEA-2038")
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
        # Adjusted (#2702, EL-7154): DEV no longer renders the terminal END node on an
        # empty canvas — it is created together with the first node added. A fresh
        # pipeline's canvas must therefore hold NO nodes at all (still exact, not weaker).
        assert pipeline_page.get_node_ids() == [], (
            "A fresh pipeline's canvas should be empty (no nodes, END included) before any node is added"
        )

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
        # EL-7159: Input/Output live in the node panel's collapsed "Advanced" section
        pipeline_page.expand_agent_node_advanced_section(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.agent_node_input_select.is_visible(), "Input select should be visible inline"
        assert pipeline_page.agent_node_output_select.is_visible(), "Output select should be visible inline"
        # Interrupt before/after toggles (and their disabled-state checks)
        # were removed from node cards (EliteaUI EL-3872; human sign-off #2541).
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

    with allure.step(
        'Step 7 (case steps 2, 3, 7) — Attach the agent: the TOOLS "+ Agent" button was removed (EL-7159); open the Agent '
        'node\'s "Agents & Pipelines" picker and select the fixture agent'
    ):
        pipeline_page.open_agent_node_picker(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.pick_agent_node_application(agent_name, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.wait_for_agent_node_agent_value(agent_name, timeout=UI_ELEMENT_TIMEOUT) == agent_name, (
            f"Agent select should show {agent_name!r} after selection"
        )
        assert pipeline_page.is_agent_node_input_mapping_section_visible(1, timeout=UI_ELEMENT_TIMEOUT), (
            "TASK input-mapping field should appear once an Agent is selected"
        )
        # EL-7159 (class A, UI drift): the picker no longer auto-persists on select; the attachment
        # is written on Save (asserted in Step 11 via the same application_relation endpoint).
        pipeline_page.close_node_panel(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        "Step 4 — Verify the agent appears attached in TOOLS as a flat-list card (no 'sub-tab' — "
        "same root cause as EliteaAI/elitea-testing-public#1149/#530)"
    ):
        pipeline_page.ensure_toolkits_section_visible(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.is_toolkit_attached(agent_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"TOOLS section should show a card for the attached agent {agent_name!r}"
        )
        assert not console_errors, f"Attaching the agent should not introduce console errors: {console_errors}"

    with allure.step("Step 8 — Set Input combobox — add 'normalized_issue', 'kb_results'"):
        pipeline_page.expand_agent_node_advanced_section(timeout=UI_ELEMENT_TIMEOUT)
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
        # EL-7159: the agent attach is persisted by Save (PATCH application_relation 201 + pipeline PUT 201).
        # Endpoint regression guard retained: /application_relation/, not /tool/.
        save_response = pipeline_page.save_and_wait_for_attach(
            "/application_relation/prompt_lib/", project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted relation payload (PATCH 201)"
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
        # EL-7159: the node panel is closed after a reload; reopen it (Input/Output sit in Advanced)
        pipeline_page.expand_agent_node_advanced_section(timeout=UI_ELEMENT_TIMEOUT)
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
