"""UI test — Pipeline: Node Auto-Increment Naming.

TMS: ELITEA-2061
(test-specs/pipelines/l2_pipeline-node-auto-increment-naming_ELITEA-2061.md)

Adds two LLM nodes to an empty pipeline via the canvas "+" Add Node menu and
confirms the auto-generated node names increment ("LLM 1", then "LLM 2"),
then adds a Code node and confirms its counter starts independently at 1
("Code 1"), not continuing the LLM sequence.

Source case title ("Pipeline — Node Duplicate via Node Menu") is stale
metadata — no "Duplicate" action exists on the node menu (Delete and
Expand/Collapse only); the case's own Objective/Steps describe auto-naming
on ADD, which is what this test automates. See the AFS's "Case-text note"
section for the full CLARIFICATION.

Identifies each newly-added node via a `get_node_ids()` before/after
set-difference rather than `wait_for_node_on_canvas()`'s return value, which
resolves via `.first` and returns the WRONG (pre-existing) node id once a
second node of the same type exists on canvas — a documented live collision
(`test-specs/pipelines/_surface.md` § "Flow → YAML sync +
`wait_for_node_on_canvas()` same-type collision").
"""

import allure
import pytest

from tests.ui.pipelines.helpers import _navigate_to_canvas

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000


def _add_node_and_get_new_id(pipeline_page, internal_type: str) -> str:
    """Add one node of *internal_type* via the Add Node menu; return its new node id.

    Uses the before/after `get_node_ids()` set-difference pattern (not
    `wait_for_node_on_canvas()`'s return value) so the correct node is
    identified even when another node of the same type already exists on
    canvas.
    """
    ids_before = set(pipeline_page.get_node_ids())
    pipeline_page.get_add_node_menu_items(timeout=UI_ELEMENT_TIMEOUT)
    pipeline_page.select_add_node_menu_item(internal_type, timeout=UI_ELEMENT_TIMEOUT)
    pipeline_page.wait_for_node_count(len(ids_before) + 1, timeout=UI_ELEMENT_TIMEOUT)
    new_ids = set(pipeline_page.get_node_ids()) - ids_before
    assert len(new_ids) == 1, (
        f"Adding one {internal_type!r} node should add exactly one new node id, "
        f"got {new_ids!r} (before={ids_before!r})"
    )
    return new_ids.pop()


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2061_pipeline-node-duplicate-via-node-menu.md",
    "onetest-ai Test Case link",
)
def test_node_auto_increment_naming_by_type(page, pipeline_id):
    """Nodes of the same type auto-name with an incrementing number; a
    different type's counter starts independently at 1."""
    with allure.step("Step 1 — Navigate to the pipeline's canvas"):
        pipeline_page = _navigate_to_canvas(page, pipeline_id)
        assert pipeline_page.canvas_wrapper.is_visible(), "Canvas wrapper should be visible"

    with allure.step("Step 2 — Add the first LLM node; verify it is named 'LLM 1'"):
        llm_node_1_id = _add_node_and_get_new_id(pipeline_page, "llm")
        assert llm_node_1_id == "LLM 1", (
            f"First LLM node added to an empty pipeline should have data-id 'LLM 1', "
            f"got {llm_node_1_id!r}"
        )
        assert pipeline_page.get_node_name(llm_node_1_id) == "LLM 1", (
            "First LLM node's rendered display name should be 'LLM 1'"
        )

    with allure.step(
        "Step 3 — Add a second LLM node; verify its name increments to 'LLM 2'"
    ):
        llm_node_2_id = _add_node_and_get_new_id(pipeline_page, "llm")
        assert llm_node_2_id == "LLM 2", (
            f"Second LLM node should have data-id 'LLM 2' (incremented from the first "
            f"same-type node), got {llm_node_2_id!r}"
        )
        assert pipeline_page.get_node_name(llm_node_2_id) == "LLM 2", (
            "Second LLM node's rendered display name should be 'LLM 2'"
        )
        assert pipeline_page.get_node_count() == 3, (
            "Canvas should have 3 nodes (LLM 1, LLM 2, END) after adding two LLM nodes"
        )

    with allure.step(
        "Step 4 — Add a Code node (different type); verify its counter starts "
        "independently at 'Code 1', not continuing the LLM sequence"
    ):
        code_node_1_id = _add_node_and_get_new_id(pipeline_page, "code")
        assert code_node_1_id == "Code 1", (
            f"First Code node should have data-id 'Code 1' — a different type's "
            f"counter starts at 1 regardless of the LLM counter already being at 2, "
            f"got {code_node_1_id!r}"
        )
        assert pipeline_page.get_node_name(code_node_1_id) == "Code 1", (
            "First Code node's rendered display name should be 'Code 1'"
        )
        assert pipeline_page.get_node_count() == 4, (
            "Canvas should have 4 nodes (LLM 1, LLM 2, Code 1, END) after adding "
            "the Code node"
        )
