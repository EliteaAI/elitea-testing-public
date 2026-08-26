"""Agent Hub — E2E start conversation with a no-starters agent, send message,
receive reply (ELITEA-2368).

Opens a Catalog agent that has no conversation starters and no welcome
message, verifies the preview modal's empty-state copy, starts a chat via
"Start Chat", verifies the new-conversation greeting + agent chip +
Participants panel entry, types and sends a message, and verifies the user
message, the "Thought for N secs" processing indicator, the AI reply, the
sidebar "Today" grouping, and the Context Budget counter going from
absent/0 to a real value.

Spec: test-specs/agent-hub/l3_agent-hub-start-conversation-no-starters_ELITEA-2368.md

Reuses ``AgentHubPage`` (Catalog listing + preview modal, ELITEA-2356/2075)
and ``ChatPage`` (new-conversation greeting, composer, participants panel,
context budget — ELITEA-2075/2167/2168) as-is — no new page-object work,
every locator this case touches already exists.

Case-text drifts (CLARIFICATION, already tracked, not re-filed — AFS §
Known Defects Found): "CONVERSATION STARTERS" / "Start conversation" ->
live product reads "CHAT STARTERS" / "Start Chat"; "WELCOME MESSAGE"
(all-caps) -> live product reads "Welcome Message" (title-case). Tracked in
EliteaAI/elitea-testing-public#1042, which explicitly names ELITEA-2368 as
an affected sibling. Asserted against the live copy, not the case's literal
text.

Deferred (not filed — AFS § Known Defects Found): case step 7's implied
single combined "AgentName vX.X" chip is actually two separate adjacent
elements live (``chat-switch-participant-button`` +
``chat-version-selector-trigger``); this case only asserts SOME
agent-identifying chip is visible — the split shape is
ELITEA-2362/#870's job to formally document.
"""

import logging
import re

import allure
import pytest
from api import ConversationAPI
from pages.agent_hub_page import AgentHubPage
from pages.chat_page import ChatPage
from playwright.sync_api import Page

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 90_000  # live LLM completion — AFS Automation Hints (30-90s)

# Implementer-time finding (technique substitution, not a scope change — AFS §
# Preconditions explicitly sanctions either agent, and the case text's "e.g.,
# Business Analyst" is a non-binding example): the case's own literal example,
# "Business Analyst" (id 31), reliably hits known defect #1043 (Catalog modal's
# "Start Chat" button has no `isFetching` guard) when clicked immediately after
# `open_agent_by_name()` returns — confirmed live, 3/3 deterministic runs, click
# registers (no exception) but no navigation occurs and the modal stays open.
# "User Story Creator" (id 172) — the agent the analyst actually drove through
# the FULL live flow (steps 5-16) per the AFS's own precondition note — does
# not hit this race and is used here instead. Both satisfy the case's actual
# precondition ("no starters / no welcome message") identically.
CATALOG_AGENT_NAME = "User Story Creator"
TEST_MESSAGE = "execute agent"

EXPECTED_CHAT_STARTERS_EMPTY_TEXT = "No predefined chat starters – just type your request to begin."
EXPECTED_WELCOME_MESSAGE_EMPTY_TEXT = "No welcome message set – the agent will start without a greeting."


class TestAgentHubStartConversationNoStarters:
    """ELITEA-2368: Agent Hub — start conversation with a no-starters agent (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2368_agent-hub-e2e-start-conversation-with-agent-that-has-no-conversation-starters"
        "-type-and-send-message-receive-reply.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_agent_hub_start_conversation_no_starters(self, page: Page, _browser_cookies):
        """A no-starters/no-welcome-message Catalog agent can be opened, chatted
        with via "Start Chat", sent a message, and produces a visible reply —
        with the sidebar and Context Budget counter reflecting the new
        conversation."""
        agent_hub = AgentHubPage(page)
        chat = ChatPage(page)
        conversation_api = ConversationAPI(browser_cookies=_browser_cookies)
        conv_id: int | None = None

        console_errors = agent_hub.capture_console_errors()
        failed_responses: list[int] = []
        page.on("response", lambda resp: failed_responses.append(resp.status) if resp.status >= 400 else None)

        try:
            with allure.step("Step 1 — Navigate to Agent Hub"):
                agent_hub.navigate()
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

            with allure.step(
                f"Step 2 — Click on the {CATALOG_AGENT_NAME!r} agent card (shows no conversation starters)"
            ):
                assert agent_hub.get_agent_card(CATALOG_AGENT_NAME).first.is_visible(), (
                    f"Agent card {CATALOG_AGENT_NAME!r} should be visible on the Catalog page"
                )
                # open_agent_by_name() waits on the agent-details GET response
                # (.../public_application/prompt_lib/{id} -> 200) — deterministic
                # ready-signal, avoids known defect #1043's race class (AFS Axis 2).
                agent_hub.open_agent_by_name(CATALOG_AGENT_NAME, timeout=NAVIGATION_TIMEOUT)
                assert not console_errors, f"Unexpected console errors while opening the modal: {console_errors}"

            with allure.step(
                'Step 3 — Verify the modal shows the agent name and the no-starters / '
                'no-welcome-message empty-state copy (live: "CHAT STARTERS" / "Welcome Message" — '
                "case-text drift, tracked EliteaAI/elitea-testing-public#1042)"
            ):
                assert agent_hub.modal_agent_name.text_content().strip() == CATALOG_AGENT_NAME, (
                    f"Preview modal should show the agent name {CATALOG_AGENT_NAME!r}"
                )

                assert agent_hub.modal_chat_starters_section.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "CHAT STARTERS section should be visible in the preview modal"
                )
                starters_text = agent_hub.modal_chat_starters_section.text_content() or ""
                assert EXPECTED_CHAT_STARTERS_EMPTY_TEXT in starters_text, (
                    f"Expected no-starters empty-state text, got: {starters_text!r}"
                )

                assert agent_hub.modal_welcome_message_section.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "Welcome Message section should be visible in the preview modal"
                )
                welcome_text = agent_hub.modal_welcome_message_section.text_content() or ""
                assert EXPECTED_WELCOME_MESSAGE_EMPTY_TEXT in welcome_text, (
                    f"Expected no-welcome-message empty-state text, got: {welcome_text!r}"
                )
                assert not console_errors, f"Unexpected console errors while reading the modal: {console_errors}"

            with allure.step(
                'Step 4 — Click "Start Chat" (case text: "Start conversation" — same #1042 drift)'
            ):
                # Known defect EliteaAI/elitea-testing-public#1043 (already tracked,
                # explicitly names ELITEA-2368 as an affected sibling): AgentModal.jsx's
                # "Start Chat" button reads `agentDetails.version_details.*` from a
                # `useState(null)` populated by an async `getPublicApplicationDetail`
                # RTK-Query fetch; the modal's visible content (name/description/CHAT
                # STARTERS/Welcome Message) renders from the synchronously-available
                # `agent` prop, so the modal LOOKS ready before `agentDetails` actually
                # commits — clicking in that window throws an uncaught TypeError and
                # silently no-ops (confirmed live this dispatch: deterministic 0/3 nav
                # success with <=200ms post-modal-open, deterministic 3/3 success at
                # >=300ms, reproduced for BOTH "Business Analyst" id 31 and "User Story
                # Creator" id 172 — root cause is generic, not agent-specific). No DOM
                # signal distinguishes "agentDetails loaded" from "agentDetails still
                # null" (the CHAT STARTERS/Welcome Message sections render identical
                # empty-state text in both states for a no-starters agent), so this is
                # test synchronization for an unobservable async gap — not defect
                # masking; the underlying product gap stays tracked on #1043, untouched.
                page.wait_for_timeout(1000)
                agent_hub.click_start_chat(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 5 — Verify a new chat is created and the user is redirected to the Chat interface"):
                page.wait_for_url(re.compile(r"/chat"), timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_page_load()
                assert not failed_responses, f"Unexpected 4xx/5xx responses: {failed_responses}"

            with allure.step(
                'Step 6 — Verify the welcome message "Hello, [user]! What can I do for you today?" is displayed'
            ):
                assert chat.new_conversation_greeting.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "Blank-conversation greeting should be displayed in the chat area"
                )
                greeting_text = chat.new_conversation_greeting.text_content() or ""
                assert "What can I do for you today?" in greeting_text, (
                    f"Expected the standard greeting text, got: {greeting_text!r}"
                )

            with allure.step(
                f"Step 7 — Verify the agent chip for {CATALOG_AGENT_NAME!r} is visible in the message input bar"
            ):
                assert chat.is_agent_participant_in_composer(CATALOG_AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Composer should show {CATALOG_AGENT_NAME!r} as the active agent participant"
                )
                assert chat.chat_version_selector_trigger.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "Version selector chip should be visible next to the agent chip in the composer"
                )

            with allure.step("Step 8 — Verify the agent appears under the Agents section in the Participants panel"):
                chat.expand_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)
                participant_row = chat.get_participant_row_by_name(CATALOG_AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT)
                row_text = (participant_row.text_content() or "").strip()
                assert CATALOG_AGENT_NAME in row_text, (
                    f"PARTICIPANTS panel row should show {CATALOG_AGENT_NAME!r}, got: {row_text!r}"
                )
                assert not console_errors, (
                    f"Unexpected console errors after opening the Participants panel: {console_errors}"
                )

            with allure.step("Step 16a — Before sending: no Context Budget panel/indicator renders yet"):
                assert not chat.is_context_budget_panel_visible(), (
                    "Context Budget panel should NOT be visible before any message has been sent"
                )

            with allure.step(
                f"Step 9-10 — Click the message input, type {TEST_MESSAGE!r}, verify the send button activates"
            ):
                initial_count = chat.get_message_count()
                chat.message_input.click()
                chat.message_input.fill(TEST_MESSAGE)
                assert chat.message_input.input_value() == TEST_MESSAGE, (
                    "Typed text should appear in the message input field"
                )
                assert chat.is_send_button_enabled(), (
                    "Send button should become enabled once text is present in the input"
                )

            with allure.step("Step 11 — Click the send button"):
                chat.send_button.click(force=True)
                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=NAVIGATION_TIMEOUT)
                match = re.search(r"/chat/(\d+)", page.url)
                assert match, f"Conversation id should appear in the URL after Send, got: {page.url}"
                conv_id = int(match.group(1))

            with allure.step("Step 12 — Verify the user message is displayed in the chat as sent"):
                chat.wait_for_message_count(initial_count + 1, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_message_count() > initial_count, (
                    "Message count should increase once the user's message is sent"
                )

            with allure.step(
                'Step 13 — Verify the agent begins processing ("Thought for X secs" indicator is shown)'
            ):
                chat.answer_thought_accordion.wait_for(state="visible", timeout=AI_RESPONSE_TIMEOUT)
                thought_text = chat.answer_thought_accordion.text_content() or ""
                assert "Thought for" in thought_text, (
                    f"Expected 'Thought for N secs' text, got: {thought_text!r}"
                )

            with allure.step("Step 14 — Verify the agent reply is received and displayed in the chat"):
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                reply_text = chat.get_last_message_text()
                assert reply_text.strip(), "Agent reply text should be non-empty"
                assert not console_errors, f"Unexpected console errors during the AI exchange: {console_errors}"

            with allure.step('Step 15 — Verify the new conversation appears in the sidebar under "Today"'):
                assert chat.is_conversation_in_group(conv_id, group="today", timeout=UI_ELEMENT_TIMEOUT), (
                    f"Conversation {conv_id} should appear under the sidebar's 'Today' date-group"
                )

            with allure.step("Step 16b — After the exchange: the Context Budget counter updates to a real value"):
                chat.wait_for_context_budget_panel(timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_context_budget_messages_count("2", timeout=UI_ELEMENT_TIMEOUT)
                messages_count = chat.get_context_budget_messages_count()
                assert messages_count == "2", (
                    f"Context Budget messages count should read '2' after the exchange, got: {messages_count!r}"
                )

            with allure.step("Side-channel check — zero console errors, zero 4xx/5xx across the whole flow"):
                assert not console_errors, f"Unexpected console errors: {console_errors}"
                assert not failed_responses, f"Unexpected 4xx/5xx responses: {failed_responses}"
        finally:
            console_errors.stop()
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                    logger.info("Cleaned up conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Failed to clean up conversation %s: %s", conv_id, exc)
