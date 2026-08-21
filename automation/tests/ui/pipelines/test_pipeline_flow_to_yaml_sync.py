"""UI test — Pipeline: Flow Canvas to YAML Editor Sync.

TMS: ELITEA-2029
(test-specs/pipelines/l2_flow-to-yaml-sync_ELITEA-2029.md)

Adds a new LLM node via the Flow (visual) editor's Add-node menu and
verifies it is immediately reflected in the YAML view — the reverse
direction of the sibling ELITEA-2028 case (YAML edit -> Flow canvas).
No Save is involved; the addition is purely client-side ReactFlow state,
already reflected in the YAML view before any persistence call.

Uses the testid-based Add-node pair (`get_add_node_menu_items()` +
`select_add_node_menu_item()`, ELITEA-2030) rather than the legacy
raw-handle `add_node()` — `add_node()` remains valid pre-existing tech
debt for tests that already use it, but a new test uses the testid path.

`wait_for_node_on_canvas("llm")`'s return value is NOT used to identify the
new node: its `.first` selector resolves to the pre-existing "LLM 1" node
on this fixture's non-empty starting canvas (confirmed live, AFS Concrete
Handles "Ambiguity caveat"). The new node's id is instead found via a
before/after `get_node_ids()` set diff.
"""

import allure
import pytest
from pages.pipeline_detail_page import PipelineDetailPage

from tests.ui.pipelines.helpers import _navigate_to_canvas

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p1, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2029_pipeline-flow-to-yaml-sync.md",
    "onetest-ai Test Case link",
)
def test_add_node_in_flow_view_syncs_to_yaml(page, pipeline_with_llm_id):
    """A node added in Flow view is immediately reflected in the YAML view
    and remains on canvas after switching back to Flow view."""
    pipeline_page: PipelineDetailPage = _navigate_to_canvas(page, pipeline_with_llm_id)

    # Registered before step 1 so console errors / failed requests across
    # the whole flow (add-node, both view switches, the YAML read) are
    # captured — AFS Expected Results requires "zero console errors, zero
    # failed network requests, throughout".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
    failed_requests = []
    page.on("response", lambda resp: failed_requests.append(resp) if resp.status >= 400 else None)

    with allure.step("Step 1 — Open the pipeline in Flow view"):
        assert pipeline_page.is_flow_view_active(timeout=UI_ELEMENT_TIMEOUT), (
            "Pipeline detail page should default to the Flow view"
        )
        assert pipeline_page.canvas_wrapper.is_visible(), "Flow canvas should be visible"
        node_ids_before = set(pipeline_page.get_node_ids())
        node_count_before = pipeline_page.get_node_count()

    with allure.step('Step 2 — Add a new LLM node via the "Add node" button'):
        pipeline_page.get_add_node_menu_items(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.select_add_node_menu_item("llm", timeout=UI_ELEMENT_TIMEOUT)
        # Settles for the new node to attach to the DOM. Its return value
        # is NOT trusted as the new node's id — see module docstring /
        # AFS Concrete Handles "Ambiguity caveat".
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

        node_ids_after_add = set(pipeline_page.get_node_ids())
        new_node_ids = node_ids_after_add - node_ids_before
        assert len(new_node_ids) == 1, (
            f"Exactly one new node should appear after adding an LLM node, "
            f"got new ids: {new_node_ids} (before: {node_ids_before}, after: {node_ids_after_add})"
        )
        new_node_id = next(iter(new_node_ids))
        assert pipeline_page.get_node_count() == node_count_before + 1, (
            "Node count should increase by exactly 1 after adding the LLM node"
        )

    with allure.step('Step 3 — Switch to "Yaml" view'):
        pipeline_page.switch_to_yaml_view()
        pipeline_page.yaml_editor.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.yaml_editor.is_visible(), "YAML CodeMirror editor should become visible"

    with allure.step("Step 4 — Verify the new node appears in the YAML definition"):
        yaml_content = pipeline_page.get_yaml_content()
        assert f"id: {new_node_id}" in yaml_content, (
            f"YAML content should include the newly-added node {new_node_id!r}: {yaml_content!r}"
        )
        assert "id: LLM 1" in yaml_content, (
            f"The pre-existing LLM 1 node should still be present in the YAML, not replaced: {yaml_content!r}"
        )

    with allure.step('Step 5 — Switch back to "Flow" view; verify the node is still present on canvas'):
        pipeline_page.switch_to_flow_view()
        assert pipeline_page.is_flow_view_active(timeout=UI_ELEMENT_TIMEOUT), (
            "Flow view (ReactFlow canvas) should become visible after switching back"
        )
        node_ids_after_switch = set(pipeline_page.get_node_ids())
        assert new_node_id in node_ids_after_switch, (
            f"New node {new_node_id!r} should still be present on the canvas after switching "
            f"Yaml -> Flow: {node_ids_after_switch}"
        )
        assert pipeline_page.get_node_count() == node_count_before + 1, (
            "Node count should be unchanged by the two view switches (no node lost or duplicated)"
        )

    assert not console_errors, f"No console errors expected at any step: {console_errors}"
    assert not failed_requests, f"No failed network requests expected at any step: {failed_requests}"
