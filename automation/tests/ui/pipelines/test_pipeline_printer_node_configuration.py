"""UI test — Pipeline Printer Node: Configuration and Persistence.

TMS: ELITEA-2039
(test-specs/pipelines/l2_pipeline-printer-node-configuration_ELITEA-2039.md)

Adds a Printer node to a pipeline, configures its PRINTER section (Type +
Value) and Final Message field, saves, and confirms every field survives a
full page reload. Also confirms the Printer node renders no Input/Output
state-variable comboboxes (unlike Code/LLM/State-modifier) — only the two
generic ReactFlow connection handles.
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

_PRINTER_VALUE = "## GitHub Issue Triage Complete\\n\\n{triage_summary}"
_FINAL_MESSAGE = "Type 'ok' to end"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2039_pipeline-printer-node-configuration.md",
    "onetest-ai Test Case link",
)
def test_printer_node_configuration_and_persistence(page, pipeline_id):
    """Configure a Printer node's PRINTER/Final Message fields; verify they persist through Save + reload."""
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from every step (node add,
    # field entry, save, reload) are captured — AFS Expected Results require
    # "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    pipeline_page.navigate(pipeline_id)
    pipeline_page.wait_for_canvas()
    canonical_url = page.url  # captured for the reload step (?viewMode=owner already included)

    with allure.step("Step 1 — Add a Printer node via canvas '+' button -> 'Printer'"):
        node_count_before = pipeline_page.get_node_count()
        pipeline_page.add_node("Printer")
        printer_node_id = pipeline_page.wait_for_node_on_canvas("printer", timeout=UI_ELEMENT_TIMEOUT)
        assert printer_node_id, "Printer node should appear on canvas with a non-empty data-id"
        assert pipeline_page.get_node_count() == node_count_before + 1, (
            "Node count should increase by exactly 1 after adding the Printer node"
        )

    with allure.step(
        "Step 2 — Verify Printer node panel shows: PRINTER section (Type + Value), "
        "Final Message field, Output handle at bottom"
    ):
        assert pipeline_page.printer_node_type_select.is_visible(), "PRINTER Type select should be visible inline"
        assert pipeline_page.printer_node_value.is_visible(), "PRINTER Value field should be visible inline"
        assert pipeline_page.printer_node_final_message_input.is_visible(), (
            "Final Message field should be visible inline"
        )
        handle_count = pipeline_page.get_node_handle_count(printer_node_id)
        assert handle_count == 2, (
            f"Printer node should expose exactly 2 ReactFlow connection handles "
            f"(target + source), got {handle_count}"
        )

    with allure.step('Step 3 — In PRINTER section: set Type dropdown to "F-String"'):
        # Type already defaults to "Fixed" on a freshly-added node — asserted
        # anyway (AFS Axis 2) to guard a future default-value regression.
        assert pipeline_page.get_printer_node_type() == "Fixed", "PRINTER Type should default to 'Fixed'"
        pipeline_page.select_printer_node_type("F-String", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_printer_node_type() == "F-String", (
            "PRINTER Type should read 'F-String' after selecting it"
        )

    with allure.step("Step 4 — Set Value field with the f-string test data"):
        pipeline_page.fill_printer_node_value(_PRINTER_VALUE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_printer_node_value() == _PRINTER_VALUE, (
            "PRINTER Value field should hold the entered f-string exactly"
        )

    with allure.step('Step 5 — Set "Final Message" field'):
        pipeline_page.fill_printer_node_final_message(_FINAL_MESSAGE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_printer_node_final_message() == _FINAL_MESSAGE, (
            "Final Message field should hold the entered text exactly"
        )

    with allure.step("Step 6 — Save the pipeline; verify no console errors and a 201 Created response"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 7 — Reload via the canonical URL; PRINTER Type, Value, and Final Message all persist"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("printer", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_printer_node_type() == "F-String", (
            "PRINTER Type should persist as 'F-String' after reload"
        )
        assert pipeline_page.get_printer_node_value() == _PRINTER_VALUE, (
            "PRINTER Value should persist exactly after reload"
        )
        assert pipeline_page.get_printer_node_final_message() == _FINAL_MESSAGE, (
            "Final Message should persist exactly after reload"
        )
        assert not console_errors, f"Reload should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 8 — Note: Printer node has only Output handle (no Input combobox visible in panel)"
    ):
        assert pipeline_page.printer_node_input_select.count() == 0, (
            "Printer node should render zero Input state-variable comboboxes"
        )
        assert pipeline_page.printer_node_output_select.count() == 0, (
            "Printer node should render zero Output state-variable comboboxes"
        )
        handle_count_after_reload = pipeline_page.get_node_handle_count(printer_node_id)
        assert handle_count_after_reload == 2, (
            "Printer node should still expose exactly 2 connection handles (incl. Output) after reload"
        )
