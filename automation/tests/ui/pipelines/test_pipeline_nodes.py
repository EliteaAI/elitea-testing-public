"""UI Tests for Pipeline Node Operations.

Tests adding nodes to the pipeline canvas via the + button menu, and
creating edges (transitions) between existing ordinary nodes.
Each test uses a fresh isolated pipeline fixture that is automatically
cleaned up after the test.

Test IDs:
    PIPE-031: Add Human-in-the-loop node and verify connection to END
    ELITEA-2031: Edge creation between two ordinary nodes (drag-connect)

Markers:
    - ui: requires browser
    - pipelines: pipeline-related tests
    - p1/p2: priority marker

Usage:
    cd automation
    pytest tests/ui/pipelines/test_pipeline_nodes.py -v
"""

import re

import pytest
from tests.ui.pipelines.helpers import _navigate_to_canvas
import allure

from config import settings

pytestmark = [pytest.mark.ui, pytest.mark.pipelines]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000

# The END node's edge-endpoint id on a YAML-derived edge (loaded from the
# pipeline's own transition graph, e.g. right after navigate()/reload()) is
# the literal string "EliteAPipelineEnd" — NOT "END" (see _surface.md's
# Edge-id quirk, confirmed live during ELITEA-2018/ELITEA-2031 analysis).
# edge_exists(source, "END") silently false-negatives for these edges.
_END_NODE_ID = "EliteAPipelineEnd"


# ===========================================================================
# Tests — Adding nodes to the canvas
# ===========================================================================


class TestAddNode:
    """PIPE-031: Human-in-the-loop node addition and connection test."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0853_pipeline-node-operations-add-edit-delete-connect.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_add_human_in_the_loop_node_and_connect_to_end(self, page, pipeline_id):
        """PIPE-031: Add a HITL node and connect it to END."""
        with allure.step("Step 1 — Navigate to pipeline canvas"):
            pipelines = _navigate_to_canvas(page, pipeline_id)
            initial_count = pipelines.get_node_count()

        with allure.step("Step 2 — Add Human-in-the-loop node via + menu"):
            pipelines.add_node("Human-in-the-loop")

        with allure.step("Step 3 — Wait for HITL node to appear on canvas"):
            hitl_id = pipelines.wait_for_node_on_canvas("hitl", timeout=UI_ELEMENT_TIMEOUT)
            assert hitl_id, (
                "Human-in-the-loop node should have a non-empty data-id after being added"
            )

        with allure.step("Step 4 — Verify node count increased"):
            node_count = pipelines.get_node_count()
            assert node_count == initial_count + 1, (
                f"Node count should be {initial_count + 1} after adding HITL node: "
                f"before={initial_count}, after={node_count}"
            )

        with allure.step("Step 5 — Connect HITL node to END (approve handle)"):
            pipelines.fit_view()
            pipelines.wait_for_network()
            pipelines.connect_nodes(hitl_id, "END", source_handle="approve")
            pipelines.wait_for_network()

        with allure.step("Step 6 — Verify edge from HITL to END exists"):
            assert pipelines.edge_exists(hitl_id, "END"), (
                f"Edge from HITL node '{hitl_id}' to 'END' should exist after connecting"
            )


# ===========================================================================
# Tests — Edge creation between existing ordinary nodes
# ===========================================================================


class TestEdgeCreation:
    """ELITEA-2031: Edge creation between two ordinary pipeline nodes."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/pipelines/"
        "ELITEA-2031_pipeline-edge-creation-between-nodes.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_edge_creation_between_llm_and_printer_nodes(
        self, page, pipeline_with_llm_and_printer_id
    ):
        """ELITEA-2031: Drag-connect LLM 1 -> Printer 1.

        An ordinary node type (LLM, Printer, ...) has no in-panel
        transition/routes field (that field only exists for HITL/Router
        nodes — case-text clarification EliteaAI/elitea-testing-public#1031).
        The real, live mechanism for setting an ordinary node's transition
        target is a canvas drag-connect, which this test exercises end to
        end: baseline -> drag -> canvas + YAML verification -> save ->
        reload -> persistence verification.
        """
        pipeline_id = pipeline_with_llm_and_printer_id
        project_id = str(settings.elitea_project_id)

        # Registered before Step 1 so console errors from every step (zoom,
        # drag, YAML switch, save, reload) are captured — AFS Step 6 checks
        # the whole flow, not just the tail.
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        with allure.step(
            "Step 1 — Open pipeline with 2 nodes (LLM 1 + Printer 1); verify baseline"
        ):
            pipelines = _navigate_to_canvas(page, pipeline_id)
            pipelines.zoom_in()
            pipelines.fit_view()

            # get_node_count() counts every .react-flow__node in the DOM,
            # including END (matches the merged test_save_multi_node_pipeline
            # precedent: 1 custom node + END == 2) — confirmed live via
            # get_node_ids() == ['END', 'LLM 1', 'Printer 1'] on this exact
            # fixture (AFS amended per this implementer-exploration finding).
            node_count = pipelines.get_node_count()
            assert node_count == 3, (
                f"Expected 3 nodes (LLM 1 + Printer 1 + END), got {node_count}"
            )
            assert pipelines.edge_exists("LLM 1", _END_NODE_ID), (
                "Baseline: 'LLM 1' should start wired to END"
            )
            assert pipelines.edge_exists("Printer 1", _END_NODE_ID), (
                "Baseline: 'Printer 1' should start wired to END"
            )

        with allure.step(
            "Step 2 — LLM node panel has no transition/routes field for this node "
            "type (case-text clarification EliteaAI/elitea-testing-public#1031); the "
            "real mechanism is the canvas drag-connect exercised in Step 3"
        ):
            # Documentary step only — no UI assertion beyond the connect
            # action itself (AFS Coverage Map row 2 / Known Defects).
            pass

        with allure.step(
            "Step 3 — Drag-connect LLM 1 -> Printer 1; transition updates client-side"
        ):
            pipelines.connect_nodes("LLM 1", "Printer 1")
            assert pipelines.edge_exists("LLM 1", "Printer 1"), (
                "Edge 'LLM 1' -> 'Printer 1' should exist immediately after the drag"
            )

            pipelines.switch_to_yaml_view()
            yaml_content = pipelines.get_yaml_content()
            llm_block = re.search(
                r"-\s*id:\s*LLM 1\b(.*?)(?=\n-\s*id:|\Z)", yaml_content, re.DOTALL
            )
            assert llm_block, (
                f"'LLM 1' node block not found in YAML view, got: {yaml_content}"
            )
            assert "transition: Printer 1" in llm_block.group(1), (
                f"'LLM 1' node's transition should read 'Printer 1' after the drag, "
                f"got node block: {llm_block.group(1)!r}"
            )
            pipelines.switch_to_flow_view()

        with allure.step(
            "Step 4 — Edge appears on canvas; old LLM 1 -> END edge is gone "
            "(not merely superseded); Printer 1 -> END unaffected"
        ):
            assert pipelines.edge_exists("LLM 1", "Printer 1"), (
                "Edge 'LLM 1' -> 'Printer 1' should be drawn on the canvas"
            )
            assert not pipelines.edge_exists("LLM 1", _END_NODE_ID), (
                "Old edge 'LLM 1' -> END should be gone, not merely superseded "
                "by an additional edge"
            )
            assert pipelines.edge_exists("Printer 1", _END_NODE_ID), (
                "Untouched edge 'Printer 1' -> END should remain, scoped only "
                "to the node actually edited"
            )

        with allure.step(
            "Step 5 — Save and reload; edge persists; untouched edge persists; "
            "Save re-disables"
        ):
            assert pipelines.is_save_enabled(), "Save should be enabled after the edit"
            save_response = pipelines.save_and_wait_for_update(
                project_id, pipeline_id, timeout=FORM_SAVE_TIMEOUT
            )
            assert save_response is not None, (
                "Save should return the persisted pipeline version"
            )

            page.reload()
            pipelines.wait_for_network()
            pipelines.wait_for_detail_page_load()
            pipelines.dismiss_banner_if_present()
            pipelines.wait_for_canvas()

            assert pipelines.edge_exists("LLM 1", "Printer 1"), (
                "Edge 'LLM 1' -> 'Printer 1' should persist after a hard reload"
            )
            assert pipelines.edge_exists("Printer 1", _END_NODE_ID), (
                "Untouched edge 'Printer 1' -> END should still be present after reload"
            )
            assert not pipelines.is_save_enabled(), (
                "Save should be disabled again after reload (clean state)"
            )

        with allure.step("Step 6 — No console errors across the whole flow"):
            assert not console_errors, (
                f"No console errors expected, got: {[e.text for e in console_errors]}"
            )
