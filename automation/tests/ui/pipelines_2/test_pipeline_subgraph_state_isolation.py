"""UI test — Subgraph State Sharing: Non-Common State Isolation.

TMS: ELITEA-2444
(test-specs/pipelines/l2_pipeline-subgraph-non-common-state-isolation_ELITEA-2444.md)

Sibling of ELITEA-2443 (`test_pipeline_subgraph_state_sharing.py`) on the
same Agent-node-attaches-child-pipeline mechanism (see that file's own
CLARIFICATION docstring for the "Subgraph" terminology note and the
Tools-section "+ Pipeline" attach precondition -- both apply unchanged
here). This case's own focus is the OPPOSITE property: state variables that
are NOT common between parent and child.

  - `state_1` (common-named, declared in BOTH pipelines) IS shared -- a
    control/sanity check confirming the fixture wiring, symmetric with
    ELITEA-2443's central finding.
  - `state_2` (parent-only, declared ONLY in the parent's own `state:`
    block) is set by the parent's own CODE1 node and is NEVER touched by
    the Agent-node call or the child's own execution -- confirmed unchanged
    across the Agent-node boundary.
  - `state_3` (child-only, declared ONLY in the child's own `state:` block)
    NEVER appears as a row in the parent's Run Details STATES panel, at
    ANY timeline step -- CORE CASE ASSERTION. A child-only variable's
    existence is fully opaque to the parent's panel.

IMPORTANT PLATFORM-BEHAVIOR DISCOVERY (AFS Test Step 12, confirmed live):
Run Details STATES panel Before/After values are computed PER the
CURRENTLY SELECTED timeline step's own input/output declaration, not as a
run-level snapshot. A variable absent from the selected step's own
input/output renders BOTH Before and After as empty, even though the value
is genuinely non-empty elsewhere in the run. This did not surface in
ELITEA-2443 because that case's child pipeline declared BOTH state_1 AND
state_2, so every timeline step had both variables in scope. Consequently,
`state_2` (parent-only) is read at timeline step 0 (the parent's own CODE1
execution) for its After value, and at timeline step 1 (the first
Agent/child-boundary entry) for its Before value -- NOT at the LAST
timeline step (the convention used for `state_1`, which stays in scope at
every step since the child also declares it) -- a step0-After ==
step1-Before comparison proves continuity across the Agent-node boundary
per the AFS's own reasoning for why a single-step read would be
ambiguous (a blank render is indistinguishable between "step doesn't
touch this variable" and "value lost").
"""

import logging

import allure
import pytest
from config import settings

from tests.ui.pipelines.helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
PIPELINE_EXECUTION_TIMEOUT = 90_000
STABLE_DURATION_MS = 3_000


def _is_known_1267_stepper_prop_leak(msg) -> bool:
    """Filter the Run Details panel's Timeline Stepper prop-leak warning.

    Same known, filed defect as the sibling ELITEA-2443/2450/2451/2452 Run
    Details tests (`EliteaAI/elitea-testing-public#1267`) -- this test opens
    the same `RunStateDialog.jsx` panel.
    """
    return "non-boolean attribute" in msg.text


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2444_subgraph-state-sharing-non-common-state-isolation.md",
    "onetest-ai Test Case link",
)
def test_subgraph_state_sharing_non_common_state_isolation(page, pipeline_parent_child_state_isolation):
    """Non-common state vars stay isolated between a parent pipeline and a child
    pipeline attached as a tool to its Agent node: state_3 (child-only) never
    surfaces in the parent's Run Details, state_2 (parent-only) is untouched by
    the child, and state_1 (common) IS shared (sanity control)."""
    project_id = str(settings.elitea_project_id)
    parent_id = pipeline_parent_child_state_isolation["parent_id"]
    child_name = pipeline_parent_child_state_isolation["child_name"]

    console_errors = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_1267_stepper_prop_leak(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    with allure.step(
        "Step 1 — Open the parent pipeline; both nodes render, Agent combobox is empty pre-attach"
    ):
        pipeline_page = _navigate_to_canvas(page, parent_id)
        node_ids = pipeline_page.get_node_ids()
        assert "CODE1" in node_ids, f"Canvas should render the parent's CODE1 node, got {node_ids!r}"
        assert "AGENT1" in node_ids, f"Canvas should render the parent's AGENT1 node, got {node_ids!r}"
        assert pipeline_page.get_agent_node_agent_value(timeout=UI_ELEMENT_TIMEOUT) == "", (
            "Agent node's Agent combobox should be EMPTY before the Tools-section attach -- the "
            "YAML `tool:` field alone does not resolve the child pipeline reference (AFS Preconditions)"
        )

    with allure.step('Step 2 — Click TOOLS "+ Pipeline"; select the child pipeline from the popper'):
        popper = pipeline_page.open_pipeline_popper(timeout=UI_ELEMENT_TIMEOUT)
        assert popper.is_visible(), "'+ Pipeline' popper should open"

        # Regression guard: hard-blocks on the attach's own PATCH-201 response
        # (same endpoint/mechanism as ELITEA-2443/2064) -- confirmed live.
        attach_response = pipeline_page.select_pipeline_in_popper(
            popper, child_name, project_id, timeout=UI_ELEMENT_TIMEOUT
        )
        assert attach_response is not None, (
            "Pipeline attach should return the persisted relation payload from the immediate "
            "PATCH .../application_relation/prompt_lib/{project}/{child_id}/{version_id} 201 response"
        )
        page.keyboard.press("Escape")

    with allure.step(
        "Step 3 — Re-inspect the Agent node: the child pipeline now resolves in the Agent combobox"
    ):
        assert pipeline_page.get_agent_node_agent_value(timeout=UI_ELEMENT_TIMEOUT) == child_name, (
            f"Agent combobox should show the attached child pipeline name {child_name!r} after attach"
        )
        assert not console_errors, f"Attaching the child pipeline should not introduce console errors: {console_errors}"

    with allure.step("Step 4 — Execute the parent pipeline via the embedded chat"):
        initial_count = pipeline_page.get_embedded_chat_message_count()
        pipeline_page.send_message_in_embedded_chat("Run the graph.", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.wait_for_embedded_chat_response(
            initial_count=initial_count,
            stable_duration_ms=STABLE_DURATION_MS,
            timeout=PIPELINE_EXECUTION_TIMEOUT,
        )
        assert pipeline_page.get_embedded_chat_message_count() > initial_count, (
            "Embedded chat should show at least one new message after the run completes"
        )

    with allure.step("Step 5 — Open Run Details; the run completed"):
        pipeline_page.open_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_run_details_status_badge_text() == "Completed", (
            f"Run should complete before assessing the state panel -- got "
            f"{pipeline_page.get_run_details_status_badge_text()!r}"
        )

    with allure.step(
        "Step 6 — Timeline nests the CHILD pipeline's own execution steps inside the SAME panel "
        "(structural check, per ELITEA-2443's own fixture-shape finding for this recipe)"
    ):
        timeline_count = pipeline_page.get_run_details_timeline_step_count()
        assert timeline_count >= 3, (
            f"Timeline should show >= 3 steps (parent CODE1 + nested child step(s)) for a "
            f"nested-pipeline run, got {timeline_count}"
        )
        timeline_node_ids = [
            pipeline_page.get_run_details_timeline_step_node_id(i, timeout=UI_ELEMENT_TIMEOUT)
            for i in range(timeline_count)
        ]
        assert any(child_name in node_id for node_id in timeline_node_ids), (
            f"The child pipeline's own name ({child_name!r}) should appear among the nested "
            f"timeline step ids, got {timeline_node_ids!r}"
        )

    with allure.step(
        "Step 7 — CORE CASE ASSERTION: state_3 (child-only) does NOT appear as a row in the "
        "parent's Run Details STATES panel, at ANY timeline step"
    ):
        for index in range(timeline_count):
            pipeline_page.select_run_details_timeline_step(index, timeout=UI_ELEMENT_TIMEOUT)
            state_3_count = pipeline_page.get_run_details_state_row_locator("state_3").count()
            assert state_3_count == 0, (
                f"state_3 (declared ONLY in the child's own state: block) should never render as "
                f"a row in the PARENT's Run Details STATES panel -- got {state_3_count} row(s) at "
                f"timeline step {index}"
            )

    with allure.step(
        "Step 8 — state_1 (common var): Before/After differ at the LAST timeline step -- "
        "confirms the child's write propagates back (sanity control, symmetric with ELITEA-2443)"
    ):
        last_index = timeline_count - 1
        pipeline_page.select_run_details_timeline_step(last_index, timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.expand_run_details_state_row("state_1", timeout=UI_ELEMENT_TIMEOUT)
        state_1_before = pipeline_page.get_run_details_state_before_value("state_1", timeout=UI_ELEMENT_TIMEOUT)
        state_1_after = pipeline_page.get_run_details_state_after_value("state_1", timeout=UI_ELEMENT_TIMEOUT)
        assert state_1_before == '"parent_value"', (
            f"state_1's Before value (at the last step) should reflect the PARENT's own CODE1 "
            f"write, got {state_1_before!r}"
        )
        assert state_1_after == '"child_value"', (
            f"state_1's After value should reflect the CHILD pipeline's own write, proving the "
            f"common-named var IS shared -- got {state_1_after!r}"
        )

    with allure.step(
        "Step 9 — state_2 (parent-only): unchanged across the Agent-node boundary -- read at "
        "timeline step 0 (parent's own CODE1) and step 1 (first Agent/child-boundary entry), "
        "per the AFS's per-timeline-step Before/After discovery (see module docstring)"
    ):
        pipeline_page.select_run_details_timeline_step(0, timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.expand_run_details_state_row("state_2", timeout=UI_ELEMENT_TIMEOUT)
        state_2_before_step0 = pipeline_page.get_run_details_state_before_value(
            "state_2", timeout=UI_ELEMENT_TIMEOUT
        )
        state_2_after_step0 = pipeline_page.get_run_details_state_after_value(
            "state_2", timeout=UI_ELEMENT_TIMEOUT
        )
        assert state_2_before_step0 == '""', (
            f"state_2's Before value at timeline step 0 should be empty (unset before CODE1 "
            f"runs), got {state_2_before_step0!r}"
        )
        assert state_2_after_step0 == '"parent_only_value"', (
            f"state_2's After value at timeline step 0 should reflect the PARENT's own CODE1 "
            f"write, got {state_2_after_step0!r}"
        )

        pipeline_page.select_run_details_timeline_step(1, timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.expand_run_details_state_row("state_2", timeout=UI_ELEMENT_TIMEOUT)
        state_2_before_step1 = pipeline_page.get_run_details_state_before_value(
            "state_2", timeout=UI_ELEMENT_TIMEOUT
        )
        assert state_2_before_step1 == state_2_after_step0 == '"parent_only_value"', (
            f"state_2's Before value at timeline step 1 should equal step 0's After value, proving "
            f"the parent-only var is UNCHANGED across the Agent-node boundary -- step0 After="
            f"{state_2_after_step0!r}, step1 Before={state_2_before_step1!r}"
        )

    with allure.step("Step 10 — Verify no unexpected console errors (excluding the known #1267 signature)"):
        page.remove_listener("console", _on_console)
        assert not console_errors, (
            f"Unexpected console errors during attach->execute->open-run-details->select-step->"
            f"expand-state-rows: {[m.text for m in console_errors]}"
        )
