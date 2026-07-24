"""UI test — Pipeline Canvas: Delete Node.

TMS: ELITEA-2018
(test-specs/pipelines/l2_pipeline-canvas-delete-node_ELITEA-2018.md)

Deletes a node in the middle of a pipeline chain (LLM 1 -> Code 1 -> END)
via both of its documented activation gestures — the node's three-dot menu
and the keyboard Delete key — and verifies the deletion + the upstream
node's transition auto-rewire persist through Save + full reload, confirmed
identically via the Flow-view canvas, the YAML tab, and a direct API read.
"""

import logging

import allure
import pytest
import yaml
from components.mui import Dialog
from config import settings

from tests.ui.pipelines.helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000


def _version_details(pipeline: dict) -> dict:
    """Return the version dict from a PipelineAPI.get_pipeline() response.

    Mirrors the ``_vd`` helper in
    ``tests/api/export_import/test_export_import_pipelines.py`` — prefers
    ``version_details`` when present, else falls back to ``versions[0]``.
    """
    vd = pipeline.get("version_details")
    if vd:
        return vd
    versions = pipeline.get("versions", [])
    return versions[0] if versions else {}


class TestDeleteNode:
    """ELITEA-2018: Pipeline Canvas — Delete Node."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/pipelines/ELITEA-2018_pipeline-canvas-delete-node.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_delete_node_via_menu(self, page, pipeline_with_llm_code_end_id, pipeline_api):
        """Delete the middle node (Code 1) via its three-dot menu; verify 3-source persistence."""
        pipeline_id = pipeline_with_llm_code_end_id
        project_id = str(settings.elitea_project_id)

        # Registered before Step 1 so console errors from every step (node
        # select, menu open, delete confirm, Save, reload) are captured —
        # AFS Expected Results require "no console errors at any step".
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

        with allure.step("Step 1 — Navigate to canvas; verify 3 nodes + both edges"):
            pipelines = _navigate_to_canvas(page, pipeline_id)
            canonical_url = page.url
            node_ids = set(pipelines.get_node_ids())
            assert node_ids == {"LLM 1", "Code 1", "END"}, (
                f"Canvas should show exactly the 3 fixture nodes, got {node_ids!r}"
            )
            assert pipelines.edge_exists("LLM 1", "Code 1"), "Edge LLM 1 -> Code 1 should exist"
            assert pipelines.edge_exists("Code 1", "END"), "Edge Code 1 -> END should exist"

        with allure.step("Step 2 — Select the Code 1 node"):
            pipelines.select_node("Code 1")
            assert pipelines.is_node_selected("Code 1"), (
                "Code 1 should carry ReactFlow's 'selected' class after clicking its title label"
            )

        with allure.step("Step 3 — Open node menu, click Delete; verify confirmation dialog content"):
            pipelines.open_node_menu("Code 1")
            dialog = pipelines.click_delete_in_node_menu(timeout=UI_ELEMENT_TIMEOUT)
            title_text = (dialog.locator(pipelines.DELETE_CONFIRM_TITLE_SELECTOR).text_content() or "").strip()
            message_text = (
                dialog.locator(pipelines.DELETE_CONFIRM_MESSAGE_SELECTOR).text_content() or ""
            ).strip()
            assert title_text == "Delete confirmation", (
                f"Dialog title should read 'Delete confirmation', got {title_text!r}"
            )
            assert "Code 1" in message_text, (
                f"Dialog message should name the node 'Code 1', got {message_text!r}"
            )

        with allure.step(
            "Step 4 — Confirm delete; verify node removed, LLM 1/END unaffected, transition auto-rewired"
        ):
            pipelines.confirm_node_delete(dialog)
            node_ids_after = set(pipelines.get_node_ids())
            assert node_ids_after == {"LLM 1", "END"}, (
                f"Canvas should show exactly LLM 1 and END after deleting Code 1, got {node_ids_after!r}"
            )
            assert not pipelines.any_edge_touches_node("Code 1"), (
                "No edge should reference the deleted Code 1 node"
            )
            # The transition auto-rewire is asserted via the YAML `transition:`
            # field (AFS Axis 2's own stated mechanism), not the canvas edge —
            # confirmed live during implementation that the ReactFlow canvas's
            # edges array only recomputes on a Flow/YAML view remount (or a
            # full reload, see Step 6); the underlying YAML model updates
            # instantly on delete, which is what actually proves the pipeline
            # stays executable/valid.
            pipelines.switch_to_yaml_view()
            yaml_after_delete = yaml.safe_load(pipelines.get_yaml_content())
            pipelines.switch_to_flow_view()
            assert yaml_after_delete.get("entry_point") == "LLM 1", (
                f"YAML entry_point should still be 'LLM 1', got {yaml_after_delete.get('entry_point')!r}"
            )
            remaining_node_ids_yaml = {n.get("id") for n in yaml_after_delete.get("nodes", [])}
            assert remaining_node_ids_yaml == {"LLM 1"}, (
                f"YAML should contain exactly one node block, 'LLM 1', got {remaining_node_ids_yaml!r} "
                "— 'Code 1' must not reappear"
            )
            assert yaml_after_delete["nodes"][0].get("transition") == "END", (
                "LLM 1's YAML transition should auto-rewire to 'END' (Code 1's own former "
                f"downstream target) immediately after delete, got "
                f"{yaml_after_delete['nodes'][0].get('transition')!r}"
            )

        with allure.step("Step 5 — Save; verify 201 + zero console errors"):
            save_response = pipelines.save_and_wait_for_update(
                project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
            )
            assert save_response is not None, "Save should return the persisted pipeline version"
            assert not console_errors, f"Delete + Save should not introduce console errors: {console_errors}"

        with allure.step("Step 6 — Reload; canvas shows only LLM 1 + END"):
            page.goto(canonical_url)
            pipelines.wait_for_detail_page_load()
            pipelines.wait_for_canvas()
            node_ids_reloaded = set(pipelines.get_node_ids())
            assert node_ids_reloaded == {"LLM 1", "END"}, (
                f"Canvas should show exactly LLM 1 and END after reload, got {node_ids_reloaded!r}"
            )
            assert pipelines.get_edge_count() == 1, (
                f"Exactly 1 edge (LLM 1 -> END) should remain after reload, got {pipelines.get_edge_count()}"
            )
            assert pipelines.edge_exists("LLM 1", "END"), "Edge LLM 1 -> END should persist after reload"

        with allure.step("Step 7 — Cross-verify via the YAML tab"):
            pipelines.switch_to_yaml_view()
            yaml_text = pipelines.get_yaml_content()
            parsed_yaml = yaml.safe_load(yaml_text)
            assert parsed_yaml.get("entry_point") == "LLM 1", (
                f"YAML entry_point should be 'LLM 1', got {parsed_yaml.get('entry_point')!r}"
            )
            yaml_node_ids = {n.get("id") for n in parsed_yaml.get("nodes", [])}
            assert yaml_node_ids == {"LLM 1"}, (
                f"YAML should contain exactly one node block, 'LLM 1', got {yaml_node_ids!r} "
                "— 'Code 1' must not reappear"
            )
            llm_node_yaml = parsed_yaml["nodes"][0]
            assert llm_node_yaml.get("transition") == "END", (
                f"LLM 1's YAML transition should be 'END', got {llm_node_yaml.get('transition')!r}"
            )

        with allure.step("Step 8 — Cross-verify via the API (server-side YAML matches YAML tab)"):
            api_pipeline = pipeline_api.get_pipeline(pipeline_id)
            api_yaml = yaml.safe_load(_version_details(api_pipeline).get("instructions", ""))
            assert api_yaml.get("entry_point") == parsed_yaml.get("entry_point"), (
                f"API entry_point {api_yaml.get('entry_point')!r} should match "
                f"YAML-tab entry_point {parsed_yaml.get('entry_point')!r}"
            )
            api_node_ids = {n.get("id") for n in api_yaml.get("nodes", [])}
            assert api_node_ids == yaml_node_ids, (
                f"API nodes {api_node_ids!r} should match YAML-tab nodes {yaml_node_ids!r} "
                "(catches a UI-cache-vs-backend divergence)"
            )
            assert api_yaml["nodes"][0].get("transition") == llm_node_yaml.get("transition"), (
                "API transition should match the YAML-tab transition"
            )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/pipelines/ELITEA-2018_pipeline-canvas-delete-node.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_delete_node_via_keyboard_delete_key(self, page, pipeline_with_llm_code_end_id):
        """Delete the middle node (Code 1) by selecting it and pressing the Delete key.

        Lighter assertion set than ``test_delete_node_via_menu`` — that test
        already proves the Save/reload/YAML/API persistence chain; this
        test's own purpose is proving the keyboard trigger reaches the
        identical deletion flow, not re-proving persistence.
        """
        pipeline_id = pipeline_with_llm_code_end_id

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

        with allure.step("Step 1 — Navigate to canvas"):
            pipelines = _navigate_to_canvas(page, pipeline_id)

        with allure.step("Step 2 — Select the Code 1 node"):
            pipelines.select_node("Code 1")
            assert pipelines.is_node_selected("Code 1"), (
                "Code 1 should carry ReactFlow's 'selected' class after clicking its title label — "
                "required for the Delete key to reach this node (focus gotcha, AFS Automation Hints)"
            )

        with allure.step("Step 3 — Press Delete key; verify the identical confirmation dialog appears"):
            page.keyboard.press("Delete")
            dialog = Dialog.wait_for(page, timeout=UI_ELEMENT_TIMEOUT)
            title_text = (dialog.locator(pipelines.DELETE_CONFIRM_TITLE_SELECTOR).text_content() or "").strip()
            message_text = (
                dialog.locator(pipelines.DELETE_CONFIRM_MESSAGE_SELECTOR).text_content() or ""
            ).strip()
            assert title_text == "Delete confirmation", (
                f"Keyboard-triggered dialog title should read 'Delete confirmation', got {title_text!r} — "
                "confirms this alternate trigger reaches the identical dialog as the menu path, not just a "
                "similarly-worded one"
            )
            assert "Code 1" in message_text, (
                f"Keyboard-triggered dialog should name the node 'Code 1', got {message_text!r} — "
                "confirms this alternate trigger reaches the same deletion flow as the menu path"
            )

        with allure.step("Step 4 — Confirm delete; verify Code 1 removed, LLM 1/END remain"):
            pipelines.confirm_node_delete(dialog)
            node_ids_after = set(pipelines.get_node_ids())
            assert node_ids_after == {"LLM 1", "END"}, (
                f"Canvas should show exactly LLM 1 and END after deleting Code 1, got {node_ids_after!r}"
            )

        with allure.step("Step 5 — Verify zero console errors"):
            assert not console_errors, f"Keyboard delete should not introduce console errors: {console_errors}"
