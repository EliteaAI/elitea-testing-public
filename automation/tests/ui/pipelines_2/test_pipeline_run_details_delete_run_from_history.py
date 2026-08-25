"""UI test — Run Details: Delete Run from History.

TMS: ELITEA-2454
(test-specs/pipelines/l2_run-details-delete-run-from-history_ELITEA-2454.md)

Executes a pipeline 3 times via the embedded chat to accumulate 3 runs in
the on-canvas run-node stack (`RunStateNodeGroup.jsx` — the SAME feature
covered by ELITEA-2450/2451/2452/2453, NOT the embedded chat's separate
"view run history" panel). Opens the history toggle, opens a specific run's
Run Details panel, deletes it, and verifies the deleted run's label is gone
while the other runs' labels/content are unaffected.

Live-confirmed mechanics (see the AFS "Live-Confirmed Mechanics" section for
full detail):
  - Client-side only (`useRunEvent.hooks.js`'s `pipelineRunNodes` state) —
    no persistence, no REST endpoint.
  - Only the newest run renders its `pipeline-run-node-label` directly; all
    older runs live inside a closed-by-default MUI `Menu` that unmounts
    entirely while closed — the history toggle must be opened FIRST before
    counting/asserting run labels.
  - Delete has NO confirmation dialog — clicking the delete button removes
    the run and closes the panel immediately.
  - When only 1 run remains, the history toggle AND the menu disappear from
    the DOM entirely (not just visually collapsed).

Testid for the history-toggle (clock icon) did not exist before this case
and was added via `add-data-testid`, EliteaAI/EliteaUI@89282f5e. Every other
handle this case touches was already added by ELITEA-2450
(EliteaAI/EliteaUI@fb66d978).
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


def _run_pipeline_and_wait(pipeline_page, message: str):
    """Send one message via the embedded chat and wait for its run to complete."""
    initial_count = pipeline_page.get_embedded_chat_message_count()
    pipeline_page.send_message_in_embedded_chat(message, timeout=UI_ELEMENT_TIMEOUT)
    pipeline_page.wait_for_embedded_chat_response(
        initial_count=initial_count,
        stable_duration_ms=STABLE_DURATION_MS,
        timeout=PIPELINE_EXECUTION_TIMEOUT,
    )


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2454_run-details-delete-run-from-history.md",
    "onetest-ai Test Case link",
)
def test_run_details_delete_run_from_history(page, pipeline_with_llm_id):
    """Deleting a run from history removes only that run; others stay intact."""
    with allure.step("Step 1 — Execute a pipeline 3 times to accumulate multiple runs in history"):
        pipeline_page = _navigate_to_canvas(page, pipeline_with_llm_id)
        expect(pipeline_page.canvas_wrapper).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        _run_pipeline_and_wait(pipeline_page, "Hello run 1. Reply with just OK.")
        _run_pipeline_and_wait(pipeline_page, "Hello run 2. Reply with just OK.")
        _run_pipeline_and_wait(pipeline_page, "Hello run 3. Reply with just OK.")
        expect(pipeline_page.run_node_label).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        chat_message_count_before_delete = pipeline_page.get_embedded_chat_message_count()

    with allure.step('Step 2 — Open Run Details for one run, note the run number ("Run 2 details")'):
        pipeline_page.open_run_node_history(timeout=UI_ELEMENT_TIMEOUT)
        labels_before_delete = set(pipeline_page.get_run_history_labels())
        assert labels_before_delete == {"Run 1 details", "Run 2 details", "Run 3 details"}, (
            f"Expected 3 runs in history before deleting, got {labels_before_delete!r}"
        )

        pipeline_page.open_run_details_by_label("Run 3 details", timeout=UI_ELEMENT_TIMEOUT)
        header_text = pipeline_page.get_run_details_header_text()
        assert header_text == "Run 3 details", f"Expected header 'Run 3 details', got {header_text!r}"

    with allure.step("Step 3 — Click the trash/delete icon button in the Run Details header"):
        expect(pipeline_page.run_details_delete_button).to_be_visible()

    with allure.step(
        "Step 4 — Confirm deletion if prompted (confirmed live: no confirmation dialog exists; "
        "the panel closes immediately)"
    ):
        pipeline_page.delete_current_run_details(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.run_details_panel).to_have_count(0)

    with allure.step("Step 5 — Verify the run is removed from run history"):
        pipeline_page.open_run_node_history(timeout=UI_ELEMENT_TIMEOUT)
        labels_after_delete = set(pipeline_page.get_run_history_labels())
        assert "Run 3 details" not in labels_after_delete, (
            f"Deleted run 'Run 3 details' should no longer appear in history, got {labels_after_delete!r}"
        )

    with allure.step("Step 6 — Verify other runs remain unaffected"):
        assert labels_after_delete == {"Run 1 details", "Run 2 details"}, (
            f"Expected the 2 surviving runs unaffected, got {labels_after_delete!r}"
        )

        pipeline_page.open_run_details_by_label("Run 1 details", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_run_details_header_text() == "Run 1 details"
        assert pipeline_page.get_run_details_status() == "Completed"
        pipeline_page.close_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)

        pipeline_page.open_run_node_history(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.open_run_details_by_label("Run 2 details", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_run_details_header_text() == "Run 2 details"
        assert pipeline_page.get_run_details_status() == "Completed"
        pipeline_page.close_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)

        # Axis 2 extra observable — deleting a run must not touch the embedded
        # chat's own message list (guards a coupling regression between chat
        # history and run-node state).
        assert pipeline_page.get_embedded_chat_message_count() == chat_message_count_before_delete, (
            "Deleting a run from history should not change the embedded chat message count"
        )

    with allure.step("Step 7 — Re-open run history — verify the deleted run no longer appears"):
        pipeline_page.open_run_node_history(timeout=UI_ELEMENT_TIMEOUT)
        labels_reopened = set(pipeline_page.get_run_history_labels())
        assert labels_reopened == {"Run 1 details", "Run 2 details"}, (
            f"Deleted run should still be absent on re-open, got {labels_reopened!r}"
        )

        # Axis 2 extra observable — delete a second run so the group drops to
        # 1, and verify the history toggle disappears ENTIRELY (not merely
        # visually collapsed) — the strongest live-verifiable form of "no
        # longer appears" once the group re-renders as the bare single-node
        # branch.
        pipeline_page.open_run_details_by_label("Run 1 details", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.delete_current_run_details(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.run_node_history_button).to_have_count(0)
        expect(pipeline_page.run_node_label).to_have_text("Run 2 details")
