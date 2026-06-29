"""UI Tests for Agent with GitHub Toolkit integration.

Tests the end-to-end flow of creating an agent, attaching a GitHub toolkit
to it, and verifying the agent can use the toolkit to execute GitHub API calls.

Each test creates its own resources via API fixtures and cleans up afterwards.

Markers:
    - ui: requires browser
    - agents: agent-related tests
    - toolkits: toolkit-related tests
    - p0: critical priority tests
    - p1: high priority tests

Usage:
    cd automation
    pytest test_agent_with_github_toolkit.py -v
    pytest test_agent_with_github_toolkit.py -v -m p0
"""

import logging

import pytest

from pages.agent_page import AgentPage
from pages.chat_page import ChatPage
import allure

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.toolkits]

_flaky = pytest.mark.flaky(reruns=3, reruns_delay=2)

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000
FORM_SAVE_TIMEOUT = 15000
AI_RESPONSE_TIMEOUT = 30000
TOOLKIT_EXECUTION_TIMEOUT = 120000


# ===========================================================================
# Shared helpers
# ===========================================================================


def _attach_toolkit_to_agent(
    page, agent_id: int, toolkit_name: str, timeout: int = FORM_SAVE_TIMEOUT
) -> AgentPage:
    """Navigate to agent, add toolkit, assert attached, save. Returns AgentPage."""
    agents = AgentPage(page)
    agents.navigate_to_agent(agent_id)
    agents.wait_for_agent_detail()
    agents.add_toolkit(toolkit_name)
    assert agents.is_toolkit_attached(toolkit_name), (
        f"Toolkit '{toolkit_name}' should appear in the agent's Toolkits section"
    )
    agents.save_and_wait(timeout=timeout)
    return agents


# ===========================================================================
# Test 1: Add toolkit to agent via UI
# ===========================================================================


class TestAddToolkitToAgent:
    """Add a GitHub toolkit to an agent and verify it's attached."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0143_agent-with-toolkits.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    def test_add_toolkit_to_agent(
        self,
        page,
        agent_id: int,
        github_toolkit: dict,
    ):
        """Add a GitHub toolkit to an existing agent via the UI, then chat.

        Steps:
        1. Navigate to agent detail page
        2. Click "Toolkit" button in the Toolkits section
        3. Search for and select the toolkit
        4. Verify toolkit card appears in the agent config
        5. Save the agent
        6. Find chat input in the embedded chat (right side of agent detail page)
        7. Type message: 'List all branches in the repository'
        8. Click Send button
        9. Wait for AI response to stabilise (3000ms stable duration)
        10. Verify response contains 'branch' keyword (toolkit executed)
        """
        toolkit_name = github_toolkit["name"]

        agents = _attach_toolkit_to_agent(page, agent_id, toolkit_name)

        # --- Step 6-10: Test embedded chat with toolkit ---
        logger.info("Sending message in embedded chat to trigger toolkit...")
        initial_count = agents.get_embedded_chat_message_count()
        agents.send_message_in_embedded_chat("List all branches in the repository")

        logger.info("Waiting for AI + toolkit response in embedded chat...")
        agents.wait_for_embedded_chat_response(
            initial_count=initial_count,
            stable_duration_ms=3000,
            timeout=TOOLKIT_EXECUTION_TIMEOUT,
        )

        last_content = agents.get_embedded_chat_last_message()
        assert last_content, "Expected AI to respond with content in embedded chat"
        logger.info(
            "Embedded chat response (%d chars): %s",
            len(last_content), last_content[:500],
        )

        assert "branch" in last_content.lower(), (
            f"Expected embedded chat response to mention 'branch' from toolkit output. "
            f"Response: {last_content[:200]}"
        )


# ===========================================================================
# Test 2: Remove toolkit from agent via UI
# ===========================================================================


class TestRemoveToolkitFromAgent:
    """Remove a toolkit from an agent and verify it's gone."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0143_agent-with-toolkits.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_remove_toolkit_from_agent(
        self,
        page,
        agent_id: int,
        github_toolkit: dict,
    ):
        """Add a toolkit, then remove it, and verify it's gone.

        Steps:
        1. Navigate to agent detail page
        2. Add the toolkit
        3. Verify it's attached
        4. Remove the toolkit via delete button + confirmation
        5. Verify toolkit is no longer attached
        """
        toolkit_name = github_toolkit["name"]

        agents = _attach_toolkit_to_agent(page, agent_id, toolkit_name)

        # Remove the toolkit
        agents.remove_toolkit(toolkit_name)

        # Verify toolkit is gone
        assert not agents.is_toolkit_attached(toolkit_name, timeout=2000), (
            f"Toolkit '{toolkit_name}' should no longer be attached after removal"
        )


# ===========================================================================
# Test 3: Chat with agent that has toolkit attached
# ===========================================================================


class TestChatWithAgentToolkit:
    """Chat with an agent that has a GitHub toolkit and verify tool execution."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0143_agent-with-toolkits.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    def test_agent_chat_with_github_toolkit(
        self,
        page,
        agent_id: int,
        agent_api,
        github_toolkit: dict,
        conversation_id: str,
    ):
        """Add toolkit to agent, chat via /app/chat, verify toolkit execution.

        Steps:
        1. Navigate to agent detail page
        2. Add the GitHub toolkit
        3. Save the agent
        4. Navigate to conversation in /app/chat
        5. Add agent as participant
        6. Send a message asking to list branches
        7. Wait for AI + toolkit response (stable content)
        8. Verify the response mentions branches
        """
        toolkit_name = github_toolkit["name"]

        # --- Step 1-3: Add toolkit to agent and save ---
        _attach_toolkit_to_agent(page, agent_id, toolkit_name)

        # --- Step 4-5: Navigate to chat and add agent as participant ---
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)
        chat.wait_for_page_load()
        chat.wait_for_network(timeout=NAVIGATION_TIMEOUT)

        logger.info("Adding agent as chat participant...")
        agent_name = agent_api.get_agent(agent_id)["name"]
        chat.add_agent_participant(agent_name, timeout=UI_ELEMENT_TIMEOUT)
        logger.info("Agent added as chat participant")

        # --- Step 6: Send message ---
        logger.info("Sending message to trigger toolkit...")
        initial_count = chat.get_message_count()
        chat.send_message("List all branches in the repository")

        # --- Step 7: Wait for response with toolkit execution ---
        logger.info("Waiting for AI + toolkit response...")
        chat.wait_for_ai_response(initial_count=initial_count, timeout=TOOLKIT_EXECUTION_TIMEOUT)
        chat.wait_for_message_content_stable(
            stable_duration_ms=3000, timeout=TOOLKIT_EXECUTION_TIMEOUT
        )

        # --- Step 8: Verify response ---
        last_content = chat.get_last_message_text()
        assert last_content, "Expected AI to respond with content"
        logger.info("AI response (%d chars): %s", len(last_content), last_content[:500])

        # Verify response is not just a transient thinking state
        assert "thinking" not in last_content.lower().strip().rstrip("."), (
            f"Response appears to be a transient thinking state, not a final answer: "
            f"{last_content[:200]}"
        )

        # Verify toolkit actually executed and returned GitHub data
        assert any(
            keyword in last_content.lower()
            for keyword in ["branch", "repository"]
        ), (
            f"Expected AI response to mention branches/repository from toolkit output. "
            f"Response: {last_content[:200]}"
        )

        logger.info("Agent executed toolkit successfully in chat")
