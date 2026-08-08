"""UI test — Pipeline Canvas: Zoom and Pan.

TMS: ELITEA-2019
(test-specs/pipelines/l2_pipeline-canvas-zoom-and-pan_ELITEA-2019.md)

Seeds a pipeline ``LLM 1 -> Code 1 -> END`` (3 nodes, 2 edges, reused
`pipeline_llm_code_end` fixture — any already-proven multi-node pipeline
satisfies this case's precondition), then:
1. Fit View -> asserts every node is fully contained within the canvas
   viewport.
2. Zoom In -> asserts the ReactFlow viewport scale AND a node's on-screen
   bounding-box size both increase.
3. Pans the canvas by dragging empty canvas space -> asserts the viewport
   translate offset AND the same node's bounding-box position both shift by
   the exact drag delta.
4. Fit View again -> asserts the canvas returns to the exact same transform
   step 1 produced (all nodes visible again) — confirmed live this is fully
   deterministic for a static node layout.

Zoom/pan/Fit-View are pure client-side ReactFlow viewport state — confirmed
live no network request fires for any of them (see AFS Network Behavior).
"""

import allure
import pytest

from tests.ui.pipelines.helpers import _navigate_to_canvas

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
# The exact drag delta panned in step 3 — asserted 1:1 against the resulting
# transform/bounding-box shift (confirmed live: ReactFlow pans px-perfectly).
PAN_DX = 100
PAN_DY = 80


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2019_pipeline-canvas-zoom-and-pan.md",
    "onetest-ai Test Case link",
)
def test_canvas_zoom_pan_and_fit_view(page, pipeline_llm_code_end):
    """Fit View shows all nodes; Zoom In enlarges the canvas; dragging pans
    the viewport by the exact delta; Fit View again restores the exact
    original all-nodes-visible transform."""
    with allure.step("Step 1 — Navigate to the pipeline's canvas"):
        pipeline_page = _navigate_to_canvas(page, pipeline_llm_code_end)
        node_ids = pipeline_page.get_node_ids()
        assert pipeline_page.get_node_count() == 3, (
            f"Canvas should show exactly 3 seeded nodes, got {pipeline_page.get_node_count()}"
        )
        probe_node_id = "LLM 1"
        assert probe_node_id in node_ids, f"Expected probe node {probe_node_id!r} in {node_ids}"

    with allure.step("Step 2 — Click Fit View, verify all nodes are visible"):
        pipeline_page.fit_canvas_view(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.all_nodes_within_viewport(), (
            "All nodes should be fully contained within the canvas viewport after Fit View"
        )
        baseline_transform = pipeline_page.get_canvas_viewport_transform()
        baseline_box = pipeline_page.get_node_bounding_box(probe_node_id)

    with allure.step("Step 3/4 — Zoom in, verify canvas scale and node size both increase"):
        pipeline_page.zoom_in_canvas(timeout=UI_ELEMENT_TIMEOUT)
        zoomed_transform = pipeline_page.get_canvas_viewport_transform()
        zoomed_box = pipeline_page.get_node_bounding_box(probe_node_id)

        assert zoomed_transform["scale"] > baseline_transform["scale"], (
            f"Zoom In should increase viewport scale: "
            f"{baseline_transform['scale']} -> {zoomed_transform['scale']}"
        )
        baseline_area = baseline_box["width"] * baseline_box["height"]
        zoomed_area = zoomed_box["width"] * zoomed_box["height"]
        assert zoomed_area > baseline_area, (
            f"Node {probe_node_id!r} should appear larger after Zoom In: "
            f"{baseline_area:.1f}px^2 -> {zoomed_area:.1f}px^2"
        )

    with allure.step(
        "Step 5/6 — Pan the canvas by dragging, verify viewport position and node position both change"
    ):
        pre_pan_transform = pipeline_page.get_canvas_viewport_transform()
        pre_pan_box = pipeline_page.get_node_bounding_box(probe_node_id)

        pipeline_page.pan_canvas(PAN_DX, PAN_DY, timeout=UI_ELEMENT_TIMEOUT)

        panned_transform = pipeline_page.get_canvas_viewport_transform()
        panned_box = pipeline_page.get_node_bounding_box(probe_node_id)

        tx_delta = panned_transform["tx"] - pre_pan_transform["tx"]
        ty_delta = panned_transform["ty"] - pre_pan_transform["ty"]
        assert tx_delta == pytest.approx(PAN_DX, abs=1.0), (
            f"Viewport translate-x should shift by the exact drag delta ({PAN_DX}px), got {tx_delta:.1f}px"
        )
        assert ty_delta == pytest.approx(PAN_DY, abs=1.0), (
            f"Viewport translate-y should shift by the exact drag delta ({PAN_DY}px), got {ty_delta:.1f}px"
        )
        assert panned_transform["scale"] == pytest.approx(pre_pan_transform["scale"], abs=1e-6), (
            "Panning should not change the zoom scale"
        )

        node_dx = panned_box["x"] - pre_pan_box["x"]
        node_dy = panned_box["y"] - pre_pan_box["y"]
        assert node_dx == pytest.approx(PAN_DX, abs=1.0), (
            f"Node {probe_node_id!r} x-position should shift by the same drag delta, got {node_dx:.1f}px"
        )
        assert node_dy == pytest.approx(PAN_DY, abs=1.0), (
            f"Node {probe_node_id!r} y-position should shift by the same drag delta, got {node_dy:.1f}px"
        )

    with allure.step(
        "Step 7 — Click Fit View again, verify canvas returns to the all-nodes-visible state"
    ):
        pipeline_page.fit_canvas_view(timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.all_nodes_within_viewport(), (
            "All nodes should be fully visible again after clicking Fit View a second time"
        )
        restored_transform = pipeline_page.get_canvas_viewport_transform()
        assert restored_transform["scale"] == pytest.approx(baseline_transform["scale"], abs=1e-6), (
            f"Fit View should be deterministic — scale should return to the original "
            f"{baseline_transform['scale']}, got {restored_transform['scale']}"
        )
        assert restored_transform["tx"] == pytest.approx(baseline_transform["tx"], abs=1.0), (
            f"Fit View should be deterministic — translate-x should return to the original "
            f"{baseline_transform['tx']}, got {restored_transform['tx']}"
        )
        assert restored_transform["ty"] == pytest.approx(baseline_transform["ty"], abs=1.0), (
            f"Fit View should be deterministic — translate-y should return to the original "
            f"{baseline_transform['ty']}, got {restored_transform['ty']}"
        )
