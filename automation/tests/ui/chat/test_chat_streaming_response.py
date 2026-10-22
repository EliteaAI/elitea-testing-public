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
import time

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

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
            initial_count = chat.get_message_count()
            # Baseline: send button is absent while the input is empty (general rule).
            expect(chat.send_button).to_have_count(0)
            chat.send_message(_PROMPT)
            # User prompt + AI reply item appear; exactly one item carries the prompt text.
            expect(chat.messages_container).to_have_count(initial_count + 2, timeout=STREAM_START_TIMEOUT)
            expect(chat.messages_container.filter(has_text=_PROMPT)).to_have_count(1)
            assert chat.message_input.input_value() == "", "Input must be cleared after send"

        # AI answer item: lazy locator, resolves once the Thought accordion renders.
        ai_msg = chat.messages_container.filter(has=chat.answer_thought_accordion)

        with allure.step("Step 2 — Loading placeholder, then Thought accordion with the model chip"):
            # Placeholder lives ~0-2s. If missed, the response must provably still be in flight
            # (no completion action yet) so the accordion/chip below are streaming-state evidence.
            try:
                chat.answer_loading_placeholder.wait_for(state="visible", timeout=5_000)
            except PlaywrightTimeoutError:
                logger.info("Placeholder already gone; verifying generation still in flight")
                expect(chat.REGENERATE_ACTION_BUTTON.within(ai_msg)).to_have_count(0)
            expect(chat.answer_thought_accordion).to_be_visible(timeout=STREAM_START_TIMEOUT)
            expect(chat.answer_model_chip).to_be_visible(timeout=STREAM_START_TIMEOUT)
            expect(chat.answer_model_chip).not_to_be_empty()

        # Streaming lasts only ~4-8s on DEV: sample growth immediately, while the Pause-scroll
        # toggle (live-streaming indicator) is still on screen, before the Step 4-6 checks.
        with allure.step("Step 3 — Response text grows progressively (>=2 growing samples) and never shrinks"):
            samples = [len(chat._extract_message_body(ai_msg))]
            deadline = time.monotonic() + 20
            while len(set(samples)) < 3 and time.monotonic() < deadline:
                # Observation interval between samples, not a synchronisation wait.
                page.wait_for_timeout(300)
                samples.append(len(chat._extract_message_body(ai_msg)))
            assert samples == sorted(samples), f"Streamed text shrank: {samples}"
            assert len(set(samples)) >= 3, f"Text did not grow progressively while streaming: {samples}"
            # still streaming when growth was seen
            expect(chat.REGENERATE_ACTION_BUTTON.within(ai_msg)).to_have_count(0)

        with allure.step("Step 4 — 'Pause scroll' control is visible during streaming"):
            expect(chat.answer_pause_scroll_toggle).to_have_text("Pause scroll")

        with allure.step("Step 6 — Send button is not visible during streaming"):
            # Toggle visible == still streaming, so the zero count is a streaming-state fact.
            expect(chat.answer_pause_scroll_toggle).to_be_visible(timeout=1_000)
            expect(chat.send_button).to_have_count(0)

        with allure.step("Step 5 — Click 'Pause scroll'; the toggle flips to 'Resume scroll'"):
            chat.answer_pause_scroll_toggle.click()
            expect(chat.answer_pause_scroll_toggle).to_have_text("Resume scroll")

        with allure.step("Step 7 — Streaming completes: Pause/Resume toggle gone, Copy visible"):
            expect(chat.answer_pause_scroll_toggle).to_have_count(0, timeout=GENERATION_TIMEOUT)
            expect(chat.answer_loading_placeholder).to_have_count(0)
            expect(chat.REGENERATE_ACTION_BUTTON.within(ai_msg)).to_be_attached(timeout=GENERATION_TIMEOUT)
            ai_msg.hover()
            expect(chat.COPY_ACTION_BUTTON.within(ai_msg)).to_be_visible()

        with allure.step("Step 8 — Read-out, Copy, Regenerate and Delete icons appear on hover"):
            ai_msg.hover()
            expect(chat.READ_OUT_ACTION_BUTTON.within(ai_msg)).to_be_visible()
            expect(chat.COPY_ACTION_BUTTON.within(ai_msg)).to_be_visible()
            expect(chat.REGENERATE_ACTION_BUTTON.within(ai_msg)).to_be_visible()
            expect(chat.DELETE_ACTION_BUTTON.within(ai_msg)).to_be_visible()

        with allure.step("Step 9 — Input field is active again"):
            assert chat.message_input.is_editable(), "Input must be editable after streaming completes"
