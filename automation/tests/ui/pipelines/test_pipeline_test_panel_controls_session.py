"""UI test — Pipeline: Test Pipeline panel controls and session behavior.

TMS: ELITEA-4720
(test-specs/pipelines/l1_pipeline-test-panel-controls-and-session-behavior_ELITEA-4720.md)

Walks the on-demand Test panel: open/close, run, context pill + popover, Run History, unsaved-change send gate,
close mid-run, resize persistence, Clear chat.

Case-text drift (AFS § Clarifications): the unsaved edit is a NODE edit (LLM System) because a Description edit
does not gate sending (C1); Run History is a route and returning leaves the panel closed with an empty
conversation, so the chat is re-seeded with Message 1 after it (C2); the pill reads "0%" for a short exchange (C3).
"""

import re

import allure
import pytest
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p1, pytest.mark.regression]

T = 15_000
SAVE_TIMEOUT = 30_000
RUN_TIMEOUT = 90_000
LLM = "LLM 1"
MESSAGE_1 = "Hello"
MESSAGE_2 = "Write a short poem about pipelines"
SEND_HINT = "Save the pipeline to test the latest changes."
DEFAULT_WIDTH = 373
WIDTH_TOLERANCE = 2


def _send_and_settle(pp: PipelineDetailPage, message: str, expected_items: int) -> None:
    """Send *message* and wait until the conversation holds *expected_items* items with a non-empty answer."""
    pp.send_message_in_embedded_chat(message, timeout=T)
    expect(pp.embedded_chat_items()).to_have_count(expected_items, timeout=RUN_TIMEOUT)
    expect(pp.skill_test_last_response.last).not_to_be_empty(timeout=RUN_TIMEOUT)


@pytest.mark.tms("ELITEA-4720")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-4720_pipeline-test-pipeline-panel-controls-and-session-behavior.md",
    "onetest-ai Test Case link",
)
def test_pipeline_test_panel_controls_and_session(page, pipeline_with_fstring_llm_id):
    """Test panel: on-demand open, run, context, history, unsaved gate, close mid-run, width persistence, clear."""
    pipeline_id = pipeline_with_fstring_llm_id
    page.set_viewport_size({"width": 1600, "height": 1400})
    pp = PipelineDetailPage(page)
    items = pp.embedded_chat_items()
    width_key_prefix = "pipelineTestPanelWidth"

    with allure.step("Step 1 — Open the pipeline: panel closed, Test Pipeline button enabled"):
        pp.navigate(pipeline_id)
        pp.dismiss_banner_if_present()
        pp.wait_for_canvas()
        expect(pp.test_pipeline_panel).to_be_hidden(timeout=T)
        expect(pp.test_pipeline_button).to_be_visible(timeout=T)
        expect(pp.test_pipeline_button).to_be_enabled(timeout=T)

    with allure.step("Step 2 — Click Test Pipeline: panel opens with input, model selector and controls"):
        pp.test_pipeline_button.click()
        expect(pp.test_pipeline_panel).to_be_visible(timeout=T)
        expect(pp.chat_input).to_be_visible(timeout=T)
        expect(pp.model_selector_button).to_be_visible(timeout=T)
        expect(pp.test_panel_controls).to_be_visible(timeout=T)
        expect(pp.history_tab).to_be_visible(timeout=T)
        expect(pp.chat_clear_button).to_be_visible(timeout=T)
        expect(pp.test_panel_close_button).to_be_visible(timeout=T)
        expect(pp.test_pipeline_button).to_be_hidden(timeout=T)

    with allure.step("Step 3 — Send Hello: messages appear and the LLM node is highlighted running"):
        pp.send_message_in_embedded_chat(MESSAGE_1, timeout=T)
        expect(pp.node_card_running(LLM)).to_have_count(1, timeout=T)
        expect(items).to_have_count(2, timeout=RUN_TIMEOUT)
        expect(pp.skill_test_last_response.last).not_to_be_empty(timeout=RUN_TIMEOUT)
        expect(pp.chat_answer_model_chip.first).to_be_visible(timeout=T)

    with allure.step("Step 4 — The Context pill shows a percentage"):
        expect(pp.context_budget_pill).to_have_text(re.compile(r"^\d+%$"), timeout=T)

    with allure.step("Step 5 — Context popover: tokens, 2 messages, 0 summaries, Edit action"):
        pp.context_budget_pill.click()
        expect(pp.context_budget_popover).to_be_visible(timeout=T)
        expect(pp.context_budget_tokens).to_be_visible(timeout=T)
        expect(pp.context_budget_messages_count).to_have_text("2", timeout=T)
        expect(pp.context_budget_summaries_count).to_have_text("0", timeout=T)
        expect(pp.context_budget_edit_button).to_be_visible(timeout=T)

    with allure.step("Step 6 — Close popover; Run History tooltip; the route lists the run; return"):
        page.keyboard.press("Escape")
        expect(pp.context_budget_popover).to_have_count(0, timeout=T)
        assert pp.hover_history_tab_tooltip() == "Run History"
        pp.history_tab.click()
        page.wait_for_url(re.compile(rf"/pipelines/all/{pipeline_id}/history"), timeout=T)
        pp.wait_for_run_history_rows(timeout=T)
        assert pp.get_run_history_item_count() >= 1
        page.go_back()
        pp.wait_for_detail_page_load()
        pp.dismiss_banner_if_present()
        # Returning from the route leaves the panel closed with an empty conversation (AFS C2): re-seed it.
        expect(pp.test_pipeline_panel).to_be_hidden(timeout=T)
        pp.open_test_pipeline_panel(timeout=T)
        _send_and_settle(pp, MESSAGE_1, expected_items=2)

    with allure.step("Step 7 — Unsaved node edit, close the panel: Test Pipeline button shown and enabled"):
        pp.open_node_panel_by_card(LLM, timeout=T)
        pp.fill_llm_node_section_value("system", "You are a concise assistant.", timeout=T)
        expect(pp.save_button).to_be_enabled(timeout=T)
        pp.close_test_panel(timeout=T)
        expect(pp.test_pipeline_button).to_be_enabled(timeout=T)

    with allure.step("Step 7a — Reopen: the same conversation"):
        pp.test_pipeline_button.click()
        expect(pp.test_pipeline_panel).to_be_visible(timeout=T)
        expect(items).to_have_count(2, timeout=T)

    with allure.step("Step 8 — Unsaved change: send disabled with the save hint, Enter sends nothing"):
        pp.chat_input.fill(MESSAGE_1)
        expect(pp.chat_send_button).to_be_disabled(timeout=T)
        assert pp.hover_send_button_hint() == SEND_HINT
        pp.chat_input.press("Enter")
        expect(items).to_have_count(2, timeout=T)

    with allure.step("Step 9 — Save, then send Hello: a response arrives"):
        pp.dismiss_banner_if_present()
        pp.save_and_wait_for_saved(timeout=SAVE_TIMEOUT)
        expect(pp.save_button).to_be_disabled(timeout=T)
        expect(pp.chat_send_button).to_be_enabled(timeout=T)
        pp.chat_input.fill(MESSAGE_1)
        pp.chat_send_button.click()
        expect(items).to_have_count(4, timeout=RUN_TIMEOUT)
        expect(pp.skill_test_last_response.last).not_to_be_empty(timeout=RUN_TIMEOUT)

    with allure.step("Step 10 — Send the poem prompt and close the panel mid-run: run keeps highlighting"):
        pp.send_message_in_embedded_chat(MESSAGE_2, timeout=T)
        expect(pp.node_card_running(LLM)).to_have_count(1, timeout=T)
        pp.close_test_panel(timeout=T)
        expect(pp.node_card_running(LLM)).to_have_count(1, timeout=1_000)

    with allure.step("Step 11 — Reopen: same conversation with the completed poem"):
        pp.test_pipeline_button.click()
        expect(pp.test_pipeline_panel).to_be_visible(timeout=T)
        expect(items).to_have_count(6, timeout=RUN_TIMEOUT)
        expect(pp.skill_test_last_response.last).not_to_be_empty(timeout=RUN_TIMEOUT)
        assert len(pp.get_last_embedded_chat_message_text().splitlines()) > 1, "Poem should span several lines"
        expect(pp.node_card_running(LLM)).to_have_count(0, timeout=RUN_TIMEOUT)

    with allure.step("Step 12 — Drag the handle wider; the width survives a reload"):
        try:
            before = pp.test_panel_width()
            pp.drag_test_panel_handle_left(100)
            widened = pp.test_panel_width()
            assert widened > before + 50, f"Panel should widen by ~100px: {before} -> {widened}"
            page.reload()
            pp.wait_for_detail_page_load()
            pp.dismiss_banner_if_present()
            pp.open_test_pipeline_panel(timeout=T)
            after = pp.test_panel_width()
            assert abs(after - widened) <= WIDTH_TOLERANCE, f"Width not persisted: {widened} -> {after}"
        finally:
            page.evaluate(
                "prefix => Object.keys(localStorage).filter(k => k.startsWith(prefix))"
                ".forEach(k => localStorage.removeItem(k))",
                width_key_prefix,
            )

    with allure.step("Step 13 — Clear chat: messages removed, pill gone, clear disabled"):
        # The reload dropped the conversation (AFS C2); seed one exchange so Clear is enabled.
        _send_and_settle(pp, MESSAGE_1, expected_items=2)
        expect(pp.chat_clear_button).to_be_enabled(timeout=T)
        pp.chat_clear_button.click()
        expect(items).to_have_count(0, timeout=T)
        expect(pp.context_budget_pill).to_have_count(0, timeout=T)
        expect(pp.chat_clear_button).to_be_disabled(timeout=T)
