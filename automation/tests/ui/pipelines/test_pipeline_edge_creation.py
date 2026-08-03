"""UI test — Pipeline: Edge Creation Between Nodes.

TMS: ELITEA-2031
(test-specs/pipelines/l2_pipeline-edge-creation-between-nodes_ELITEA-2031.md)

Seeds a pipeline with ``LLM 1`` and ``Printer 1``, each independently
``transition: END`` (NOT connected to each other), drags a connection from
LLM 1's output handle to Printer 1's input handle, and confirms the new edge
replaces LLM 1's prior ``-> END`` edge (single-source-single-transition
model — re-pointing, not adding a second outgoing edge) and survives Save +
full page reload.

Case-text drift (AFS Preconditions, filed as
EliteaAI/elitea-testing-public#1136, clarification): the case's Steps 2-3
describe a "transition/routes field" in the LLM node's config panel — no
such field exists for LLM (or Printer/Code/any non-HITL node type),
confirmed both via live DOM read and source (LLMNode.jsx/PrinterNode.jsx).
The real mechanism is dragging a connection on the ReactFlow canvas, which
this test exercises via ``connect_nodes()``.
"""

import allure
import pytest

from tests.ui.pipelines.helpers import _navigate_to_canvas

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2031_pipeline-edge-creation-between-nodes.md",
    "onetest-ai Test Case link",
)
def test_drag_connect_creates_edge_replacing_prior_transition(page, pipeline_llm_printer_disconnected):
    """Dragging LLM 1 -> Printer 1 creates the edge, replacing LLM 1's prior
    -> END edge; the new edge survives Save + reload."""
    with allure.step("Step 1 — Navigate to the pipeline's canvas"):
        pipeline_page = _navigate_to_canvas(page, pipeline_llm_printer_disconnected)
        node_ids = set(pipeline_page.get_node_ids())
        assert {"LLM 1", "Printer 1", "END"} <= node_ids, (
            f"Canvas should show both seeded nodes plus END, got: {node_ids}"
        )
        edge_count_before = pipeline_page.get_edge_count()
        assert edge_count_before == 2, (
            f"Pre-connect canvas should show 2 edges (LLM 1->END, Printer 1->END, "
            f"neither node connected to the other yet), got {edge_count_before}"
        )

    with allure.step(
        "Step 2 — Drag a connection from LLM 1's output handle to Printer 1's input handle"
    ):
        pipeline_page.connect_nodes("LLM 1", "Printer 1")
        assert not pipeline_page.is_popup_menu_visible(), (
            "No stray ReactFlow context menu should be left open after the drag-connect"
        )

    with allure.step(
        "Step 3 — Verify the LLM 1 -> Printer 1 edge exists and the old LLM 1 -> END "
        "edge is specifically gone (re-pointed, not additively created)"
    ):
        assert pipeline_page.edge_exists("LLM 1", "Printer 1"), (
            "Edge from LLM 1 to Printer 1 should exist after the drag-connect"
        )
        edge_count_after = pipeline_page.get_edge_count()
        assert edge_count_after == 2, (
            f"Edge count should stay at 2 (one edge re-pointed, not added) — "
            f"a single-source-single-transition model means LLM 1 can only ever have "
            f"ONE outgoing edge, got {edge_count_after}"
        )

    with allure.step("Step 4 — Save, then reload — verify the edge persists"):
        assert pipeline_page.save_button.is_enabled(), (
            "Save button should be enabled after the connect (unsaved-change state)"
        )
        pipeline_page.save_button.click()
        pipeline_page.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
        page.reload()
        pipeline_page.wait_for_canvas()

        assert pipeline_page.edge_exists("LLM 1", "Printer 1"), (
            "LLM 1 -> Printer 1 edge should still exist after Save + reload"
        )
