"""UI test — Pipeline Code Node: Configuration and Persistence.

TMS: ELITEA-2009
(test-specs/pipelines/l2_pipeline-code-node-configuration_ELITEA-2009.md)

Adds a Code node to a pipeline, configures its CODE section (Type + Value),
Input, and Output, saves, and confirms every field survives a full page
reload.

Step 0 is added ahead of the case's own step 1 (AFS Preconditions/Test Data
clarification): the case's Test Data table implies the Output variable
"result" is directly selectable, but live behavior requires it to exist as a
custom pipeline state variable first — the Output combobox (like Input) only
lists EXISTING state variables (`OutputSelect.jsx`/`InputSelect.jsx` share
the same `useInputOptions()` hook), it is not a freeform/creatable field.
Filed as a case-text CLARIFICATION, not a defect — same pattern already
documented for the Decision node's Input select (ELITEA-2034).
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

_CODE_VALUE = "import json\nresult = input.upper()"
_OUTPUT_VARIABLE = "result"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2009_configure-code-node.md",
    "onetest-ai Test Case link",
)
def test_code_node_configuration_and_persistence(page, pipeline_id):
    """Configure a Code node's CODE/Input/Output fields; verify they persist through Save + reload."""
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 0 so console errors from every step (state
    # setup, node add, field entry, save, reload) are captured — AFS
    # Expected Results require "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step(
        "Step 0 (setup) — create the 'result' custom state variable via the STATE "
        "panel, so it's selectable in the Code node's Output combobox later"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step (?viewMode=owner already included)

        pipeline_page.open_state_panel(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.add_state_variable(_OUTPUT_VARIABLE, timeout=UI_ELEMENT_TIMEOUT)
        # Close the drawer — it overlaps the canvas and would intercept the
        # Code node's own inline field clicks in later steps (same gotcha
        # already documented for the Decision/Router node AFSes).
        pipeline_page.close_state_panel(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 1 — Add a Code node via canvas '+' button -> 'Code'"):
        node_count_before = pipeline_page.get_node_count()
        pipeline_page.add_node("Code")
        code_node_id = pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)
        assert code_node_id, "Code node should appear on canvas with a non-empty data-id"
        assert pipeline_page.get_node_count() == node_count_before + 1, (
            "Node count should increase by exactly 1 after adding the Code node"
        )

    with allure.step(
        "Step 2 — 'Click on Code node to open configuration panel' is trivially satisfied: "
        "config renders inline on the canvas card, no click-to-open action exists"
    ):
        assert pipeline_page.code_node_type_select.is_visible(), "CODE Type select should be visible inline"
        assert pipeline_page.code_node_value.is_visible(), "CODE Value field should be visible inline"

    with allure.step(
        "Step 3 — Verify panel shows: CODE (Type+Value), Input, Output, "
        "Interrupt before/after, Structured output"
    ):
        assert pipeline_page.code_node_type_select.is_visible(), "CODE Type select should be present"
        assert pipeline_page.code_node_value.is_visible(), "CODE Value field should be present"
        assert pipeline_page.code_node_input_select.is_visible(), "Input select should be present"
        assert pipeline_page.code_node_output_select.is_visible(), "Output select should be present"
        assert pipeline_page.is_node_interrupt_before_toggle_visible(code_node_id), (
            "Interrupt before switch should be present"
        )
        assert pipeline_page.code_node_interrupt_after_toggle.is_visible(), (
            "Interrupt after switch should be present"
        )
        assert pipeline_page.code_node_structured_output_toggle.is_visible(), (
            "Structured output switch should be present"
        )

    with allure.step(
        "Step 4 — In CODE section: set Type to 'Fixed', enter Value with Python code"
    ):
        # Type already defaults to "Fixed" on a freshly-added node — asserted
        # anyway (AFS Axis 2) to guard a future default-value regression.
        assert pipeline_page.get_code_node_type() == "Fixed", "CODE Type should default to 'Fixed'"
        pipeline_page.select_code_node_type("Fixed", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_code_node_type() == "Fixed", "CODE Type should read 'Fixed' after selecting it"

        pipeline_page.fill_code_node_value(_CODE_VALUE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_code_node_value() == _CODE_VALUE, (
            "CODE Value field should hold the entered Python code exactly"
        )

    with allure.step('Step 5 — Set Input combobox — add variable "input"'):
        pipeline_page.select_code_node_input_variable("input", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_code_node_input_value() == "input", (
            "Input select should show 'input' as the selected chip"
        )

    with allure.step('Step 6 — Set Output combobox — add variable "result"'):
        pipeline_page.select_code_node_output_variable(_OUTPUT_VARIABLE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_code_node_output_value() == _OUTPUT_VARIABLE, (
            "Output select should show 'result' as the selected chip"
        )

    with allure.step("Step 7 — Save the pipeline; verify no console errors and a 201 Created response"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 8 — Reload via the canonical URL; CODE Type, Value, Input, and Output all persist"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_code_node_type() == "Fixed", "CODE Type should persist as 'Fixed' after reload"
        assert pipeline_page.get_code_node_value() == _CODE_VALUE, (
            "CODE Value should persist exactly after reload"
        )
        assert pipeline_page.get_code_node_input_value() == "input", (
            "Input should persist as 'input' after reload"
        )
        assert pipeline_page.get_code_node_output_value() == _OUTPUT_VARIABLE, (
            "Output should persist as 'result' after reload"
        )
        assert not console_errors, f"Reload should not introduce console errors: {console_errors}"
