"""UI test — Subgraph State Sharing: Common State Variables.

TMS: ELITEA-2443
(test-specs/pipelines/l2_pipeline-subgraph-state-sharing-common-vars_ELITEA-2443.md)

Attaches a CHILD pipeline as a tool to a PARENT pipeline's Agent node (the
current, non-deprecated mechanism for what the case's title calls
"Subgraph" -- the dedicated Pipeline/subgraph flow-editor node type is
legacy and not offered by the modern Add Node menu; the case's own step 3
already names the correct `agent`-node mechanism -- see the AFS
Preconditions CLARIFICATION), executes the parent pipeline, and verifies:
  - the child pipeline's own timeline steps render NESTED in the SAME Run
    Details panel/timeline as the parent's own nodes -- the mechanism
    through which state sharing becomes observable at all
  - COMMON-NAMED state variables (`state_1`, `state_2`) ARE SHARED between
    parent and child: a value the child's own node sets is reflected as the
    AFTER value of the SAME-NAMED variable in the parent's Run Details
    STATES panel

CLARIFICATION (confirmed live, AFS Preconditions): an Agent node's `tool:`
YAML field alone does NOT resolve a pipeline-as-tool reference -- the
pipeline must ALSO be attached via the TOOLS section's "+ Pipeline" popper
(same mechanism as ELITEA-2064), even when the YAML already names the
correct pipeline byte-for-byte. Step 1 below exercises that attach
explicitly and asserts the empty pre-attach Agent combobox per the AFS; the
`AgentNode.jsx` "Agent not found" orphan-warning banner (`Box`/`Typography`,
no testid) is NOT separately asserted -- the AFS lists it only as an Axis-2
documentary observation, and it carries no testid to bind to (same
documented-not-asserted treatment as ELITEA-2038's absent "Structured
output" toggle).

Timeline entry count/order is fixture-shape-dependent (AFS Test Step 9
clarification) -- this test asserts STRUCTURALLY (count >= 3, the child's
name appears among the timeline step ids, the run's Before/After state at
the LAST entry), not a literal step-count/id tuple. Confirmed live during
implementation: THIS fixture's own recipe produced 4 timeline entries
ending in the child's own "pyodide" code-node step, not a distinct
trailing "AGENT1" wrap-up entry (unlike the AFS author's own live session,
whose slightly different 2-node-parent/1-node-child recipe produced 5,
ending in "AGENT1") -- selecting whichever entry is actually last still
satisfies case step 6 ("click on the Agent node step in the timeline"), and
the Before/After values for state_1/state_2 hold either way since the
child's own CODE1 node is what performs the write in both shapes.

ELITEA-2445 (`extend-existing` onto this module -- AFS
test-specs/pipelines/lextend_pipeline-subgraph-node-c-state-propagation_ELITEA-2445.md)
adds a SIBLING test below,
`test_subgraph_state_sharing_node_c_state_propagation`, using a NEW 3-node
parent fixture (`pipeline_parent_child_state_sharing_three_node`: CODE1 ->
AGENT1 (agent, tool = child) -> CODE2/"Node_C" -> END). It covers two gaps
this module's original test never exercises: (1) selecting timeline index 0
(CODE1's OWN entry) produces a step-specific Before/After pair, distinct
from the LAST-index selection above; (2) a node chained via `transition:`
immediately after an Agent node's nested-pipeline tool call NEVER executes
-- CONFIRMED DEFECT `EliteaAI/elitea-testing-public#1381` -- soft-asserted,
not masked. This module's original test and its fixture are UNCHANGED.
"""

import logging
from datetime import datetime

import allure
import pytest
from config import settings

from tests.ui.pipelines.helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
PIPELINE_EXECUTION_TIMEOUT = 90_000
STABLE_DURATION_MS = 3_000


def _is_known_1267_stepper_prop_leak(msg) -> bool:
    """Filter the Run Details panel's Timeline Stepper prop-leak warning.

    Same known, filed defect as the sibling ELITEA-2450/2451/2452 Run
    Details tests (`EliteaAI/elitea-testing-public#1267`) -- this test opens
    the same `RunStateDialog.jsx` panel.
    """
    return "non-boolean attribute" in msg.text


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2443_pipeline-subgraph-state-sharing-common-vars.md",
    "onetest-ai Test Case link",
)
def test_subgraph_state_sharing_common_vars(page, pipeline_parent_child_state_sharing):
    """Common-named state vars (state_1/state_2) are shared between a parent pipeline and a
    child pipeline attached as a tool to its Agent node."""
    project_id = str(settings.elitea_project_id)
    parent_id = pipeline_parent_child_state_sharing["parent_id"]
    child_name = pipeline_parent_child_state_sharing["child_name"]

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
        # (same endpoint/mechanism as the Agent picker, NOT the Toolkit/MCP
        # picker's /tool/prompt_lib/ PATCH) -- confirmed live, ELITEA-2064.
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
            f"Run should complete before assessing nested timeline/state -- got "
            f"{pipeline_page.get_run_details_status_badge_text()!r}"
        )

    with allure.step(
        "Step 6 — Timeline nests the CHILD pipeline's own execution steps inside the SAME panel; "
        "select the LAST entry (the Agent node's own step, 'AGENT1') -- satisfies case step 6"
    ):
        timeline_count = pipeline_page.get_run_details_timeline_step_count()
        assert timeline_count >= 3, (
            f"Timeline should show >= 3 steps (parent CODE1 + >=1 nested child step + AGENT1 "
            f"wrap-up) for a nested-pipeline run, got {timeline_count}"
        )

        timeline_node_ids = [
            pipeline_page.get_run_details_timeline_step_node_id(i, timeout=UI_ELEMENT_TIMEOUT)
            for i in range(timeline_count)
        ]
        assert any(child_name in node_id for node_id in timeline_node_ids), (
            f"The child pipeline's own name ({child_name!r}) should appear among the nested "
            f"timeline step ids, got {timeline_node_ids!r}"
        )

        # Select the LAST entry -- the AFS's own Automation Hints call for a
        # STRUCTURAL assertion here (count / child-name presence / last-entry
        # identity), not the literal id string, because entry count/order is
        # fixture-shape-dependent: this fixture's own live run showed 4
        # entries ending in the CHILD's own "pyodide" code-node step, not a
        # distinct trailing "AGENT1" entry (unlike the AFS author's session,
        # whose 2-node-parent/1-node-child recipe produced 5, ending in
        # "AGENT1") -- confirmed live for THIS recipe during implementation.
        # Either shape satisfies case step 6 ("click on the Agent node step
        # in the timeline"): the last entry is always the deepest point of
        # the nested execution, immediately before the run reports Completed.
        last_index = timeline_count - 1
        pipeline_page.select_run_details_timeline_step(last_index, timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        "Step 7 — state_1: Before shows the value set by the parent's preceding CODE1 node"
    ):
        pipeline_page.expand_run_details_state_row("state_1", timeout=UI_ELEMENT_TIMEOUT)
        state_1_before = pipeline_page.get_run_details_state_before_value("state_1", timeout=UI_ELEMENT_TIMEOUT)
        assert state_1_before == '"parent_value"', (
            f"state_1's Before value (at the AGENT1 step) should reflect the PARENT's own CODE1 "
            f"write ('parent_value'), got {state_1_before!r}"
        )

    with allure.step(
        "Step 8 — state_1/state_2: After shows the value written by the CHILD pipeline's own "
        "execution -- CORE CASE ASSERTION: common-named state IS shared between parent and child"
    ):
        state_1_after = pipeline_page.get_run_details_state_after_value("state_1", timeout=UI_ELEMENT_TIMEOUT)
        assert state_1_after == '"child_value"', (
            f"state_1's After value should reflect the CHILD pipeline's own write ('child_value'), "
            f"proving the child's write propagates back into the parent's own state -- got {state_1_after!r}"
        )

        pipeline_page.expand_run_details_state_row("state_2", timeout=UI_ELEMENT_TIMEOUT)
        state_2_before = pipeline_page.get_run_details_state_before_value("state_2", timeout=UI_ELEMENT_TIMEOUT)
        assert state_2_before == "", (
            f"state_2's Before value should be empty -- the parent never touches state_2, only "
            f"the child does -- got {state_2_before!r}"
        )
        state_2_after = pipeline_page.get_run_details_state_after_value("state_2", timeout=UI_ELEMENT_TIMEOUT)
        assert state_2_after == "99", (
            f"state_2's After value should reflect the CHILD pipeline's own write (99), got {state_2_after!r}"
        )

    with allure.step(
        "Step 9 — Confirm BOTH state_1 and state_2's After values match the child's own writes exactly"
    ):
        assert (state_1_after, state_2_after) == ('"child_value"', "99"), (
            "Both common-named state variables should carry the child pipeline's exact written "
            f"values after the nested run, got state_1={state_1_after!r} state_2={state_2_after!r}"
        )

    with allure.step("Step 10 — Verify no unexpected console errors (excluding the known #1267 signature)"):
        page.remove_listener("console", _on_console)
        assert not console_errors, (
            f"Unexpected console errors during attach->execute->open-run-details->select-step->"
            f"expand-state-rows: {[m.text for m in console_errors]}"
        )


_KNOWN_DEFECT_1381 = "https://github.com/EliteaAI/elitea-testing-public/issues/1381"

# Timeline step count THIS fixture recipe (3-node parent: CODE1 -> AGENT1 -> CODE2) is
# confirmed to produce -- the SAME count the 2-node-parent fixture above produces, because
# CODE2/Node_C never joins the run (confirmed defect #1381). Not a general assumption about
# nested-pipeline timelines -- specific to this exact recipe (AFS Automation Hints).
_EXPECTED_TIMELINE_STEP_COUNT_WITH_BLOCKED_NODE_C = 4


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2445_subgraph-execution-verify-state-flow-in-run-details.md",
    "onetest-ai Test Case link",
)
def test_subgraph_state_sharing_node_c_state_propagation(
    page, pipeline_parent_child_state_sharing_three_node
):
    """Node_C (CODE2), chained via `transition:` immediately after an Agent node's
    nested-pipeline tool call, never executes -- CONFIRMED DEFECT #1381, soft-asserted, not
    masked. Also proves the Run Details STATES panel keys Before/After off the SELECTED
    timeline step (index 0 = CODE1's own write), not a run-level aggregate, and that every
    timeline step renders a non-decreasing timestamp.

    TMS: ELITEA-2445 (extend-existing onto this module -- see module docstring)."""
    project_id = str(settings.elitea_project_id)
    parent_id = pipeline_parent_child_state_sharing_three_node["parent_id"]
    child_name = pipeline_parent_child_state_sharing_three_node["child_name"]

    console_errors = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_1267_stepper_prop_leak(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    with allure.step(
        "Step 1 — Open the 3-node parent (CODE1 -> AGENT1 -> CODE2/Node_C); CODE2 is wired "
        "into the graph; attach the child pipeline via the Tools-section popper"
    ):
        pipeline_page = _navigate_to_canvas(page, parent_id)
        node_ids = pipeline_page.get_node_ids()
        assert "CODE1" in node_ids, f"Canvas should render the parent's CODE1 node, got {node_ids!r}"
        assert "AGENT1" in node_ids, f"Canvas should render the parent's AGENT1 node, got {node_ids!r}"
        assert "CODE2" in node_ids, (
            f"Canvas should render the parent's CODE2 (Node_C) node -- confirms it is wired into "
            f"the graph, distinguishing 'never wired' from 'wired but never executed' -- got "
            f"{node_ids!r}"
        )
        assert pipeline_page.get_agent_node_agent_value(timeout=UI_ELEMENT_TIMEOUT) == "", (
            "Agent node's Agent combobox should be EMPTY before the Tools-section attach"
        )

        popper = pipeline_page.open_pipeline_popper(timeout=UI_ELEMENT_TIMEOUT)
        assert popper.is_visible(), "'+ Pipeline' popper should open"
        attach_response = pipeline_page.select_pipeline_in_popper(
            popper, child_name, project_id, timeout=UI_ELEMENT_TIMEOUT
        )
        assert attach_response is not None, (
            "Pipeline attach should return the persisted relation payload from the immediate "
            "PATCH .../application_relation/prompt_lib/{project}/{child_id}/{version_id} 201 "
            "response"
        )
        page.keyboard.press("Escape")
        assert pipeline_page.get_agent_node_agent_value(timeout=UI_ELEMENT_TIMEOUT) == child_name, (
            f"Agent combobox should show the attached child pipeline name {child_name!r} after attach"
        )
        assert not console_errors, (
            f"Attaching the child pipeline should not introduce console errors: {console_errors}"
        )

    with allure.step("Step 2 — Execute the parent pipeline via the embedded chat"):
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

    with allure.step("Step 3 — Open Run Details; the run completed"):
        pipeline_page.open_run_details_panel(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_run_details_status_badge_text() == "Completed", (
            f"Run should complete before assessing the timeline/state -- got "
            f"{pipeline_page.get_run_details_status_badge_text()!r}"
        )

    soft_failures = []

    with allure.step(
        "Step 4 — Select timeline index 0 (CODE1's OWN entry) -- satisfies case step 6: "
        "state_1 Before is empty/initial, After is CODE1's own write -- proving the panel keys "
        "Before/After off the SELECTED step, not a run-level aggregate (a DIFFERENT pair than "
        "the LAST-index selection the sibling test above asserts)"
    ):
        pipeline_page.select_run_details_timeline_step(0, timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.expand_run_details_state_row("state_1", timeout=UI_ELEMENT_TIMEOUT)
        state_1_before_index0 = pipeline_page.get_run_details_state_before_value(
            "state_1", timeout=UI_ELEMENT_TIMEOUT
        )
        state_1_after_index0 = pipeline_page.get_run_details_state_after_value(
            "state_1", timeout=UI_ELEMENT_TIMEOUT
        )
        assert state_1_before_index0 == '""', (
            f"state_1's Before value at timeline index 0 (CODE1's own entry) should be empty/"
            f"initial -- state_1 has never been set before CODE1 runs -- got "
            f"{state_1_before_index0!r}"
        )
        assert state_1_after_index0 == '"parent_value"', (
            f"state_1's After value at timeline index 0 should reflect CODE1's OWN write "
            f"('parent_value') -- got {state_1_after_index0!r}"
        )

    with allure.step(
        "Step 5 — CONFIRMED DEFECT (#1381, soft-asserted, not masked): the timeline does NOT "
        "gain a distinct entry for CODE2/Node_C despite it being wired into the graph -- "
        "documents case steps 5/8's blocked premise (case step 5: timeline should show all 3 "
        "nodes; case step 8: click Node_C's own step to read the child-modified value)"
    ):
        timeline_count = pipeline_page.get_run_details_timeline_step_count()
        timeline_node_ids = [
            pipeline_page.get_run_details_timeline_step_node_id(i, timeout=UI_ELEMENT_TIMEOUT)
            for i in range(timeline_count)
        ]
        # Polarity (fix round, 2026-08-09): the condition must fire on the CURRENT
        # buggy symptom (timeline stuck at the blocked count / CODE2 absent), not
        # on a DEVIATION from it -- matching the compliant #1103 precedent above
        # (`restarted_types` fires when the defect's symptom occurs). The inverted
        # form (fire only on deviation) makes this test a hidden GREEN while #1381
        # is open, since it would go RED only if the defect were fixed -- see
        # `.agents/memory/qa-engineer/known_defect_soft_assert_polarity_must_encode_correct_behavior.md`.
        if timeline_count == _EXPECTED_TIMELINE_STEP_COUNT_WITH_BLOCKED_NODE_C:
            soft_failures.append(
                f"Known defect {_KNOWN_DEFECT_1381}: timeline is stuck at "
                f"{_EXPECTED_TIMELINE_STEP_COUNT_WITH_BLOCKED_NODE_C} steps (the 2-node-parent "
                f"shape -- CODE2/Node_C never executes) -- got {timeline_count}. This is the "
                f"CURRENT known-defect signature; it will clear on its own once #1381 is fixed "
                f"and CODE2 starts joining the run."
            )
        if not any("CODE2" in node_id for node_id in timeline_node_ids):
            soft_failures.append(
                f"Known defect {_KNOWN_DEFECT_1381}: no timeline entry's node-id aria-label "
                f"matches 'CODE2' (case step 8's target control does not exist while the defect "
                f"stands) -- got {timeline_node_ids!r}. This is the CURRENT known-defect "
                f"signature; it will clear on its own once #1381 is fixed."
            )

    with allure.step(
        "Step 6 — Every rendered timeline step exposes a non-empty timestamp, monotonically "
        "non-decreasing across the run -- satisfies case step 5's 'timestamps in execution "
        "order' wording (previously-unused handle)"
    ):
        timestamps = [
            pipeline_page.get_run_details_timeline_step_timestamp(i, timeout=UI_ELEMENT_TIMEOUT)
            for i in range(timeline_count)
        ]
        assert all(timestamps), (
            f"Every timeline step should render a non-empty timestamp, got {timestamps!r}"
        )
        parsed_timestamps = [datetime.strptime(ts, "%H:%M:%S") for ts in timestamps]
        assert parsed_timestamps == sorted(parsed_timestamps), (
            f"Timeline timestamps should be monotonically non-decreasing in execution order, "
            f"got {timestamps!r}"
        )

    with allure.step("Step 7 — Verify no unexpected console errors (excluding the known #1267 signature)"):
        page.remove_listener("console", _on_console)
        assert not console_errors, (
            f"Unexpected console errors during attach->execute->open-run-details->select-step->"
            f"expand-state-rows: {[m.text for m in console_errors]}"
        )

    if soft_failures:
        pytest.fail(
            "Soft assertion(s) failed (sanctioned RED — known defect #1381):\n"
            + "\n".join(soft_failures)
        )
