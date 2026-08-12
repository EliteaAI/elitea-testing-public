"""UI test — Run Details: State Before/After per Node.

TMS: ELITEA-2452
(test-specs/pipelines/l3_run-details-state-before-after-per-node_ELITEA-2452.md)

Executes a 2-node LLM->LLM->END pipeline (LLM 1 writes to `messages`, LLM 2
writes to nothing), opens the Run Details panel (`RunStateDialog.jsx`,
reused from ELITEA-2450), selects each timeline step, expands the STATES
accordion rows, and verifies:
  - an unmodified variable (`input` at the LLM2 step) shows Before == After
  - a modified variable (`messages` at the LLM1 step) shows Before != After
  - the fullscreen/expand icon opens a second modal showing the complete,
    unclipped value, matching the row's own (truncated) value

Case-text CLARIFICATION: `input`'s Before->After transition at the FIRST
node is not caused by that node's own `input`/`output` mapping (LLM 1 never
references `input`) -- `input` is the pipeline's chat-message variable,
populated at pipeline entry concurrently with the first node's execution.
This test does not assert a causal claim about `input`'s mapping, only the
observed Before/After values.

KNOWN DEFECT (filed EliteaAI/elitea-testing-public#1271): the panel's
"Before" value at the FIRST timeline step (index 0) is hardcoded to `''`,
never the variable's actual pre-run value. This test deliberately asserts
the "unmodified -> Before=After" case at the SECOND timeline step (LLM2),
never the first, to route around the defect rather than assert it as
correct.

Testids for this feature (timeline-step-{index}, state-row-{variable},
state-value-before/after-{variable}, state-expand-before/after-{variable},
value-modal + header/close-button/content) did not exist before this case
and were added via `add-data-testid`, EliteaAI/EliteaUI@2b40e5a6.

Step 8 also asserts `messages`' After value is a genuine JSON ARRAY (not
merely non-empty/non-identical) -- this is the citation target for
ELITEA-2453's case step 8 ("MESSAGES: shows list representation"), which
cannot be exercised directly in ELITEA-2453's own structured-output
pipeline (see `EliteaAI/elitea-testing-public#1274`). Confirmed live: the
value is a `JSON.stringify`d array of stringified LangChain message
objects, e.g. `["content='...' ...", "content='...' ..."]`.
"""

import json
import logging

import allure
import pytest
from playwright.sync_api import expect

from tests.ui.pipelines.helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
PIPELINE_EXECUTION_TIMEOUT = 90_000
STABLE_DURATION_MS = 3_000


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
    "ELITEA-2452_run-details-state-before-after-per-node.md",
    "onetest-ai Test Case link",
)
def test_run_details_state_before_after_per_node(page, pipeline_with_two_llm_nodes_id):
    """Run Details STATES section shows correct per-variable Before/After per timeline step."""
    console_errors = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_1267_stepper_prop_leak(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    with allure.step(
        "Step 1 — Execute a 2-node pipeline (LLM 1 writes 'messages', LLM 2 writes nothing)"
    ):
        pipeline_page = _navigate_to_canvas(page, pipeline_with_two_llm_nodes_id)
        expect(pipeline_page.canvas_wrapper).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        initial_count = pipeline_page.get_embedded_chat_message_count()
        pipeline_page.send_message_in_embedded_chat(
            "Say hello in exactly three words.", timeout=UI_ELEMENT_TIMEOUT
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

    with allure.step("Step 2 — Open Run Details"):
        pipeline_page.open_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.run_details_panel).to_be_visible()
        assert pipeline_page.get_run_details_status() == "Completed", (
            f"Run should complete before assessing state -- got {pipeline_page.get_run_details_status()!r}"
        )

    with allure.step("Step 3 — Click the FIRST timeline step (LLM1) to select it"):
        pipeline_page.select_run_details_timeline_step(0, timeout=UI_ELEMENT_TIMEOUT)
        timeline_text = pipeline_page.get_run_details_selected_timeline_step_id()
        # Node id "LLM 1" renders WITHOUT the YAML id's space (confirmed live, ELITEA-2450).
        assert "LLM1" in timeline_text, (
            f"Timeline label should show 'LLM1' after selecting step 0, got {timeline_text!r}"
        )

    with allure.step("Step 4 — STATES section shows all pipeline state variables as expandable rows"):
        expect(pipeline_page.get_run_details_state_row_locator("input")).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.get_run_details_state_row_locator("messages")).to_be_visible(
            timeout=UI_ELEMENT_TIMEOUT
        )

    with allure.step("Step 5 — Expand the 'messages' row (starts collapsed, list index 1)"):
        pipeline_page.expand_run_details_state_row("messages", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step('Step 6 — Verify "Before" and "After" value boxes appear for messages'):
        expect(pipeline_page.get_run_details_state_value_locator("messages", "before")).to_be_visible(
            timeout=UI_ELEMENT_TIMEOUT
        )
        expect(pipeline_page.get_run_details_state_value_locator("messages", "after")).to_be_visible(
            timeout=UI_ELEMENT_TIMEOUT
        )

    with allure.step("Step 8 — Modified variable (messages @ LLM1): After differs from Before"):
        messages_before = pipeline_page.get_run_details_state_before_value("messages")
        messages_after = pipeline_page.get_run_details_state_after_value("messages")
        assert messages_before != messages_after, (
            f"'messages' is written by LLM1's output mapping -- Before/After should differ, "
            f"got identical value {messages_before!r}"
        )
        assert messages_after, "'messages' After value should be non-empty (LLM1 wrote a response into it)"

        # Shape check (ELITEA-2453 case step 8 citation target): `messages` renders
        # as a genuine JSON ARRAY, not merely a non-empty/non-identical opaque
        # string. Each element is the string repr of a LangChain message object.
        parsed_messages_after = json.loads(messages_after)
        assert isinstance(parsed_messages_after, list), (
            f"'messages' After value should render as a JSON array (list representation), "
            f"got {type(parsed_messages_after).__name__}: {messages_after!r}"
        )
        assert len(parsed_messages_after) > 0, "'messages' After value should be a non-empty array"

    with allure.step("Step 7 — Unmodified variable (input @ LLM2): Before equals After"):
        # Deliberately the SECOND timeline step, not the first -- known defect
        # #1271 makes the FIRST step's Before value always '' regardless of
        # the variable's real pre-run value (see module docstring).
        pipeline_page.select_run_details_timeline_step(1, timeout=UI_ELEMENT_TIMEOUT)
        timeline_text = pipeline_page.get_run_details_selected_timeline_step_id()
        assert "LLM2" in timeline_text, (
            f"Timeline label should show 'LLM2' after selecting step 1, got {timeline_text!r}"
        )

        pipeline_page.expand_run_details_state_row("input", timeout=UI_ELEMENT_TIMEOUT)
        input_before = pipeline_page.get_run_details_state_before_value("input")
        input_after = pipeline_page.get_run_details_state_after_value("input")
        assert input_before == input_after, (
            f"'input' is not referenced by LLM2 -- Before/After should be identical, "
            f"got Before={input_before!r} After={input_after!r}"
        )
        assert input_before, "'input' Before value should be non-empty (populated at pipeline entry)"

    with allure.step(
        "Step 9 — Fullscreen/expand icon opens a modal with the complete, unclipped value"
    ):
        # Re-select LLM1 so the 'messages' row (still expanded) shows the
        # values under test for this step.
        pipeline_page.select_run_details_timeline_step(0, timeout=UI_ELEMENT_TIMEOUT)
        row_after_value = pipeline_page.get_run_details_state_after_value("messages")

        pipeline_page.open_run_details_state_value_fullscreen(
            "messages", "after", timeout=UI_ELEMENT_TIMEOUT
        )
        expect(pipeline_page.run_details_value_modal).to_be_visible()
        modal_header_text = (pipeline_page.run_details_value_modal_header.text_content() or "").strip()
        assert "messages" in modal_header_text, (
            f"Fullscreen modal heading should show the variable name 'messages', got {modal_header_text!r}"
        )
        modal_content_text = (pipeline_page.run_details_value_modal_content.text_content() or "").strip()
        assert modal_content_text == row_after_value, (
            "Fullscreen modal content should match the (unclipped) row value exactly -- "
            f"modal={modal_content_text!r} row={row_after_value!r}"
        )

        with allure.step("Axis 2 — Closing the value modal leaves the Run Details panel open"):
            pipeline_page.close_run_details_value_modal(timeout=UI_ELEMENT_TIMEOUT)
            expect(pipeline_page.run_details_value_modal).to_have_count(0)
            expect(pipeline_page.run_details_panel).to_be_visible()

    with allure.step("Step 10 — Verify no unexpected console errors (excluding the known #1267 signature)"):
        page.remove_listener("console", _on_console)
        assert not console_errors, (
            f"Unexpected console errors during navigate->execute->select-step->expand-row->fullscreen: "
            f"{[m.text for m in console_errors]}"
        )
