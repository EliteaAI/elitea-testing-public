"""UI Tests for Chat search filters and Modules panel toggles (ELITEA-2162).

Verifies the search icon opens a search field, partial and full-name queries
filter the conversation list, clicking a result opens the conversation, and
the Modules panel (+ -> Modules, hover) shows 7 toggleable modules that
persist via a confirmation toast — and that only an outside click (not
Escape) closes the panel.

Markers:
    - ui: requires browser
    - p1: high priority (case priority "high" -> p1 pytest marker convention)
    - chat: chat-related tests
    - regression: regression suite

Usage:
    cd automation
    pytest tests/ui/chat/test_chat_search_and_modules_panel.py -v
"""

import logging
from uuid import uuid4

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 10000
NETWORK_RESPONSE_TIMEOUT = 10000


class TestChatSearchAndModulesPanel:
    """ELITEA-2162: Chat search filters conversations, opens result, Modules panel toggles work."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2162_chat-search-icon-opens-search-input-and-returns-partial-results-then-access-modules.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_search_filters_and_modules_panel_toggles(self, page, conversation_api):
        """Search icon filters conversations by partial/exact query, opens a
        result, and the Modules panel's 7 toggles persist with a
        confirmation toast; closing works via outside click only (not
        Escape)."""
        conv_name = f"AutomationUnique{uuid4().hex[:8]}"

        with allure.step("Setup — create a conversation with a unique name via API"):
            conv = conversation_api.create_conversation(conv_name)
            conv_id = str(conv["id"])
            logger.info("Created conversation %s (%s)", conv_id, conv_name)

        try:
            with allure.step("Step 1 — Navigate to chat; verify search icon visible"):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                expect(chat.search_conversations_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 2 — Click search icon; verify input focused + clear icon visible"):
                chat.open_search_conversations_button(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.search_conversations_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.search_conversations_input).to_be_focused(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.search_conversations_clear_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 3 — Type partial query 'un'; verify the generated conversation appears"):
                chat.type_conversation_search_query("un", timeout=NETWORK_RESPONSE_TIMEOUT)
                expect(chat.get_conversation_item(conv_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 4 — Type the exact full-name query; verify exactly one matching row"):
                chat.type_conversation_search_query(conv_name, timeout=NETWORK_RESPONSE_TIMEOUT)
                expect(chat.get_conversation_item_rows()).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_conversation_item(conv_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 5 — Click the matching conversation; verify it opens"):
                chat.click_conversation_item(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_conversation_url(conv_id, timeout=NAVIGATION_TIMEOUT)
                expect(chat.new_conversation_greeting).not_to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.search_conversations_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 6 — Open Modules panel via + -> Modules (hover); verify 7 toggles in order"):
                chat.open_internal_tools_menu(timeout=UI_ELEMENT_TIMEOUT)
                chat.verify_module_toggle_order(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 7 — Toggle Image creation on then off; verify state + toast each time"):
                initial_checked = chat.is_module_toggle_checked("image_generation")

                chat.click_module_toggle("image_generation", timeout=NETWORK_RESPONSE_TIMEOUT)
                assert chat.is_module_toggle_checked("image_generation") != initial_checked, (
                    "Image creation toggle state should flip after the first click"
                )
                expect(chat.toast_message).to_have_text(
                    "Modules configuration updated", timeout=UI_ELEMENT_TIMEOUT
                )

                chat.click_module_toggle("image_generation", timeout=NETWORK_RESPONSE_TIMEOUT)
                assert chat.is_module_toggle_checked("image_generation") == initial_checked, (
                    "Image creation toggle state should flip back after the second click"
                )
                expect(chat.toast_message).to_have_text(
                    "Modules configuration updated", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 8 — Toggle Data Analysis on; verify state + toast, then restore"):
                initial_checked_da = chat.is_module_toggle_checked("data_analysis")

                chat.click_module_toggle("data_analysis", timeout=NETWORK_RESPONSE_TIMEOUT)
                assert chat.is_module_toggle_checked("data_analysis") != initial_checked_da, (
                    "Data Analysis toggle state should flip after click"
                )
                expect(chat.toast_message).to_have_text(
                    "Modules configuration updated", timeout=UI_ELEMENT_TIMEOUT
                )

                # Restore original state so this run doesn't leak config forward.
                chat.click_module_toggle("data_analysis", timeout=NETWORK_RESPONSE_TIMEOUT)
                assert chat.is_module_toggle_checked("data_analysis") == initial_checked_da, (
                    "Data Analysis toggle should be restored to its original state"
                )

            with allure.step("Step 9 — Escape does NOT close the panel; an outside click does"):
                page.keyboard.press("Escape")
                expect(chat.get_module_toggle_switches()).to_have_count(
                    len(chat.MODULE_TOGGLE_ORDER), timeout=UI_ELEMENT_TIMEOUT
                )

                chat.close_modules_panel(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_module_toggle_switches()).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

        finally:
            with allure.step("Cleanup — delete the generated conversation"):
                try:
                    conversation_api.delete_conversation(int(conv_id))
                    logger.info("Deleted conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Cleanup failed for conversation %s: %s", conv_id, exc)
