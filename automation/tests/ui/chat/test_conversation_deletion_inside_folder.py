"""UI Test for ELITEA-2115 — Chat: Conversation Deletion Inside a Folder.

Verifies that deleting a conversation that lives INSIDE a folder removes only
that conversation — the folder itself is never touched (no folder-level
DELETE call fires) and renders its own empty state once its last conversation
is gone.

Spec: test-specs/chat-interface/l3_conversation-deletion-inside-folder_ELITEA-2115.md

Uses project 400 ("UI Testing") — a dedicated sandbox project confirmed live
to be genuinely empty of conversations/folders, so this test's setup/teardown
never touches the shared Team/Private project fixture data other analyses in
this suite reuse (see AFS § Automation Hints / `_surface.md`).

No product defects found — this case automates exactly as written.
"""

import logging

import allure
import pytest
from api.client import ConversationAPI
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Dedicated, normally-empty sandbox project — see module docstring.
SANDBOX_PROJECT_ID = "400"


class TestConversationDeletionInsideFolder:
    """ELITEA-2115: Chat – Conversation Deletion – Conversation Inside a Folder (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2115_chat-conversation-deletion-conversation-inside-a-folder.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_delete_conversation_inside_folder_preserves_folder(self, page, _browser_cookies):
        """Deleting a conversation inside a folder removes it while the folder
        itself is preserved and shows its empty state.

        Steps (AFS
        test-specs/chat-interface/l3_conversation-deletion-inside-folder_ELITEA-2115.md):
        1. Navigate to Chats, expand the seeded folder — conversation visible inside.
        2. Hover the conversation, click the 3-dot icon — context menu with Delete.
        3. Click Delete — confirmation dialog appears with the live body text.
        4. Click the Delete (confirm) button — conversation removed, DELETE 204.
        5. Verify the folder still exists in the left panel.
        6. Verify the folder now shows its empty state ("No conversations added").
        """
        sandbox_api = ConversationAPI(browser_cookies=_browser_cookies, project_id=SANDBOX_PROJECT_ID)
        chat = ChatPage(page)
        folder_id = None
        conv_id = None

        try:
            with allure.step(
                "Setup — switch to the sandbox project (400); seed a folder "
                "with one conversation via the API, then navigate to it"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.switch_project(SANDBOX_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)

                folder = sandbox_api.create_folder("autotest_2115_folder")
                folder_id = folder["id"]
                conv = sandbox_api.create_conversation("autotest_2115_in_folder")
                conv_id = conv["id"]
                sandbox_api.move_conversation_to_folder(conv_id, folder_id)

                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step(
                "Step 1 — Expand the folder; verify the conversation renders inside it"
            ):
                if not chat.is_folder_expanded(folder_id):
                    chat.expand_folder(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_conversation_in_folder(folder_id, conv_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Conversation {conv_id} should render inside folder {folder_id}"
                )

            with allure.step(
                "Step 2 — Hover the conversation, click the 3-dot icon; verify "
                "the context menu shows a Delete option"
            ):
                chat.open_conversation_context_menu(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_conversation_menu_item("delete")).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 3 — Click Delete; verify the confirmation dialog appears "
                "with the live body text"
            ):
                no_folder_delete = chat.capture_requests_matching(
                    url_substring="/folder/prompt_lib/", method="DELETE",
                )
                chat.click_conversation_menu_item("delete", timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.delete_confirm_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expected_message = f"Are you sure to delete the {conv['name']} chat? It can't be restored."
                expect(chat.delete_confirm_message).to_have_text(
                    expected_message, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 4 — Click the Delete (confirm) button; verify the "
                "conversation is removed and the DELETE request resolves 204"
            ):
                delete_response = chat.confirm_delete_conversation(conv_id, timeout=NAVIGATION_TIMEOUT)
                assert delete_response.status == 204, (
                    f"DELETE conversation request should resolve 204, got {delete_response.status}"
                )
                expect(chat.delete_confirm_dialog).to_be_hidden(timeout=NAVIGATION_TIMEOUT)
                expect(chat.get_conversation_item(conv_id)).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 5 — Verify the folder still exists in the left panel"):
                expect(chat.get_folder_item(folder_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 6 — Verify the folder now shows its empty state "
                "('No conversations added') — it was the last conversation"
            ):
                empty_text = chat.get_folder_empty_state_text(folder_id)
                assert empty_text == "No conversations added", (
                    f"Expected folder empty-state text 'No conversations added', got {empty_text!r}"
                )

            with allure.step(
                "Verify no folder-level DELETE request fired at any point "
                "(the case's own core assertion — folder preserved — made "
                "network-verifiable, not just DOM-persistence)"
            ):
                assert len(no_folder_delete) == 0, (
                    f"No folder DELETE request should fire; captured: {list(no_folder_delete)!r}"
                )
                no_folder_delete.stop()

        finally:
            try:
                if folder_id:
                    sandbox_api.delete_folder(folder_id)
            except Exception as exc:
                logger.warning("Cleanup failed for folder %s: %s", folder_id, exc)
            sandbox_api.close()
