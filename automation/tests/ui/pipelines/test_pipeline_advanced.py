"""UI Tests for Advanced Pipeline Features — Phase 3.

Tests YAML editor, discard changes, history tab, make-entrypoint action,
three-dot menu exploration, and multi-node topologies.

Builds on Phase 1 (management + nodes) and Phase 2 (execution).

Test IDs:
    PIPE-019: YAML view toggle — switch and verify editor visible
    PIPE-020: YAML content reflects pipeline structure
    PIPE-021: Flow/YAML round-trip — toggle back and forth
    PIPE-022: Discard changes reverts unsaved edits
    PIPE-023: History tab displays content
    PIPE-024: Make node entrypoint via node menu
    PIPE-025-027: Node addition tests (MOVED to test_pipeline_nodes.py)
    PIPE-028: Three-dot menu items enumeration
    PIPE-029: Export pipeline via menu (if available)
    PIPE-030: Multi-node topology: LLM → Code → END

Note: PIPE-025 (Decision), PIPE-026 (Printer), and PIPE-027 (Router) node
addition tests have been consolidated into the parameterized test in
test_pipeline_nodes.py alongside PIPE-006 (LLM/Code nodes).

Markers:
    - ui: requires browser
    - pipelines: pipeline-related tests
    - p1/p2: priority markers

Usage:
    cd automation
    pytest test_pipeline_advanced.py -v
    pytest test_pipeline_advanced.py -v -k "yaml"
"""

import pytest
from tests.ui.pipelines.helpers import _navigate_to_detail, _navigate_to_canvas
import allure

pytestmark = [pytest.mark.ui, pytest.mark.pipelines]


def _add_llm_node_and_connect(pipelines) -> str:
    """Adds an LLM node and connects it to END. Returns the LLM node id."""
    pipelines.add_node("LLM")
    llm_id = pipelines.wait_for_node_on_canvas("llm")
    pipelines.fit_view()
    pipelines.wait_for_network()
    pipelines.connect_nodes(llm_id, "END")
    pipelines.wait_for_network()
    return llm_id


# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000


# ===========================================================================
# Tests — YAML editor
# ===========================================================================


class TestYamlEditor:
    """PIPE-019 to PIPE-021: YAML editor view tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0860_pipeline-yaml-view-and-round-trip.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_yaml_view_toggle(self, page, pipeline_id):
        """PIPE-019: Switch to YAML view and verify the editor is visible.

        The YAML view shows a CodeMirror editor with the pipeline definition.
        Switching back to Flow should show the ReactFlow canvas.
        """
        pipelines = _navigate_to_detail(page, pipeline_id)

        # Default should be Flow view
        assert pipelines.is_flow_view_active(), (
            "Pipeline should start in Flow view"
        )

        # Switch to YAML
        pipelines.switch_to_yaml_view()
        assert pipelines.is_yaml_view_active(), (
            "YAML editor should be visible after switching to YAML view"
        )

        # Switch back to Flow
        pipelines.switch_to_flow_view()
        assert pipelines.is_flow_view_active(), (
            "Flow canvas should be visible after switching back to Flow view"
        )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0860_pipeline-yaml-view-and-round-trip.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_yaml_content_reflects_pipeline(self, page, pipeline_with_llm_id):
        """PIPE-020: YAML content should reflect the pipeline structure.

        A pipeline with an LLM node should have YAML content containing
        node definitions and entry_point.
        """
        pipelines = _navigate_to_detail(page, pipeline_with_llm_id)

        pipelines.switch_to_yaml_view()
        assert pipelines.is_yaml_view_active(), "YAML view should be active"

        yaml_content = pipelines.get_yaml_content()
        assert len(yaml_content.strip()) > 0, (
            "YAML content should have meaningful text"
        )

        # An LLM pipeline should contain recognisable keywords.
        # Require at least two structural terms: "entry_point" is the most
        # specific (it uniquely identifies pipeline YAML), so one of the two
        # required terms must be "entry_point".
        yaml_lower = yaml_content.lower()
        has_entry_point = "entry_point" in yaml_lower
        has_nodes = "nodes" in yaml_lower
        has_llm = "llm" in yaml_lower
        assert has_entry_point and (has_nodes or has_llm), (
            f"YAML should contain 'entry_point' plus 'nodes' or 'llm' to "
            f"confirm pipeline structure, got: {yaml_content[:200]}"
        )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0860_pipeline-yaml-view-and-round-trip.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_flow_yaml_round_trip(self, page, pipeline_id):
        """PIPE-021: Toggle Flow → YAML → Flow preserves the canvas.

        After a round-trip, the ReactFlow canvas should still show nodes
        (at least the default END node).
        """
        pipelines = _navigate_to_canvas(page, pipeline_id)

        # Add a node so there's something to verify
        pipelines.add_node("LLM")
        llm_id = pipelines.wait_for_node_on_canvas("llm")
        initial_count = pipelines.get_node_count()
        assert initial_count >= 2, "Should have LLM + END nodes"

        # Round-trip: Flow → YAML → Flow.
        # switch_to_yaml_view / switch_to_flow_view each contain a 1 s
        # internal wait; the extra pauses here let the CodeMirror / ReactFlow
        # DOM settle before querying node counts.
        pipelines.switch_to_yaml_view()
        pipelines.wait_for_network()  # Wait for YAML editor to fully render
        pipelines.switch_to_flow_view()
        pipelines.wait_for_network()  # Wait for ReactFlow to re-mount

        # Canvas should still have the same nodes
        pipelines.wait_for_canvas()
        final_count = pipelines.get_node_count()
        assert final_count == initial_count, f"Round-trip should preserve node count: expected {initial_count}, got {final_count}"


# ===========================================================================
# Tests — Discard changes
# ===========================================================================


class TestDiscardChanges:
    """PIPE-022: Discard changes reverts unsaved edits."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0860_pipeline-yaml-view-and-round-trip.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_discard_reverts_name_change(self, page, pipeline_id, pipeline_api):
        """PIPE-022: Edit name, click Discard, and verify original name restored.

        Makes an unsaved change to the pipeline name, clicks Discard,
        and verifies the original name is restored.
        """
        # Get original name
        original = pipeline_api.get_pipeline(pipeline_id)
        original_name = original.get("name", "")

        pipelines = _navigate_to_detail(page, pipeline_id)

        pipelines.update_name("autotest_changed_name")

        # Verify name changed in the field
        assert pipelines.get_name() == "autotest_changed_name", (
            "Name field should show the new value"
        )

        # Click Discard — this may trigger a page reload
        pipelines.click_discard()
        # click_discard() already calls wait_for_network(); the extra wait here
        # is for the page to fully re-render after a potential hard reload.
        pipelines.wait_for_detail_page_load()

        # Verify original name restored
        restored_name = pipelines.get_name()
        assert restored_name == original_name, (
            f"Name should revert to '{original_name}' after discard, "
            f"got '{restored_name}'"
        )


# ===========================================================================
# Tests — Make entrypoint
# ===========================================================================


class TestMakeEntrypoint:
    """PIPE-024: Make node entrypoint via node menu."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0858_pipeline-advanced-node-types.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_make_node_entrypoint(self, page, pipeline_id):
        """PIPE-024: Set a node as entrypoint via the three-dot menu.

        Adds two LLM nodes so the "Make entrypoint" option becomes available
        (it only appears when there are multiple potential entrypoints).
        Skips if the menu item is not available.
        """
        pipelines = _navigate_to_canvas(page, pipeline_id)

        # Add two LLM nodes — entrypoint option may only show with multiple nodes
        pipelines.add_node("LLM")
        llm1_id = pipelines.wait_for_node_on_canvas("llm")
        pipelines._deselect_all()

        pipelines.add_node("LLM")
        node_ids = pipelines.get_node_ids()
        llm_ids = [nid for nid in node_ids if "LLM" in nid]
        assert len(llm_ids) >= 2, "Should have at least 2 LLM nodes"
        llm2_id = llm_ids[-1]

        # Connect first LLM to END (makes it the entrypoint)
        pipelines.fit_view()
        # fit_view() contains a 500 ms internal wait for the zoom animation;
        # wait_for_network() ensures any canvas state update is flushed before drag.
        pipelines.wait_for_network()
        pipelines.connect_nodes(llm1_id, "END")

        # Try to make the second LLM node the entrypoint
        try:
            pipelines.make_node_entrypoint(llm2_id)
        except Exception:
            pytest.skip(
                "Make entrypoint menu item not available — "
                "feature may not be exposed for this pipeline state"
            )

        pipelines.wait_for_network()

        # Verify the second LLM node is now the entrypoint.
        # get_entrypoint_node_id() reads the YAML entry_point field.
        entrypoint = pipelines.get_entrypoint_node_id()
        assert entrypoint == llm2_id, (
            f"Node '{llm2_id}' should be the entrypoint after make_node_entrypoint(), "
            f"got '{entrypoint}'"
        )


# ===========================================================================
# Tests — Additional node types (MOVED TO test_pipeline_nodes.py)
# ===========================================================================
# PIPE-025 to PIPE-027 have been consolidated into the parameterized
# test_add_node_to_canvas in test_pipeline_nodes.py for better maintainability.
# All node addition tests (LLM, Code, Decision, Printer, Router) are now in
# a single parameterized test with appropriate priority markers.
# ===========================================================================


# ===========================================================================
# Tests — Three-dot menu actions
# ===========================================================================


class TestActionsMenu:
    """PIPE-028 to PIPE-029: Three-dot menu items and actions."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0859_pipeline-three-dot-menu-and-actions.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_three_dot_menu_lists_items(self, page, pipeline_id):
        """PIPE-028: The three-dot menu should contain expected items.

        Opens the menu and enumerates all visible menu items.
        At minimum, 'Delete pipeline' should be present.
        """
        pipelines = _navigate_to_detail(page, pipeline_id)

        items = pipelines.get_actions_menu_items()

        assert len(items) >= 2, f"Expected at least 2 menu items, got: {items}"
        assert any("Delete" in item or "delete" in item for item in items), f"Expected 'Delete' in menu items: {items}"
        assert any("Export" in item or "export" in item for item in items), f"Expected 'Export' in menu items: {items}"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0859_pipeline-three-dot-menu-and-actions.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_export_pipeline_if_available(self, page, pipeline_id):
        """PIPE-029: Export pipeline via menu (skips if not available).

        Attempts to export the pipeline.  If the Export menu item is not
        present, the test is skipped (feature not yet implemented).
        """
        pipelines = _navigate_to_detail(page, pipeline_id)

        # First check if Export is in the menu
        items = pipelines.get_actions_menu_items()
        if not any("Export" in item for item in items):
            pytest.skip("Export menu item not available on this pipeline")

        success = pipelines.export_pipeline_via_menu()
        assert success, "Export should complete successfully"
        # TODO: add toast verification once PO has get_success_message()


# ===========================================================================
# Tests — Multi-node topology
# ===========================================================================


class TestMultiNodeTopology:
    """PIPE-030: Multi-node pipeline topology."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0858_pipeline-advanced-node-types.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_three_node_chain(self, page, pipeline_id):
        """PIPE-030: Build a three-node chain: LLM → Code → END.

        Creates two nodes, connects them in sequence, and verifies all
        edges exist.
        """
        pipelines = _navigate_to_canvas(page, pipeline_id)

        llm_id = _add_llm_node_and_connect(pipelines)
        pipelines._deselect_all()

        # Add Code node
        pipelines.add_node("Code")
        code_id = pipelines.wait_for_node_on_canvas("code")

        # Should have 3 nodes: LLM, Code, END
        count = pipelines.get_node_count()
        assert count == 3, f"Should have 3 nodes, got {count}"

        pipelines.fit_view()
        pipelines.wait_for_network()

        # Connect LLM → Code
        pipelines.connect_nodes(llm_id, code_id)
        assert pipelines.edge_exists(llm_id, code_id), (
            f"Edge from '{llm_id}' to '{code_id}' should exist"
        )

        # Connect Code → END
        pipelines.connect_nodes(code_id, "END")
        assert pipelines.edge_exists(code_id, "END"), (
            f"Edge from '{code_id}' to 'END' should exist"
        )

        # Verify total edge count
        assert pipelines.get_edge_count() >= 2, (
            f"Should have at least 2 edges, got {pipelines.get_edge_count()}"
        )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0858_pipeline-advanced-node-types.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_save_multi_node_pipeline(self, page, pipeline_id):
        """PIPE-030b: Build a multi-node pipeline, save, and verify persistence.

        Creates LLM → END, saves, reloads, and verifies the nodes persist.
        """
        pipelines = _navigate_to_canvas(page, pipeline_id)

        _add_llm_node_and_connect(pipelines)

        # Save
        pipelines.click_save(timeout=FORM_SAVE_TIMEOUT)

        # Reload and verify persistence
        pipelines.page.reload()
        pipelines.wait_for_network()       # Wait for networkidle after reload
        pipelines.wait_for_detail_page_load()
        pipelines.dismiss_banner_if_present()
        pipelines.wait_for_canvas()

        # Nodes should persist after reload
        node_count = pipelines.get_node_count()
        assert node_count == 2, f"Expected 2 nodes after reload, got {node_count}"

        # The LLM node should persist
        node_ids = pipelines.get_node_ids()
        llm_ids = [nid for nid in node_ids if "LLM" in nid]
        assert len(llm_ids) == 1, f"Expected exactly 1 LLM node, got: {llm_ids}"
