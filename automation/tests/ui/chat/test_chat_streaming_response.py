"""UI Test for ELITEA-2181 — streaming response displayed while the LLM generates output.

Sends one long-poem prompt in a fresh conversation and observes the streaming
timeline: loading placeholder -> Thought accordion + model chip -> progressive
text -> Pause/Resume-scroll toggle -> completion (toggle gone, action icons,
input editable). Case-text drift (no spinning circle; Pause scroll scoped to
the Thought accordion) is CLARIFICATION #1100 — the live contract is asserted.

Usage:
    cd automation
    pytest tests/ui/chat/test_chat_streaming_response.py -v
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from pages.chat_page import ChatPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p2, pytest.mark.regression]

_PROMPT = "Write a long poem about the city"
GENERATION_TIMEOUT = 120_000  # AFS: 12-54s observed on DEV; size generously
STREAM_START_TIMEOUT = 30_000


@allure.epic("Chat")
@allure.feature("Streaming Response")
class TestStreamingResponse:
    """ELITEA-2181 — streaming response with progressive display and indicators."""

    @pytest.mark.tms("ELITEA-2181")
    @allure.title("Streaming response is displayed progressively while the LLM generates output")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2181_chat-streaming-response-displayed-while-llm-generates-output.md",
        "onetest-ai Test Case link",
    )
    def test_streaming_response_displayed_progressively(self, page, conversation_id):
        chat = ChatPage(page)

        with allure.step("Step 1 — Send the long-poem prompt in a fresh conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.dismiss_banner_if_present()
            # Baseline: send button is absent while the input is empty (general rule).
            expect(chat.send_button).to_have_count(0)
            chat.send_message(_PROMPT)
            # Fresh conversation: the just-sent user prompt is the last message item.
            expect(chat.messages_container.last).to_contain_text(_PROMPT)
            assert chat.message_input.input_value() == "", "Input must be cleared after send"

        with allure.step("Step 2 — Loading placeholder, then Thought accordion with the model chip"):
            # Placeholder lives ~0-2s; tolerate it being gone only if the accordion is already up.
            try:
                chat.answer_loading_placeholder.wait_for(state="visible", timeout=5_000)
            except Exception:
                expect(chat.answer_thought_accordion).to_be_visible(timeout=STREAM_START_TIMEOUT)
            expect(chat.answer_thought_accordion).to_be_visible(timeout=STREAM_START_TIMEOUT)
            expect(chat.answer_model_chip).to_be_visible(timeout=STREAM_START_TIMEOUT)
            expect(chat.answer_model_chip).not_to_be_empty()

        with allure.step("Step 4 — 'Pause scroll' control is visible during streaming"):
            expect(chat.answer_pause_scroll_toggle).to_be_visible(timeout=STREAM_START_TIMEOUT)
            expect(chat.answer_pause_scroll_toggle).to_have_text("Pause scroll")

        with allure.step("Step 6 — Send button is not visible during streaming"):
            expect(chat.send_button).to_have_count(0)

        with allure.step("Step 5 — Click 'Pause scroll'; the toggle flips to 'Resume scroll'"):
            chat.answer_pause_scroll_toggle.click()
            expect(chat.answer_pause_scroll_toggle).to_have_text("Resume scroll")

        with allure.step("Step 3 — Response text grows progressively and never shrinks"):
            last = chat.messages_container.last
            first = chat._extract_message_body(last)
            # Condition wait: body text longer than the first sample, or generation already finished.
            page.wait_for_function(
                """(first) => {
                    const items = document.querySelectorAll('[data-testid="chat-message-item"]');
                    const el = items[items.length - 1];
                    if (!el) return false;
                    const text = Array.from(el.querySelectorAll('p, li')).map(n => n.textContent || '').join('\\n').trim();
                    return text.length > first.length || !!el.querySelector('[data-testid="chat-copy-button"]');
                }""",
                arg=first,
                timeout=GENERATION_TIMEOUT,
            )
            second = chat._extract_message_body(last)
            assert len(second) >= len(first), f"Streamed text shrank: {len(first)} -> {len(second)}"
            if chat.copy_action_button.count() == 0:
                assert second != first, "Text must grow while streaming is still in progress"

        with allure.step("Step 7 — Streaming completes: Pause/Resume toggle gone, Copy visible"):
            expect(chat.answer_pause_scroll_toggle).to_have_count(0, timeout=GENERATION_TIMEOUT)
            expect(chat.answer_loading_placeholder).to_have_count(0)
            last = chat.messages_container.last
            last.hover()
            expect(chat.copy_action_button.last).to_be_visible(timeout=GENERATION_TIMEOUT)

        with allure.step("Step 8 — Read-out, Copy, Regenerate and Delete icons appear on hover"):
            last.hover()
            expect(chat.read_out_button.last).to_be_visible()
            expect(chat.copy_action_button.last).to_be_visible()
            expect(chat.regenerate_action_button).to_be_visible()
            expect(chat.delete_action_button.last).to_be_visible()

        with allure.step("Step 9 — Input field is active again"):
            assert chat.message_input.is_editable(), "Input must be editable after streaming completes"
