"""Embedded chat — Shift+Enter inserts new line, Enter sends message (ELITEA-1875).

Verifies that Shift+Enter inserts a newline into the embedded chat's composer
without submitting, while Enter (without Shift) submits the accumulated
multi-line message and triggers an agent response.

Test-data strategy (per AFS): a dedicated, uniquely-named agent with plain
"helpful assistant" instructions is created per-test via
``AgentAPI.create_agent()`` — this case needs a message sent and any
non-empty response, not a specific deterministic reply (contrast with
ELITEA-1874's "Reply only with: PONG").

Spec: test-specs/agents/l2_embedded-chat-shift-enter-newline-enter-sends_ELITEA-1875.md
"""

import uuid

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000

AGENT_INSTRUCTIONS = "You are a helpful assistant. Reply concisely."
LINE_1 = "First line"
LINE_2 = "Second line"

# Timeout budget for the Step 3 negative-existence wait (see below) — the
# window a WOULD-BE wrongful submission has to attach a new chat-message-item
# before we accept that Shift+Enter correctly sent nothing. Not a sleep: it
# backs a `Locator.wait_for()` call, a framework-native polling wait that
# resolves EARLY (failing fast) if a message does appear, and only runs out
# the full window on the expected/passing path.
NEGATIVE_ASSERTION_WINDOW_MS = 1500


class TestAgentEmbeddedChatShiftEnter:
    """Embedded chat — Shift+Enter newline vs Enter-submit (ELITEA-1875, p1)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1875_embedded-chat-shift-enter-inserts-new-line-enter-sends-message.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_shift_enter_new_line_enter_sends(self, page: Page, agent_api):
        """Shift+Enter inserts a newline without sending; Enter submits the
        accumulated multi-line message and triggers a response."""
        with allure.step("Precondition — create a dedicated agent"):
            agent_name = f"elitea-1875-chat-{uuid.uuid4().hex[:8]}"
            agent = agent_api.create_agent(
                agent_name,
                "Auto-created for ELITEA-1875 embedded chat test",
                AGENT_INSTRUCTIONS,
            )
            agent_id = agent["id"]

        detail_page = None
        try:
            with allure.step("Step 1 — Open the agent's detail page with embedded chat"):
                detail_page = AgentDetailPage(page)
                detail_page.navigate(agent_id)
                assert detail_page.information_section.is_visible(), (
                    "Agent detail page's Information section should be visible"
                )
                assert detail_page.chat_message_input.is_visible(), (
                    "Embedded chat message input should be visible"
                )

            with allure.step("Step 2 — Click the chat input field"):
                detail_page.chat_message_input.click()
                expect(detail_page.chat_message_input).to_be_focused(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            baseline_count = detail_page.get_chat_message_count()
            with allure.step(
                "Step 3 — Press Shift+Enter — verify a new line is inserted "
                "and no message is sent"
            ):
                detail_page.chat_message_input.press_sequentially(LINE_1, delay=10)
                detail_page.chat_message_input.press("Shift+Enter")
                assert "\n" in detail_page.chat_message_input.input_value(), (
                    "Chat input should contain a literal newline after Shift+Enter, "
                    f"got: {detail_page.chat_message_input.input_value()!r}"
                )

                # Prove the negative (no message submitted) with a framework
                # wait, not a raw sleep: Locator.wait_for() polls for the
                # chat-message-item slot a wrongful submit WOULD populate.
                # It resolves EARLY — failing fast — if that item attaches,
                # and raises TimeoutError (expected/caught below) only when
                # nothing arrives within the window. Per the AFS's Network
                # Behavior section, Shift+Enter fires no network request at
                # all (purely client-side textarea state), so this wait
                # exists solely to catch a hypothetical regression, not to
                # await a real async operation.
                would_be_next_message = detail_page.chat_message_item.nth(
                    baseline_count
                )
                with pytest.raises(PlaywrightTimeoutError):
                    would_be_next_message.wait_for(
                        state="attached", timeout=NEGATIVE_ASSERTION_WINDOW_MS
                    )

                assert detail_page.get_chat_message_count() == baseline_count, (
                    "No message should have been submitted by Shift+Enter — "
                    f"count changed from {baseline_count} to "
                    f"{detail_page.get_chat_message_count()}"
                )

            with allure.step("Step 4 — Type additional text on the new line"):
                detail_page.chat_message_input.press_sequentially(LINE_2, delay=10)
                composer_value = detail_page.chat_message_input.input_value()
                assert LINE_1 in composer_value and LINE_2 in composer_value, (
                    f"Composer should contain both lines, got: {composer_value!r}"
                )

            with allure.step(
                "Step 5 — Press Enter (without Shift) — verify the multi-line "
                "message is submitted"
            ):
                detail_page.chat_message_input.press("Enter")

            with allure.step("Step 6 — Verify an assistant response appears"):
                detail_page.wait_for_chat_response(
                    initial_count=baseline_count, timeout=AI_RESPONSE_TIMEOUT
                )
                assert detail_page.get_chat_message_count() > baseline_count, (
                    "Message count should have increased after pressing Enter"
                )
                response_text = detail_page.get_last_chat_response_text()
                assert response_text != "", "Assistant response should be non-empty"

                # Axis-2 addition (AFS): confirm the SUBMITTED message itself
                # carried both typed lines, not just that "a" message went
                # through — catches a regression that silently dropped the
                # Shift+Enter-inserted line.
                messages = detail_page.chat_message_item
                message_count = messages.count()
                submitted_user_message = ""
                for i in range(message_count):
                    text = messages.nth(i).text_content() or ""
                    if LINE_1 in text and LINE_2 in text:
                        submitted_user_message = text
                        break
                assert submitted_user_message, (
                    f"Expected a chat message item containing both {LINE_1!r} and "
                    f"{LINE_2!r} (the submitted multi-line message)"
                )
        finally:
            with allure.step("Cleanup — delete the dedicated agent"):
                agent_api.delete_agent(agent_id)
