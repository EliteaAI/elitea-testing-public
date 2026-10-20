"""UI Test for ELITEA-2181 — streaming response displayed while the LLM generates output.

AFS: test-specs/chat-interface/l2_streaming-response-progressive-display_ELITEA-2181.md
Live contract (CLARIFICATION #1100): the "loading indicator" is a rotating text
placeholder followed by a model-chip-bearing "Thought for N secs" accordion; the
Pause/Resume-scroll toggle is scoped to that accordion.

Markers:
    - ui: requires browser
    - chat: chat-related test
    - p2: AFS priority l2

Usage:
    cd automation
    pytest tests/ui/chat/test_chat_streaming_response_display.py -v
"""

import logging
import time

import allure
import pytest
from playwright.sync_api import expect

from pages.chat_page import ChatPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p2, pytest.mark.regression]

_PROMPT = "Write a long poem about the city"
PLACEHOLDER_TIMEOUT = 15_000
CHIP_TIMEOUT = 15_000
STREAM_GROWTH_TIMEOUT_S = 45
COMPLETION_TIMEOUT = 120_000  # AFS: generation 12-54s depending on participant/tool path


@allure.epic("Chat")
@allure.feature("Streaming response")
class TestStreamingResponseDisplay:
    """ELITEA-2181 — progressive streaming with indicators, pause-scroll and restored input."""

    @pytest.mark.tms("ELITEA-2181")
    @allure.title("LLM response streams progressively with indicators; input restored after completion")
    @allure.severity(allure.severity_level.NORMAL)
    def test_streaming_response_displayed_while_generating(self, page, conversation_id):
        chat = ChatPage(page)

        with allure.step("Step 1 — Type the prompt and send; user message appears, input cleared"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.dismiss_popups()
            initial_count = chat.get_message_count()
            # Baseline: send button is absent while the input is empty (explains step 6)
            expect(chat.send_button).to_have_count(0)
            chat.message_input.fill(_PROMPT)
            expect(chat.send_button).to_have_count(1)
            chat.send_message(_PROMPT)
            expect(chat.messages_container).to_have_count(initial_count + 2, timeout=30_000)
            expect(chat.messages_container.filter(has_text=_PROMPT)).to_have_count(1)
            assert chat.message_input.input_value() == "", "Input must be cleared after send"

        with allure.step("Step 2 — Loading placeholder shows, then model-name chip in the Thought accordion"):
            # Placeholder lives ~0-2s; tolerate it already gone only if accordion+chip are visible.
            placeholder_seen = False
            try:
                chat.answer_loading_placeholder.wait_for(state="visible", timeout=PLACEHOLDER_TIMEOUT)
                placeholder_seen = True
            except Exception:
                logger.info("Placeholder already gone; relying on accordion + chip")
            chat.answer_thought_accordion.wait_for(state="visible", timeout=CHIP_TIMEOUT)
            chat.answer_model_chip.wait_for(state="visible", timeout=CHIP_TIMEOUT)
            assert (chat.answer_model_chip.text_content() or "").strip(), "Model chip must name the model"
            if not placeholder_seen:
                assert chat.answer_model_chip.is_visible()

        ai_msg = chat.messages_container.last

        with allure.step("Step 3 — Response text streams progressively (grows monotonically)"):
            previous = ""
            grew = False
            deadline = time.monotonic() + STREAM_GROWTH_TIMEOUT_S
            while time.monotonic() < deadline:
                current = chat._extract_message_body(ai_msg)
                if previous:
                    assert current.startswith(previous) or previous in current, (
                        f"Streamed text shrank/reset: {previous[:60]!r} -> {current[:60]!r}"
                    )
                if previous and len(current) > len(previous):
                    grew = True
                    break
                if current:
                    previous = current
                # Observation interval for sampling growth, not a synchronisation wait.
                page.wait_for_timeout(2000)
            assert grew, "Response body never grew across samples during streaming"

        with allure.step("Step 4 — 'Pause scroll' control is visible during streaming"):
            expect(chat.answer_pause_scroll_toggle).to_have_text("Pause scroll", timeout=30_000)

        with allure.step("Step 5 — Click 'Pause scroll'; control flips to 'Resume scroll'"):
            chat.answer_pause_scroll_toggle.click()
            expect(chat.answer_pause_scroll_toggle).to_have_text("Resume scroll", timeout=5_000)

        with allure.step("Step 6 — Send button is not visible during streaming"):
            expect(chat.send_button).to_have_count(0)

        with allure.step("Step 7 — On completion the loading indicator and pause-scroll toggle are gone"):
            expect(chat.regenerate_action_button).to_be_attached(timeout=COMPLETION_TIMEOUT)
            expect(chat.answer_pause_scroll_toggle).to_have_count(0)
            expect(chat.answer_loading_placeholder).to_have_count(0)

        with allure.step("Step 8 — Speaker, copy, regenerate and delete icons appear on hover"):
            ai_msg.hover()
            expect(chat.read_out_button).to_be_visible()
            expect(chat.copy_action_button).to_be_visible()
            expect(chat.regenerate_action_button).to_be_visible()
            expect(chat.delete_action_button).to_be_visible()

        with allure.step("Step 9 — Input field is active again"):
            expect(chat.message_input).to_be_editable()
