"""UI Test for ELITEA-2875 — Basic interjection queuing and sequential processing.

Verifies the mid-turn interjection flow end-to-end: while an agent turn is
still streaming, the user can queue an interjection message; the queue
indicator shows the correct count/text while it is pending; once the
initial response completes, the queued interjection is processed and
receives its own, separate agent response — in strict FIFO order, with no
duplicate or missing responses.

Feature-gated: mid-turn injection is OFF by default at the project tier
(`midturn_injection_enabled`) — the `midturn_injection_enabled` fixture
(`fixtures/data_fixtures.py`) flips it on for the test and restores the
original value after.

Markers:
    - ui: requires browser
    - chat: chat-related test
    - p0: critical priority (AFS Priority l1 == TMS `priority: critical`)

Usage:
    cd automation
    pytest tests/ui/chat/test_chat_interjection_queuing.py -v
"""

import logging

import allure
import pytest

from pages.chat_page import ChatPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p0, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
INTERJECTABLE_WINDOW_TIMEOUT = 30_000   # time for the turn to report "listening"
AI_RESPONSE_TIMEOUT = 60_000            # first (initial) agent response
DRAIN_TIMEOUT = 30_000                  # interjection drain after initial response

# Confirmed live (ELITEA-2875 AFS exploration): this prompt reliably takes
# the model ~5-6s ("Thought for N secs") against this environment's default
# model — long enough to reach the interjectable window every time.
_LONG_RUNNING_PROMPT = (
    "Please write a detailed 500-word story about a dragon who learns to code. "
    "Take your time and be thorough."
)
_INTERJECTION_TEXT = "Interjection message"

# Exact live queue-label text (en dash, confirmed via source read of
# PendingInjectionList.jsx — "Waiting messages – {N}"). The TMS case's own
# "Waiting messages · 1" (middot) paraphrase is case-text drift, not the
# live contract — see AFS Known Defects / role-overrides.md reverse-masking
# guard. Assert the live string, not the case's paraphrase.
_QUEUE_LABEL_ONE_PENDING = "Waiting messages – 1"


@allure.epic("Chat")
@allure.feature("Mid-turn Interjection")
class TestInterjectionQueuingSequentialProcessing:
    """ELITEA-2875 — Queue an interjection mid-turn; it processes after the
    initial response, in FIFO order, with its own separate response."""

    @pytest.mark.tms("ELITEA-2875")
    @allure.title("Interjection queues mid-turn and is processed in FIFO order after the initial response")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat-interface/ELITEA-2875_interjection-queuing-sequential-processing.md",
        "onetest-ai Test Case link",
    )
    def test_interjection_queues_and_processes_in_fifo_order(
        self, page, conversation_id, midturn_injection_enabled
    ):
        chat = ChatPage(page)

        with allure.step("Step 1 — Navigate to a fresh conversation and confirm the chat interface is displayed"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            assert chat.message_input.is_visible(), "chat-message-input should be visible"
            assert chat.message_input.is_editable(), "chat-message-input should be enabled"

        with allure.step("Step 2 — Send the long-running prompt and confirm the agent begins processing"):
            initial_count = chat.get_message_count()
            chat.send_message(_LONG_RUNNING_PROMPT)
            # The user's own message lands at nth(initial_count) immediately on send.
            chat.messages_container.nth(initial_count).wait_for(state="visible", timeout=10_000)

        with allure.step(
            "Step 3 — Wait for the interjectable window: interjection-composer present "
            "confirms the turn is both streaming AND accepting interjections"
        ):
            chat.wait_for_interjectable(timeout=INTERJECTABLE_WINDOW_TIMEOUT)

        with allure.step("Step 4 — Queue an interjection while the agent is still processing"):
            chat.queue_interjection(_INTERJECTION_TEXT)
            assert chat.chat_inject_button.get_attribute("aria-disabled") is None, (
                "chat-inject-button should carry no aria-disabled/error state after a successful click"
            )

        with allure.step("Step 5 — Verify the queue indicator shows the correct count and text"):
            chat.interjection_queue_area.wait_for(state="visible", timeout=5_000)
            label_text = chat.get_interjection_queue_label_text()
            assert label_text == _QUEUE_LABEL_ONE_PENDING, (
                f"Expected queue label '{_QUEUE_LABEL_ONE_PENDING}' (en dash), got {label_text!r}"
            )
            assert chat.get_interjection_queue_count() == 1, "Exactly one interjection should be queued"
            item_texts = chat.get_interjection_queue_item_texts()
            assert item_texts == [_INTERJECTION_TEXT], (
                f"Queued item text should match the sent interjection, got {item_texts}"
            )

        with allure.step("Step 6 — Wait for the initial (first) agent response to complete"):
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        with allure.step(
            "Step 7 — Verify the interjection is processed with its own separate response, "
            "in FIFO order, and the queue indicator disappears"
        ):
            chat.wait_for_interjection_drain(timeout=DRAIN_TIMEOUT)
            chat.wait_for_message_content_stable(timeout=30_000)

            n = chat.get_message_count()
            assert n == initial_count + 4, (
                f"Expected exactly {initial_count + 4} timeline entries "
                f"(initial msg, its response, interjection, its response), got {n}"
            )

            user_initial = chat._extract_message_body(chat.messages_container.nth(initial_count))
            ai_initial_response = chat._extract_message_body(chat.messages_container.nth(initial_count + 1))
            user_interjection = chat._extract_message_body(chat.messages_container.nth(initial_count + 2))
            ai_interjection_response = chat._extract_message_body(chat.messages_container.nth(initial_count + 3))

            assert user_initial == _LONG_RUNNING_PROMPT, "First timeline entry should be the user's initial message"
            assert ai_initial_response, "Second timeline entry should be the agent's response to the initial message"
            assert user_interjection == _INTERJECTION_TEXT, (
                "Third timeline entry should be the user's interjection, now a normal message"
            )
            assert ai_interjection_response, (
                "Fourth timeline entry should be the agent's separate response to the interjection"
            )
            assert ai_interjection_response != ai_initial_response, (
                "The interjection's response must be distinct from the initial message's response "
                "(no duplicate response)"
            )

            assert chat.interjection_queue_area.count() == 0, (
                "interjection-queue-area should unmount entirely once the interjection has been folded "
                "into the timeline (PendingInjectionList returns null on empty items)"
            )
