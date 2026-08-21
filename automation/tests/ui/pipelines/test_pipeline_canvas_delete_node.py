"""UI test — Pipeline Canvas: Delete Node.

TMS: ELITEA-2018
(test-specs/pipelines/l2_pipeline-canvas-delete-node_ELITEA-2018.md)

Seeds a pipeline ``LLM 1 -> Code 1 -> END`` (3 nodes, 2 edges) via the API,
deletes the middle node (Code 1) via its 3-dot header menu, and confirms
both its edges are removed (with no auto-reconnect of LLM 1 -> END), LLM 1
and END remain, and the deletion survives Save + full page reload.

Case-text drift (AFS Preconditions, filed as
EliteaAI/elitea-testing-public#1137, clarification): the case's own Step 1
implies adding "LLM" then "Code" via the canvas "+" menu auto-creates the
connecting edges. Confirmed live it does not — each node added via the menu
lands disconnected. The precondition is seeded via
``PipelineAPI.create_pipeline_with_nodes()`` with explicit ``transition``
fields instead.
"""

import allure
import pytest

from tests.ui.pipelines.helpers import _navigate_to_canvas

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2018_pipeline-canvas-delete-node.md",
    "onetest-ai Test Case link",
)
def test_delete_middle_node_removes_its_edges_and_persists(page, pipeline_llm_code_end):
    """Deleting the middle node (Code 1) removes it + both its edges; LLM 1
    and END remain; the deletion persists after Save + reload."""
    with allure.step("Step 1 — Navigate to the pipeline's canvas"):
        pipeline_page = _navigate_to_canvas(page, pipeline_llm_code_end)
        node_ids = set(pipeline_page.get_node_ids())
        assert node_ids == {"END", "LLM 1", "Code 1"}, (
            f"Canvas should show exactly 3 seeded nodes, got: {node_ids}"
        )
        assert pipeline_page.get_edge_count() == 2, (
            f"Canvas should show 2 seeded edges (LLM 1->Code 1, Code 1->END), "
            f"got {pipeline_page.get_edge_count()}"
        )

    with allure.step(
        "Step 2/3 — Delete the Code node via its 3-dot header menu -> Delete -> confirm"
    ):
        pipeline_page.delete_node("Code 1", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 4 — Verify Code node is removed from canvas"):
        node_ids_after_delete = set(pipeline_page.get_node_ids())
        assert "Code 1" not in node_ids_after_delete, (
            f"Code 1 should be removed from canvas, got: {node_ids_after_delete}"
        )

    with allure.step("Step 5 — Verify both edges connected to Code node are also removed"):
        edge_count_after_delete = pipeline_page.get_edge_count()
        assert edge_count_after_delete == 0, (
            "Edge count should be exactly 0 after deleting the middle node — both its "
            f"edges (LLM 1->Code 1, Code 1->END) should be gone with no auto-reconnect, "
            f"got {edge_count_after_delete}"
        )

    with allure.step("Step 6 — Verify LLM and END nodes remain"):
        assert node_ids_after_delete == {"END", "LLM 1"}, (
            f"Canvas should show exactly {{'END', 'LLM 1'}} after deletion, "
            f"got: {node_ids_after_delete}"
        )

    with allure.step("Step 7 — Save, then reload — verify deletion persists"):
        assert pipeline_page.save_button.is_enabled(), (
            "Save button should be enabled immediately after the delete — node/edge "
            "deletion is an unsaved canvas change"
        )
        pipeline_page.save_button.click()
        pipeline_page.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
        page.reload()
        pipeline_page.wait_for_canvas()

        node_ids_after_reload = set(pipeline_page.get_node_ids())
        assert node_ids_after_reload == {"END", "LLM 1"}, (
            f"Deletion should persist after Save + reload, got: {node_ids_after_reload}"
        )
