"""UI test — Agent Hub: Start Conversation Creates New Chat and Redirects

Verify that clicking Start Chat in an agent modal creates a new conversation
and redirects the user to the Chat interface with the welcome message displayed.

Test case: ELITEA-2360
AFS: test-specs/agent-hub/l2_agent-hub-start-conversation-creates-new-chat_ELITEA-2360.md

Markers:
    - ui: requires browser
    - agent-hub: agent hub/catalog tests
    - p2: medium priority (per AFS metadata: priority medium)
    - regression
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from pages.agent_hub_page import AgentHubPage
from pages.chat_page import ChatPage

pytestmark = [pytest.mark.ui, pytest.mark.agent_hub, pytest.mark.p2, pytest.mark.regression]


class TestStartConversationCreatesNewChat:
    """ELITEA-2360 — Agent Hub: Start Conversation Creates New Chat and Redirects"""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/"
        "tests/automated-full-regression-ui/agent-hub/ELITEA-2360.md",
        "onetest-ai Test Case link",
    )
    def test_start_conversation_creates_new_chat(self, page):
        """When user starts a conversation from an agent card, a new chat is created
        and user is redirected to Chat page with welcome message displayed."""
        hub_page = AgentHubPage(page)
        chat_page = ChatPage(page)

        with allure.step("Step 1 — Navigate to Agent Hub (Catalog page)"):
            hub_page.navigate()

        with allure.step("Step 2 — Click on User Story Creator agent card to open modal"):
            # User Story Creator is the test data example from the case
            # This method waits for modal content to load before returning
            hub_page.open_agent_by_name("User Story Creator")

        with allure.step("Step 3 — Click the Start Chat button"):
            hub_page.click_start_chat()

        with allure.step("Step 4 — Verify URL redirects from Catalog to Chat"):
            # Wait for navigation to /chat page
            page.wait_for_url(re.compile(r"/chat"), timeout=15000)

        with allure.step("Step 5 — Verify Chat page is loaded"):
            chat_page.wait_for_page_load()

        with allure.step("Step 6 — Verify chat welcome message is displayed"):
            # Verify the welcome greeting is visible in the chat area
            chat_page.new_conversation_greeting.wait_for(state="visible", timeout=10000)
            greeting_text = chat_page.new_conversation_greeting.text_content() or ""

            # Verify greeting contains expected elements:
            # "Hello, [username]! What can I do for you today?"
            assert greeting_text, "Welcome greeting should not be empty"
            assert "Hello" in greeting_text, (
                f"Welcome message should contain 'Hello', got: {greeting_text}"
            )
            assert "What can I do for you today" in greeting_text, (
                f"Welcome message should contain 'What can I do for you today', got: {greeting_text}"
            )
