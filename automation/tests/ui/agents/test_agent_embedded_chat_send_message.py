"""Embedded chat — send message and verify response is non-empty (ELITEA-1874).

Verifies that the embedded chat panel on the agent detail page accepts a
keyboard-submitted message (Enter, no Shift — distinct from every other
embedded-chat test in this suite, which all click the Send button) and
returns a non-empty response containing the agent's deterministic reply,
clearing the input field once submitted.

Test-data strategy (per AFS): a dedicated, uniquely-named agent with
instructions "You are a helpful assistant. Reply only with: PONG" is created
per-test via ``AgentAPI.create_agent()`` — same pattern as
``test_agent_llm_selector_anthropic_models.py``'s "Reply only with: CONFIRMED"
(a live, deterministic-ish LLM round trip already proven reliable there).

Spec: test-specs/agents/l2_embedded-chat-send-message-non-empty-response_ELITEA-1874.md
"""

import uuid

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from playwright.sync_api import Page

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000

AGENT_INSTRUCTIONS = "You are a helpful assistant. Reply only with: PONG"
PING_MESSAGE = "PING"
EXPECTED_RESPONSE_SUBSTRING = "PONG"


class TestAgentEmbeddedChatSendMessage:
    """Embedded chat — Enter-key send yields a non-empty response (ELITEA-1874, p1)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1874_embedded-chat-send-message-and-verify-response-is-non-empty.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_send_message_via_enter_and_verify_non_empty_response(self, page: Page, agent_api):
        """Typing "PING" and pressing Enter yields a non-empty response
        containing "PONG", and clears the chat input."""
        with allure.step("Precondition — create a dedicated agent with deterministic instructions"):
            agent_name = f"elitea-1874-chat-{uuid.uuid4().hex[:8]}"
            agent = agent_api.create_agent(
                agent_name,
                "Auto-created for ELITEA-1874 embedded chat test",
                AGENT_INSTRUCTIONS,
            )
            agent_id = agent["id"]

        detail_page = None
        try:
            with allure.step("Step 1 — Navigate to the agent's detail page"):
                detail_page = AgentDetailPage(page)
                detail_page.navigate(agent_id)
                assert detail_page.information_section.is_visible(), (
                    "Agent detail page's Information section should be visible"
                )

            with allure.step("Step 2 — Locate the embedded chat panel"):
                assert detail_page.chat_message_input.is_visible(), (
                    "Embedded chat message input should be visible"
                )
                assert detail_page.chat_message_list.is_visible(), (
                    "Embedded chat message list should be visible"
                )

            with allure.step('Step 3 — Type "PING" in the chat input'):
                detail_page.chat_message_input.click()
                detail_page.chat_message_input.clear()
                detail_page.chat_message_input.press_sequentially(PING_MESSAGE, delay=10)
                assert detail_page.chat_message_input.input_value() == PING_MESSAGE, (
                    f"Input should display {PING_MESSAGE!r} before sending, got "
                    f"{detail_page.chat_message_input.input_value()!r}"
                )

            initial_count = detail_page.get_chat_message_count()
            with allure.step("Step 4 — Press Enter (without Shift) to submit the message"):
                detail_page.chat_message_input.press("Enter")

            with allure.step("Step 5 — Wait for the assistant response to appear and stabilise"):
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT
                )
                assert detail_page.get_chat_message_count() > initial_count, (
                    "Message count should have increased after pressing Enter"
                )

            with allure.step('Step 6 — Verify the response is non-empty and contains "PONG"'):
                response_text = detail_page.get_last_chat_response_text()
                assert response_text != "", "Assistant response should be non-empty"
                assert EXPECTED_RESPONSE_SUBSTRING in response_text, (
                    f"Response should contain {EXPECTED_RESPONSE_SUBSTRING!r}, "
                    f"got: {response_text!r}"
                )

            with allure.step("Step 7 — Verify the input field is cleared after sending"):
                assert detail_page.chat_message_input.input_value() == "", (
                    "Chat input should be empty after sending, got: "
                    f"{detail_page.chat_message_input.input_value()!r}"
                )
        finally:
            with allure.step("Cleanup — delete the dedicated agent"):
                agent_api.delete_agent(agent_id)
