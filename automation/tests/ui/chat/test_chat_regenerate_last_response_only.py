"""UI Test for ELITEA-2184 — Regenerate (and Delete) are offered only on the LAST LLM response.

Two exchanges are sent so "earlier" and "last" both exist. The last AI item carries
read-out, copy, regenerate and delete; the earlier AI item carries no Regenerate and no
Delete (they are not in the DOM at all), and the whole timeline holds exactly one
Regenerate button, inside the last AI item.

AFS: test-specs/chat-interface/l2_regenerate-only-on-last-llm-response_ELITEA-2184.md

Markers:
    - ui: requires browser
    - chat: chat-related test
    - p2: AFS Priority l2 (TMS ``high``)
"""

import allure
import pytest
from playwright.sync_api import expect

from config import settings
from pages.chat_page import ChatPage

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p2, pytest.mark.regression]

_PROMPTS = ("Reply with the single word: one", "Reply with the single word: two")
_PROMPTS_THREE = (*_PROMPTS, "Reply with the single word: three")
UI_TIMEOUT = 15_000


@allure.epic("Chat")
@allure.feature("Message actions")
class TestChatRegenerateLastResponseOnly:
    """ELITEA-2184 — Regenerate is visible only on the last LLM response."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2184_chat-regenerate-button-visible-on-last-llm-response.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.tms("ELITEA-2184")
    @allure.title("Regenerate and Delete appear only on the last LLM response")
    @allure.severity(allure.severity_level.NORMAL)
    def test_regenerate_only_on_last_llm_response(self, page, conversation_id):
        chat = ChatPage(page)

        with allure.step("Step 1 — Open a fresh conversation and get two LLM responses"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            for prompt in _PROMPTS:
                count_before = chat.get_message_count()
                chat.send_message(prompt)
                chat.wait_for_ai_response(initial_count=count_before)
            expect(chat.messages_container).to_have_count(4, timeout=UI_TIMEOUT)
            items = chat.messages_container
            ai_items = [items.nth(i) for i in range(items.count()) if chat._is_ai_message(items.nth(i))]
            assert len(ai_items) == 2, f"expected 2 AI responses, found {len(ai_items)}"
            earlier_item, last_item = ai_items
            last_item.scroll_into_view_if_needed()
            expect(last_item).to_be_visible(timeout=UI_TIMEOUT)

        with allure.step("Step 2 — Last response shows speaker, copy, regenerate and delete"):
            last_item.scroll_into_view_if_needed()
            last_item.hover()
            for action in (
                ChatPage.read_out_button,
                ChatPage.copy_action_button,
                ChatPage.regenerate_action_button,
                ChatPage.delete_action_button,
            ):
                icon = action.resolve(last_item)
                expect(icon).to_have_count(1, timeout=UI_TIMEOUT)
                expect(icon).to_be_visible(timeout=UI_TIMEOUT)

        with allure.step("Step 3 — Earlier response has no Regenerate (and no Delete)"):
            page.mouse.move(0, 0)
            earlier_item.scroll_into_view_if_needed()
            earlier_item.hover()
            expect(earlier_item).to_be_visible(timeout=UI_TIMEOUT)
            expect(earlier_item.filter(has=chat.regenerate_action_button)).to_have_count(0)
            expect(earlier_item.filter(has=chat.delete_action_button)).to_have_count(0)

        with allure.step("Step 4 — Only one Regenerate on the page, and it is inside the last response"):
            expect(chat.regenerate_action_button).to_have_count(1)
            expect(last_item.filter(has=chat.regenerate_action_button)).to_have_count(1)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2187_chat-regenerate-is-only-available-on-the-last-response.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.tms("ELITEA-2187")
    @allure.title("Regenerate is offered only on the last of three LLM responses and still works")
    @allure.severity(allure.severity_level.NORMAL)
    def test_regenerate_only_on_last_of_three_responses(
        self, page, conversation_id, midturn_injection_enabled
    ):
        """ELITEA-2187 — extends ELITEA-2184: three exchanges, every earlier item, click on last."""
        chat = ChatPage(page)

        def ai_items_now():
            items = chat.messages_container
            return [items.nth(i) for i in range(items.count()) if chat._is_ai_message(items.nth(i))]

        with allure.step("Step 1 — Open a fresh conversation and get three LLM responses"):
            # navigate_to_chat(conversation_id=) times out on DEV (SPA redirect); direct goto works.
            # settings.app_base_url already carries the /app prefix - do not add it again.
            page.goto(f"{settings.app_base_url}/chat/{conversation_id}")
            assert "/app/app/" not in page.url, f"doubled app prefix in URL: {page.url}"
            expect(chat.message_input).to_be_visible(timeout=30_000)
            for prompt in _PROMPTS_THREE:
                count_before = chat.get_message_count()
                chat.send_message(prompt, use_enter=True)
                chat.wait_for_ai_response(initial_count=count_before)
            expect(chat.messages_container).to_have_count(6, timeout=UI_TIMEOUT)
            ai_items = ai_items_now()
            assert len(ai_items) == 3, f"expected 3 AI responses, found {len(ai_items)}"
            earlier_items, last_item = ai_items[:-1], ai_items[-1]

        with allure.step("Step 2 — Hover every earlier response: no Regenerate (and no Delete)"):
            for earlier in earlier_items:
                page.mouse.move(0, 0)
                earlier.scroll_into_view_if_needed()
                earlier.hover()
                expect(earlier).to_be_visible(timeout=UI_TIMEOUT)
                # Positive control: the hover revealed this item's action bar (AFS Gap assertion 1),
                # so the absence checks below cannot pass merely because nothing rendered.
                for shown in (ChatPage.copy_action_button, ChatPage.read_out_button):
                    expect(shown.resolve(earlier)).to_have_count(1, timeout=UI_TIMEOUT)
                expect(ChatPage.regenerate_action_button.resolve(earlier)).to_have_count(0)
                expect(ChatPage.delete_action_button.resolve(earlier)).to_have_count(0)

        with allure.step("Step 3 — Hover the last response: Regenerate and its icon are visible"):
            page.mouse.move(0, 0)
            last_item.scroll_into_view_if_needed()
            last_item.hover()
            regenerate = ChatPage.regenerate_action_button.resolve(last_item)
            expect(regenerate).to_have_count(1, timeout=UI_TIMEOUT)
            expect(regenerate).to_be_visible(timeout=UI_TIMEOUT)

        with allure.step("Step 4 — Click Regenerate: a new generation runs and completes in place"):
            regenerate.click()
            expect(chat.chat_inject_button).to_have_count(1, timeout=UI_TIMEOUT)
            expect(chat.chat_inject_button).to_have_count(0, timeout=60_000)
            expect(chat.messages_container).to_have_count(6, timeout=UI_TIMEOUT)

        with allure.step("Step 5 — Regenerate is still exclusive to the (new) last response"):
            ai_items = ai_items_now()
            assert len(ai_items) == 3, f"expected 3 AI responses after regenerate, found {len(ai_items)}"
            expect(chat.regenerate_action_button).to_have_count(1, timeout=UI_TIMEOUT)
            expect(ai_items[-1].filter(has=chat.regenerate_action_button)).to_have_count(1)
            for earlier in ai_items[:-1]:
                expect(earlier.filter(has=chat.regenerate_action_button)).to_have_count(0)
