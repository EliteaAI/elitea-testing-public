"""UI test — Pipeline HITL Node: Configuration and Router Mapping.

TMS: ELITEA-2014
(test-specs/pipelines/l2_hitl-node-configuration-and-router-mapping_ELITEA-2014.md)

Adds a Human-in-the-loop node to a pipeline (alongside LLM/Printer nodes that
serve as router-mapping targets), configures Input, USER MESSAGE (Type+Value),
EDIT STATE KEY, and ROUTER MAPPING (APPROVE/EDIT/REJECT), saves, and confirms
every field survives a full page reload.

Step ordering matches the AFS, NOT the original case text, plus one further
implementer-discovered reordering (documented in the AFS's step-ordering note):

- EDIT STATE KEY (AFS step 5) is set before the ROUTER MAPPING EDIT route
  (AFS step 6) because the live product gates the EDIT route select on EDIT
  STATE KEY having a value (confirmed via `aria-disabled`) — case-text drift,
  filed as EliteaAI/elitea-testing-public#1104 (clarification, not a defect).
- USER MESSAGE Type must be set to F-String BEFORE the Input combobox (AFS
  step 3) can be interacted with — the Input select is `disabled` whenever
  Type != 'fstring' (confirmed via `HITLNode.jsx`'s
  `isInputSelectDisabledByMessageType` and the select's own tooltip: "Available
  only when the User message type is set to F-String"). This test therefore
  sets USER MESSAGE Type first, then the Input combobox, reversing the AFS's
  own step 3/4 order — a technique-level correction (same class as the
  EDIT-route gating above), not a scope change.
"""

import logging

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

_USER_MESSAGE_VALUE = "Please review this response before continuing."


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2014_pipeline-hitl-node-configuration-and-router-mapping.md",
    "onetest-ai Test Case link",
)
def test_hitl_node_configuration_and_router_mapping(page, pipeline_id):
    """Configure a HITL node's fields; verify they persist through Save + reload."""
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from every step (node add,
    # dropdown opens, field entry, save, reload) are captured — AFS Expected
    # Results require "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step(
        "Step 1 — Create a pipeline and add a Human-in-the-loop node via canvas '+' button"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step (?viewMode=owner already included)

        # AFS Preconditions: the pipeline needs other nodes to serve as HITL
        # route targets. Added via the UI per AFS Cleanup/Automation Hints
        # (add_node(), not a hand-built API topology) — not part of the
        # case's own step-1 assertion (that's the HITL node count delta below).
        pipeline_page.add_node("LLM")
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.add_node("Printer")
        pipeline_page.wait_for_node_on_canvas("printer", timeout=UI_ELEMENT_TIMEOUT)
        node_count_before_hitl = pipeline_page.get_node_count()

        pipeline_page.add_node("Human-in-the-loop")
        hitl_node_id = pipeline_page.wait_for_node_on_canvas("hitl", timeout=UI_ELEMENT_TIMEOUT)
        assert hitl_node_id, "HITL node should appear on canvas with a non-empty data-id"
        assert pipeline_page.get_node_count() == node_count_before_hitl + 1, (
            "Node count should increase by exactly 1 after adding the HITL node"
        )

    with allure.step(
        "Step 2 — HITL node config renders inline on the canvas card (no click-to-open action)"
    ):
        # Live product simplification (AFS Coverage Map row 2): there is no
        # separate panel to open — every listed section is always inline.
        assert pipeline_page.hitl_node_input_select.is_visible(), "Input select should be visible inline"
        assert pipeline_page.hitl_node_user_message_type_select.is_visible(), (
            "USER MESSAGE Type select should be visible inline"
        )
        assert pipeline_page.hitl_node_user_message_value_input.is_visible(), (
            "USER MESSAGE Value field should be visible inline"
        )
        assert pipeline_page.hitl_node_router_mapping_section.is_visible(), (
            "ROUTER MAPPING accordion should be visible inline"
        )
        assert pipeline_page.hitl_node_edit_state_key_select.is_visible(), (
            "EDIT STATE KEY select should be visible inline"
        )

    with allure.step(
        "Step 3 (reordered — see module docstring) — In USER MESSAGE: set Type "
        "= F-String, which enables the Input combobox"
    ):
        pipeline_page.select_hitl_node_user_message_type("fstring", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_hitl_node_user_message_type_display() == "F-String", (
            "USER MESSAGE Type should show 'F-String' after selection"
        )

    with allure.step(
        "Step 4 (reordered) — Set Input combobox with a state variable; "
        "complete USER MESSAGE Value"
    ):
        pipeline_page.select_hitl_node_input_variable("input", timeout=UI_ELEMENT_TIMEOUT)
        assert "input" in pipeline_page.get_hitl_node_input_display_text(), (
            "Input select should show 'input' as a selected chip"
        )
        pipeline_page.fill_hitl_node_user_message_value(_USER_MESSAGE_VALUE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_hitl_node_user_message_value() == _USER_MESSAGE_VALUE, (
            "USER MESSAGE Value field should show the entered text"
        )

    with allure.step(
        "Step 5 — Set EDIT STATE KEY; verify the EDIT route select flips from "
        "aria-disabled to enabled (live product gating — case-text drift, see AFS)"
    ):
        assert pipeline_page.is_hitl_node_route_select_disabled("edit", timeout=UI_ELEMENT_TIMEOUT), (
            "EDIT route select should be aria-disabled before EDIT STATE KEY has a value"
        )
        pipeline_page.select_hitl_node_edit_state_key("input", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_hitl_node_edit_state_key_value() == "input", (
            "EDIT STATE KEY Value select should show 'input' after selection"
        )
        assert not pipeline_page.is_hitl_node_route_select_disabled("edit", timeout=UI_ELEMENT_TIMEOUT), (
            "EDIT route select should become enabled once EDIT STATE KEY has a value"
        )

    with allure.step(
        "Step 6 — In ROUTER MAPPING: set APPROVE/EDIT/REJECT targets; "
        "EDIT options exclude END"
    ):
        edit_options = pipeline_page.get_hitl_node_route_option_names("edit", timeout=UI_ELEMENT_TIMEOUT)
        assert "END" not in edit_options, (
            "EDIT route options should exclude END — an edit loop can't target the terminal node"
        )
        assert set(edit_options) == {"LLM 1", "Printer 1"}, (
            f"EDIT route options should be exactly the other non-END nodes, got {edit_options!r}"
        )

        pipeline_page.select_hitl_node_route("approve", "Printer 1", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.select_hitl_node_route("edit", "LLM 1", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.select_hitl_node_route("reject", "END", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_hitl_node_route_value("approve") == "Printer 1", (
            "APPROVE route should show 'Printer 1' after selection"
        )
        assert pipeline_page.get_hitl_node_route_value("edit") == "LLM 1", (
            "EDIT route should show 'LLM 1' after selection"
        )
        assert pipeline_page.get_hitl_node_route_value("reject") == "END", (
            "REJECT route should show 'END' after selection"
        )

    with allure.step("Step 7 — Save the pipeline; verify no console errors and a 2xx response"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 8 — Reload via the canonical URL; USER MESSAGE, all 3 routes, and "
        "EDIT STATE KEY persist"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("hitl", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_hitl_node_user_message_type_display() == "F-String", (
            "USER MESSAGE Type should persist as 'F-String' after reload"
        )
        assert pipeline_page.get_hitl_node_user_message_value() == _USER_MESSAGE_VALUE, (
            "USER MESSAGE Value should persist after reload"
        )
        assert pipeline_page.get_hitl_node_route_value("approve") == "Printer 1", (
            "APPROVE route should persist as 'Printer 1' after reload"
        )
        assert pipeline_page.get_hitl_node_route_value("edit") == "LLM 1", (
            "EDIT route should persist as 'LLM 1' after reload"
        )
        assert pipeline_page.get_hitl_node_route_value("reject") == "END", (
            "REJECT route should persist as 'END' after reload"
        )
        assert pipeline_page.get_hitl_node_edit_state_key_value() == "input", (
            "EDIT STATE KEY should persist as 'input' after reload"
        )
        assert not console_errors, f"Reload should not introduce console errors: {console_errors}"
