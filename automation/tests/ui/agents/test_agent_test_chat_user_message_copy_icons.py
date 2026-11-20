"""Agent test chat — USER message Copy markdown / Copy text icons, toast-confirmed (ELITEA-4760).

Spec: test-specs/agents/l1_agent-test-chat-user-message-copy-markdown-and-copy-text-icons-toast_ELITEA-4760.md
"""

import uuid

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.ui, pytest.mark.agents]

UI_ELEMENT_TIMEOUT = 10_000
AI_RESPONSE_TIMEOUT = 60_000
TOAST_DISMISS_TIMEOUT = 20_000

AGENT_INSTRUCTIONS = "You are a helpful assistant. Reply only with: PONG"
USER_MESSAGE = "Create a fairy tale about a dragon."


class TestAgentTestChatUserMessageCopyIcons:
    """Copy markdown / Copy text icons under the user's own test-chat message (ELITEA-4760, p1)."""

    @pytest.mark.tms("ELITEA-4760")
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-4760_user-message-copy-markdown-and-copy-text-actions.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_user_message_copy_icons_show_tooltip_and_toast(self, page: Page, agent_api):
        """Both copy icons under the user's message are visible; tooltips and click toasts match."""
        with allure.step("Precondition — create a dedicated agent"):
            agent = agent_api.create_agent(
                f"elitea-4760-copy-{uuid.uuid4().hex[:8]}",
                "Auto-created for ELITEA-4760 user message copy icons test",
                AGENT_INSTRUCTIONS,
            )
            agent_id = agent["id"]

        try:
            detail_page = AgentDetailPage(page)
            with allure.step("Step 1 — Open the agent, click Test Agent; panel with input opens"):
                detail_page.navigate(agent_id)
                assert detail_page.test_agent_button.is_visible(), "Test Agent button should be visible"
                detail_page.open_test_agent_panel()
                assert detail_page.test_agent_panel.is_visible(), "Test panel should be visible"
                assert detail_page.chat_message_input.is_visible(), "Chat input should be visible"

            with allure.step("Step 2 — Send the message; it appears in the chat"):
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message(USER_MESSAGE)
                detail_page.wait_for_chat_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                expect(detail_page.chat_message_list).to_contain_text(USER_MESSAGE, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 3 — Copy markdown and Copy text icons under the user message are visible"):
                assert detail_page.is_last_user_message_copy_icon_visible("markdown"), (
                    "Copy markdown icon should be visible under the user message"
                )
                assert detail_page.is_last_user_message_copy_icon_visible("text"), (
                    "Copy text icon should be visible under the user message"
                )
                assert detail_page.is_last_user_message_copy_icon_enabled("markdown"), "Copy markdown not clickable"
                assert detail_page.is_last_user_message_copy_icon_enabled("text"), "Copy text not clickable"

            with allure.step("Step 4 — Copy markdown: tooltip, click, toast 'Markdown copied to clipboard.'"):
                assert detail_page.hover_last_user_message_copy_icon("markdown") == "Copy markdown"
                toast = detail_page.click_last_user_message_copy_icon("markdown")
                assert toast == "Markdown copied to clipboard.", f"Unexpected toast: {toast!r}"
                # Let the first toast go so step 5 asserts the NEW toast.
                expect(detail_page.toast_message).to_have_count(0, timeout=TOAST_DISMISS_TIMEOUT)

            with allure.step("Step 5 — Copy text: tooltip, click, toast 'Text copied to clipboard.'"):
                assert detail_page.hover_last_user_message_copy_icon("text") == "Copy text"
                toast = detail_page.click_last_user_message_copy_icon("text")
                assert toast == "Text copied to clipboard.", f"Unexpected toast: {toast!r}"
        finally:
            with allure.step("Cleanup — delete the dedicated agent"):
                agent_api.delete_agent(agent_id)
