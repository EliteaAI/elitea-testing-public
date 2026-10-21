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

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2185_chat-clicking-regenerate-generates-new-response.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.tms("ELITEA-2185")
    @allure.title("Regenerate replaces the last response in place and keeps the user input unchanged")
    @allure.severity(allure.severity_level.NORMAL)
    def test_regenerate_creates_new_response_same_user_input(self, page, conversation_id):
        chat = ChatPage(page)

        def last_ai_item():
            """Enumerate the timeline and return the last AI-authored item (no positional pick)."""
            items = chat.messages_container
            ai = [items.nth(i) for i in range(items.count()) if chat._is_ai_message(items.nth(i))]
            assert ai, "no AI item in the timeline"
            return ai[-1]

        def user_items_text():
            items = chat.messages_container
            return [items.nth(i).inner_text() for i in range(items.count()) if not chat._is_ai_message(items.nth(i))]

        with allure.step("Precondition — fresh conversation with one user message and one LLM response"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            count_before = chat.get_message_count()
            chat.send_message(_PROMPT, use_enter=True)
            chat.wait_for_ai_response(initial_count=count_before)
            expect(chat.messages_container).to_have_count(count_before + 2, timeout=UI_TIMEOUT)
            ai_item = last_ai_item()
            ai_text_before = ai_item.inner_text()
            assert ai_text_before.strip(), "initial AI response is empty"
            user_texts_before = user_items_text()
            assert len(user_texts_before) == count_before + 1

        with allure.step("Step 1 — Scroll to the last LLM response and hover: Regenerate is visible"):
            ai_item.scroll_into_view_if_needed()
            ai_item.hover()
            regenerate = ChatPage.regenerate_action_button.resolve(ai_item)
            expect(regenerate).to_have_count(1, timeout=UI_TIMEOUT)
            expect(regenerate).to_be_visible(timeout=UI_TIMEOUT)

        with allure.step("Step 2 — Click Regenerate: old response replaced in place, new generation begins"):
            regenerate.click()
            ai_item = last_ai_item()
            # Replacement: the completed-response actions are gone while the new one generates.
            expect(ChatPage.copy_action_button.resolve(ai_item)).to_have_count(0, timeout=UI_TIMEOUT)
            expect(ChatPage.regenerate_action_button.resolve(ai_item)).to_have_count(0, timeout=UI_TIMEOUT)
            expect(chat.messages_container).to_have_count(count_before + 2, timeout=UI_TIMEOUT)

        with allure.step("Step 3 — In-progress state: loading/thought accordion with model label, Stop shown"):
            # Discriminating: Stop control present and Regenerate/Copy absent => genuinely generating.
            expect(chat.chat_inject_button).to_have_count(1, timeout=UI_TIMEOUT)
            expect(ChatPage.copy_action_button.resolve(last_ai_item())).to_have_count(0)
            ai_item = last_ai_item()
            placeholder = ChatPage.answer_loading_placeholder.resolve(ai_item)
            accordion = ChatPage.answer_thought_accordion.resolve(ai_item)
            expect(placeholder.or_(accordion).first).to_be_visible(timeout=UI_TIMEOUT)
            model_chip = ChatPage.answer_model_chip.resolve(ai_item)
            expect(model_chip.first).to_be_visible(timeout=UI_TIMEOUT)
            assert model_chip.first.inner_text().strip(), "model label on the regenerating response is empty"

        with allure.step("Step 4 — The user's previous input is unchanged"):
            assert user_items_text() == user_texts_before
            expect(chat.messages_container).to_have_count(count_before + 2)

        with allure.step("Step 5 — The new response completes with content and the model label"):
            ai_item = last_ai_item()
            copy_btn = ChatPage.copy_action_button.resolve(ai_item)
            ai_item.hover()
            expect(copy_btn).to_be_visible(timeout=60_000)
            ai_item = last_ai_item()
            assert ai_item.inner_text().strip(), "regenerated response body is empty"
            model_chip = ChatPage.answer_model_chip.resolve(ai_item)
            expect(model_chip.first).to_be_visible(timeout=UI_TIMEOUT)
            assert model_chip.first.inner_text().strip(), "model label missing on the completed response"
            expect(chat.messages_container).to_have_count(count_before + 2)

        with allure.step("Step 6 — Stop is gone; Regenerate and the action icons reappear"):
            expect(chat.chat_inject_button).to_have_count(0, timeout=UI_TIMEOUT)
            ai_item = last_ai_item()
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
