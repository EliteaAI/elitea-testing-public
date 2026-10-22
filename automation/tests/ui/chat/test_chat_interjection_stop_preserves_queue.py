"""UI Test for ELITEA-2878 — Stop preserves queued messages (mid-turn interjections).

Clicking Stop while interjections are queued does NOT discard them: it
rescues the pending queue and auto-drains it, one item at a time, into real
timeline messages — each with its own agent response — rather than freezing
the queue or losing anything. Verifies the intermediate rescue state, the
final fully-drained state, byte-exact message text preservation, and that
chat keeps functioning normally afterward.

AFS-amended mechanism (see `test-specs/chat-interface/l1_interjection-stop-
preserves-queued-messages_ELITEA-2878.md` § step 6 amendment, 2026-10-17):
ONE Stop click rescues and auto-drains the WHOLE queue — a second click
during the auto-drain is a no-op and is deliberately NOT sent by this test.

Feature-gated: same `midturn_injection_enabled` fixture as ELITEA-2875/2876/2877.

Markers:
    - ui: requires browser
    - chat: chat-related test
    - p0: critical priority (AFS Priority l1 == TMS `priority: critical`)

Usage:
    cd automation
    pytest tests/ui/chat/test_chat_interjection_stop_preserves_queue.py -v
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
INTERJECTABLE_WINDOW_TIMEOUT = 30_000
RESCUE_SIGNAL_TIMEOUT = 5_000       # intermediate state: head item rescued, 2nd still queued
DRAIN_TIMEOUT = 30_000
AI_RESPONSE_TIMEOUT = 30_000        # for the post-drain continuation message

_LONG_RUNNING_PROMPT = (
    "Please write a detailed 500-word story about a dragon who learns to code. "
    "Take your time and be thorough."
)
_INTERJECTION_1 = "First queued message"
_INTERJECTION_2 = "Second queued message"
_CONTINUATION_MESSAGE = "continuing chat after stop"

# Exact live queue-label text (en dash) — same family-wide clarification as
# ELITEA-2875/2876/2877.
_QUEUE_LABEL_TWO_PENDING = "Waiting messages – 2"
_QUEUE_LABEL_ONE_PENDING = "Waiting messages – 1"


@allure.epic("Chat")
@allure.feature("Mid-turn Interjection")
class TestInterjectionStopPreservesQueuedMessages:
    """ELITEA-2878 — Stop rescues and auto-drains the queue (one click), never
    discards a queued message."""

    @pytest.mark.tms("ELITEA-2878")
    @allure.title("Stop rescues and auto-drains the entire queue — no message is lost, chat keeps working")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2878_stop-preserves-queue-automated.md",
        "onetest-ai Test Case link",
    )
    def test_stop_rescues_and_auto_drains_queue_without_loss(
        self, page, conversation_id, midturn_injection_enabled
    ):
        chat = ChatPage(page)

        with allure.step(
            "Step 1 — Navigate to a fresh conversation, send the long-running prompt, "
            "and reach the interjectable window"
        ):
            chat.navigate_to_chat(conversation_id=conversation_id)
            initial_count = chat.get_message_count()
            chat.send_message(_LONG_RUNNING_PROMPT)
            chat.wait_for_interjectable(timeout=INTERJECTABLE_WINDOW_TIMEOUT)

        with allure.step("Step 2 — Queue Interjection 1"):
            chat.queue_interjection(_INTERJECTION_1)
            assert chat.get_interjection_queue_count() == 1, "Exactly one interjection should be queued"
            assert chat.get_interjection_queue_item_texts() == [_INTERJECTION_1]

        with allure.step("Step 3 — Queue Interjection 2"):
            chat.queue_interjection(_INTERJECTION_2)
            label_text = chat.get_interjection_queue_label_text()
            assert label_text == _QUEUE_LABEL_TWO_PENDING, (
                f"Expected queue label '{_QUEUE_LABEL_TWO_PENDING}' (en dash), got {label_text!r}"
            )

        with allure.step(
            "Step 4 — Click Stop ONCE and confirm the run is interrupted — the live mechanism "
            "is a rescue-and-auto-redrain, not a hard freeze (confirm live, don't assume)"
        ):
            chat.click_stop()

        with allure.step(
            "Step 5 — Verify the INTERMEDIATE rescue state: Interjection 1 converts to a normal "
            "timeline entry with its own agent response starting, while Interjection 2 remains "
            "visible in the queue with the count decremented to 1 — this proves the queue is "
            "genuinely non-destructive mid-drain, not just a coincidental end-state"
        ):
            # The rescue REPLACES the content of the ORIGINAL (already-visible)
            # message's own <li> node at nth(initial_count) in place — it is
            # not a new element appearing, so a presence-only wait resolves
            # instantly and can read back stale (pre-Stop) text (confirmed
            # live, ELITEA-2878 implementation 2026-10-17). Poll for the
            # exact expected text instead.
            rescued_text = chat.wait_for_message_body_text(
                chat.messages_container.nth(initial_count), _INTERJECTION_1, timeout=RESCUE_SIGNAL_TIMEOUT
            )
            assert rescued_text == _INTERJECTION_1, (
                f"Rescued head-of-queue item should appear as a normal message with text "
                f"'{_INTERJECTION_1}', got {rescued_text!r}"
            )
            # Interjection 2 should still be queued (not yet rescued).
            remaining_label = chat.get_interjection_queue_label_text()
            assert remaining_label == _QUEUE_LABEL_ONE_PENDING, (
                f"Expected queue label '{_QUEUE_LABEL_ONE_PENDING}' (en dash) while Interjection 2 "
                f"is still queued, got {remaining_label!r}"
            )
            assert chat.get_interjection_queue_item_texts() == [_INTERJECTION_2], (
                "Interjection 2 should still be the only queued item during the intermediate rescue state"
            )

        with allure.step(
            "Step 6 — AFS-amended: do NOT click Stop a second time (it is a no-op during the "
            "auto-drain). Wait for the full automatic redrain: both queued messages must appear "
            "as normal timeline entries, each with its own response, and the queue must be gone"
        ):
            chat.wait_for_interjection_drain(timeout=DRAIN_TIMEOUT)
            chat.wait_for_message_content_stable(timeout=30_000)

            total_entries = chat.get_message_count() - initial_count
            assert total_entries == 4, (
                f"Expected exactly 4 timeline entries (Interjection 1, its response, Interjection 2, "
                f"its response) after the single-click auto-drain, got {total_entries}"
            )
            assert chat.interjection_queue_area.count() == 0, "Queue area should be gone after full drain"
            assert chat.interjection_composer.count() == 0, "Composer should be gone — no active run remains"

        with allure.step("Step 7 — Verify both messages' text matches the original exactly (byte-for-byte)"):
            text_1 = chat._extract_message_body(chat.messages_container.nth(initial_count))
            text_2 = chat._extract_message_body(chat.messages_container.nth(initial_count + 2))
            assert text_1 == _INTERJECTION_1, f"First rescued message text corrupted: {text_1!r}"
            assert text_2 == _INTERJECTION_2, f"Second rescued message text corrupted: {text_2!r}"

            response_1 = chat._extract_message_body(chat.messages_container.nth(initial_count + 1))
            response_2 = chat._extract_message_body(chat.messages_container.nth(initial_count + 3))
            assert response_1, "Interjection 1 should have its own agent response"
            assert response_2, "Interjection 2 should have its own agent response"
            assert response_1 != response_2, "Each rescued message's response must be distinct (no duplicate)"

        with allure.step(
            "Step 8 — Send a new message to continue chatting; confirm chat is NOT left in a "
            "broken/unresponsive state after the Stop-and-drain sequence"
        ):
            count_before_continuation = chat.get_message_count()
            chat.send_message(_CONTINUATION_MESSAGE)
            chat.wait_for_ai_response(initial_count=count_before_continuation, timeout=AI_RESPONSE_TIMEOUT)
            assert chat.get_message_count() > count_before_continuation, (
                "Chat should accept and respond to a new message normally after the Stop-and-drain sequence"
            )
