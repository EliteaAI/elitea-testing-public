"""UI test — Pipeline: YAML Editor View.

TMS: ELITEA-2026
(test-specs/pipelines/l2_pipeline-yaml-editor-view_ELITEA-2026.md)

Verifies the YAML editor view is reachable via the Flow/Yaml toggle, renders
a sequential line-number gutter, shows a "Copy yaml code to clipboard"
button, contains the pipeline's entry_point/nodes/state keywords, and that
clicking Copy produces both an info toast AND the actual clipboard content
(via ``navigator.clipboard.readText()`` — safe here because the real pytest
``context`` fixture grants the clipboard-read/write permissions, see
``automation/conftest.py``).
"""

import logging

import allure
import pytest
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
TOAST_TIMEOUT = 10_000
COPY_TOAST_TEXT = "The code has been copied to the clipboard."


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2026_pipeline-yaml-editor-view.md",
    "onetest-ai Test Case link",
)
def test_pipeline_yaml_editor_view(page, pipeline_with_custom_state_var_id):
    """Flow/Yaml toggle -> YAML editor with line numbers -> Copy to clipboard."""
    pipeline_page = PipelineDetailPage(page)

    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Open the pipeline; it loads in Flow view"):
        pipeline_page.navigate(pipeline_with_custom_state_var_id)
        pipeline_page.wait_for_canvas()
        assert pipeline_page.is_flow_view_active(timeout=UI_ELEMENT_TIMEOUT), (
            "Pipeline detail page should default to the Flow view"
        )

    with allure.step("Step 2 — Locate the Flow/Yaml toggle group above the canvas"):
        assert pipeline_page.flow_view_button.is_visible(), "Flow toggle button should be visible"
        assert pipeline_page.yaml_view_button.is_visible(), "Yaml toggle button should be visible"

    with allure.step('Step 3 — Click "Yaml" button; the YAML editor view activates'):
        pipeline_page.switch_to_yaml_view()
        assert pipeline_page.is_yaml_view_active(), (
            "YAML editor (div.cm-editor) should be present after switching to Yaml view"
        )

    with allure.step("Step 4 — YAML editor shows a sequential line-number gutter starting at 1"):
        gutter_lines = pipeline_page.get_yaml_gutter_line_numbers()
        gutter_count = gutter_lines.count()
        assert gutter_count >= 1, "YAML editor gutter should render at least one line-number element"
        first_gutter_text = (gutter_lines.nth(0).text_content() or "").strip()
        assert first_gutter_text == "1", (
            f"First gutter line number should be '1', got {first_gutter_text!r}"
        )
        # Don't hardcode an absolute expected line count (the exact YAML
        # serialization is an implementation detail that will drift) — assert
        # the gutter's element count matches get_yaml_content()'s own line
        # count instead (AFS Automation Hints).
        content_line_count = len(pipeline_page.get_yaml_content().split("\n"))
        assert gutter_count == content_line_count, (
            f"Gutter line-number count ({gutter_count}) should match the "
            f"editor's actual line count ({content_line_count})"
        )

    with allure.step('Step 5 — "Copy yaml code to clipboard" button is visible'):
        assert pipeline_page.copy_yaml_button.is_visible(), (
            "Copy yaml code to clipboard button should be visible in YAML view"
        )

    with allure.step("Step 6 — YAML content contains entry_point, nodes, and state keywords"):
        yaml_content = pipeline_page.get_yaml_content()
        assert "entry_point:" in yaml_content, f"YAML should contain 'entry_point:': {yaml_content!r}"
        assert "nodes:" in yaml_content, f"YAML should contain 'nodes:': {yaml_content!r}"
        assert "state:" in yaml_content, f"YAML should contain 'state:': {yaml_content!r}"
        assert not console_errors, f"No console errors should occur through the Flow->Yaml switch: {console_errors}"

    with allure.step("Step 7 — Click the Copy yaml code to clipboard button"):
        pipeline_page.click_copy_yaml_button()

    with allure.step(
        "Step 8 — Verify the info toast AND that the clipboard actually contains the YAML text"
    ):
        toast_alert = pipeline_page.get_toast_alert("info")
        toast_alert.wait_for(state="visible", timeout=TOAST_TIMEOUT)
        toast_text = pipeline_page.get_toast_text(timeout=TOAST_TIMEOUT)
        assert COPY_TOAST_TEXT in toast_text, (
            f"Copy success toast should confirm the clipboard copy, got: {toast_text!r}"
        )

        clipboard_text = page.evaluate("navigator.clipboard.readText()")
        normalized_clipboard = "\n".join(line.rstrip() for line in clipboard_text.splitlines())
        normalized_yaml = "\n".join(line.rstrip() for line in yaml_content.splitlines())
        assert normalized_clipboard == normalized_yaml, (
            f"Clipboard content should match the YAML editor content.\n"
            f"Clipboard: {clipboard_text!r}\nEditor: {yaml_content!r}"
        )

        assert not console_errors, (
            f"No console errors should occur through the whole Flow->Yaml->Copy flow: {console_errors}"
        )
