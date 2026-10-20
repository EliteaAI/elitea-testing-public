"""UI Test for ELITEA-2185 — Regenerate replaces the last LLM response, reusing the same user input.

One exchange is sent; Regenerate is clicked on the last AI item. The response is replaced
in place (message count stays 2), an in-progress state shows (loading placeholder or thought
accordion), the user message is untouched, the new response completes, and the action icons
return.

AFS: test-specs/chat-interface/l2_regenerate-creates-new-response-same-user-input_ELITEA-2185.md

Markers:
    - ui: requires browser
    - chat: chat-related test
    - p2: AFS Priority l2 (TMS ``high``)
"""

import allure
import pytest
from playwright.sync_api import expect

from pages.chat_page import ChatPage

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p2, pytest.mark.regression]

# Longer prompt widens the in-progress window (the short one regenerates in ~2s).
_PROMPT = "Write a 120-word paragraph about rivers."
UI_TIMEOUT = 15_000


@allure.epic("Chat")
@allure.feature("Message actions")
class TestChatRegenerateNewResponse:
    """ELITEA-2185 — Regenerate produces a new response from the previous user input."""

    @pytest.mark.tms("ELITEA-2185")
    @allure.title("Regenerate replaces the last response in place and keeps the user input unchanged")
    @allure.severity(allure.severity_level.NORMAL)
    def test_regenerate_creates_new_response_same_user_input(self, page, conversation_id):
        chat = ChatPage(page)

        with allure.step("Precondition — fresh conversation with one user message and one LLM response"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            count_before = chat.get_message_count()
            chat.send_message(_PROMPT, use_enter=True)
            chat.wait_for_ai_response(initial_count=count_before)
            expect(chat.messages_container).to_have_count(count_before + 2, timeout=UI_TIMEOUT)
            items = chat.messages_container
            ai_item = items.nth(count_before + 1)
            user_item = items.nth(count_before)
            assert chat._is_ai_message(ai_item), "last timeline item is not the AI response"

        with allure.step("Step 1 — Scroll to the last LLM response and hover: Regenerate is visible"):
            ai_item.scroll_into_view_if_needed()
            ai_item.hover()
            regenerate = ChatPage.regenerate_action_button.resolve(ai_item)
            expect(regenerate).to_have_count(1, timeout=UI_TIMEOUT)
            expect(regenerate).to_be_visible(timeout=UI_TIMEOUT)

        with allure.step("Step 2 — Click Regenerate: response replaced in place, new generation begins"):
            user_text_before = user_item.inner_text()
            regenerate.click()
            expect(chat.messages_container).to_have_count(count_before + 2, timeout=UI_TIMEOUT)

        with allure.step("Step 3 — In-progress state is shown on the AI item"):
            placeholder = ChatPage.answer_loading_placeholder.resolve(ai_item)
            accordion = ChatPage.answer_thought_accordion.resolve(ai_item)
            expect(placeholder.or_(accordion).first).to_be_visible(timeout=UI_TIMEOUT)

        with allure.step("Step 4 — The user's previous input is unchanged"):
            assert user_item.inner_text() == user_text_before
            expect(chat.messages_container).to_have_count(count_before + 2)

        with allure.step("Step 5 — The new response completes with content"):
            copy_btn = ChatPage.copy_action_button.resolve(ai_item)
            ai_item.hover()
            expect(copy_btn).to_be_visible(timeout=60_000)
            assert ai_item.inner_text().strip(), "regenerated response body is empty"
            expect(chat.messages_container).to_have_count(count_before + 2)

        with allure.step("Step 6 — Regenerate and the action icons reappear"):
            ai_item.hover()
            for action in (
                ChatPage.regenerate_action_button,
                ChatPage.copy_action_button,
                ChatPage.read_out_button,
                ChatPage.delete_action_button,
            ):
                icon = action.resolve(ai_item)
                expect(icon).to_have_count(1, timeout=UI_TIMEOUT)
                expect(icon).to_be_visible(timeout=UI_TIMEOUT)
