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
from tests.ui.pipeline_helpers import _navigate_to_canvas
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

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/pipelines/ELITEA-0853_pipeline-node-operations-add-edit-delete-connect.md", "onetest-ai Test Case link")
    @pytest.mark.tms("ELITEA-0853")
    @pytest.mark.p1
    def test_add_human_in_the_loop_node_and_connect_to_end(self, page, pipeline_id):
        """PIPE-031: Add a HITL node and connect it to END."""
        with allure.step("Step 1 — Navigate to pipeline canvas"):
            pipelines = _navigate_to_canvas(page, pipeline_id)
            initial_count = pipelines.get_node_count()
            ids_before = set(pipelines.get_node_ids())

        with allure.step("Step 2 — Add Human-in-the-loop node via + menu"):
            pipelines.add_node("Human-in-the-loop")

        with allure.step("Step 3 — Wait for HITL node to appear on canvas"):
            hitl_id = pipelines.wait_for_node_on_canvas("hitl", timeout=UI_ELEMENT_TIMEOUT)
            assert hitl_id, (
                "Human-in-the-loop node should have a non-empty data-id after being added"
            )

        with allure.step("Step 4 — Verify node count increased"):
            # DEV materialises the END terminal node together with the first node on an
            # empty canvas, so the expected delta is the HITL node (+1) plus END when
            # it was not on the canvas yet.
            end_added = "END" not in ids_before
            expected_count = initial_count + 1 + (1 if end_added else 0)
            pipelines.wait_for_node_count(expected_count, timeout=UI_ELEMENT_TIMEOUT)
            node_count = pipelines.get_node_count()
            new_ids = set(pipelines.get_node_ids()) - ids_before
            assert new_ids - {"END"} == {hitl_id}, (
                f"Exactly one new non-END node (the HITL node) should be added: "
                f"before={ids_before}, new={new_ids}"
            )
            assert node_count == expected_count, (
                f"Node count should be {expected_count} after adding HITL node "
                f"(END newly added: {end_added}): before={initial_count}, after={node_count}"
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
