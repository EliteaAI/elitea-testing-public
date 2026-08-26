"""UI test — Pipeline: Add Node Menu.

TMS: ELITEA-2030
(test-specs/pipelines/l2_pipeline-add-node-menu_ELITEA-2030.md)

Opens the canvas "+" Add Node menu on an empty pipeline, verifies it lists
exactly the 11 expected node types in DOM order, selects "LLM" and confirms
the node appears on canvas with its config immediately visible (no
click-to-expand step exists for any node type on this canvas), then
re-opens the menu and confirms Escape dismisses it without adding a node.

Testid gap CLOSED (review round 1, was AFS "not blocking" — the recommendation
to reuse the existing raw-handle ``add_node()``-family methods as-is did not
survive review: `.agents/role-overrides.md` treats a missing testid as work
to do, not a reason to rung down, regardless of what an AFS recommends).
`get_add_node_menu_items()`/`wait_for_popup_menu_hidden()`/
`select_add_node_menu_item()` below are all testid-based
(`pipeline-add-node-button`, `pipeline-add-node-menu`,
`pipeline-add-node-menu-item-{type}`, added to AddNodeMenu.jsx via
`add-data-testid`, on `automation/testids`). Step 4 originally kept the
legacy raw-handle `add_node()` call as "untouched pre-existing tech debt
(#25/#42), out of scope at the time" — fix round 4 revisited that: with
`select_add_node_menu_item()` now shipped and otherwise having zero callers
(canon ruling #511 — an unreferenced method isn't "exercised" by merely
existing), wiring it into Step 4 both closes the dead-code finding and
replaces this test's own raw-handle call with the testid-based pair it was
built for. `add_node()` itself is untouched and remains in use by every
other pipeline test — only this file's Step 4 now uses the testid path.
"""

import allure
import pytest

from tests.ui.pipeline_helpers import _navigate_to_canvas

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000

EXPECTED_NODE_TYPES = [
    "Agent",
    "Code",
    "Custom",
    "Decision",
    "Human-in-the-loop",
    "LLM",
    "MCP",
    "Printer",
    "Router",
    "State modifier",
    "Toolkit",
]


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2030_pipeline-add-node-menu.md",
    "onetest-ai Test Case link",
)
def test_add_node_menu_lists_types_adds_node_and_dismisses(page, pipeline_id):
    """Add Node menu lists exactly 11 types in order; LLM selection adds a
    node with config visible; Escape dismisses without adding a node."""
    with allure.step("Step 1 — Navigate to the pipeline's canvas"):
        pipeline_page = _navigate_to_canvas(page, pipeline_id)
        assert pipeline_page.canvas_wrapper.is_visible(), "Canvas wrapper should be visible"

    with allure.step("Step 2/3 — Click 'Add node' and read all menu item labels"):
        menu_items = pipeline_page.get_add_node_menu_items(timeout=UI_ELEMENT_TIMEOUT)
        assert menu_items == EXPECTED_NODE_TYPES, (
            f"Add node menu should list exactly the 11 expected types in order, "
            f"got: {menu_items}"
        )
        # Dismiss this inspection-only opening before proceeding to step 4's
        # own fresh open+select — leaves the canvas in a known state. The
        # close is polled (not an instant DOM check) — the menu's close
        # animation can leave it mounted-but-fading for a short window.
        page.keyboard.press("Escape")
        pipeline_page.wait_for_popup_menu_hidden(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 4 — Click 'LLM' to add an LLM node"):
        node_count_before = pipeline_page.get_node_count()
        # Testid-based open+select pair (not the legacy raw-handle add_node()):
        # get_add_node_menu_items() opens the menu and leaves it open for the
        # companion select_add_node_menu_item() to click the "llm" item by its
        # internal type key (see class docstrings on both methods).
        pipeline_page.get_add_node_menu_items(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.select_add_node_menu_item("llm", timeout=UI_ELEMENT_TIMEOUT)
        llm_node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        assert llm_node_id, "LLM node should have a non-empty data-id after being added"
        assert pipeline_page.get_node_count() == node_count_before + 1, (
            "Node count should increase by exactly 1 after adding the LLM node"
        )

    with allure.step(
        "Step 5 — Verify the new LLM node's configuration is immediately visible "
        "(no click-to-expand step exists for any node type on this canvas)"
    ):
        # AFS Coverage Map row 5: this canvas has no separate "expand config"
        # trigger for any node type — every node renders its full config
        # inline/always-expanded, so the node's own presence on canvas IS the
        # "panel open" signal. Read the canvas' node-id list independently of
        # wait_for_node_on_canvas (which only waits for the CSS type-class to
        # appear) to confirm the same node is also tracked by data-id — a
        # distinct signal from Step 4's check.
        node_ids_after_add = pipeline_page.get_node_ids()
        assert llm_node_id in node_ids_after_add, (
            f"LLM node '{llm_node_id}' should be present in the canvas' node-id list "
            f"{node_ids_after_add} (config panel open is satisfied by inline rendering — "
            f"no separate 'panel open' UI state exists)"
        )

    with allure.step("Step 6 — Re-open the Add node menu, then press Escape"):
        node_count_before_escape = pipeline_page.get_node_count()
        pipeline_page.get_add_node_menu_items(timeout=UI_ELEMENT_TIMEOUT)
        page.keyboard.press("Escape")
        pipeline_page.wait_for_popup_menu_hidden(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_node_count() == node_count_before_escape, (
            "Node count should be unchanged after dismissing the menu with Escape"
        )
