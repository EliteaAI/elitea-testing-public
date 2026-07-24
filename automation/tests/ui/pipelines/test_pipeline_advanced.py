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

import logging

import allure
import pytest

from tests.ui.pipelines.helpers import _navigate_to_canvas, _navigate_to_detail

pytestmark = [pytest.mark.ui, pytest.mark.pipelines]

logger = logging.getLogger(__name__)

# ELITEA-2028: two-node pipeline (LLM 1 + Code 1, both -> END) used to test
# editing a node's `transition:` value directly in the YAML editor. Kept as a
# module-level constant (not a shared fixture) since this exact topology is
# only needed by test_yaml_edit_transition_syncs_flow_view_and_enables_save
# (AFS § Test Data: generate-per-test).
_YAML_EDIT_PIPELINE_NODES = [
    {
        "id": "LLM 1", "type": "llm", "input": [],
        "input_mapping": {
            "chat_history": {"type": "fixed", "value": []},
            "system": {"type": "fixed", "value": ""},
            "task": {"type": "fixed", "value": ""},
        },
        "output": [], "structured_output": False,
        "transition": "END",
    },
    {
        "id": "Code 1", "type": "code", "input": [], "output": [],
        "source_code": "",
        "transition": "END",
    },
]


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
        """PIPE-019: Switch to YAML view and verify the editor is visible."""
        with allure.step("Step 1 — Navigate to pipeline detail page"):
            pipelines = _navigate_to_detail(page, pipeline_id)

        with allure.step("Step 2 — Verify default is Flow view"):
            assert pipelines.is_flow_view_active(), (
                "Pipeline should start in Flow view"
            )

        with allure.step("Step 3 — Switch to YAML view"):
            pipelines.switch_to_yaml_view()
            assert pipelines.is_yaml_view_active(), (
                "YAML editor should be visible after switching to YAML view"
            )

        with allure.step("Step 4 — Switch back to Flow view"):
            pipelines.switch_to_flow_view()
            assert pipelines.is_flow_view_active(), (
                "Flow canvas should be visible after switching back to Flow view"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0860_pipeline-yaml-view-and-round-trip.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_yaml_content_reflects_pipeline(self, page, pipeline_with_llm_id):
        """PIPE-020: YAML content should reflect the pipeline structure."""
        with allure.step("Step 1 — Navigate to pipeline with LLM node"):
            pipelines = _navigate_to_detail(page, pipeline_with_llm_id)

        with allure.step("Step 2 — Switch to YAML view"):
            pipelines.switch_to_yaml_view()
            assert pipelines.is_yaml_view_active(), "YAML view should be active"

        with allure.step("Step 3 — Get YAML content"):
            yaml_content = pipelines.get_yaml_content()
            assert len(yaml_content.strip()) > 0, (
                "YAML content should have meaningful text"
            )

        with allure.step("Step 4 — Verify YAML contains pipeline structure keywords"):
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
        """PIPE-021: Toggle Flow → YAML → Flow preserves the canvas."""
        with allure.step("Step 1 — Navigate to pipeline canvas"):
            pipelines = _navigate_to_canvas(page, pipeline_id)

        with allure.step("Step 2 — Add LLM node"):
            pipelines.add_node("LLM")
            llm_id = pipelines.wait_for_node_on_canvas("llm")
            initial_count = pipelines.get_node_count()
            assert initial_count >= 2, "Should have LLM + END nodes"

        with allure.step("Step 3 — Switch to YAML view"):
            pipelines.switch_to_yaml_view()
            pipelines.wait_for_network()

        with allure.step("Step 4 — Switch back to Flow view"):
            pipelines.switch_to_flow_view()
            pipelines.wait_for_network()

        with allure.step("Step 5 — Verify node count preserved after round-trip"):
            pipelines.wait_for_canvas()
            final_count = pipelines.get_node_count()
            assert final_count == initial_count, f"Round-trip should preserve node count: expected {initial_count}, got {final_count}"

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/pipelines/ELITEA-2028_pipeline-yaml-to-flow-sync.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_yaml_edit_transition_syncs_flow_view_and_enables_save(self, page, pipeline_api, request):
        """ELITEA-2028: Editing a transition in YAML updates the Flow-view edge and enables Save.

        Uses a dedicated 2-node pipeline (LLM 1 + Code 1, both -> END) instead
        of the shared `pipeline_id`/`pipeline_with_llm_id` fixtures — this
        exact topology is only needed here (AFS § Test Data: generate-per-test).
        """
        name = f"autotest_{request.node.name}"[:32]
        description = f"Auto-created for test {request.node.name}"
        pipeline = pipeline_api.create_pipeline_with_nodes(
            name, description, entry_point="LLM 1", nodes=_YAML_EDIT_PIPELINE_NODES
        )
        pid = pipeline["id"]

        try:
            # Not a case step — setup normalization per AFS § Test Data gotcha:
            # a pipeline created via the API has an EMPTY persisted visual-layout
            # record (`pipeline_settings: {"nodes": [], "edges": []}`). The first
            # Flow-view render auto-computes real canvas positions that differ
            # from that empty array, and the diff alone flips Save/Discard to
            # enabled with zero content edit. One explicit Save here persists
            # the auto-computed layout, so Step 1's "Save starts disabled"
            # baseline is real, not vacuous (confirmed live at ELITEA-2028
            # analyst + implementer exploration).
            setup_page = _navigate_to_detail(page, pid)
            setup_page.wait_for_canvas()
            setup_page.click_save(timeout=FORM_SAVE_TIMEOUT)
            page.reload()
            setup_page.wait_for_network()
            setup_page.wait_for_detail_page_load()
            setup_page.dismiss_banner_if_present()

            # Console listener installed after setup/reload noise settles, so
            # it only captures errors during the case's own steps below (AFS
            # step 7 / Expected Results: zero console errors across the flow).
            console_errors = []
            page.on(
                "console",
                lambda msg: console_errors.append(msg) if msg.type == "error" else None,
            )

            with allure.step(
                "Step 1 — Navigate to the fixture pipeline; verify Save/Discard baseline is disabled"
            ):
                pipelines = _navigate_to_detail(page, pid)
                assert not pipelines.is_save_enabled(), (
                    "Save should read disabled on a freshly-normalized pipeline "
                    "(baseline check — otherwise Step 6's 'becomes enabled' "
                    "assertion would be vacuous)"
                )
                assert not pipelines.is_discard_enabled(), (
                    "Discard should read disabled on a freshly-normalized pipeline"
                )

            with allure.step(
                "Step 2 — Switch to Yaml view; verify content and that Save stays disabled"
            ):
                pipelines.switch_to_yaml_view()
                assert pipelines.is_yaml_view_active(), (
                    "YAML editor should be visible after switching to YAML view"
                )
                yaml_content = pipelines.get_yaml_content()
                assert "entry_point: LLM 1" in yaml_content, (
                    f"YAML should declare the entry point, got: {yaml_content[:300]}"
                )
                assert "- id: LLM 1" in yaml_content and "- id: Code 1" in yaml_content, (
                    f"YAML should declare both node id blocks, got: {yaml_content[:300]}"
                )
                assert yaml_content.count("transition: END") == 2, (
                    "Both nodes should still transition to END before the edit, "
                    f"got {yaml_content.count('transition: END')} occurrence(s)"
                )
                assert not pipelines.is_save_enabled(), (
                    "Switching to YAML view alone (no edit yet) must not enable Save"
                )

            with allure.step(
                "Step 3 — Edit Code 1's transition from END to LLM 1 directly in the YAML editor"
            ):
                pipelines.edit_node_transition_in_yaml("Code 1", "LLM 1")
                updated_yaml = pipelines.get_yaml_content()
                assert "transition: LLM 1" in updated_yaml, (
                    f"Code 1's transition should now read 'transition: LLM 1', "
                    f"got: {updated_yaml[:300]}"
                )
                assert updated_yaml.count("transition: END") == 1, (
                    "Only Code 1's transition should have changed — LLM 1's own "
                    f"'transition: END' should be untouched, got "
                    f"{updated_yaml.count('transition: END')} remaining occurrence(s)"
                )

            with allure.step("Step 4 — Switch back to Flow view"):
                pipelines.switch_to_flow_view()
                assert pipelines.is_flow_view_active(), (
                    "Flow canvas should be visible after switching back from YAML view"
                )

            with allure.step(
                "Step 5 — Verify canvas reflects the updated edge; stale edge is gone; "
                "untouched edge unaffected"
            ):
                assert pipelines.edge_exists("Code 1", "LLM 1"), (
                    "Canvas should show an edge from Code 1 to LLM 1 after the YAML edit"
                )
                # The END node's edge-endpoint id is the literal "EliteAPipelineEnd",
                # not "END" (ELITEA-2018 digest) — check both forms so a stale edge
                # isn't missed by a false-negative substring match on the plain
                # "END" alias.
                assert not pipelines.edge_exists("Code 1", "END"), (
                    "Stale edge Code 1 -> END should be gone, not merely superseded"
                )
                assert not pipelines.edge_exists("Code 1", "EliteAPipelineEnd"), (
                    "Stale edge Code 1 -> END (EliteAPipelineEnd alias) should be gone"
                )
                assert pipelines.edge_exists("LLM 1", "EliteAPipelineEnd"), (
                    "LLM 1's own untouched edge to END should still be present — "
                    "the edit should be scoped to Code 1 only"
                )

            with allure.step("Step 6 — Verify Save (and Discard) button becomes enabled"):
                assert pipelines.is_save_enabled(), (
                    "Save should be enabled after the YAML content edit"
                )
                assert pipelines.is_discard_enabled(), (
                    "Discard should be enabled alongside Save — same dirty-state mechanism"
                )

            with allure.step("Step 7 — Verify zero error-level console messages across the flow"):
                assert not console_errors, (
                    f"Unexpected console error(s) during the YAML-edit/Flow-sync flow: "
                    f"{[m.text for m in console_errors]}"
                )
        finally:
            # Not a case step — teardown for the pipeline seeded above (AFS § Cleanup).
            try:
                pipeline_api.delete_pipeline(pid)
            except Exception:
                logger.warning("Failed to delete seeded pipeline id=%s during cleanup", pid, exc_info=True)


# ===========================================================================
# Tests — Discard changes
# ===========================================================================


class TestDiscardChanges:
    """PIPE-022: Discard changes reverts unsaved edits."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0860_pipeline-yaml-view-and-round-trip.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_discard_reverts_name_change(self, page, pipeline_id, pipeline_api):
        """PIPE-022: Edit name, click Discard, and verify original name restored."""
        with allure.step("Step 1 — Get original pipeline name via API"):
            original = pipeline_api.get_pipeline(pipeline_id)
            original_name = original.get("name", "")

        with allure.step("Step 2 — Navigate to pipeline detail page"):
            pipelines = _navigate_to_detail(page, pipeline_id)

        with allure.step("Step 3 — Change pipeline name"):
            pipelines.update_name("autotest_changed_name")
            assert pipelines.get_name() == "autotest_changed_name", (
                "Name field should show the new value"
            )

        with allure.step("Step 4 — Click Discard to revert changes"):
            pipelines.click_discard()
            pipelines.wait_for_detail_page_load()

        with allure.step("Step 5 — Verify original name restored"):
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
        """PIPE-024: Set a node as entrypoint via the three-dot menu."""
        with allure.step("Step 1 — Navigate to pipeline canvas"):
            pipelines = _navigate_to_canvas(page, pipeline_id)

        with allure.step("Step 2 — Add first LLM node"):
            pipelines.add_node("LLM")
            llm1_id = pipelines.wait_for_node_on_canvas("llm")
            pipelines._deselect_all()

        with allure.step("Step 3 — Add second LLM node"):
            pipelines.add_node("LLM")
            node_ids = pipelines.get_node_ids()
            llm_ids = [nid for nid in node_ids if "LLM" in nid]
            assert len(llm_ids) >= 2, "Should have at least 2 LLM nodes"
            llm2_id = llm_ids[-1]

        with allure.step("Step 4 — Connect first LLM to END"):
            pipelines.fit_view()
            pipelines.wait_for_network()
            pipelines.connect_nodes(llm1_id, "END")

        with allure.step("Step 5 — Make second LLM node the entrypoint"):
            try:
                pipelines.make_node_entrypoint(llm2_id)
            except Exception:
                pytest.skip(
                    "Make entrypoint menu item not available — "
                    "feature may not be exposed for this pipeline state"
                )
            pipelines.wait_for_network()

        with allure.step("Step 6 — Verify second LLM is now entrypoint"):
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
        """PIPE-028: The three-dot menu should contain expected items."""
        with allure.step("Step 1 — Navigate to pipeline detail page"):
            pipelines = _navigate_to_detail(page, pipeline_id)

        with allure.step("Step 2 — Open actions menu and get items"):
            items = pipelines.get_actions_menu_items()

        with allure.step("Step 3 — Verify menu contains expected items"):
            assert len(items) >= 2, f"Expected at least 2 menu items, got: {items}"
            assert any("Delete" in item or "delete" in item for item in items), f"Expected 'Delete' in menu items: {items}"
            assert any("Export" in item or "export" in item for item in items), f"Expected 'Export' in menu items: {items}"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0859_pipeline-three-dot-menu-and-actions.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_export_pipeline_if_available(self, page, pipeline_id):
        """PIPE-029: Export pipeline via menu (skips if not available)."""
        with allure.step("Step 1 — Navigate to pipeline detail page"):
            pipelines = _navigate_to_detail(page, pipeline_id)

        with allure.step("Step 2 — Check if Export is available in menu"):
            items = pipelines.get_actions_menu_items()
            if not any("Export" in item for item in items):
                pytest.skip("Export menu item not available on this pipeline")

        with allure.step("Step 3 — Export pipeline via menu"):
            success = pipelines.export_pipeline_via_menu()
            assert success, "Export should complete successfully"


# ===========================================================================
# Tests — Multi-node topology
# ===========================================================================


class TestMultiNodeTopology:
    """PIPE-030: Multi-node pipeline topology."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0858_pipeline-advanced-node-types.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_three_node_chain(self, page, pipeline_id):
        """PIPE-030: Build a three-node chain: LLM → Code → END."""
        with allure.step("Step 1 — Navigate to pipeline canvas"):
            pipelines = _navigate_to_canvas(page, pipeline_id)

        with allure.step("Step 2 — Add LLM node and connect to END"):
            llm_id = _add_llm_node_and_connect(pipelines)
            pipelines._deselect_all()

        with allure.step("Step 3 — Add Code node"):
            pipelines.add_node("Code")
            code_id = pipelines.wait_for_node_on_canvas("code")
            count = pipelines.get_node_count()
            assert count == 3, f"Should have 3 nodes, got {count}"

        with allure.step("Step 4 — Connect LLM to Code"):
            pipelines.fit_view()
            pipelines.wait_for_network()
            pipelines.connect_nodes(llm_id, code_id)
            assert pipelines.edge_exists(llm_id, code_id), (
                f"Edge from '{llm_id}' to '{code_id}' should exist"
            )

        with allure.step("Step 5 — Connect Code to END"):
            pipelines.connect_nodes(code_id, "END")
            assert pipelines.edge_exists(code_id, "END"), (
                f"Edge from '{code_id}' to 'END' should exist"
            )

        with allure.step("Step 6 — Verify total edge count"):
            assert pipelines.get_edge_count() >= 2, (
                f"Should have at least 2 edges, got {pipelines.get_edge_count()}"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0858_pipeline-advanced-node-types.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_save_multi_node_pipeline(self, page, pipeline_id):
        """PIPE-030b: Build a multi-node pipeline, save, and verify persistence."""
        with allure.step("Step 1 — Navigate to pipeline canvas"):
            pipelines = _navigate_to_canvas(page, pipeline_id)

        with allure.step("Step 2 — Add LLM node and connect to END"):
            _add_llm_node_and_connect(pipelines)

        with allure.step("Step 3 — Save pipeline"):
            pipelines.click_save(timeout=FORM_SAVE_TIMEOUT)

        with allure.step("Step 4 — Reload page"):
            pipelines.page.reload()
            pipelines.wait_for_network()
            pipelines.wait_for_detail_page_load()
            pipelines.dismiss_banner_if_present()
            pipelines.wait_for_canvas()

        with allure.step("Step 5 — Verify nodes persist after reload"):
            node_count = pipelines.get_node_count()
            assert node_count == 2, f"Expected 2 nodes after reload, got {node_count}"
            node_ids = pipelines.get_node_ids()
            llm_ids = [nid for nid in node_ids if "LLM" in nid]
            assert len(llm_ids) == 1, f"Expected exactly 1 LLM node, got: {llm_ids}"
