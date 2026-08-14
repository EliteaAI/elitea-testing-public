"""UI test — Pipeline Canvas: Zoom and Pan; Canvas Control Panel.

TMS: ELITEA-2019 (test_canvas_zoom_pan_and_fit_view)
(test-specs/pipelines/l2_pipeline-canvas-zoom-and-pan_ELITEA-2019.md)
TMS: ELITEA-2057 (test_canvas_control_panel_zoom_out_interactivity_cards_size_and_auto_arrange)
(test-specs/pipelines/lextend_pipeline-canvas-control-panel_ELITEA-2057.md)
— extends this module (additive-only) rather than duplicating the already-
asserted Zoom In / Fit View coverage below.

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
Steps 3/5/7 assert zero console errors and zero `prompt_lib`-related network
requests across the whole zoom -> pan -> Fit-View sequence (AFS Axis 2) —
capture starts right after the step-2 baseline is established so the initial
canvas navigation's own (expected) fetch doesn't false-positive the check.

ELITEA-2057 (second test below) covers the case's remaining, genuinely
unasserted control-panel buttons: control-panel visibility (all 6 buttons),
Zoom Out (the pre-existing ``zoom_out_canvas()`` method was never called by
any test before this), Toggle Interactivity, Toggle cards size, and
Auto-arrange — all confirmed live to be deterministic round-trips, same
pure-client-side network/console profile as Zoom In/Pan/Fit-View.
"""

import allure
import pytest

from tests.ui.pipelines.helpers import _navigate_to_canvas

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
# The exact drag delta panned in step 3 — asserted 1:1 against the resulting
# transform/bounding-box shift (confirmed live: ReactFlow pans px-perfectly).
PAN_DX = 100
PAN_DY = 80
# Pipeline persist/fetch endpoints all share this segment (e.g.
# .../application/prompt_lib/{project}/{id}, .../tool/prompt_lib/{project}/,
# .../applications/prompt_lib/{project}) — a single substring catches any
# accidental save/persist/refetch call the viewport ops must never trigger.
PIPELINE_NETWORK_SUBSTRING = "prompt_lib"


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

        # Registered right after the step-2 baseline (not before) so the
        # canvas's own initial-load fetch isn't counted — from here on,
        # zoom/pan/Fit-View are pure client-side viewport ops (AFS Network
        # Behavior) and must fire neither console errors nor pipeline
        # network requests. Checked cumulatively at steps 3, 5 and 7.
        console_errors = pipeline_page.capture_console_errors()
        viewport_op_requests = pipeline_page.capture_requests_matching(PIPELINE_NETWORK_SUBSTRING)

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
        assert not console_errors, f"Zoom In should not introduce console errors: {list(console_errors)}"
        assert not viewport_op_requests, (
            "Zoom In is a pure client-side viewport transform — expected zero "
            f"pipeline network requests, got: {list(viewport_op_requests)}"
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
        assert not console_errors, f"Panning should not introduce console errors: {list(console_errors)}"
        assert not viewport_op_requests, (
            "Panning is a pure client-side viewport transform — expected zero "
            f"pipeline network requests, got: {list(viewport_op_requests)}"
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
        assert not console_errors, (
            f"Zoom/pan/Fit-View sequence should not introduce console errors: {list(console_errors)}"
        )
        assert not viewport_op_requests, (
            "Zoom/pan/Fit-View sequence is pure client-side viewport state — "
            f"expected zero pipeline network requests, got: {list(viewport_op_requests)}"
        )
        console_errors.stop()
        viewport_op_requests.stop()


# Screen-px drag deltas used by the interactivity-lock and auto-arrange probes
# below (ELITEA-2057) — reuse the existing `move_node()` (added ELITEA-2047,
# drags from the node's header strip, clear of inner form-field inputs).
INTERACTIVITY_DRAG_DX = 60
INTERACTIVITY_DRAG_DY = 40
AUTO_ARRANGE_DRAG_DX = 150
AUTO_ARRANGE_DRAG_DY = -120


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2057_pipeline-canvas-control-panel.md",
    "onetest-ai Test Case link",
)
def test_canvas_control_panel_zoom_out_interactivity_cards_size_and_auto_arrange(page, pipeline_llm_code_end):
    """Extends the ELITEA-2019 coverage above with the case's remaining
    control-panel buttons: visibility of all 6 buttons, Zoom Out (the
    pre-existing `zoom_out_canvas()` method was never exercised by any
    test before this), Toggle Interactivity (lock/unlock node dragging),
    Toggle cards size (compact/expanded node height, exact round trip), and
    Auto-arrange (deterministic layout — a dragged-away node returns to its
    exact original position)."""
    with allure.step("Step 1 — Navigate to the pipeline's canvas"):
        pipeline_page = _navigate_to_canvas(page, pipeline_llm_code_end)
        node_ids = pipeline_page.get_node_ids()
        assert pipeline_page.get_node_count() == 3, (
            f"Canvas should show exactly 3 seeded nodes, got {pipeline_page.get_node_count()}"
        )
        probe_node_id = "LLM 1"
        assert probe_node_id in node_ids, f"Expected probe node {probe_node_id!r} in {node_ids}"
        pipeline_page.fit_canvas_view(timeout=UI_ELEMENT_TIMEOUT)

        # Registered right after the Fit-View baseline (not before) so the
        # canvas's own initial-load fetch isn't counted — from here on, every
        # control-panel action in this test must fire neither console errors
        # nor pipeline network requests, same as the zoom/pan/Fit-View test
        # above. Checked cumulatively at every step below.
        console_errors = pipeline_page.capture_console_errors()
        viewport_op_requests = pipeline_page.capture_requests_matching(PIPELINE_NETWORK_SUBSTRING)

    with allure.step("Step 2 — Verify the control panel is visible with all 6 buttons"):
        assert pipeline_page.is_control_panel_fully_visible(timeout=UI_ELEMENT_TIMEOUT), (
            "All 6 canvas control-panel buttons (Zoom In, Zoom Out, Fit View, "
            "Toggle Interactivity, Toggle cards size, Auto-arrange) should be visible"
        )
        assert not console_errors, f"Control panel should be visible with no console errors: {list(console_errors)}"

    with allure.step("Step 4 — Click Zoom Out, verify canvas scale and node size both decrease"):
        baseline_transform = pipeline_page.get_canvas_viewport_transform()
        baseline_box = pipeline_page.get_node_bounding_box(probe_node_id)

        pipeline_page.zoom_out_canvas(timeout=UI_ELEMENT_TIMEOUT)

        zoomed_out_transform = pipeline_page.get_canvas_viewport_transform()
        zoomed_out_box = pipeline_page.get_node_bounding_box(probe_node_id)

        assert zoomed_out_transform["scale"] < baseline_transform["scale"], (
            f"Zoom Out should decrease viewport scale: "
            f"{baseline_transform['scale']} -> {zoomed_out_transform['scale']}"
        )
        baseline_area = baseline_box["width"] * baseline_box["height"]
        zoomed_out_area = zoomed_out_box["width"] * zoomed_out_box["height"]
        assert zoomed_out_area < baseline_area, (
            f"Node {probe_node_id!r} should appear smaller after Zoom Out: "
            f"{baseline_area:.1f}px^2 -> {zoomed_out_area:.1f}px^2"
        )
        assert not console_errors, f"Zoom Out should not introduce console errors: {list(console_errors)}"
        assert not viewport_op_requests, (
            "Zoom Out is a pure client-side viewport transform — expected zero "
            f"pipeline network requests, got: {list(viewport_op_requests)}"
        )

    with allure.step("Step 6 — Toggle Interactivity off then on, verify node dragging locks and unlocks"):
        pre_toggle_box = pipeline_page.get_node_bounding_box(probe_node_id)

        pipeline_page.toggle_canvas_interactivity(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.move_node(probe_node_id, INTERACTIVITY_DRAG_DX, INTERACTIVITY_DRAG_DY)
        locked_box = pipeline_page.get_node_bounding_box(probe_node_id)
        assert locked_box["x"] == pytest.approx(pre_toggle_box["x"], abs=1.0), (
            f"Node {probe_node_id!r} should NOT move while interactivity is off "
            f"(x): {pre_toggle_box['x']:.1f} -> {locked_box['x']:.1f}"
        )
        assert locked_box["y"] == pytest.approx(pre_toggle_box["y"], abs=1.0), (
            f"Node {probe_node_id!r} should NOT move while interactivity is off "
            f"(y): {pre_toggle_box['y']:.1f} -> {locked_box['y']:.1f}"
        )

        pipeline_page.toggle_canvas_interactivity(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.move_node(probe_node_id, INTERACTIVITY_DRAG_DX, INTERACTIVITY_DRAG_DY)
        unlocked_box = pipeline_page.get_node_bounding_box(probe_node_id)
        dx = unlocked_box["x"] - locked_box["x"]
        dy = unlocked_box["y"] - locked_box["y"]
        # abs=6.0 (not the pan_canvas/get_canvas_viewport_transform tests' abs=1.0):
        # confirmed live a NODE drag (unlike a canvas-PANE drag) absorbs a few px
        # into ReactFlow's own node-drag-activation threshold before it starts
        # tracking the mouse 1:1 (observed 56px delivered for a 60px request,
        # i.e. ~4px lost) — a real, distinct-from-pan interaction detail, not
        # test flakiness; still tight enough to fail hard on a genuinely locked
        # node (which would show ~0px, not ~54-60px).
        assert dx == pytest.approx(INTERACTIVITY_DRAG_DX, abs=6.0), (
            f"Node {probe_node_id!r} SHOULD move by (approximately) the exact drag delta once "
            f"interactivity is re-enabled (x-delta), got {dx:.1f}px"
        )
        assert dy == pytest.approx(INTERACTIVITY_DRAG_DY, abs=6.0), (
            f"Node {probe_node_id!r} SHOULD move by (approximately) the exact drag delta once "
            f"interactivity is re-enabled (y-delta), got {dy:.1f}px"
        )
        assert not console_errors, f"Toggle Interactivity should not introduce console errors: {list(console_errors)}"
        assert not viewport_op_requests, (
            "Toggle Interactivity is a pure client-side operation — expected zero "
            f"pipeline network requests, got: {list(viewport_op_requests)}"
        )

    with allure.step("Step 7 — Toggle cards size, verify node height shrinks then restores exactly"):
        # Toggle cards size internally RE-LAYOUTS node positions AND re-fits the
        # view (FlowEditor's onExpandAll -> onReLayout -> fitView) — it does not
        # merely resize cards in place. A plain Fit View (no re-layout) on top of
        # step 6's manually-dragged position is therefore NOT the same basis the
        # post-toggle measurements land on (confirmed during implementation: a
        # plain-Fit-View baseline produced a false mismatch, 232.9px vs 251.2px,
        # then 304.0px vs 251.2px on a second attempt — the manually-dragged
        # position doesn't match the re-layout-computed one). Use Auto-arrange
        # itself to establish the baseline so it's on the SAME "re-layout +
        # fit-view" basis every subsequent toggle/re-arrange in this test lands
        # on — this is the reset-to-known-state technique, not an assertion
        # about Auto-arrange (that's step 8's job).
        pipeline_page.auto_arrange_canvas(timeout=UI_ELEMENT_TIMEOUT)
        expanded_box = pipeline_page.get_node_bounding_box(probe_node_id)

        pipeline_page.toggle_canvas_cards_size(timeout=UI_ELEMENT_TIMEOUT)
        compact_box = pipeline_page.get_node_bounding_box(probe_node_id)
        assert compact_box["height"] < expanded_box["height"] / 2, (
            f"Node {probe_node_id!r} should shrink to a compact card height: "
            f"{expanded_box['height']:.1f}px -> {compact_box['height']:.1f}px"
        )

        pipeline_page.toggle_canvas_cards_size(timeout=UI_ELEMENT_TIMEOUT)
        restored_box = pipeline_page.get_node_bounding_box(probe_node_id)
        assert restored_box["height"] == pytest.approx(expanded_box["height"], abs=1.0), (
            f"Node {probe_node_id!r} should restore its exact expanded height: "
            f"{expanded_box['height']:.1f}px -> {restored_box['height']:.1f}px"
        )
        assert not console_errors, f"Toggle cards size should not introduce console errors: {list(console_errors)}"
        assert not viewport_op_requests, (
            "Toggle cards size is a pure client-side operation — expected zero "
            f"pipeline network requests, got: {list(viewport_op_requests)}"
        )

    with allure.step("Step 8 — Drag a node away, click Auto-arrange, verify it returns to the exact arranged position"):
        # Same fit-to-view-basis reasoning as step 7 — Auto-arrange also calls
        # onReLayout -> fitView internally, so the baseline must be captured
        # right after a Fit View, not after a manual drag/zoom left over from
        # an earlier step.
        pipeline_page.fit_canvas_view(timeout=UI_ELEMENT_TIMEOUT)
        arranged_box = pipeline_page.get_node_bounding_box(probe_node_id)

        pipeline_page.move_node(probe_node_id, AUTO_ARRANGE_DRAG_DX, AUTO_ARRANGE_DRAG_DY)
        dragged_box = pipeline_page.get_node_bounding_box(probe_node_id)
        assert dragged_box["x"] != pytest.approx(arranged_box["x"], abs=1.0) or dragged_box["y"] != pytest.approx(
            arranged_box["y"], abs=1.0
        ), f"Sanity check: node {probe_node_id!r} should actually have moved before Auto-arrange is clicked"

        pipeline_page.auto_arrange_canvas(timeout=UI_ELEMENT_TIMEOUT)
        rearranged_box = pipeline_page.get_node_bounding_box(probe_node_id)
        assert rearranged_box["x"] == pytest.approx(arranged_box["x"], abs=1.0), (
            f"Auto-arrange should be deterministic — node {probe_node_id!r} x-position should return to the "
            f"original {arranged_box['x']:.1f}, got {rearranged_box['x']:.1f}"
        )
        assert rearranged_box["y"] == pytest.approx(arranged_box["y"], abs=1.0), (
            f"Auto-arrange should be deterministic — node {probe_node_id!r} y-position should return to the "
            f"original {arranged_box['y']:.1f}, got {rearranged_box['y']:.1f}"
        )
        assert not console_errors, f"Auto-arrange should not introduce console errors: {list(console_errors)}"
        assert not viewport_op_requests, (
            "Auto-arrange is a pure client-side operation — expected zero "
            f"pipeline network requests, got: {list(viewport_op_requests)}"
        )
        console_errors.stop()
        viewport_op_requests.stop()
