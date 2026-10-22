"""UI Test for ELITEA-2182 — Stop button cancels generation and restores the input.

Sending ``generate a poem`` and clicking Stop while the agent turn is still in
its early (waking/thinking) phase cancels the run: the cancelled turn is
removed from the timeline, no answer text ever streams, the Stop control goes
away, the default Send bar returns, and the input is editable again holding
the exact original prompt.

AFS: test-specs/chat-interface/l2_stop-button-cancels-generation-restores-input_ELITEA-2182.md

Declared improvisations (see Run Report):
  - Uses the ``midturn_injection_enabled`` fixture so the existing
    ``ChatPage.STOP_BUTTON`` anchor (``chat_inject_button``) exists (AFS
    Question 1, recommended route). Stop is the same button either way.
  - Stop is clicked as soon as it is visible (the "Waking the agent…" / early
    phase), not gated on the ``Thinking`` label: that label has no ladder
    handle and the whole pre-answer window is ~1-3s on DEV; the AFS records
    that clicking at "Waking the agent…" behaves identically.

Markers:
    - ui: requires browser
    - chat: chat-related test
    - p2: AFS Priority l2 (TMS ``high``)
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from pages.chat_page import ChatPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p2, pytest.mark.regression]

_PROMPT = "generate a poem"
_SECOND_PROMPT = "hello"
STOP_VISIBLE_TIMEOUT = 15_000
RESTORE_TIMEOUT = 10_000


@allure.epic("Chat")
@allure.feature("Stop generation")
class TestChatStopButtonCancelsGeneration:
    """ELITEA-2182 — Stop cancels the generation and restores the exact prompt."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2182_chat-stop-button-appears-during-response-generation.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.tms("ELITEA-2182")
    @allure.title("Stop button cancels generation during thinking and restores the original input")
    @allure.severity(allure.severity_level.NORMAL)
    def test_stop_cancels_generation_and_restores_input(
        self, page, conversation_id, midturn_injection_enabled
    ):
        chat = ChatPage(page)

        with allure.step("Step 1 — Send 'generate a poem' in a fresh conversation; generation starts"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            initial_count = chat.get_message_count()
            chat.send_message(_PROMPT)
            expect(chat.send_button).to_have_count(0, timeout=STOP_VISIBLE_TIMEOUT)
            expect(chat.messages_container).to_have_count(initial_count + 2, timeout=STOP_VISIBLE_TIMEOUT)
            expect(chat.messages_container.filter(has_text=_PROMPT)).to_have_count(
                1, timeout=STOP_VISIBLE_TIMEOUT
            )

        stop_button = chat.STOP_BUTTON.within(chat.chat_inject_button)

        with allure.step("Step 2 — Stop control is visible in the composer footer while generating"):
            expect(stop_button).to_be_visible(timeout=STOP_VISIBLE_TIMEOUT)

        with allure.step("Step 3 — Click Stop while the turn is still in its pre-answer phase"):
            stop_button.click(timeout=5000)

        with allure.step("Step 4 — No further text streams: the cancelled turn leaves the timeline and stays gone"):
            expect(chat.messages_container).to_have_count(initial_count, timeout=RESTORE_TIMEOUT)

        with allure.step("Step 5 — Stop control disappears and the default Send bar returns"):
            expect(stop_button).to_have_count(0, timeout=RESTORE_TIMEOUT)
            expect(chat.send_button).to_be_visible(timeout=RESTORE_TIMEOUT)

        with allure.step("Step 6 — Input is active and editable again"):
            expect(chat.message_input).to_be_editable(timeout=RESTORE_TIMEOUT)

        with allure.step("Step 7 — Input holds the exact original message text"):
            expect(chat.message_input).to_have_value(_PROMPT, timeout=RESTORE_TIMEOUT)
            # Final no-stream check, no sleep: Steps 5-7 have just elapsed, so a stray
            # stream would have repopulated the timeline by now.
            expect(chat.messages_container).to_have_count(initial_count)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2183_chat-after-stopping-generation-new-message-can-be-sent-normally.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.tms("ELITEA-2183")
    @allure.title("After stopping a generation a new message can be sent and answered normally")
    @allure.severity(allure.severity_level.NORMAL)
    def test_send_new_message_after_stop_works(self, page, conversation_id, midturn_injection_enabled):
        """ELITEA-2183 — extends ELITEA-2182: the post-stop send works, no trace of the stopped exchange.

        AFS: test-specs/chat-interface/lextend_stop-generation-then-send-new-message-works_ELITEA-2183.md
        """
        chat = ChatPage(page)
        stop_button = chat.STOP_BUTTON.within(chat.chat_inject_button)

        with allure.step("Step 1 — Send 'generate a poem'; Stop control is visible while generating"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            initial_count = chat.get_message_count()
            chat.send_message(_PROMPT)
            expect(stop_button).to_be_visible(timeout=STOP_VISIBLE_TIMEOUT)

        with allure.step("Step 2 — Click Stop; input is restored with the exact original text"):
            stop_button.click(timeout=5000)
            expect(stop_button).to_have_count(0, timeout=RESTORE_TIMEOUT)
            expect(chat.message_input).to_have_value(_PROMPT, timeout=RESTORE_TIMEOUT)

        with allure.step("Step 3 — No user or assistant bubble remains for the stopped exchange"):
            expect(chat.messages_container).to_have_count(initial_count, timeout=RESTORE_TIMEOUT)

        with allure.step("Step 4 — Clear the input and type 'hello'; Send button appears"):
            chat.message_input.fill("")
            chat.message_input.fill(_SECOND_PROMPT)
            expect(chat.send_button).to_be_visible(timeout=RESTORE_TIMEOUT)

        with allure.step("Step 5 — Click Send; the new message is sent and the LLM answers"):
            count_before_send = chat.get_message_count()
            chat.send_message(_SECOND_PROMPT)
            expect(chat.messages_container.filter(has_text=_SECOND_PROMPT)).to_be_visible(
                timeout=STOP_VISIBLE_TIMEOUT
            )
            chat.wait_for_ai_response(initial_count=count_before_send)

        with allure.step("Step 6 — No error shown; history holds only the new exchange, no stopped bubble"):
            expect(chat.get_toast_alert("error")).to_have_count(0)
            expect(chat.messages_container).to_have_count(count_before_send + 2)
            expect(chat.messages_container.filter(has_text=_PROMPT)).to_have_count(0)
