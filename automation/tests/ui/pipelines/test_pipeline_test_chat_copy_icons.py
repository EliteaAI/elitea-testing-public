"""Pipeline test chat — Copy markdown / Copy text icons visible, clickable, toast-confirmed (ELITEA-4756).

Spec: test-specs/pipelines/l1_pipeline-test-chat-copy-markdown-and-copy-text-icons-toast_ELITEA-4756.md
"""

import allure
import pytest
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p1, pytest.mark.regression]

T = 15_000
RUN_TIMEOUT = 90_000
TOAST_DISMISS_TIMEOUT = 20_000


@pytest.mark.tms("ELITEA-4756")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-4756_pipeline-test-chat-copy-markdown-and-copy-text-actions.md",
    "onetest-ai Test Case link",
)
def test_pipeline_test_chat_copy_icons_show_tooltip_and_toast(page, pipeline_with_fstring_llm_id):
    """Both copy icons are visible under the pipeline response; tooltips and click toasts match."""
    page.set_viewport_size({"width": 1600, "height": 1400})
    pp = PipelineDetailPage(page)

    with allure.step("Step 1 — Open the pipeline in Flow view; Test Pipeline button visible"):
        pp.navigate(pipeline_with_fstring_llm_id)
        pp.dismiss_banner_if_present()
        pp.wait_for_canvas()
        expect(pp.test_pipeline_button).to_be_visible(timeout=T)
        expect(pp.test_pipeline_button).to_be_enabled(timeout=T)

    with allure.step("Step 2 — Click Test Pipeline; panel with input opens"):
        pp.test_pipeline_button.click()
        expect(pp.test_pipeline_panel).to_be_visible(timeout=T)
        expect(pp.chat_input).to_be_visible(timeout=T)

    with allure.step("Step 3 — Send input; the final response is shown"):
        pp.send_message_in_embedded_chat("go", timeout=T)
        expect(pp.embedded_chat_items()).to_have_count(2, timeout=RUN_TIMEOUT)
        expect(pp.skill_test_last_response.last).not_to_be_empty(timeout=RUN_TIMEOUT)

    with allure.step("Step 4 — Copy markdown and Copy text icons are visible"):
        assert pp.is_last_response_copy_icon_visible("markdown"), "Copy markdown icon should be visible"
        assert pp.is_last_response_copy_icon_visible("text"), "Copy text icon should be visible"

    with allure.step("Step 5 — Hover the Copy markdown icon; tooltip 'Copy markdown'"):
        assert pp.hover_last_response_copy_icon("markdown") == "Copy markdown"

    with allure.step("Step 6 — Click Copy markdown; toast 'Markdown copied to clipboard.'"):
        toast = pp.click_last_response_copy_icon("markdown")
        assert toast == "Markdown copied to clipboard.", f"Unexpected toast: {toast!r}"
        expect(pp.toast_message).to_have_count(0, timeout=TOAST_DISMISS_TIMEOUT)

    with allure.step("Step 7 — Hover the Copy text icon; tooltip 'Copy text'"):
        assert pp.hover_last_response_copy_icon("text") == "Copy text"

    with allure.step("Step 8 — Click Copy text; toast 'Text copied to clipboard.'"):
        toast = pp.click_last_response_copy_icon("text")
        assert toast == "Text copied to clipboard.", f"Unexpected toast: {toast!r}"
