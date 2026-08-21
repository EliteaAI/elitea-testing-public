"""UI test — Run Details: Open Panel After Execution.

TMS: ELITEA-2450
(test-specs/pipelines/l3_run-details-open-panel-after-execution_ELITEA-2450.md)

Executes a pipeline via the embedded chat, clicks the run indicator that
appears above the Flow canvas (a `RunStateNode`, NOT inside the embedded
chat's own message list — case-text CLARIFICATION, filed as
`EliteaAI/elitea-testing-public#1268`) to open the Run Details panel
(`RunStateDialog.jsx`), and verifies the panel's header, "Completed" status
badge, delete/close icon buttons, Timeline step section, and States section.

Case-text CLARIFICATION (also #1268): the case's "Expand/fullscreen button"
step refers to the header's second icon button, which is actually a Close
button (`CollapseIcon`) — the dialog is already sized responsively the
moment it opens, so there is no separate expand/fullscreen toggle in the
header. The genuine per-state-value expand/fullscreen controls live inside
the States section instead (out of this case's assertion depth).

Testids for the Run Details feature (run node label, panel root, header,
status badge + `data-status`, delete/close buttons, timeline/states
sections) did not exist before this case and were added via
`add-data-testid`, EliteaAI/EliteaUI@fb66d978.
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from tests.ui.pipelines.helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
PIPELINE_EXECUTION_TIMEOUT = 90_000
STABLE_DURATION_MS = 3_000


def _is_known_1267_stepper_prop_leak(msg) -> bool:
    """Filter the Run Details panel's Timeline Stepper prop-leak warning.

    Filed as EliteaAI/elitea-testing-public#1267 — sibling of #611 (same
    root-cause class: `RunStateDialog.jsx`'s `ProcessConnector` spreads
    MUI Stepper-injected booleans like `last`/`active`/`completed` onto a
    raw DOM `<div>` via `StepConnector`'s `{...rest}`), different
    component/screen so not a duplicate. Matches on the STABLE React
    warning text alone (`.agents/testing.md` merge-gate discipline —
    same technique as `test_agent_publish_unpublish_version.py`'s
    `_is_known_defect_611`), not a location/stack-trace string that may
    not always be present in the captured console message.
    """
    return "non-boolean attribute" in msg.text


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2450_run-details-open-panel-after-execution.md",
    "onetest-ai Test Case link",
)
def test_run_details_panel_opens_after_execution(page, pipeline_with_llm_id):
    """Run Details panel opens after execution and shows header/status/controls/sections."""
    console_errors = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_1267_stepper_prop_leak(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    with allure.step("Step 1 — Navigate to a pipeline with a runnable LLM node in Flow view"):
        pipeline_page = _navigate_to_canvas(page, pipeline_with_llm_id)
        expect(pipeline_page.canvas_wrapper).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 2 — Send a message in the embedded chat and wait for the run to complete"):
        initial_count = pipeline_page.get_embedded_chat_message_count()
        pipeline_page.send_message_in_embedded_chat(
            "What is 2 + 2? Reply with just the number.", timeout=UI_ELEMENT_TIMEOUT
        )
        pipeline_page.wait_for_embedded_chat_response(
            initial_count=initial_count,
            stable_duration_ms=STABLE_DURATION_MS,
            timeout=PIPELINE_EXECUTION_TIMEOUT,
        )
        expect(pipeline_page.run_node_label).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step('Step 3 — Click the run\'s label to open the Run Details panel'):
        pipeline_page.open_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.run_details_panel).to_be_visible()

    with allure.step('Step 4 — Verify the panel header reads "Run N details"'):
        header_text = pipeline_page.get_run_details_header_text()
        assert header_text == "Run 1 details", f"Expected header 'Run 1 details', got {header_text!r}"

    with allure.step('Step 5 — Verify a "Completed" green status badge appears next to the header'):
        expect(pipeline_page.run_details_status_badge).to_be_visible()
        assert pipeline_page.get_run_details_status() == "Completed", (
            f"Expected data-status='Completed', got {pipeline_page.get_run_details_status()!r}"
        )
        assert pipeline_page.get_run_details_status_badge_text() == "Completed", (
            f"Expected status badge text 'Completed', got {pipeline_page.get_run_details_status_badge_text()!r}"
        )

    with allure.step("Step 6 — Verify a trash (delete) icon button is present in the panel header"):
        expect(pipeline_page.run_details_delete_button).to_be_visible()

    with allure.step(
        "Step 7 — Verify the header's second icon button (Close) is present "
        "(case's 'expand/fullscreen' wording is stale — see docstring CLARIFICATION)"
    ):
        expect(pipeline_page.run_details_close_button).to_be_visible()

    with allure.step("Step 8 — Verify the panel contains a TIMELINE STEP section and a STATES section"):
        timeline_text = pipeline_page.get_run_details_timeline_section_text()
        assert "Timeline step:" in timeline_text, (
            f"Timeline section should contain 'Timeline step:', got {timeline_text!r}"
        )
        # The timeline's node-id value renders WITHOUT the YAML id's space
        # ("LLM 1" -> "LLM1") — confirmed live; AFS Step 8 documents the
        # same rendering.
        assert "LLM1" in timeline_text, f"Timeline section should show the run node id 'LLM1', got {timeline_text!r}"

        states_text = pipeline_page.get_run_details_states_section_text()
        assert "States" in states_text, f"States section should contain 'States' heading, got {states_text!r}"
        assert "input" in states_text, f"States section should show the 'input' state variable, got {states_text!r}"
        assert "messages" in states_text, (
            f"States section should show the 'messages' state variable, got {states_text!r}"
        )

    with allure.step("Step 9 — Close button actually closes the dialog (Axis 2 extra observable)"):
        pipeline_page.close_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.run_details_panel).to_have_count(0)

    with allure.step("Step 10 — Verify no unexpected console errors (excluding the known #1267 signature)"):
        page.remove_listener("console", _on_console)
        assert not console_errors, (
            f"Unexpected console errors during navigate->execute->open-panel: "
            f"{[m.text for m in console_errors]}"
        )
