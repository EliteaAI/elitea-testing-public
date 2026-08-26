"""UI test — Pipeline: Create Pipeline Version — Save, List, and Switch
Preserves Canvas State.

TMS: ELITEA-2002
(test-specs/pipelines/l2_create-pipeline-version_ELITEA-2002.md)

Adds an LLM node to a fresh, zero-node pipeline, saves the change as a new
named version ("v1_test") via "Save As Version", verifies it's listed in the
VERSION dropdown alongside "base", then switches back to "base" (canvas
reverts to the original node-less topology) and forward to "v1_test" again
(the LLM node is restored) — proving each version's canvas state is
independently preserved and restored on selection, with no cross-version
leakage in either direction.

Test-data strategy: the pre-existing ``pipeline_id`` fixture (data_fixtures.py)
already creates a dedicated, uniquely-named, zero-node pipeline per test and
deletes it afterwards — exactly the AFS's precondition (a saved "base"
version with NO nodes yet, created via the API to keep this case's
assertions focused on versioning rather than re-proving pipeline-creation-
via-UI, already covered by
``lextend_create-pipeline-minimal-sidebar_ELITEA-2020.md`` /
``test_pipeline_creation.py``). No custom setup/teardown needed — reusing
the fixture per Hard Rule 7 (reuse before create).

Version-management methods (``open_save_as_version_dialog``,
``confirm_new_version``, ``save_as_version``, ``open_version_selector``,
``is_version_option_visible``, ``select_version_by_name``,
``close_versions_menu``, ``get_version_id``) and the
``save_as_version_button``/``create_version_*``/``VERSION_OPTION`` locators
were ported onto ``PipelineDetailPage``/``PipelineFormPage`` for this case —
same shared components (SaveNewVersionButton.jsx, ApplicationVersionSelect.jsx,
BaseModal.jsx) ``AgentDetailPage`` already wires, confirmed live end-to-end on
a pipeline detail page (zero ``add-data-testid`` work needed).
"""

import allure
import pytest

from tests.ui.pipeline_helpers import _navigate_to_canvas

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
VERSION_NAME = "v1_test"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2002_create-pipeline-version.md",
    "onetest-ai Test Case link",
)
def test_create_pipeline_version_save_list_switch_preserves_canvas_state(page, pipeline_id):
    """Save As Version creates 'v1_test' with the LLM node preserved;
    switching to 'base' shows the original (node-less) topology; switching
    back to 'v1_test' restores the LLM node — each version's canvas state is
    independently preserved with no cross-version leakage."""
    with allure.step(
        "Step 1 — Navigate to the dedicated (zero-node) pipeline's canvas and "
        "verify the clean 'base' baseline"
    ):
        pipeline_page = _navigate_to_canvas(page, pipeline_id)
        assert pipeline_page.get_version_display() == "base", (
            "A freshly created pipeline should load showing its 'base' version"
        )
        assert not pipeline_page.is_save_enabled(), (
            "Save should be disabled on a clean, zero-node pipeline"
        )
        assert not pipeline_page.is_discard_enabled(), (
            "Discard should be disabled on a clean, zero-node pipeline"
        )
        # Save As Version is NOT gated on form dirtiness (confirmed live +
        # via ApplicationTabBar.jsx source, 2026-08-07 — it renders
        # SaveNewVersionButton with no `disabled` prop at all, so it only
        # ever reflects a mid-request state, never dirtiness). It is
        # available even on this clean baseline — see the AFS/_surface.md
        # CORRECTION this implementation added.
        assert pipeline_page.is_save_as_version_enabled(), (
            "Save As Version should be enabled even on a clean pipeline — "
            "it is not gated on form dirtiness (see AFS correction note)"
        )

    with allure.step('Step 2 — Add an LLM node via the canvas "Add node" menu'):
        # Testid-based open+select pair (pipeline-add-node-button /
        # pipeline-add-node-menu-item-llm — AFS's recommended handles),
        # not the legacy raw-handle add_node() — same choice
        # test_pipeline_add_node_menu.py's Step 4 made (ELITEA-2030 review
        # round 4).
        pipeline_page.get_add_node_menu_items(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.select_add_node_menu_item("llm", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.wait_for_node_type_count("llm", 1, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.is_save_enabled(), (
            "Save should become enabled once a node is added (dirty state)"
        )
        assert pipeline_page.is_save_as_version_enabled(), (
            "Save As Version should remain enabled (it was already enabled "
            "before this edit — not dirty-gated, see Step 1's note)"
        )

    with allure.step(
        'Step 3 — Click "Save As Version"; verify the "Create version" dialog, '
        'type "v1_test", and confirm'
    ):
        previous_version_id = pipeline_page.get_version_id()
        pipeline_page.open_save_as_version_dialog(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.create_version_name_input.is_visible(), (
            'The "Create version" dialog should show a Name input'
        )
        assert not pipeline_page.create_version_save_button.is_enabled(), (
            "Dialog Save button should be disabled while Name is empty"
        )

        pipeline_page.confirm_new_version(VERSION_NAME, timeout=NAVIGATION_TIMEOUT)

        assert pipeline_page.get_version_display() == VERSION_NAME, (
            f"VERSION selector should show {VERSION_NAME!r} after Save As Version"
        )
        new_version_id = pipeline_page.get_version_id()
        assert new_version_id != previous_version_id, (
            "Version ID should change after creating a new named version"
        )
        pipeline_page.wait_for_node_type_count("llm", 1, timeout=UI_ELEMENT_TIMEOUT)
        assert not pipeline_page.is_save_enabled(), (
            "Save should return to disabled — the new version is persisted, "
            "not a lingering local edit"
        )

    with allure.step(
        'Step 4 — Open the VERSION dropdown and verify it lists both "base" '
        'and "v1_test"'
    ):
        pipeline_page.open_version_selector()
        assert pipeline_page.is_version_option_visible("base", timeout=UI_ELEMENT_TIMEOUT), (
            "VERSION dropdown should list the 'base' version"
        )
        assert pipeline_page.is_version_option_visible(VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT), (
            f"VERSION dropdown should list the new {VERSION_NAME!r} version"
        )
        pipeline_page.close_versions_menu()

    with allure.step(
        "Step 5 — Switch back to 'base' and verify the canvas reverts to the "
        "original (node-less) topology — no cross-version leakage"
    ):
        base_version_id = pipeline_page.select_version_by_name("base", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_version_display() == "base", (
            "VERSION selector should show 'base' after switching back"
        )
        assert base_version_id == previous_version_id, (
            "'base' should resolve to the SAME version id the pipeline "
            "started on before Save As Version — confirms a true revert, "
            "not a new base-named version"
        )
        pipeline_page.wait_for_node_type_count("llm", 0, timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        "Step 6 — Switch to 'v1_test' again and verify the LLM node is "
        "restored (the node config is not re-created empty)"
    ):
        v1_version_id = pipeline_page.select_version_by_name(VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_version_display() == VERSION_NAME, (
            f"VERSION selector should show {VERSION_NAME!r} after switching back"
        )
        assert v1_version_id == new_version_id, (
            f"{VERSION_NAME!r} should resolve to the SAME version id created in Step 3"
        )
        pipeline_page.wait_for_node_type_count("llm", 1, timeout=UI_ELEMENT_TIMEOUT)
