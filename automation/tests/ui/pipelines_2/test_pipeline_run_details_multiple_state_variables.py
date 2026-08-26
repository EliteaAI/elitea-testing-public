"""UI test — Run Details: Multiple State Variables of Different Types.

TMS: ELITEA-2453
(test-specs/pipelines/l3_run-details-multiple-state-variables-different-types_ELITEA-2453.md)

Executes a single-node LLM pipeline with `structured_output: true` that
writes 4 CUSTOM state variables of 4 distinct types (`custom_text`/str,
`custom_num`/number, `custom_list`/list, `custom_json`/dict), opens the Run
Details panel (`RunStateDialog.jsx`, reused from ELITEA-2450/2452), and
verifies:
  - all 4 custom-variable rows appear in the STATES section
  - each row is individually expandable, independent of the others
  - each row's After value renders per its OWN type's `JSON.stringify`
    representation (quoted string / bare number / bracketed array / braced
    object)

Case-text CLARIFICATION: the case's step 5 wording ("displayed uppercase")
describes a CSS `text-transform: uppercase` applied by `BasicAccordion.jsx`,
NOT the row's DOM text content, which is the raw lowercase variable name
(confirmed live via `getComputedStyle`). This test asserts presence via the
raw-lowercase testid/text and the CSS property, never the uppercase text.

Case steps 7 (INPUT string rendering) and 8 (MESSAGES list rendering) are
NOT re-verified here -- both are already covered by
`test_pipeline_run_details_state_before_after.py` (ELITEA-2452) via the SAME
`StateItemView` rendering path. Combining `messages` with `dict`/`list`-typed
custom variables in a `structured_output: true` node's `output` mapping is a
CONFIRMED product defect (`EliteaAI/elitea-testing-public#1274`); this test's
fixture deliberately excludes `messages` from `output` to route around it
(see `pipeline_with_typed_state_vars_id`). Step 8's "list representation" is
asserted by a real shape check (`isinstance(json.loads(after_value), list)`)
in that spec's Step 8 block, not merely by visibility/non-emptiness.

Zero new testids -- every handle this case touches (STATE panel, LLM node
Output-select/structured-output-toggle, Run Details panel/timeline/state-row/
value-box) already exists on `automation/testids`, reused unmodified from
ELITEA-2042/2450/2452.
"""

import json
import logging

import allure
import pytest
from playwright.sync_api import expect

from tests.ui.pipeline_helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
PIPELINE_EXECUTION_TIMEOUT = 90_000
STABLE_DURATION_MS = 3_000

_CUSTOM_VARIABLES = ["custom_text", "custom_num", "custom_list", "custom_json"]


def _is_known_1267_stepper_prop_leak(msg) -> bool:
    """Filter the Run Details panel's Timeline Stepper prop-leak warning.

    Same known, filed defect as `test_pipeline_run_details_panel.py`'s
    `_is_known_1267_stepper_prop_leak` (`EliteaAI/elitea-testing-public#1267`)
    -- this test opens the same `RunStateDialog.jsx` panel.
    """
    return "non-boolean attribute" in msg.text


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2453_run-details-multiple-state-variables-of-different-types.md",
    "onetest-ai Test Case link",
)
def test_run_details_multiple_state_variables_different_types(page, pipeline_with_typed_state_vars_id):
    """Run Details STATES section renders 4 typed custom variables, each independently expandable."""
    console_errors = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_1267_stepper_prop_leak(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    with allure.step(
        "Step 1-3 — Execute the single-node structured-output pipeline "
        "(4 typed custom variables, no 'messages' in output -- see Known Defects)"
    ):
        pipeline_page = _navigate_to_canvas(page, pipeline_with_typed_state_vars_id)
        expect(pipeline_page.canvas_wrapper).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        initial_count = pipeline_page.get_embedded_chat_message_count()
        pipeline_page.send_message_in_embedded_chat(
            "Please populate the state variables now.", timeout=UI_ELEMENT_TIMEOUT
        )
        pipeline_page.wait_for_embedded_chat_response(
            initial_count=initial_count,
            stable_duration_ms=STABLE_DURATION_MS,
            timeout=PIPELINE_EXECUTION_TIMEOUT,
        )
        expect(pipeline_page.run_node_label).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_embedded_chat_message_count() > initial_count, (
            "Embedded chat should show at least one new message after the run completes"
        )

    with allure.step("Step 4 — Open Run Details, node step is selected"):
        pipeline_page.open_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.run_details_panel).to_be_visible()
        assert pipeline_page.get_run_details_status() == "Completed", (
            f"Run should complete before assessing state -- got {pipeline_page.get_run_details_status()!r}"
        )
        timeline_text = pipeline_page.get_run_details_selected_timeline_step_id()
        # Node id "LLM 1" renders WITHOUT the YAML id's space (confirmed live, ELITEA-2450);
        # the default-selected step on open is the LAST step (confirmed, ELITEA-2452).
        assert "LLM1" in timeline_text, (
            f"Timeline label should show 'LLM1' on open, got {timeline_text!r}"
        )

    with allure.step(
        "Step 5 — All 4 custom-variable rows appear in the STATES section "
        "(visible 'uppercase' is a CSS text-transform on the label; the row's own "
        "DOM text content is the raw lowercase variable name -- see module docstring)"
    ):
        for variable in _CUSTOM_VARIABLES:
            row = pipeline_page.get_run_details_state_row_locator(variable)
            expect(row).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert (row.text_content() or "").strip() == variable, (
                f"Row testid text content should be the raw variable name {variable!r}"
            )

    with allure.step("Step 6, 13 — Expand each variable; each expands independently"):
        # custom_text (list index 0) is auto-expanded on open (accordion's
        # `defaultExpanded={!index}`) -- clicking it again would COLLAPSE it
        # (MUI accordion click toggles). Only the remaining 3 need a click.
        for variable in _CUSTOM_VARIABLES[1:]:
            pipeline_page.expand_run_details_state_row(variable, timeout=UI_ELEMENT_TIMEOUT)

        # All 4 remain visibly expanded simultaneously -- a non-exclusive
        # accordion, not a single-open one (confirmed live).
        for variable in _CUSTOM_VARIABLES:
            expect(
                pipeline_page.get_run_details_state_value_locator(variable, "after")
            ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 9 — CUSTOM_TEXT (str): After value renders as a JSON-quoted string"):
        custom_text_after = pipeline_page.get_run_details_state_after_value("custom_text")
        assert custom_text_after.startswith('"') and custom_text_after.endswith('"'), (
            f"'custom_text' (str) After value should be JSON-string-quoted, got {custom_text_after!r}"
        )
        assert custom_text_after != '""', "'custom_text' After value should be non-empty"

    with allure.step("Step 10 — CUSTOM_NUM (number): After value renders as a bare JSON number"):
        custom_num_after = pipeline_page.get_run_details_state_after_value("custom_num")
        parsed_num = json.loads(custom_num_after)
        assert isinstance(parsed_num, (int, float)), (
            f"'custom_num' (number) After value should parse as a JSON number, got {custom_num_after!r}"
        )
        assert not (custom_num_after.startswith('"') and custom_num_after.endswith('"')), (
            f"'custom_num' After value should NOT be quoted like 'custom_text', got {custom_num_after!r}"
        )

    with allure.step("Step 11 — CUSTOM_LIST (list): After value renders as a bracketed JSON array"):
        custom_list_after = pipeline_page.get_run_details_state_after_value("custom_list")
        parsed_list = json.loads(custom_list_after)
        assert isinstance(parsed_list, list), (
            f"'custom_list' (list) After value should parse as a JSON array, got {custom_list_after!r}"
        )
        assert len(parsed_list) > 0, "'custom_list' After value should be a non-empty array"

    with allure.step("Step 12 — CUSTOM_JSON (dict): After value renders as a braced JSON object"):
        custom_json_after = pipeline_page.get_run_details_state_after_value("custom_json")
        parsed_json = json.loads(custom_json_after)
        assert isinstance(parsed_json, dict), (
            f"'custom_json' (Json) After value should parse as a JSON object, got {custom_json_after!r}"
        )
        assert len(parsed_json) > 0, "'custom_json' After value should be a non-empty object"

    with allure.step("Axis 2 — Verify no unexpected console errors (excluding the known #1267 signature)"):
        page.remove_listener("console", _on_console)
        assert not console_errors, (
            f"Unexpected console errors during navigate->execute->open-panel->expand-rows: "
            f"{[m.text for m in console_errors]}"
        )
