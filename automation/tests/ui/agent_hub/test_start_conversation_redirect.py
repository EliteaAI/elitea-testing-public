"""Test: Agent Hub — start conversation creates new chat and redirects to Chat page.

ELITEA-2360: Verify that clicking "Start Chat" in an Agent Hub detail modal
creates a new conversation and redirects to the Chat page, displaying the welcome message.

AFS: test-specs/agent-hub/l2_agent-hub-start-conversation-creates-new-chat-and-redirects_ELITEA-2360.md
"""

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.agent_hub_page import AgentHubPage
from pages.chat_page import ChatPage


class TestAgentHubStartConversation:
    """Agent Hub start conversation flow — modal to Chat page redirect."""

    @pytest.mark.p2
    @pytest.mark.regression
    @pytest.mark.agent_hub
    @allure.title("Start conversation creates new chat and redirects to Chat page")
    @allure.description(
        "Verify that clicking 'Start Chat' in an Agent Hub detail modal creates a new "
        "conversation and redirects to the Chat page, with the welcome message displayed."
    )
    @pytest.mark.tryfirst  # @ELITEA-2360
    def test_start_conversation_creates_chat_and_redirects(self, page: Page):
        """
        ELITEA-2360: Agent Hub — start conversation creates new chat and redirects to Chat page.

        Steps:
        1. Navigate to Agent Hub (Catalog)
        2. Click on an agent card (e.g., "User Story Creator")
        3. Verify detail modal opens
        4. Click "Start Chat" button
        5. Verify redirect to Chat page (/chat)
        6. Verify chat welcome message is displayed
        """

        agent_hub = AgentHubPage(page)
        chat_page = ChatPage(page)
        agent_name = "User Story Creator"

        # Step 1: Navigate to Agent Hub
        with allure.step("Step 1 — Navigate to Agent Hub"):
            agent_hub.navigate()
            agent_hub.wait_for_page_load()

        # Step 2: Click on agent card (e.g., "User Story Creator")
        with allure.step(f"Step 2 — Click agent card: {agent_name}"):
            agent_hub.open_agent_by_name(agent_name)

        # Step 3: Verify detail modal opens (implicit via open_agent_by_name)
        with allure.step("Step 3 — Verify agent detail modal displayed"):
            # Verify modal is open by checking that the start chat button is visible
            start_chat_button = agent_hub.get_modal_like_button()  # Use page to check modal presence
            # Instead, let's just verify the button is present before clicking
            modal_locator = page.locator('[data-testid="catalog-agent-modal"]')
            expect(modal_locator).to_be_visible(timeout=10000)

        # Step 4: Click "Start Chat" button
        with allure.step("Step 4 — Click 'Start Chat' button in modal"):
            # Wait for modal's async fetch to complete (known defect #1043)
            # Clicking before the fetch completes throws a silent TypeError
            page.wait_for_timeout(1000)
            agent_hub.click_start_chat(timeout=10000)
            page.wait_for_timeout(2000)  # Wait for navigation to complete

        # Step 5: Verify redirect to Chat page
        with allure.step("Step 5 — Verify redirect to Chat page (/chat)"):
            current_url = page.url
            assert "/chat" in current_url, f"Expected URL to contain '/chat', got {current_url}"

        # Step 6: Verify chat welcome message is displayed
        with allure.step("Step 6 — Verify chat welcome message displayed"):
            # Wait for chat page to load
            chat_page.wait_for_page_load(timeout=15000)

            # Verify welcome greeting is visible
            welcome_msg = page.locator('[data-testid="chat-new-conversation-greeting"]')
            welcome_msg.wait_for(state="visible", timeout=10000)
            expect(welcome_msg).to_be_visible()

            # Verify message contains expected text pattern
            welcome_text = welcome_msg.text_content()
            assert "Hello" in welcome_text, (
                f"Welcome message should contain 'Hello', got: {welcome_text}"
            )
            assert "What can I do for you today" in welcome_text, (
                f"Welcome message should contain 'What can I do for you today', got: {welcome_text}"
            )

        # Cleanup: Delete conversation if needed (optional, depends on test environment)
        # The conversation will persist in the test environment, which is acceptable for
        # this case as it doesn't affect subsequent tests (each test uses auth_state fixture)
