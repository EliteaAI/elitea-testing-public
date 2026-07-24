"""UI Tests for Pipeline Add Node Menu.

Covers ELITEA-2030: the "Add node" menu lists all 11 currently-supported node
types, selecting a type adds that node to the canvas with its default
configuration panel already open, and the menu can be dismissed — via Escape
or a click genuinely outside its popup panel — without adding a node.

Test IDs:
    ELITEA-2030: Pipeline — Add Node Menu

Markers:
    - ui: requires browser
    - pipelines: pipeline-related tests
    - p2: priority marker

Usage:
    cd automation
    pytest tests/ui/pipelines/test_pipeline_add_node_menu.py -v
"""

import allure
import pytest

from tests.ui.pipelines.helpers import _navigate_to_canvas

pytestmark = [pytest.mark.ui, pytest.mark.pipelines]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000

# Expected node-type menu contents — verbatim from the source enum, confirmed
# live during AFS analysis (AddNodeMenu.jsx's getVisibleNodeTypes(), filtered
# against DeprecatedConstants.DeprecatedOrInvisibleNode). Exactly 11 entries;
# order matches the menu's own confirmed live DOM order (alphabetical by
# label — see ELITEA-2030 AFS Concrete Handles).
EXPECTED_NODE_TYPE_LABELS = {
    "agent": "Agent",
    "code": "Code",
    "custom": "Custom",
    "decision": "Decision",
    "hitl": "Human-in-the-loop",
    "llm": "LLM",
    "mcp": "MCP",
    "printer": "Printer",
    "router": "Router",
    "state_modifier": "State modifier",
    "toolkit": "Toolkit",
}


class TestAddNodeMenu:
    """ELITEA-2030: Add Node menu lists all types, adds a node, dismisses."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/pipelines/ELITEA-2030_pipeline-add-node-menu.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_add_node_menu_lists_all_types_and_adds_llm_node(self, page, pipeline_id):
        """ELITEA-2030 steps 1-6 (Escape gesture): the menu lists all 11
        node types with the expected labels, selecting LLM adds the node
        with its default configuration panel already open, and re-opening
        + pressing Escape dismisses the menu without adding a second node.
        """
        with allure.step("Step 1 — Navigate to pipeline canvas"):
            pipelines = _navigate_to_canvas(page, pipeline_id)
            assert pipelines.get_node_count() == 1, (
                "Fresh pipeline should start with only the END node"
            )

        with allure.step("Step 2 — Click 'Add node' button and verify the menu opens"):
            pipelines.open_add_node_menu(timeout=UI_ELEMENT_TIMEOUT)
            assert pipelines.is_add_node_menu_open(), (
                "Add node menu should be open (aria-expanded=true) after clicking the trigger"
            )

        with allure.step("Step 3 — Verify all 11 node types are listed with the expected labels"):
            for type_slug, expected_label in EXPECTED_NODE_TYPE_LABELS.items():
                actual_label = pipelines.get_add_node_menu_item_label(
                    type_slug, timeout=UI_ELEMENT_TIMEOUT
                )
                assert actual_label == expected_label, (
                    f"Menu item '{type_slug}' should show label '{expected_label}', "
                    f"got '{actual_label}'"
                )

        with allure.step("Step 4 — Click 'LLM' to add an LLM node"):
            pipelines.click_add_node_menu_item("llm", timeout=UI_ELEMENT_TIMEOUT)
            assert not pipelines.is_add_node_menu_open(), (
                "Menu should close after selecting a node type"
            )
            llm_node_id = pipelines.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
            assert llm_node_id, (
                "LLM node should have a non-empty data-id after being added"
            )
            assert pipelines.get_node_count() == 2, (
                "Node count should increase from 1 to 2 after adding the LLM node"
            )

        with allure.step("Step 5 — Verify the new LLM node's default configuration panel is open"):
            node_text = pipelines.get_node_rendered_text(llm_node_id, timeout=UI_ELEMENT_TIMEOUT)
            for expected_field in ("System", "Task", "Chat history"):
                assert expected_field in node_text, (
                    f"LLM node's rendered text should contain '{expected_field}' "
                    f"(config panel should be open by default): {node_text!r}"
                )

        with allure.step(
            "Step 6 — Re-open the menu and press Escape; verify it dismisses without adding a node"
        ):
            pipelines.open_add_node_menu(timeout=UI_ELEMENT_TIMEOUT)
            pipelines.close_add_node_menu_via_escape(timeout=UI_ELEMENT_TIMEOUT)
            assert pipelines.get_node_count() == 2, (
                "Node count should be unchanged after dismissing the menu via Escape"
            )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/pipelines/ELITEA-2030_pipeline-add-node-menu.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_add_node_menu_dismiss_via_click_outside(self, page, pipeline_id):
        """ELITEA-2030 step 6, alternate gesture: clicking genuinely outside
        the menu's popup panel dismisses it without adding a node.
        """
        with allure.step("Step 1 — Navigate to pipeline canvas"):
            pipelines = _navigate_to_canvas(page, pipeline_id)
            assert pipelines.get_node_count() == 1, (
                "Fresh pipeline should start with only the END node"
            )

        with allure.step("Step 2 — Click 'Add node' button and verify the menu opens"):
            pipelines.open_add_node_menu(timeout=UI_ELEMENT_TIMEOUT)
            assert pipelines.is_add_node_menu_open(), (
                "Add node menu should be open (aria-expanded=true) after clicking the trigger"
            )

        with allure.step(
            "Step 3 — Click a point genuinely outside the menu's popup panel; "
            "verify it dismisses without adding a node"
        ):
            pipelines.dismiss_add_node_menu_by_click_outside(timeout=UI_ELEMENT_TIMEOUT)
            assert not pipelines.is_add_node_menu_open(), (
                "Menu should close after clicking outside its popup panel"
            )
            assert pipelines.get_node_count() == 1, (
                "Node count should be unchanged after dismissing the menu via click-outside"
            )
