"""Agent test chat — Copy markdown / Copy text icons visible, clickable, toast-confirmed (ELITEA-4755).

Spec: test-specs/agents/l1_agent-test-chat-copy-markdown-and-copy-text-icons-toast_ELITEA-4755.md
"""

import uuid

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.ui, pytest.mark.agents]

UI_ELEMENT_TIMEOUT = 10_000
AI_RESPONSE_TIMEOUT = 60_000
TOAST_DISMISS_TIMEOUT = 15_000

AGENT_INSTRUCTIONS = "You are a helpful assistant. Reply only with: PONG"
PING_MESSAGE = "PING"


class TestAgentTestChatCopyIcons:
    """Copy markdown / Copy text icons on an agent test-chat response (ELITEA-4755, p1)."""

    @pytest.mark.tms("ELITEA-4755")
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-4755_agent-test-chat-copy-markdown-and-copy-text-actions.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_copy_markdown_and_copy_text_icons_show_tooltip_and_toast(self, page: Page, agent_api):
        """Both copy icons are visible under the response; tooltips and click toasts match."""
        with allure.step("Precondition — create a dedicated agent"):
            agent = agent_api.create_agent(
                f"elitea-4755-copy-{uuid.uuid4().hex[:8]}",
                "Auto-created for ELITEA-4755 copy icons test",
                AGENT_INSTRUCTIONS,
            )
            agent_id = agent["id"]

        try:
            detail_page = AgentDetailPage(page)
            with allure.step("Step 1 — Open the agent; Test Agent button is visible"):
                detail_page.navigate(agent_id)
                assert detail_page.information_section.is_visible(), "Agent configuration page should be open"
                assert detail_page.test_agent_button.is_visible(), "Test Agent button should be visible"

            with allure.step("Step 2 — Click Test Agent; panel with input opens"):
                detail_page.open_test_agent_panel()
                assert detail_page.test_agent_panel.is_visible(), "Test panel should be visible"
                assert detail_page.chat_message_input.is_visible(), "Chat input should be visible"

            with allure.step("Step 3 — Send a request; response is generated"):
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message(PING_MESSAGE)
                detail_page.wait_for_chat_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                assert detail_page.get_last_chat_response_text() != "", "Agent response should be non-empty"

            with allure.step("Step 4 — Copy markdown and Copy text icons are visible"):
                assert detail_page.is_last_response_copy_icon_visible("markdown"), (
                    "Copy markdown icon should be visible under the response"
                )
                assert detail_page.is_last_response_copy_icon_visible("text"), (
                    "Copy text icon should be visible under the response"
                )

            with allure.step("Step 5 — Hover the Copy markdown icon; tooltip 'Copy markdown'"):
                assert detail_page.hover_last_response_copy_icon("markdown") == "Copy markdown"

            with allure.step("Step 6 — Click Copy markdown; toast 'Markdown copied to clipboard.'"):
                toast = detail_page.click_last_response_copy_icon("markdown")
                assert toast == "Markdown copied to clipboard.", f"Unexpected toast: {toast!r}"
                # Let the first toast go so step 8 asserts the NEW toast.
                expect(detail_page.toast_message).to_have_count(0, timeout=TOAST_DISMISS_TIMEOUT)

            with allure.step("Step 7 — Hover the Copy text icon; tooltip 'Copy text'"):
                assert detail_page.hover_last_response_copy_icon("text") == "Copy text"

            with allure.step("Step 8 — Click Copy text; toast 'Text copied to clipboard.'"):
                toast = detail_page.click_last_response_copy_icon("text")
                assert toast == "Text copied to clipboard.", f"Unexpected toast: {toast!r}"
        finally:
            with allure.step("Cleanup — delete the dedicated agent"):
                agent_api.delete_agent(agent_id)
