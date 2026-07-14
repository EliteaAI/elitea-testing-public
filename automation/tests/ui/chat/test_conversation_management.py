"""UI Tests for Elitea Conversation Management.

Tests conversation creation, listing, navigation, rename, delete, and search.

Each test that interacts with conversations uses the ``conversation_id``
fixture so it gets a fresh, isolated conversation that is cleaned up
automatically after the test.

Spec: ui-tests/chat-conversations/test_conversation_management.md
TC-CONV-001 through TC-CONV-007 (P0/P1 only; P2 folders/sharing skipped).

Markers:
    - ui: requires browser
    - p0: critical priority tests
    - p1: high priority tests

Usage:
    cd automation
    pytest test_conversation_management.py -v
    pytest test_conversation_management.py -v -m p0
"""

import re
import logging

import pytest
from playwright.sync_api import expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from pages.chat_page import ChatPage
from components.mui import Dialog
from conftest import attach_screenshot
import allure

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
AI_RESPONSE_TIMEOUT = 30000
UI_ELEMENT_TIMEOUT = 5000
NAVIGATION_TIMEOUT = 10000


# ---------------------------------------------------------------------------
# Shared assertion helpers
# ---------------------------------------------------------------------------

def _verify_conversation_page_loaded(chat_page, conversation_id, page):
    """Verify conversation page loaded correctly with valid state.

    Common verification shared by multiple tests to ensure the conversation
    page is in a valid, ready-to-interact state after navigation.

    Checks:
    - URL contains the conversation ID
    - Message input is visible
    - Message input is editable (not disabled)

    Args:
        chat_page: ChatPage instance
        conversation_id: Expected conversation ID (str or int)
        page: Playwright Page instance

    Raises:
        AssertionError: If any check fails
    """
    conv_id_str = str(conversation_id)

    assert f"/chat/{conv_id_str}" in page.url, (
        f"URL should contain conversation ID {conv_id_str}, got: {page.url}"
    )

    assert chat_page.message_input.is_visible(), (
        "Message input should be visible on loaded conversation page"
    )

    assert chat_page.message_input.is_editable(), (
        "Message input should be editable (not disabled) on loaded conversation page"
    )


def _extract_conversation_id(page, conversation_api, test_msg: str) -> str | None:
    """Extract conversation ID from URL or find via API.

    After creating a conversation, the URL may or may not update to include
    the conversation ID. This helper tries URL first, then falls back to API.

    Args:
        page: Playwright page instance
        conversation_api: API client for conversation operations
        test_msg: Message prefix used to identify the conversation in API

    Returns:
        Conversation ID as string, or None if not found
    """
    # Try URL first
    match = re.search(r"/chat/(\d+)", page.url)
    if match:
        conv_id = match.group(1)
        logger.info(f"Conversation ID from URL: {conv_id}")
        return conv_id

    # Fallback: find by message prefix in API
    convo_list = conversation_api.list_conversations()
    for conv in convo_list.get("rows", []):
        name = conv.get("name", "")
        if test_msg in name or name.startswith("at_"):
            conv_id = str(conv["id"])
            logger.info(f"Conversation ID from API: {conv_id}")
            return conv_id

    logger.warning("Could not extract conversation ID from URL or API")
    return None


class TestCreateConversation:
    """TC-CONV-001 / TC-CONV-002: Creating new conversations."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/conversations/ELITEA-0571_conversation-creation-and-list.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    def test_create_conversation_via_ui_button(self, page, conversation_api):
        """TC-CONV-001 UI: Create a conversation by clicking the UI button."""
        conv_id = None

        try:
            with allure.step("Step 1 — Navigate to chat page"):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step("Step 2 — Click Create Conversation button"):
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)

            with allure.step("Step 3 — Send a message to create conversation"):
                test_msg = "at_create_ui_test"
                initial_count = chat.get_message_count()
                chat.send_message(test_msg, use_enter=True)
                chat.wait_for_input_ready()
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

            with allure.step("Step 4 — Extract conversation ID for cleanup"):
                conv_id = _extract_conversation_id(page, conversation_api, test_msg)

            with allure.step("Step 5 — Verify conversation appears in sidebar"):
                chat.wait_for_naming_label_to_resolve()
                chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_conversation_link_count() > 0, (
                    "At least one conversation should appear in sidebar after creation"
                )

        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(int(conv_id))
                except Exception as exc:
                    logger.warning("Cleanup failed: %s", exc)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/conversations/ELITEA-0571_conversation-creation-and-list.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.smoke
    def test_create_conversation_via_api(self, page, conversation_id, conversation_api):
        """TC-CONV-001, TC-CONV-003: Create conversation and verify it appears in UI."""
        with allure.step("Step 1 — Navigate to conversation"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.wait_for_page_load()

        with allure.step("Step 2 — Verify conversation page loaded correctly"):
            _verify_conversation_page_loaded(chat, conversation_id, page)

        with allure.step("Step 3 — Verify conversation appears in sidebar"):
            conv = conversation_api.get_conversation(int(conversation_id))
            conv_name = conv.get("name", "")
            assert chat.conversation_exists_in_list(conv_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Conversation '{conv_name}' should appear in the sidebar list"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/conversations/ELITEA-0569_conversation-management-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_new_conversation_default_settings(self, page, conversation_id):
        """TC-CONV-002: New conversation has default settings."""
        with allure.step("Step 1 — Navigate to conversation"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.wait_for_page_load()

        with allure.step("Step 2 — Verify default model is selected"):
            model_text = chat.get_selected_model()
            assert model_text, "A default model should be displayed in the selector"


class TestConversationList:
    """TC-CONV-003 / TC-CONV-004 / TC-CONV-005: Viewing, navigating, and searching."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/conversations/ELITEA-0569_conversation-management-advanced-features.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/conversations/ELITEA-0571_conversation-creation-and-list.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.smoke
    def test_click_conversation_to_open(self, page, conversation_id, conversation_api):
        """TC-CONV-004: Click conversation to open it."""
        with allure.step("Step 1 — Get conversation name from API"):
            conv = conversation_api.get_conversation(int(conversation_id))
            conv_name = conv.get("name", "")
            assert conv_name, f"Failed to fetch name for conversation {conversation_id}"

        with allure.step("Step 2 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat()
            chat.wait_for_page_load()

        with allure.step("Step 3 — Click conversation in sidebar"):
            chat.select_conversation_from_list(conv_name, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 4 — Verify URL contains conversation ID"):
            chat.wait_for_conversation_url(conversation_id, timeout=NAVIGATION_TIMEOUT)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/conversations/ELITEA-0569_conversation-management-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_search_conversations_button(self, page, conversation_id):
        """TC-CONV-005: Search conversations button opens search panel."""
        with allure.step("Step 1 — Navigate to conversation"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.wait_for_page_load()

        with allure.step("Step 2 — Click Search conversations button"):
            chat.open_search_conversations_button(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 3 — Verify search input is visible"):
            expect(chat.search_conversations_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)


class TestConversationNavigation:
    """Navigation between conversations and back to chat list."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/conversations/ELITEA-0569_conversation-management-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_navigate_between_conversations(self, page, conversation_api):
        """Navigate from one conversation to another via the sidebar list."""
        with allure.step("Step 1 — Create two conversations via API"):
            conv_a = conversation_api.create_conversation("at_nav_a")
            conv_b = conversation_api.create_conversation("at_nav_b")
            conv_a_id = str(conv_a["id"])
            conv_b_id = str(conv_b["id"])

        with allure.step("Step 2 — Fetch conversation names from API"):
            conv_a_data = conversation_api.get_conversation(int(conv_a_id))
            conv_a_name = conv_a_data.get("name", "")
            assert conv_a_name, f"Failed to fetch name for conversation A ({conv_a_id})"

            conv_b_data = conversation_api.get_conversation(int(conv_b_id))
            conv_b_name = conv_b_data.get("name", "")
            assert conv_b_name, f"Failed to fetch name for conversation B ({conv_b_id})"

        try:
            with allure.step("Step 3 — Navigate to chat page"):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step("Step 4 — Click conversation A in sidebar"):
                chat.select_conversation_from_list(conv_a_name, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_conversation_url(conv_a_id, timeout=NAVIGATION_TIMEOUT)
                assert f"/chat/{conv_a_id}" in page.url, (
                    f"Should navigate to conversation A ({conv_a_id}), got URL: {page.url}"
                )
                attach_screenshot(page, "conv_a_loaded", f"Conversation A '{conv_a_name}' loaded")

            with allure.step("Step 5 — Click conversation B in sidebar"):
                chat.select_conversation_from_list(conv_b_name, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_conversation_url(conv_b_id, timeout=NAVIGATION_TIMEOUT)
                assert f"/chat/{conv_b_id}" in page.url, (
                    f"Should navigate to conversation B ({conv_b_id}), got URL: {page.url}"
                )
                attach_screenshot(page, "conv_b_loaded", f"Conversation B '{conv_b_name}' loaded")

        finally:
            for cid in (conv_a["id"], conv_b["id"]):
                try:
                    conversation_api.delete_conversation(cid)
                except Exception as exc:
                    logger.warning("Cleanup failed: %s", exc)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/conversations/ELITEA-0569_conversation-management-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_send_message_persists_conversation(self, page, conversation_id):
        """After sending a message, the conversation stays in the sidebar list."""
        with allure.step("Step 1 — Navigate to conversation"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.wait_for_page_load()

        with allure.step("Step 2 — Send a message"):
            initial_count = chat.get_message_count()
            chat.send_message("Test message for history verification", use_enter=True)
            chat.wait_for_input_ready()
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        with allure.step("Step 3 — Wait for conversation title to be generated"):
            chat.wait_for_naming_label_to_resolve()

        with allure.step("Step 4 — Navigate to chat root"):
            chat.navigate_to_chat()
            chat.wait_for_page_load()
            chat.wait_for_network(timeout=NAVIGATION_TIMEOUT)

        with allure.step("Step 5 — Verify conversation appears in sidebar"):
            assert chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT), (
                "Conversation should appear in sidebar after sending a message"
            )
            conversation_count = chat.get_conversation_link_count()
            assert conversation_count > 0, (
                f"At least one conversation should appear in sidebar, found {conversation_count}"
            )

        with allure.step("Step 6 — Verify no conversations stuck on 'Naming' placeholder"):
            titles = chat.get_conversation_link_titles(limit=5)
            for title in titles:
                if "Naming" in title:
                    pytest.fail(
                        f"Conversation should have a real title, not 'Naming' placeholder. "
                        f"Got: {title}"
                    )


class TestConversationActions:
    """TC-CONV-006 / TC-CONV-007: Rename and delete conversations."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/conversations/ELITEA-0570_conversation-rename-and-delete.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    @pytest.mark.smoke
    def test_rename_conversation_via_ui(self, page, conversation_api):
        """TC-CONV-006 UI: Rename a conversation through the three-dot menu."""
        original_name = "at_rename_ui_orig"
        new_name = "at_rename_ui_new"

        with allure.step("Step 1 — Create conversation via API"):
            conv = conversation_api.create_conversation(original_name)
            conv_id = conv["id"]

        try:
            with allure.step("Step 2 — Navigate to chat page"):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step("Step 3 — Verify original name appears in sidebar"):
                assert chat.conversation_exists_in_list(
                    original_name, timeout=UI_ELEMENT_TIMEOUT,
                ), f"Conversation '{original_name}' should appear before rename"

            with allure.step("Step 4 — Rename via three-dot menu"):
                chat.rename_conversation_via_menu(
                    new_name, conv_name=original_name, timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step("Step 5 — Verify new name appears in sidebar"):
                assert chat.conversation_exists_in_list(
                    new_name, timeout=UI_ELEMENT_TIMEOUT,
                ), f"Conversation should show new name '{new_name}' in sidebar"

            with allure.step("Step 6 — Verify old name is gone"):
                assert not chat.conversation_exists_in_list(
                    original_name, timeout=3000,
                ), f"Old name '{original_name}' should no longer appear"

            with allure.step("Step 7 — Verify rename persisted via API"):
                chat.wait_for_network(timeout=NAVIGATION_TIMEOUT)
                data = conversation_api.get_conversation(conv_id)
                assert data.get("name") == new_name, (
                    f"API should return new name '{new_name}', "
                    f"got '{data.get('name')}'"
                )
        finally:
            try:
                conversation_api.delete_conversation(conv_id)
            except Exception as exc:
                logger.warning("Cleanup failed: %s", exc)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/conversations/ELITEA-0570_conversation-rename-and-delete.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/conversations/ELITEA-0568_conversation-delete-with-confirmation.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    @pytest.mark.smoke
    def test_delete_conversation_with_confirmation(self, page, conversation_api):
        """TC-CONV-007: Delete conversation via UI and verify removal."""
        with allure.step("Step 1 — Create conversation via API"):
            conv_name = "at_del_confirm"
            conv = conversation_api.create_conversation(conv_name)
            conv_id = conv["id"]

        with allure.step("Step 2 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat()
            chat.wait_for_page_load()

        with allure.step("Step 3 — Verify conversation appears in sidebar"):
            assert chat.conversation_exists_in_list(
                conv_name, timeout=UI_ELEMENT_TIMEOUT,
            ), f"Conversation '{conv_name}' should appear before deletion"

        with allure.step("Step 4 — Open three-dot menu and click Delete"):
            chat.open_conversation_menu(conv_name, timeout=UI_ELEMENT_TIMEOUT)
            chat.click_delete_menu_item()

        with allure.step("Step 5 — Verify confirmation dialog"):
            dialog = Dialog.wait_for(page, timeout=UI_ELEMENT_TIMEOUT)
            title_text = Dialog.get_title(dialog)
            assert "Delete conversation" in title_text, f"Expected 'Delete conversation' in title, got: {title_text}"
            assert Dialog.has_button(dialog, "Cancel"), "Cancel button should be visible in dialog"
            assert Dialog.has_button(dialog, "Delete"), "Delete button should be visible in dialog"

        with allure.step("Step 6 — Confirm deletion"):
            Dialog.click_button(dialog, "Delete")
            Dialog.wait_for_hidden(page, timeout=NAVIGATION_TIMEOUT)
            chat.wait_for_network(timeout=NAVIGATION_TIMEOUT)

        with allure.step("Step 7 — Reload page and verify conversation removed from sidebar"):
            page.reload(wait_until="networkidle")
            chat.wait_for_page_load()
            logger.info(f"Checking if conversation '{conv_name}' still exists in list...")
            still_exists = chat.conversation_exists_in_list(conv_name, timeout=3000)
            assert not still_exists, (
                f"Conversation '{conv_name}' should be gone after deletion, but still appears in list"
            )

        with allure.step("Step 8 — Verify conversation removed from API"):
            data = conversation_api.list_conversations()
            ids = [c["id"] for c in data.get("rows", [])]
            logger.info(f"Conversations in API list: {ids}")
            assert conv_id not in ids, (
                f"Deleted conversation {conv_id} should not appear in API list, got IDs: {ids}"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/conversations/ELITEA-0568_conversation-delete-with-confirmation.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_delete_conversation_cancel(self, page, conversation_api):
        """TC-CONV-007b: Cancel the delete confirmation dialog."""
        with allure.step("Step 1 — Create conversation via API"):
            conv_name = "at_del_cancel"
            conv = conversation_api.create_conversation(conv_name)
            conv_id = conv["id"]

        try:
            with allure.step("Step 2 — Navigate to chat page"):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step("Step 3 — Verify conversation appears in sidebar"):
                assert chat.conversation_exists_in_list(
                    conv_name, timeout=UI_ELEMENT_TIMEOUT,
                ), f"Conversation '{conv_name}' should be visible before attempting deletion"

            with allure.step("Step 4 — Open three-dot menu and click Delete"):
                chat.open_conversation_menu(conv_name, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_delete_menu_item()

            with allure.step("Step 5 — Click Cancel in confirmation dialog"):
                dialog = Dialog.wait_for(page, timeout=UI_ELEMENT_TIMEOUT)
                Dialog.click_button(dialog, "Cancel")
                Dialog.wait_for_hidden(page, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 6 — Verify conversation still appears in list"):
                assert chat.conversation_exists_in_list(
                    conv_name, timeout=UI_ELEMENT_TIMEOUT,
                ), f"Conversation '{conv_name}' should still appear after cancel"
        finally:
            try:
                conversation_api.delete_conversation(conv_id)
            except Exception as exc:
                logger.warning("Cleanup failed: %s", exc)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/conversations/ELITEA-0569_conversation-management-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_multiple_conversations_listed(self, page, conversation_api):
        """Multiple conversations appear in the sidebar list."""
        created = []
        names = ["at_multi_1", "at_multi_2", "at_multi_3"]

        with allure.step("Step 1 — Create three conversations via API"):
            for name in names:
                c = conversation_api.create_conversation(name)
                created.append(c)

        try:
            with allure.step("Step 2 — Navigate to chat page"):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step("Step 3 — Verify all conversations appear in sidebar"):
                for name in names:
                    assert chat.conversation_exists_in_list(name, timeout=UI_ELEMENT_TIMEOUT), (
                        f"Conversation '{name}' should appear in the list"
                    )
        finally:
            for c in created:
                try:
                    conversation_api.delete_conversation(c["id"])
                except Exception as exc:
                    logger.warning("Cleanup failed: %s", exc)


class TestConversationIsolation:
    """Verify test isolation — each test gets a clean conversation."""

    @pytest.mark.p1
    def test_fixture_creates_fresh_conversation(self, page, conversation_id):
        """Verify the conversation_id fixture produces a valid conversation."""
        with allure.step("Step 1 — Navigate to conversation"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.wait_for_page_load()
            chat.dismiss_banner_if_present()

        with allure.step("Step 2 — Verify conversation page loaded correctly"):
            _verify_conversation_page_loaded(chat, conversation_id, page)

        with allure.step("Step 3 — Verify fresh conversation is empty"):
            delete_btn_count = chat.get_delete_button_count()
            if delete_btn_count > 0:
                page.reload(wait_until="networkidle")
                chat.wait_for_page_load()
                delete_btn_count = chat.get_delete_button_count()

            assert delete_btn_count == 0, (
                f"Fresh conversation should be empty, but found {delete_btn_count} "
                f"Delete button(s) on the page (URL: {page.url})"
            )

    @pytest.mark.p1
    @pytest.mark.smoke
    def test_fixture_cleanup_cycle(self, conversation_api):
        """Verify that creating and deleting conversations via the API works."""
        with allure.step("Step 1 — Create conversation via API"):
            conv = conversation_api.create_conversation("at_cleanup")
            cid = conv["id"]

        with allure.step("Step 2 — Verify conversation exists in API list"):
            data = conversation_api.list_conversations()
            ids = [c["id"] for c in data.get("rows", [])]
            assert cid in ids, f"Created conversation {cid} should appear in list"

        with allure.step("Step 3 — Delete conversation via API"):
            conversation_api.delete_conversation(cid)

        with allure.step("Step 4 — Verify conversation is gone from API list"):
            data = conversation_api.list_conversations()
            ids = [c["id"] for c in data.get("rows", [])]
            assert cid not in ids, f"Deleted conversation {cid} should not appear"
