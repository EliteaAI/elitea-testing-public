"""UI Test for ELITEA-2876 — FIFO message order preservation (mid-turn interjections).

Queues three interjections back-to-back while an agent turn is streaming,
then verifies: each appears in the queue in strict submission order (0/1/2),
the queue count label reflects 3 pending, the full drain processes all three
in submission order, and each gets exactly one agent response — no
duplicate, no skipped, no reordered entry.

Feature-gated: same `midturn_injection_enabled` fixture as ELITEA-2875.

Markers:
    - ui: requires browser
    - chat: chat-related test
    - p0: critical priority (AFS Priority l1 == TMS `priority: critical`)

Usage:
    cd automation
    pytest tests/ui/chat/test_chat_interjection_fifo_order.py -v
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
DRAIN_TIMEOUT = 30_000       # confirmed live: ~11-12s for 3 queued items against this model
STABLE_CONTENT_TIMEOUT = 30_000

_LONG_RUNNING_PROMPT = (
    "Please write a detailed 500-word story about a dragon who learns to code. "
    "Take your time and be thorough."
)
# Case text's own literal wording — confirmed live, no drift (unlike the
# queue-count-text paraphrase below).
_MESSAGE_A = "First message"
_MESSAGE_B = "Second message"
_MESSAGE_C = "Third message"

# Exact live queue-label text (en dash) — same clarification as ELITEA-2875.
_QUEUE_LABEL_THREE_PENDING = "Waiting messages – 3"


@allure.epic("Chat")
@allure.feature("Mid-turn Interjection")
class TestInterjectionFifoMessageOrderPreservation:
    """ELITEA-2876 — Three rapid interjections queue, drain, and respond in
    strict FIFO order with no duplicate or missing responses."""

    @pytest.mark.tms("ELITEA-2876")
    @allure.title("Three rapid interjections queue, process, and respond in strict FIFO order")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2876_message-order-fifo-automated.md",
        "onetest-ai Test Case link",
    )
    def test_three_interjections_process_in_fifo_order(
        self, page, conversation_id, midturn_injection_enabled
    ):
        chat = ChatPage(page)

        with allure.step("Step 1 — Navigate to a fresh conversation and send the long-running prompt"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            initial_count = chat.get_message_count()
            chat.send_message(_LONG_RUNNING_PROMPT)
            chat.wait_for_interjectable(timeout=INTERJECTABLE_WINDOW_TIMEOUT)

        with allure.step(
            "Step 2 — Queue Message A, B, C in rapid succession; after each queue action "
            "the newest item appends to the END of the existing items, in submission order"
        ):
            chat.queue_interjection(_MESSAGE_A)
            assert chat.get_interjection_queue_item_texts() == [_MESSAGE_A], (
                "Queue should hold exactly Message A after the first queue action"
            )

            chat.queue_interjection(_MESSAGE_B)
            assert chat.get_interjection_queue_item_texts() == [_MESSAGE_A, _MESSAGE_B], (
                "Queue should hold A, B in submission order after the second queue action"
            )

            chat.queue_interjection(_MESSAGE_C)
            assert chat.get_interjection_queue_item_texts() == [_MESSAGE_A, _MESSAGE_B, _MESSAGE_C], (
                "Queue should hold A, B, C in submission order after the third queue action"
            )

        with allure.step("Step 3 — Verify the queue count label shows 3"):
            label_text = chat.get_interjection_queue_label_text()
            assert label_text == _QUEUE_LABEL_THREE_PENDING, (
                f"Expected queue label '{_QUEUE_LABEL_THREE_PENDING}' (en dash), got {label_text!r}"
            )

        with allure.step(
            "Step 4 — Wait for all three messages to fully drain (queue area gone AND "
            "the agent's turn fully settled, no interjection-composer present)"
        ):
            chat.wait_for_interjection_drain(timeout=DRAIN_TIMEOUT)
            chat.wait_for_message_content_stable(timeout=STABLE_CONTENT_TIMEOUT)

        with allure.step(
            "Step 5 — Assert processing order matches send order by reading the full "
            "message timeline (user-authored entries only)"
        ):
            user_texts = chat.get_user_message_texts()
            assert user_texts == [_LONG_RUNNING_PROMPT, _MESSAGE_A, _MESSAGE_B, _MESSAGE_C], (
                f"User-authored timeline order must be [prompt, A, B, C], got {user_texts}"
            )

        with allure.step("Step 6 — Verify each message has exactly one response (8 total timeline entries)"):
            total_entries = chat.get_message_count() - initial_count
            assert total_entries == 8, (
                f"Expected exactly 8 timeline entries (prompt, response, A, response, B, response, "
                f"C, response), got {total_entries} — a non-8 count is a genuine failure, not noise"
            )

            # Alternate ai/user/ai/user... starting with the initial user prompt:
            # entries [0]=user prompt, [1]=ai, [2]=user A, [3]=ai, [4]=user B, [5]=ai, [6]=user C, [7]=ai
            for offset in (0, 2, 4, 6):
                idx = initial_count + offset
                assert not chat._is_ai_message(chat.messages_container.nth(idx)), (
                    f"Timeline entry at offset {offset} should be user-authored"
                )
            for offset in (1, 3, 5, 7):
                idx = initial_count + offset
                assert chat._is_ai_message(chat.messages_container.nth(idx)), (
                    f"Timeline entry at offset {offset} should be the agent's response "
                    f"to the preceding user message"
                )

            assert chat.interjection_queue_area.count() == 0, "Queue area should be gone after full drain"
            assert chat.interjection_composer.count() == 0, "Composer should be gone after full drain (no active run)"
