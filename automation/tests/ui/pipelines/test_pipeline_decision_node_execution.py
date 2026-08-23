"""UI test — Pipeline Decision Node: Multi-Branch Routing Execution.

TMS: ELITEA-2016
(test-specs/pipelines/l2_pipeline-decision-node-multi-branch-execution_ELITEA-2016.md)

Distinguishing content vs the sibling ELITEA-2034 configuration test
(``test_pipeline_decision_node_configuration.py``): this test wires the
Decision node's three branches all the way through to ``END`` (including
the ``default_output`` edge), then actually SENDS a message and confirms
the Decision node's LLM classification routes execution to the correct
branch — zero prior coverage of Decision-node *execution* anywhere in this
suite. ELITEA-2034's target nodes are never connected to ``END`` and its
AFS explicitly scopes execution out.

Step 1 is Decision-node-first, exactly matching the case's own step 1
ordering ("Create a pipeline **with a Decision node**") — this is NOT
cosmetic. Confirmed via source
(``EliteaUI/src/[fsd]/features/pipelines/flow-editor/ui/nodes/BaseNode/
NodeCardHeader.jsx``) that the "Make entrypoint" menu action is
unconditionally excluded for Decision (and legacy Condition) node types —
the ONLY way to make a Decision node the pipeline's entry point via the UI
is for it to be the FIRST node added (entry_point auto-sets to the first
node's id at creation time). Filed as
https://github.com/EliteaAI/elitea-testing-public/issues/1347 (bug, not
blocking — the case's own step order sidesteps it). Do NOT reorder steps
1-2.

The Decision node's Input combobox must include the built-in ``input``
state variable for classification to work at all — the case text never
mentions this, but skipping it doesn't error; it silently produces an
unrouted, "completed" pipeline run (``content: '{}'``, ``tool_calls: []``,
confirmed live via 3 repeated runs). Step 3 asserts it explicitly.

Printer "Final Message" is NOT what renders in the chat response —
"Value" is (confirmed live: Final Message alone produced ``content: '{}'``
even after correct routing). Branch nodes are configured with a fixed,
distinguishing Value string per branch, and the chat response is asserted
against that string.

Sending a second, differently-classified message in the SAME conversation
does NOT re-invoke the Decision node — a Printer node with
``transition: END`` pauses for acknowledgement, and the run resumes at the
FIRST message's branch (confirmed live via the Run details dialog's
Timeline: ``bug_responder_reset`` — same classification result reused).
Proving differential routing requires clearing the chat
(``PipelineDetailPage.clear_chat()``) between messages.
"""

import logging

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000
PIPELINE_EXECUTION_TIMEOUT = 90_000
STABLE_DURATION_MS = 3_000

_TARGET_NODE_NAMES = ["bug_responder", "feature_responder", "question_responder"]
_DESCRIPTION_TEMPLATE = (
    "Classify this input into one category: - bug_responder: reports a defect "
    "- feature_responder: requests new functionality - question_responder: asks a question"
)
_PRINTER_VALUES = {
    "bug_responder": "BUG_BRANCH_REACHED",
    "feature_responder": "FEATURE_BRANCH_REACHED",
    "question_responder": "QUESTION_BRANCH_REACHED",
}
_END_INTERNAL_ID = "EliteAPipelineEnd"  # ReactFlow's internal id for the synthetic END node post-reload


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2016_pipeline-decision-node-multi-branch-execution.md",
    "onetest-ai Test Case link",
)
def test_decision_node_routes_execution_to_correct_branch(page, pipeline_id):
    """Decision node classifies chat input and routes execution to the matching branch; config persists."""
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from every step (node
    # add/rename/move, drag-connects, field entry, save, reload, chat
    # execution) are captured — AFS Expected Results require "no console
    # errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    pipeline_page.navigate(pipeline_id)
    pipeline_page.wait_for_canvas()
    canonical_url = page.url  # captured for the reload step (?viewMode=owner already included)

    with allure.step(
        "Step 1 — Create a pipeline with a Decision node, added FIRST (before any other "
        "node) so it becomes the pipeline's entry point"
    ):
        pipeline_page.add_node("Decision")
        decision_node_id = pipeline_page.wait_for_node_on_canvas("decision", timeout=UI_ELEMENT_TIMEOUT)
        assert decision_node_id, "Decision node should appear on canvas with a non-empty data-id"
        assert pipeline_page.get_entrypoint_node_id() == decision_node_id, (
            f"Decision node added first should be the pipeline's entry point, "
            f"got entry_point={pipeline_page.get_entrypoint_node_id()!r}"
        )

    with allure.step(
        "Step 2 — Add three Printer nodes as branch targets, rename them, and give each "
        "a distinct PRINTER Value (the branch's observable 'which branch fired' signal)"
    ):
        target_node_ids = []
        for i, target_name in enumerate(_TARGET_NODE_NAMES):
            node_ids_before = set(pipeline_page.get_node_ids())
            pipeline_page.add_node("Printer")
            pipeline_page.wait_for_node_count(len(node_ids_before) + 1, timeout=UI_ELEMENT_TIMEOUT)
            new_printer_id = (set(pipeline_page.get_node_ids()) - node_ids_before).pop()
            # ELITEA-2047 gotcha: every add_node() spawns at the same default
            # canvas position, overlapping whatever was added before it —
            # move each one clear before the next add. Modest, distinct
            # offsets per node (mirroring the proven single-node dx=450/
            # dy=100 pattern in test_pipeline_interrupt_before_after_toggles.py)
            # — large offsets zoom fit_view() out so far the connection
            # handles become sub-pixel and drag-connect misses them.
            pipeline_page.move_node(new_printer_id, 280, 90 * (i + 1))
            renamed_id = pipeline_page.edit_node_name(new_printer_id, target_name)
            assert renamed_id == target_name, (
                f"edit_node_name should return the verbatim new name as the node's new "
                f"data-id (got {renamed_id!r} for target {target_name!r})"
            )
            pipeline_page.fill_printer_node_value_for_node(
                renamed_id, _PRINTER_VALUES[renamed_id], timeout=UI_ELEMENT_TIMEOUT
            )
            assert pipeline_page.get_printer_node_value_for_node(renamed_id) == _PRINTER_VALUES[renamed_id], (
                f"Printer node {renamed_id!r}'s Value field should hold its distinguishing text"
            )
            target_node_ids.append(renamed_id)

        node_ids_after_setup = set(pipeline_page.get_node_ids())
        assert set(_TARGET_NODE_NAMES).issubset(node_ids_after_setup), (
            f"All three renamed branch nodes should be on canvas as {_TARGET_NODE_NAMES!r}, "
            f"got {node_ids_after_setup!r}"
        )
        assert {decision_node_id, "END"}.issubset(node_ids_after_setup), (
            "Decision node and the synthetic END node should still be on canvas"
        )

        # move_node()'s drag can auto-pan the ReactFlow viewport toward the
        # dragged node (edge-of-pane autoscroll), pushing the Decision node
        # (added earlier, at the default spawn position) outside the
        # visible viewport — recenter before interacting with its fields.
        # Same fit_view() call already proven for connect_nodes() after a
        # move_node() reposition (test_pipeline_interrupt_before_after_toggles.py).
        pipeline_page.fit_view()

    with allure.step(
        "Step 3 — Configure the Decision node: Input includes the built-in 'input' "
        "variable, Description holds the classification prompt, and all three DECISION "
        "OUTPUTS are wired via drag-connect"
    ):
        pipeline_page.select_decision_node_input_variables(["input"], timeout=UI_ELEMENT_TIMEOUT)
        input_value = pipeline_page.get_decision_node_input_value()
        assert "input" in input_value, (
            f"Decision node Input select must include the built-in 'input' state variable "
            f"for classification to work at all (silently produces an unrouted run "
            f"otherwise) — got {input_value!r}"
        )

        pipeline_page.fill_decision_node_description(_DESCRIPTION_TEMPLATE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_decision_node_description() == _DESCRIPTION_TEMPLATE, (
            "Description textarea should hold the entered classification prompt"
        )

        for target_name in _TARGET_NODE_NAMES:
            pipeline_page.connect_nodes(
                decision_node_id, target_name, source_handle="nodes", timeout=UI_ELEMENT_TIMEOUT
            )
            pipeline_page.wait_for_edge_present(decision_node_id, target_name, timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.edge_exists(decision_node_id, target_name), (
                f"A {decision_node_id} -> {target_name} edge should render immediately, before Save"
            )
            assert pipeline_page.is_decision_node_output_chip_present(target_name), (
                f"A '{target_name}' chip should appear under Decision outputs immediately after connecting"
            )
        assert pipeline_page.get_decision_node_output_chip_count() == len(_TARGET_NODE_NAMES), (
            f"Exactly {len(_TARGET_NODE_NAMES)} Decision output chips should be present"
        )

    with allure.step(
        "Step 4 — Connect the remaining edges: each branch node -> END, and Decision's "
        "Default output handle -> END"
    ):
        for target_name in _TARGET_NODE_NAMES:
            pipeline_page.connect_nodes(target_name, "END", timeout=UI_ELEMENT_TIMEOUT)
            pipeline_page.wait_for_edge_present(target_name, "END", timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.edge_exists(target_name, "END"), (
                f"A {target_name} -> END edge should render immediately, before Save"
            )

        pipeline_page.connect_nodes(
            decision_node_id, "END", source_handle="default_output", timeout=UI_ELEMENT_TIMEOUT
        )
        decision_default_output_source = f"{decision_node_id}default_output"
        pipeline_page.wait_for_edge_present(decision_default_output_source, "END", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.edge_exists(decision_node_id, "END", handle_suffix="default_output"), (
            "Decision node's Default output -> END edge should render immediately, before Save "
            "(every execution path, including a non-matching classification, must reach END)"
        )

        assert pipeline_page.get_edge_count() == 7, (
            f"Expected 7 edges (3 DECISION OUTPUTS + 3 branch->END + 1 default_output->END "
            f"= 7), got {pipeline_page.get_edge_count()}"
        )

    with allure.step("Step 5a — Save the pipeline; verify no console errors and a 201 Created response"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 5b — Reload via the canonical URL; entry_point, DECISION OUTPUTS chips, all "
        "7 edges (post-reload testid shape), and both Printer Values persist"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("decision", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_entrypoint_node_id() == decision_node_id, (
            f"entry_point should persist as the Decision node after reload, "
            f"got {pipeline_page.get_entrypoint_node_id()!r}"
        )

        for target_name in _TARGET_NODE_NAMES:
            assert pipeline_page.is_decision_node_output_chip_present(target_name), (
                f"'{target_name}' Decision output chip should persist after reload"
            )
        assert pipeline_page.get_decision_node_output_chip_count() == len(_TARGET_NODE_NAMES), (
            f"Exactly {len(_TARGET_NODE_NAMES)} Decision output chips should persist after reload"
        )

        # Post-reload, the edge testid SHAPE changes (nodes-handle edges drop
        # their `nodes`/`target` suffixes; branch->END edges use the literal
        # internal END id `EliteAPipelineEnd`, not "END") — confirmed live,
        # reconfirming ELITEA-2034's own flagged gotcha for THIS case's edges.
        for target_name in _TARGET_NODE_NAMES:
            pipeline_page.wait_for_edge(decision_node_id, target_name, timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.edge_testid_present(decision_node_id, target_name), (
                f"{decision_node_id} -> {target_name} edge should persist with the post-reload testid shape"
            )
            pipeline_page.wait_for_edge(target_name, _END_INTERNAL_ID, timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.edge_testid_present(target_name, _END_INTERNAL_ID), (
                f"{target_name} -> END edge should persist with the post-reload testid shape "
                f"(internal END id {_END_INTERNAL_ID!r})"
            )

        pipeline_page.wait_for_edge(decision_default_output_source, "END", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.edge_testid_present(decision_default_output_source, "END"), (
            "Decision node's Default output -> END edge should persist with the post-reload testid shape"
        )

        assert pipeline_page.get_edge_count() == 7, (
            f"Exactly 7 edges should persist after reload, got {pipeline_page.get_edge_count()}"
        )

        for target_name in _TARGET_NODE_NAMES:
            assert pipeline_page.get_printer_node_value_for_node(target_name) == _PRINTER_VALUES[target_name], (
                f"Printer node {target_name!r}'s Value field should persist after reload"
            )

        assert not console_errors, f"Reload should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 6a — Send a bug-report-shaped message via the embedded chat; verify execution "
        "routes to the bug_responder branch"
    ):
        initial_count = pipeline_page.get_embedded_chat_message_count()
        pipeline_page.send_message_in_embedded_chat(
            "The application crashes when I click the save button, this is clearly a defect.",
            timeout=UI_ELEMENT_TIMEOUT,
        )
        pipeline_page.wait_for_embedded_chat_response(
            initial_count=initial_count,
            stable_duration_ms=STABLE_DURATION_MS,
            timeout=PIPELINE_EXECUTION_TIMEOUT,
        )
        response = pipeline_page.get_embedded_chat_last_message()
        assert _PRINTER_VALUES["bug_responder"] in response, (
            f"A bug-report-shaped message should route to bug_responder "
            f"(expected {_PRINTER_VALUES['bug_responder']!r} in the response), got: {response!r}"
        )
        assert not console_errors, f"Pipeline execution should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 6b — Clear the chat (fresh conversation, else the run resumes at the FIRST "
        "message's branch instead of re-classifying), then send a feature-request-shaped "
        "message and verify execution routes to the feature_responder branch"
    ):
        pipeline_page.clear_chat(timeout=UI_ELEMENT_TIMEOUT)

        initial_count = pipeline_page.get_embedded_chat_message_count()
        pipeline_page.send_message_in_embedded_chat(
            "Could you please add a dark mode toggle? I'd love that new feature.",
            timeout=UI_ELEMENT_TIMEOUT,
        )
        pipeline_page.wait_for_embedded_chat_response(
            initial_count=initial_count,
            stable_duration_ms=STABLE_DURATION_MS,
            timeout=PIPELINE_EXECUTION_TIMEOUT,
        )
        response = pipeline_page.get_embedded_chat_last_message()
        assert _PRINTER_VALUES["feature_responder"] in response, (
            f"A feature-request-shaped message, after clearing the chat, should route to "
            f"feature_responder (expected {_PRINTER_VALUES['feature_responder']!r} in the "
            f"response), got: {response!r}"
        )
        assert not console_errors, f"Pipeline execution should not introduce console errors: {console_errors}"
