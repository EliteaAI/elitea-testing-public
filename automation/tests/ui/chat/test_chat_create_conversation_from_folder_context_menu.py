"""UI Test for ELITEA-2757 — Chat: create a new conversation from the folder context menu.

Spec: test-specs/chat-interface/l1_new-conversation-from-folder-context-menu_ELITEA-2757.md

Live-contract notes (AFS clarifications, not defects):
- The folder auto-expands when the FIRST MESSAGE is sent, not when "New chat" is clicked.
- Folders have no right-click menu; only the three-dot menu exists (not asserted).
- The default model is compared against the landing value, not a hard-coded name.
- The transient "Naming" label lasts ~0.4-0.8s, so it is not a hard gate; the end state
  (name set, not "Naming") is asserted.
"""

import logging
import re
import time

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
NAMING_TIMEOUT = 30_000
TEST_MESSAGE = "Explain the concept of machine learning"
EXPECTED_MENU_LABELS = ["New chat", "Rename", "Pin on top", "Delete"]


class TestChatCreateConversationFromFolderMenu:
    """ELITEA-2757: Chat – Create new conversation from folder context menu (l1, critical)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2757_chat-new-chat-option-available-in-folder-context-menu.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.tms("ELITEA-2757")
    @pytest.mark.p0
    def test_create_conversation_from_folder_context_menu(self, page, conversation_api):
        chat = ChatPage(page)
        folder_id = None
        conv_id = None

        try:
            with allure.step("Setup — create an empty folder via API; open Chats"):
                folder_id = chat.create_folder_via_api(f"autotest_2757_{int(time.time())}")
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.dismiss_platform_banner_dialog()
                expect(chat.get_folder_item(folder_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                landing_model = (chat.model_selector_name.first.text_content() or "").strip()
                assert landing_model, "Landing page should show a default model name"

            with allure.step("Step 1 — Open the folder three-dot menu; verify its items"):
                chat.open_folder_menu(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                labels = chat.get_folder_menu_labels()
                assert labels == EXPECTED_MENU_LABELS, (
                    f"Folder menu items should be {EXPECTED_MENU_LABELS}, got {labels}"
                )

            with allure.step("Step 2 — Click 'New chat'; a blank conversation opens"):
                chat.click_folder_menu_new_chat()
                assert re.search(r"/chat/?(\?.*)?$", page.url), (
                    f"A blank chat has no conversation id in the URL, got {page.url}"
                )
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.message_input).to_have_value("")
                expect(chat.get_folder_conversation_items(folder_id)).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 3 — Default LLM is pre-selected (same as the landing default)"):
                expect(chat.model_selector_name.first).to_have_text(landing_model, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 4 — Send the message; conversation is created inside the folder"):
                chat.send_message(TEST_MESSAGE, use_enter=True)
                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=UI_ELEMENT_TIMEOUT)
                conv_id = re.search(r"/chat/(\d+)", page.url).group(1)
                expect(chat.get_folder_item(folder_id)).to_have_attribute(
                    "data-expanded", "true", timeout=UI_ELEMENT_TIMEOUT
                )
                assert chat.is_conversation_in_folder(folder_id, conv_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Conversation {conv_id} should render inside folder {folder_id}"
                )

            with allure.step("Step 5 — Auto-naming completes: non-empty title, not 'Naming'"):
                item = chat.get_conversation_item(conv_id)
                expect(item).not_to_have_text(re.compile(r"Naming"), timeout=NAMING_TIMEOUT)
                auto_name = (item.text_content() or "").strip()
                assert auto_name, "Auto-generated conversation name should be non-empty"

            with allure.step("Step 6 — Conversation is in the folder only, not in a date group"):
                expect(chat.get_folder_conversation_items(folder_id, conv_id)).to_have_count(1)
                expect(chat.get_conversation_item(conv_id)).to_have_count(1)
                for group in ("today", "this_week", "older"):
                    assert not chat.is_conversation_in_group(conv_id, group, timeout=1000), (
                        f"Conversation {conv_id} must not appear in the '{group}' date group"
                    )

            with allure.step("Step 7 — Collapse and re-expand the folder; conversation still listed"):
                folder = chat.get_folder_item(folder_id)
                chat.toggle_folder(folder_id)
                expect(folder).to_have_attribute("data-expanded", "false", timeout=UI_ELEMENT_TIMEOUT)
                chat.toggle_folder(folder_id)
                expect(folder).to_have_attribute("data-expanded", "true", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_conversation_in_folder(folder_id, conv_id, timeout=UI_ELEMENT_TIMEOUT), (
                    "Conversation should remain in the folder after collapse/re-expand"
                )

            with allure.step("Step 8 — Reload; conversation persists in the folder with its name"):
                page.reload()
                chat.wait_for_page_load()
                chat.dismiss_platform_banner_dialog()
                expect(chat.get_folder_item(folder_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                if not chat.is_folder_expanded(folder_id):
                    chat.expand_folder(folder_id)
                assert chat.is_conversation_in_folder(folder_id, conv_id, timeout=UI_ELEMENT_TIMEOUT), (
                    "Conversation should persist inside the folder after reload"
                )
                assert chat.get_folder_conversation_items(folder_id, conv_id).count() == 1
                expect(chat.get_conversation_item(conv_id)).to_have_count(1)
                expect(chat.get_conversation_item(conv_id)).to_have_text(auto_name, timeout=UI_ELEMENT_TIMEOUT)
        finally:
            if conv_id is not None:
                try:
                    conversation_api.delete_conversation(int(conv_id))
                except Exception as exc:  # best-effort cleanup
                    logger.warning("Cleanup: conversation %s delete failed: %s", conv_id, exc)
            if folder_id is not None:
                try:
                    chat.delete_folder_via_api(folder_id)
                except Exception as exc:
                    logger.warning("Cleanup: folder %s delete failed: %s", folder_id, exc)
