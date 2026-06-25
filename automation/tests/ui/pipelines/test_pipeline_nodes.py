"""UI Tests for Pipeline Node Operations.

Tests adding nodes to the pipeline canvas via the + button menu.
Each test uses the ``pipeline_id`` fixture for a fresh isolated pipeline
that is automatically cleaned up after the test.

Test IDs:
    PIPE-031: Add Human-in-the-loop node and verify connection to END

Markers:
    - ui: requires browser
    - pipelines: pipeline-related tests
    - p1: priority marker

Usage:
    cd automation
    pytest tests/ui/pipelines/test_pipeline_nodes.py -v
"""

import pytest
from tests.ui.pipelines.helpers import _navigate_to_canvas
import allure

pytestmark = [pytest.mark.ui, pytest.mark.pipelines]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000


# ===========================================================================
# Tests — Adding nodes to the canvas
# ===========================================================================


class TestAddNode:
    """PIPE-031: Human-in-the-loop node addition and connection test."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0853_pipeline-node-operations-add-edit-delete-connect.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_add_human_in_the_loop_node_and_connect_to_end(self, page, pipeline_id):
        """PIPE-031: Add a HITL node and connect it to END.

        Exercises the complete user flow of adding a Human-in-the-loop node
        to the pipeline canvas and wiring it into the graph. Verifies:
        1. The node appears on the canvas with correct type
        2. The node can be connected to END via drag operation

        The HITL node has three output handles (approve, edit, reject).
        This test connects the approve handle to END.
        """
        pipelines = _navigate_to_canvas(page, pipeline_id)

        initial_count = pipelines.get_node_count()

        # Add the HITL node via the + menu
        pipelines.add_node("Human-in-the-loop")

        # Wait for the node to appear — HITL maps to CSS class "hitl"
        hitl_id = pipelines.wait_for_node_on_canvas("hitl", timeout=UI_ELEMENT_TIMEOUT)

        # Verify the node is present on the canvas
        assert hitl_id, (
            "Human-in-the-loop node should have a non-empty data-id after being added"
        )

        node_count = pipelines.get_node_count()
        assert node_count == initial_count + 1, (
            f"Node count should be {initial_count + 1} after adding HITL node: "
            f"before={initial_count}, after={node_count}"
        )

        # Fit view so both nodes are visible for the drag operation.
        pipelines.fit_view()
        pipelines.wait_for_network()

        # Connect HITL → END (using approve handle)
        pipelines.connect_nodes(hitl_id, "END", source_handle="approve")
        pipelines.wait_for_network()

        # Verify the edge was created
        assert pipelines.edge_exists(hitl_id, "END"), (
            f"Edge from HITL node '{hitl_id}' to 'END' should exist after connecting"
        )
