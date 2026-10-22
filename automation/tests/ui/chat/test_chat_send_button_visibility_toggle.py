"""UI Test for ELITEA-2466 — empty input shows no Send button; typing shows it; send clears the field.

AFS: test-specs/chat-interface/l1_chat-send-button-visibility-toggle-and-clear-on-send_ELITEA-2466.md

Case-text drift (see AFS): "waveform icon" is the ``enter speaking mode`` button;
"Send NOT visible" means ``chat-send-button`` is absent from the DOM; the teal focus
border is a visual judgment and is not asserted (focus only).
"""

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p1, pytest.mark.regression]

_MESSAGE = "Hello"
_TIMEOUT = 15_000
_RESPONSE_TIMEOUT = 90_000


@allure.epic("Chat")
@allure.feature("Message composer")
class TestChatSendButtonVisibilityToggle:
    """ELITEA-2466 — Send/speaking-mode swap and input clearing on send."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2466_chat-message-input-empty-shows-no-send-button-typing-shows-s.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.tms("ELITEA-2466")
    @allure.title("Empty input shows no Send button; typing shows it; sending clears the field")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_send_button_visibility_toggle_and_clear_on_send(self, page, conversation_id):
        chat = ChatPage(page)

        with allure.step("Step 1 — Open a conversation in Chat; the message input is visible"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            expect(chat.message_input).to_be_visible(timeout=_TIMEOUT)
            initial_count = chat.get_message_count()

        with allure.step("Step 2 — Input is empty and the Send button is not present"):
            expect(chat.message_input).to_have_value("")
            expect(chat.send_button).to_have_count(0)
            expect(chat.speaking_mode_button).to_be_visible()

        with allure.step("Step 3 — Bottom bar shows plus, model name, gear, microphone and speaking-mode controls"):
            expect(chat.plus_menu_button).to_be_visible()
            expect(chat.model_selector_name).to_be_visible()
            expect(chat.model_settings_button).to_be_visible()
            expect(chat.voice_input_button).to_be_visible()
            expect(chat.speaking_mode_button).to_be_visible()

        with allure.step("Step 4 — Clicking the input focuses it"):
            chat.message_input.click()
            expect(chat.message_input).to_be_focused()

        with allure.step("Step 5 — Typing a character replaces the speaking-mode button with an enabled Send"):
            chat.message_input.press_sequentially("h")
            expect(chat.send_button).to_have_count(1)
            expect(chat.send_button).to_be_enabled()
            expect(chat.speaking_mode_button).to_have_count(0)

        with allure.step("Step 6 — Deleting the character restores the speaking-mode button and hides Send"):
            chat.message_input.press("Backspace")
            expect(chat.message_input).to_have_value("")
            expect(chat.send_button).to_have_count(0)
            expect(chat.speaking_mode_button).to_be_visible()

        with allure.step("Step 7 — Type 'Hello' and click Send"):
            chat.send_message(_MESSAGE)

        with allure.step("Step 8 — The message appears in the history with the sender's name and avatar"):
            user_item = chat.messages_container.filter(has_text=_MESSAGE).first
            expect(user_item).to_be_visible(timeout=_TIMEOUT)
            expect(chat.messages_container).to_have_count(initial_count + 2, timeout=_RESPONSE_TIMEOUT)
            user_messages = [
                chat.messages_container.nth(i)
                for i in range(chat.messages_container.count())
                if not chat._is_ai_message(chat.messages_container.nth(i))
            ]
            assert user_messages, "No user-authored message item found after sending"
            sent = user_messages[-1]
            expect(sent).to_contain_text(_MESSAGE)
            header_text = sent.inner_text().replace(_MESSAGE, "").strip()
            assert header_text, "Sent message item shows no sender name"
            expect(chat.USER_MESSAGE_AVATAR.within(sent)).to_be_visible()

        with allure.step("Step 9 — The input is cleared and the Send button is gone"):
            expect(chat.message_input).to_have_value("")
            expect(chat.send_button).to_have_count(0)

        with allure.step("Step 10 — An AI response appears and the speaking-mode button returns"):
            expect(chat.AI_MESSAGE_LOGO.within(chat.messages_container.last)).to_be_visible(timeout=_RESPONSE_TIMEOUT)
            expect(chat.speaking_mode_button).to_be_visible(timeout=_RESPONSE_TIMEOUT)
