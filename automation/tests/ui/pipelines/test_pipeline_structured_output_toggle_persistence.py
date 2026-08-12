"""UI test — Pipeline: Structured Output Toggle Persistence.

TMS: ELITEA-2046
(test-specs/pipelines/l2_pipeline-structured-output-toggle-persistence_ELITEA-2046.md)

Adds an LLM node to a fresh empty pipeline (chosen as the representative
node type carrying "Structured output" — the case names "LLM, Code,
Toolkit, etc." as examples, and the toggle is wired via the same shared
CommonInterruptSettings.jsx component across all of them; see AFS
Preconditions / Coverage Map row 1), then confirms:
  - the switch is disabled (unchecked) by default on a freshly-added node
  - toggling it enabled, saving, and reloading the page correctly persists
    the enabled state, and the pipeline YAML reflects `structured_output: true`
  - toggling it back disabled, saving, and reloading correctly persists the
    disabled state, and the YAML reflects `structured_output: false`

This pipeline's YAML document is short (single node, no extra fields) and
well under the ~32-34-line truncation threshold documented for
`EliteaAI/elitea-testing-public#1025` (confirmed live during analysis — no
truncation observed reading either state), so the on-screen
`pipeline-yaml-editor` tab is read directly rather than via the
`pipeline_api.get_pipeline()` workaround ELITEA-2045's longer document needed.
"""

import logging

import allure
import pytest
import yaml
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2046_pipeline-structured-output-toggle-persistence.md",
    "onetest-ai Test Case link",
)
def test_pipeline_structured_output_toggle_persistence(page, pipeline_id):
    """Structured output toggle on an LLM node persists both directions through save + reload."""
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from every step (node add,
    # toggle clicks, both saves, both reloads, both YAML-tab reads) are
    # captured — AFS Axis 2 requires "no unexpected console errors".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Open a pipeline with a node supporting structured output (LLM)"):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload steps — a bare
        # /pipelines/all/{id} URL (no query params) 404s (ELITEA-1954 AFS
        # Known Defects); reloading THIS captured URL avoids that.

        pipeline_page.add_node("LLM")
        node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        assert node_id, "LLM node should be present on the canvas with a non-empty data-id"

    with allure.step('Step 2 — Verify "Structured output" switch is disabled by default'):
        expect(pipeline_page.llm_node_structured_output_toggle).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.llm_node_structured_output_toggle).to_be_checked(
            checked=False, timeout=UI_ELEMENT_TIMEOUT
        )

    with allure.step(
        "Step 3 — Toggle to enabled — save — reload — verify switch remains checked; "
        "YAML shows structured_output: true (case step 5, enabled state)"
    ):
        pipeline_page.llm_node_structured_output_toggle.click(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.llm_node_structured_output_toggle).to_be_checked(timeout=UI_ELEMENT_TIMEOUT)

        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"

        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

        expect(pipeline_page.llm_node_structured_output_toggle).to_be_checked(timeout=UI_ELEMENT_TIMEOUT)

        pipeline_page.switch_to_yaml_view()
        pipeline_page.yaml_editor.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        parsed_enabled = yaml.safe_load(pipeline_page.get_yaml_content())
        llm_node_enabled = next(node for node in parsed_enabled["nodes"] if node["id"] == "LLM 1")
        assert llm_node_enabled.get("structured_output") is True, (
            f"YAML should show structured_output: true after enabling + save + reload, "
            f"got: {llm_node_enabled.get('structured_output')!r}"
        )
        pipeline_page.switch_to_flow_view()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        "Step 4 — Toggle to disabled — save — reload — verify switch remains unchecked; "
        "YAML shows structured_output: false (case step 5, disabled state)"
    ):
        pipeline_page.llm_node_structured_output_toggle.click(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.llm_node_structured_output_toggle).to_be_checked(
            checked=False, timeout=UI_ELEMENT_TIMEOUT
        )

        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"

        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

        expect(pipeline_page.llm_node_structured_output_toggle).to_be_checked(
            checked=False, timeout=UI_ELEMENT_TIMEOUT
        )

        pipeline_page.switch_to_yaml_view()
        pipeline_page.yaml_editor.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        parsed_disabled = yaml.safe_load(pipeline_page.get_yaml_content())
        llm_node_disabled = next(node for node in parsed_disabled["nodes"] if node["id"] == "LLM 1")
        assert llm_node_disabled.get("structured_output") is False, (
            f"YAML should show structured_output: false after disabling + save + reload, "
            f"got: {llm_node_disabled.get('structured_output')!r}"
        )

    with allure.step("Axis 2 — Verify no unexpected console errors across the full flow"):
        assert not console_errors, f"Flow should not introduce console errors: {console_errors}"
