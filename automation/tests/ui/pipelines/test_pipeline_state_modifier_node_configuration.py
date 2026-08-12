"""UI test — Pipeline State Modifier Node: Configuration and Persistence.

TMS: ELITEA-2035
(test-specs/pipelines/l2_pipeline-state-modifier-node-configuration_ELITEA-2035.md)

Adds a State modifier node to a pipeline, configures its Jinja Template,
Input, and Output fields, saves, and confirms every field survives a full
page reload.

Step 0 is added ahead of the case's own step 1 (AFS Preconditions/Test Data
clarification): the case's Test Data table implies the Input/Output
variables "issue_details"/"normalized_issue" are directly selectable, but
live behavior requires them to exist as custom pipeline state variables
first — the Input/Output combos only list EXISTING state variables (same
`useInputOptions()` hook already documented for the Code/Decision nodes),
they are not freeform/creatable fields. Filed as a case-text CLARIFICATION,
not a defect.

Step 4 ("Expand 'Variables to clean' section") is also a case-text
CLARIFICATION: live-confirmed the field is a plain multi-select combobox
identical in shape to Input/Output, NOT an expandable/accordion section —
this test asserts presence + dropdown-openability instead.
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

_TEMPLATE_VALUE = "## GitHub Issue\n\n{{ issue_details }}"
_INPUT_VARIABLE = "issue_details"
_OUTPUT_VARIABLE = "normalized_issue"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2035_pipeline-state-modifier-node-configuration.md",
    "onetest-ai Test Case link",
)
def test_state_modifier_node_configuration_and_persistence(page, pipeline_id):
    """Configure a State modifier node's Jinja Template/Input/Output; verify they persist through Save + reload."""
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 0 so console errors from every step (state
    # setup, node add, field entry, save, reload) are captured — AFS
    # Expected Results require "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step(
        "Step 0 (setup) — create the 'issue_details'/'normalized_issue' custom state "
        "variables via the STATE panel, so they're selectable in the State modifier "
        "node's Input/Output combos later"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step (?viewMode=owner already included)

        pipeline_page.open_state_panel(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.add_state_variable(_INPUT_VARIABLE, timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.add_state_variable(_OUTPUT_VARIABLE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_state_variable_name_text(_INPUT_VARIABLE, timeout=UI_ELEMENT_TIMEOUT) == (
            _INPUT_VARIABLE
        ), "STATE panel should list 'issue_details' as a custom state variable after it's added"
        assert pipeline_page.get_state_variable_name_text(_OUTPUT_VARIABLE, timeout=UI_ELEMENT_TIMEOUT) == (
            _OUTPUT_VARIABLE
        ), "STATE panel should list 'normalized_issue' as a custom state variable after it's added"
        # Close the drawer — it overlaps the canvas and would intercept the
        # State modifier node's own inline field clicks in later steps
        # (same gotcha already documented for the Decision/Router/Code node AFSes).
        pipeline_page.close_state_panel(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 1 — Add a State modifier node via canvas '+' button -> 'State modifier'"):
        node_count_before = pipeline_page.get_node_count()
        pipeline_page.add_node("State modifier")
        state_modifier_node_id = pipeline_page.wait_for_node_on_canvas("state_modifier", timeout=UI_ELEMENT_TIMEOUT)
        assert state_modifier_node_id, "State modifier node should appear on canvas with a non-empty data-id"
        assert pipeline_page.get_node_count() == node_count_before + 1, (
            "Node count should increase by exactly 1 after adding the State modifier node"
        )

    with allure.step(
        "Step 2 — 'Verify State modifier node panel shows' is checked inline: config renders "
        "directly on the canvas card, no click-to-open action exists"
    ):
        assert pipeline_page.state_modifier_node_template.is_visible(), "Jinja Template field should be visible inline"
        assert pipeline_page.state_modifier_node_variables_to_clean_select.is_visible(), (
            "Variables to clean field should be visible inline"
        )
        assert pipeline_page.state_modifier_node_input_select.is_visible(), "Input select should be visible inline"
        assert pipeline_page.state_modifier_node_output_select.is_visible(), "Output select should be visible inline"

    with allure.step('Step 3 — In "Jinja Template" field enter the classification template'):
        pipeline_page.fill_state_modifier_node_template(_TEMPLATE_VALUE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_state_modifier_node_template() == _TEMPLATE_VALUE, (
            "Jinja Template field should hold the entered value exactly"
        )

    with allure.step(
        "Step 4 — 'Expand Variables to clean section (if applicable)': CLARIFICATION — "
        "live-confirmed this is a plain multi-select combobox (same component as Input/Output), "
        "not an expandable/accordion section; asserted as present + openable as a dropdown instead"
    ):
        assert pipeline_page.state_modifier_node_variables_to_clean_select.is_visible(), (
            "Variables to clean field should be present"
        )
        pipeline_page.open_state_modifier_node_variables_to_clean_select(timeout=UI_ELEMENT_TIMEOUT)
        page.keyboard.press("Escape")

    with allure.step('Step 5 — Set Input combobox — add variable "issue_details"'):
        pipeline_page.select_state_modifier_node_input_variable(_INPUT_VARIABLE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_state_modifier_node_input_value() == _INPUT_VARIABLE, (
            "Input select should show 'issue_details' as the selected chip"
        )

    with allure.step('Step 6 — Set Output combobox — add variable "normalized_issue"'):
        pipeline_page.select_state_modifier_node_output_variable(_OUTPUT_VARIABLE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_state_modifier_node_output_value() == _OUTPUT_VARIABLE, (
            "Output select should show 'normalized_issue' as the selected chip"
        )

    with allure.step("Step 7 — Save the pipeline; verify no console errors and a 201 Created response"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 8 — Reload via the canonical URL; Jinja Template, Input, and Output all persist"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("state_modifier", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_state_modifier_node_template() == _TEMPLATE_VALUE, (
            "Jinja Template should persist exactly after reload"
        )
        assert pipeline_page.get_state_modifier_node_input_value() == _INPUT_VARIABLE, (
            "Input should persist as 'issue_details' after reload"
        )
        assert pipeline_page.get_state_modifier_node_output_value() == _OUTPUT_VARIABLE, (
            "Output should persist as 'normalized_issue' after reload"
        )
        assert not console_errors, f"Reload should not introduce console errors: {console_errors}"
