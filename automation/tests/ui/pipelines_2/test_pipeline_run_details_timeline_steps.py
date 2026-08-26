"""UI test — Run Details: Timeline Steps Display.

TMS: ELITEA-2451
(test-specs/pipelines/l3_run-details-timeline-steps-display_ELITEA-2451.md)

Executes a 3-node plain-LLM chain (LLM 1 -> LLM 2 -> LLM 3 -> END,
deliberately NOT a `structured_output: true` node — see module docstring
note below), opens the Run Details panel (`RunStateDialog.jsx`, reused from
ELITEA-2450), and verifies each executed node renders as a timeline-step
entry: a green dot (`data-status="completed"`), a hover-revealed node-id
tooltip (read via the dot's static `aria-label`), and an `HH:mm:ss`
timestamp — plus that the entries render in execution order and that the
total entry count matches the number of executed nodes.

Case-text CLARIFICATION (filed `EliteaAI/elitea-testing-public#1375`): the
case's step 7 says nodes appear "top to bottom = first to last" — the live
Timeline is a plain MUI `Stepper` with no `orientation="vertical"` override,
so it renders horizontally LEFT TO RIGHT, not stacked top to bottom. The
underlying intent (first-executed appears first in the visual reading order)
does hold; only the described axis is wrong. This test asserts execution
order via DOM/index order correlated with ascending timestamps, which is
robust to the axis and to any future layout change.

Automation caveat (cross-reference, not this case's own fixture): a
`structured_output: true` LLM node renders TWO timeline entries per
execution (ELITEA-2453 sibling AFS finding) — this case's fixture
deliberately uses only plain LLM nodes so the "entries == executed nodes"
assertion (step 8) stays meaningful. Do not swap in a structured-output
fixture without re-deriving the expected entry count.

Testids for this case (`data-status` on the timeline-step dot,
`pipeline-run-details-timeline-timestamp-{index}` on the per-step timestamp)
did not exist before this case and were added via `add-data-testid`,
EliteaAI/EliteaUI@95b1eada.
"""

import logging
import re

import allure
import pytest
from playwright.sync_api import expect

from tests.ui.pipeline_helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
PIPELINE_EXECUTION_TIMEOUT = 90_000
STABLE_DURATION_MS = 3_000

EXECUTED_NODE_IDS = ["LLM1", "LLM2", "LLM3"]  # space-stripped, per ELITEA-2450 rendering
TIMESTAMP_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2}$")


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
    "ELITEA-2451_run-details-timeline-steps-display.md",
    "onetest-ai Test Case link",
)
def test_run_details_timeline_steps_display(page, pipeline_three_llm_chain):
    """Run Details Timeline shows one entry per executed node: green dot, node-id tooltip, timestamp, in order."""
    console_errors = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_1267_stepper_prop_leak(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    with allure.step("Step 1 — Execute a pipeline with 3 plain LLM nodes (LLM 1 -> LLM 2 -> LLM 3 -> END)"):
        pipeline_page = _navigate_to_canvas(page, pipeline_three_llm_chain)
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
            f"Run should complete before assessing the timeline -- got {pipeline_page.get_run_details_status()!r}"
        )

    with allure.step("Step 3 — Verify exactly one timeline-step dot per executed node (3 nodes)"):
        entry_count = pipeline_page.get_run_details_timeline_step_count()
        assert entry_count == len(EXECUTED_NODE_IDS), (
            f"Expected {len(EXECUTED_NODE_IDS)} timeline-step dots (one per executed node), got {entry_count}"
        )

    with allure.step("Step 4 — Every timeline-step dot shows the green (completed) indicator"):
        for index in range(len(EXECUTED_NODE_IDS)):
            status = pipeline_page.get_run_details_timeline_step_status(index, timeout=UI_ELEMENT_TIMEOUT)
            assert status == "completed", (
                f"Timeline-step dot {index} should be data-status='completed' for a Completed run, got {status!r}"
            )

    with allure.step("Step 5 — Hovering each timeline-step dot reveals the node id (space-stripped)"):
        for index, expected_id in enumerate(EXECUTED_NODE_IDS):
            pipeline_page.hover_run_details_timeline_step(index, timeout=UI_ELEMENT_TIMEOUT)
            node_id = pipeline_page.get_run_details_timeline_step_node_id(index, timeout=UI_ELEMENT_TIMEOUT)
            assert node_id == expected_id, (
                f"Timeline-step dot {index}'s hover node-id should be {expected_id!r}, got {node_id!r}"
            )

    with allure.step("Step 6 — Every timeline-step entry shows a timestamp in HH:MM:SS format"):
        timestamps = []
        for index in range(len(EXECUTED_NODE_IDS)):
            timestamp = pipeline_page.get_run_details_timeline_step_timestamp(index, timeout=UI_ELEMENT_TIMEOUT)
            assert TIMESTAMP_PATTERN.match(timestamp), (
                f"Timeline-step entry {index}'s timestamp should match HH:MM:SS, got {timestamp!r}"
            )
            timestamps.append(timestamp)

    with allure.step(
        "Step 7 — Timeline entries render in execution order "
        "(DOM index order correlated with ascending timestamps -- case-text "
        "'top to bottom' axis is stale, see module docstring CLARIFICATION)"
    ):
        assert timestamps == sorted(timestamps), (
            f"Timeline entries should be in non-decreasing timestamp order (DOM index == execution order), "
            f"got {timestamps!r}"
        )

    with allure.step("Step 8 — Total timeline entries match the number of nodes that executed (3)"):
        assert pipeline_page.get_run_details_timeline_step_count() == len(EXECUTED_NODE_IDS), (
            "Timeline entry count should still match the 3 executed nodes after all interactions above"
        )

    with allure.step("Step 9 — Verify no unexpected console errors (excluding the known #1267 signature)"):
        page.remove_listener("console", _on_console)
        assert not console_errors, (
            f"Unexpected console errors during navigate->execute->open-panel->inspect-timeline: "
            f"{[m.text for m in console_errors]}"
        )
