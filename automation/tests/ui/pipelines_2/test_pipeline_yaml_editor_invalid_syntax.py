"""UI test — Pipeline: YAML Editor Invalid Syntax.

TMS: ELITEA-2068
(test-specs/pipelines/l3_pipeline-yaml-editor-invalid-syntax_ELITEA-2068.md)

Introduces invalid YAML syntax (a colon-stripped transition line — CodeMirror's
YAML-mode auto-close-brackets/quotes extension silently auto-closes a typed
opening quote, so an unterminated quote can't be produced this way; removing
the colon is the syntax break that actually sticks) into the pipeline's
YAML editor and verifies the pipeline cannot be saved with it: Save enables
(dirty state), the update PUT is rejected server-side with 400 and an
"Invalid pipeline YAML data" message, an app-wide error toast surfaces that
message to the user, and the pipeline's server-side stored instructions are
left genuinely unchanged (verified via a direct API read, not just absence
of a UI success indicator).

This is a FRESH spec, not an extension of test_pipeline_yaml_flow_sync.py
(ELITEA-2028's covering spec) — despite sharing the same page object and
YAML-editor surface, this case's observable (invalid-YAML rejection + error
toast + unchanged server state) has zero assertion overlap with ELITEA-2028's
(valid edit syncs to the Flow canvas + Save enables). See AFS Automation
Hints for the full reasoning.
"""

import logging

import allure
import pytest
from api.client import PipelineAPI
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000
TOAST_TIMEOUT = 10_000

INVALID_TRANSITION_LINE = "transition END invalid_no_colon_xyz123"
EXPECTED_ERROR_SUBSTRING = "Invalid pipeline YAML data"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2068_pipeline-yaml-editor-invalid-syntax.md",
    "onetest-ai Test Case link",
)
def test_yaml_editor_invalid_syntax_blocks_save(page, pipeline_with_llm_id, pipeline_api: PipelineAPI):
    """Invalid YAML in the editor enables Save but is rejected server-side on attempt."""
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    pipeline_page.navigate(pipeline_with_llm_id)
    pipeline_page.wait_for_canvas()

    with allure.step("Step 1 — Open the pipeline and switch to Yaml view"):
        assert pipeline_page.is_flow_view_active(timeout=UI_ELEMENT_TIMEOUT), (
            "Pipeline detail page should default to the Flow view"
        )

        # Captured here (post-navigate, before the edit) so step 4 can prove
        # the disabled->enabled transition is CAUSED by the invalid edit, not
        # a pre-existing always-on dirty state (AFS Axis-2 addition, mirrors
        # ELITEA-2028's own rationale).
        save_enabled_before_edit = pipeline_page.is_save_enabled()
        discard_enabled_before_edit = pipeline_page.is_discard_enabled()

        pipeline_page.switch_to_yaml_view()
        pipeline_page.yaml_editor.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.yaml_editor.is_visible(), "YAML CodeMirror editor should become visible"

    with allure.step("Step 2 — Introduce invalid YAML syntax (colon-stripped transition line)"):
        pre_edit_yaml = pipeline_page.get_yaml_content()
        assert "transition: END" in pre_edit_yaml, (
            f"Precondition: pipeline should start with a valid 'transition: END' line: {pre_edit_yaml!r}"
        )

        pipeline_page.edit_yaml_line("transition: END", INVALID_TRANSITION_LINE)

        post_edit_yaml = pipeline_page.get_yaml_content()
        assert INVALID_TRANSITION_LINE in post_edit_yaml, (
            f"YAML content should contain the invalid syntax after the edit: {post_edit_yaml!r}"
        )

    with allure.step("Step 3 — Switch to Flow view"):
        pipeline_page.switch_to_flow_view()
        assert pipeline_page.is_flow_view_active(timeout=UI_ELEMENT_TIMEOUT), (
            "Flow view should remain renderable (showing the last-known-valid graph) "
            "even with invalid YAML pending in the editor"
        )

    with allure.step("Step 4 — Verify the Save button is enabled (indicating unsaved changes)"):
        assert not save_enabled_before_edit, (
            "Save should have been disabled at the clean seeded baseline, before the invalid edit"
        )
        assert not discard_enabled_before_edit, (
            "Discard should have been disabled at the clean seeded baseline, before the invalid edit"
        )
        assert pipeline_page.is_save_enabled(), "Save should be enabled after the invalid-YAML edit"

    with allure.step(
        "Step 5 — Attempt to save; verify a 400 error response and an error toast "
        "indicating invalid YAML"
    ):
        result = pipeline_page.save_and_wait_for_error_response(
            project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert result["status"] == 400, (
            f"Saving invalid YAML should be rejected with 400, got {result['status']}: {result['body']!r}"
        )
        assert EXPECTED_ERROR_SUBSTRING in result["body"], (
            f"Error response body should mention invalid YAML: {result['body']!r}"
        )

        toast_text = pipeline_page.get_toast_text(timeout=TOAST_TIMEOUT)
        assert EXPECTED_ERROR_SUBSTRING in toast_text, (
            f"Error toast should surface the invalid-YAML message to the user, got: {toast_text!r}"
        )
        assert pipeline_page.get_toast_alert("error").is_visible(), (
            "Toast should carry data-severity='error' — a genuine error toast, "
            "not a coincidental info/success toast with similar text"
        )

    with allure.step(
        "Step 6 — Verify the pipeline cannot be saved with invalid YAML "
        "(server-side instructions unchanged)"
    ):
        server_pipeline = pipeline_api.get_pipeline(pipeline_with_llm_id)
        server_instructions = server_pipeline["version_details"]["instructions"]
        assert "transition: END" in server_instructions, (
            "Server-side stored instructions should still contain the original, "
            f"valid 'transition: END' line: {server_instructions!r}"
        )
        assert INVALID_TRANSITION_LINE not in server_instructions, (
            "Server-side stored instructions should NOT contain the invalid edit "
            f"— the save attempt must be genuinely rejected, not silently persisted: {server_instructions!r}"
        )
