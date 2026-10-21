"""UI Test for ELITEA-3779 — Chat: Export option appears in the conversation context menu.

Spec: test-specs/chat-interface/l1_export-option-in-conversation-context-menu_ELITEA-3779.md

Case-text drift (declared in the AFS): the menu opens from the hover 3-dot button
(right-click opens nothing), "Duplicate" does not exist on DEV, and keyboard
navigation to the items is unsupported (case steps 13-14 are conditional, not automated).
"""

import logging
import time

import allure
import pytest
from config import settings
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
EXPECTED_MENU_ORDER = ["rename", "move-to", "playback", "export", "share-external", "pin", "delete"]


class TestChatExportMenuOption:
    """ELITEA-3779: Export option in the conversation context menu (l1, high)."""

    @pytest.mark.tms("ELITEA-3779")
    @pytest.mark.p1
    def test_export_option_in_conversation_context_menu(self, page, conversation_api):
        chat = ChatPage(page)
        conv_id = None
        chat_name = f"autotest_3779_{int(time.time())}"
        try:
            with allure.step("Step 1-2 — Open Chats; the user's conversation is visible in the list"):
                conv_id = conversation_api.create_conversation(chat_name)["id"]
                # DEV serves the app under /app (AFS precondition: direct goto, not navigate_to_chat).
                page.goto(f"{settings.app_base_url}/app/chat")
                chat.dismiss_platform_banner_dialog()
                item = chat.get_conversation_item(conv_id)
                expect(item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 3 — Hover the conversation: hover state reveals the 3-dot menu button"):
                chat.hover_conversation_item(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_conversation_menu_button(conv_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 4-5 — Open the context menu (3-dot button): multiple options are shown"):
                chat.open_conversation_context_menu(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                export_item = chat.get_conversation_menu_item("export")
                expect(export_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_open_conversation_menu_items()).to_have_count(
                    len(EXPECTED_MENU_ORDER), timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 6 — Export option is visible"):
                expect(export_item).to_be_visible()

            with allure.step("Step 7-8 — Menu order is Rename, Move to, Playback, Export, Share externally, Pin on top, Delete"):
                keys = chat.get_open_conversation_menu_item_keys()
                assert keys == EXPECTED_MENU_ORDER, f"Unexpected context-menu order: {keys}"
                assert keys.index("export") == 3
                assert keys[keys.index("export") - 1] == "playback"
                assert keys[keys.index("export") + 1] == "share-external"

            with allure.step("Step 9 — Export is enabled (not greyed out)"):
                expect(export_item).to_be_enabled()
                expect(export_item).not_to_have_attribute("aria-disabled", "true")

            with allure.step("Step 10 — Export label reads exactly 'Export'"):
                expect(export_item).to_have_text("Export")

            with allure.step("Step 11 — Export item carries an icon"):
                expect(chat.conversation_menu_item_icon.within(export_item)).to_have_count(1)

            with allure.step("Step 12 — Clicking elsewhere closes the menu without action"):
                page.mouse.click(1000, 500)
                expect(chat.get_open_conversation_menu_items()).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.export_chat_modal).to_have_count(0)
                expect(chat.get_conversation_item(conv_id)).to_be_visible()
        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_id, exc)
