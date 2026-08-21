"""Agent Hub — start conversation creates a new chat and redirects to the
Chat page, with the welcome message displayed (ELITEA-2360).

Opens a Catalog agent's detail modal, starts a chat via "Start Chat", and
verifies the SPA redirects to `/chat` with the blank-conversation welcome
greeting visible.

Spec: test-specs/agent-hub/l2_agent-hub-start-conversation-creates-new-chat-and-redirects_ELITEA-2360.md

Reuses ``AgentHubPage`` (Catalog listing + preview modal, ELITEA-2356/2075)
and ``ChatPage.new_conversation_greeting`` (ELITEA-2167/2368) as-is — no new
page-object work; every locator this case touches already exists.

Case-text drift (CLARIFICATION, already tracked, not re-filed — AFS §
Known Defects / EliteaAI/elitea-testing-public#1042, which explicitly names
the agent-hub start-conversation family as affected siblings): case text
"Start conversation" -> live product reads "Start Chat". Asserted against
the live copy, not the case's literal text.

Root-caused this dispatch (debug task ahead of this implementation, AFS §
Known Defects/Amendments): known defect
EliteaAI/elitea-testing-public#1043 — the Catalog agent-preview modal's
"Start Chat" button reads `agentDetails.version_details.*` from a
`useState(null)` populated by an async fetch; clicking before it commits
throws an uncaught TypeError inside the click handler (before
`navigate()` ever runs) and silently no-ops — the modal just stays open,
no exception surfaces to Playwright. Confirmed live via a scripted repro
matching this suite's own fixtures: 0/3 navigations succeed at <=200ms
post-modal-open, 3/3 succeed at >=300ms. This was the root cause blocking
three prior implementation attempts at this case family (ELITEA-2360/61/62)
— each omitted the wait at the call site. Fixed by moving the wait INSIDE
``AgentHubPage.click_start_chat()`` (see its docstring for the full
analysis) so every caller is protected, not just ones that remember to add
it inline. This is test synchronization for an unobservable async gap, not
defect masking — the underlying product gap (no ``disabled={isFetching}``
guard on the button) stays tracked, untouched, on #1043.
"""

import re

import allure
import pytest
from api import ConversationAPI
from pages.agent_hub_page import AgentHubPage
from pages.chat_page import ChatPage
from playwright.sync_api import Page

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

CATALOG_AGENT_NAME = "User Story Creator"


class TestAgentHubStartConversationCreatesNewChat:
    """ELITEA-2360: Agent Hub — start conversation creates new chat and redirects (l2, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2360.md",
        "onetest-ai Test Case link",
    )
    def test_agent_hub_start_conversation_creates_new_chat(self, page: Page, _browser_cookies):
        """Starting a conversation from a Catalog agent's detail modal creates a
        new chat and redirects the user to the Chat interface with the
        blank-conversation welcome message displayed."""
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

            with allure.step(f"Step 2 — Click on the {CATALOG_AGENT_NAME!r} agent card to open the detail modal"):
                assert agent_hub.get_agent_card(CATALOG_AGENT_NAME).first.is_visible(), (
                    f"Agent card {CATALOG_AGENT_NAME!r} should be visible on the Catalog page"
                )
                # open_agent_by_name() waits on the agent-details GET response
                # (.../public_application/prompt_lib/{id} -> 200) — deterministic
                # ready-signal, but NOT sufficient on its own to safely click Start
                # Chat (known defect #1043 — see module docstring). click_start_chat()
                # now owns the extra wait internally.
                agent_hub.open_agent_by_name(CATALOG_AGENT_NAME, timeout=NAVIGATION_TIMEOUT)
                assert not console_errors, f"Unexpected console errors while opening the modal: {console_errors}"

            with allure.step("Step 3 — Verify the detail modal opens displaying the agent name"):
                assert agent_hub.modal_agent_name.text_content().strip() == CATALOG_AGENT_NAME, (
                    f"Preview modal should show the agent name {CATALOG_AGENT_NAME!r}"
                )
                assert not console_errors, f"Unexpected console errors while reading the modal: {console_errors}"

            with allure.step(
                'Step 4 — Click "Start Chat" (case text: "Start conversation" — drift, '
                "tracked EliteaAI/elitea-testing-public#1042)"
            ):
                agent_hub.click_start_chat(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 5 — Verify a new chat conversation is created and the user is "
                "redirected to the Chat interface"
            ):
                page.wait_for_url(re.compile(r"/chat"), timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_page_load()
                assert not failed_responses, f"Unexpected 4xx/5xx responses: {failed_responses}"

            with allure.step(
                'Step 6 — Verify the chat welcome message "Hello, [username]! What can I do for you today?" '
                "is displayed"
            ):
                chat.new_conversation_greeting.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                greeting_text = chat.new_conversation_greeting.text_content() or ""
                assert "Hello" in greeting_text, f"Expected greeting to contain 'Hello', got: {greeting_text!r}"
                assert "What can I do for you today" in greeting_text, (
                    f"Expected greeting to contain 'What can I do for you today', got: {greeting_text!r}"
                )
                assert not console_errors, f"Unexpected console errors on the Chat page: {console_errors}"

            with allure.step("Side-channel check — zero console errors, zero 4xx/5xx across the whole flow"):
                assert not console_errors, f"Unexpected console errors: {console_errors}"
                assert not failed_responses, f"Unexpected 4xx/5xx responses: {failed_responses}"
        finally:
            console_errors.stop()
            # A conversation may not have been created yet if the flow failed before
            # navigation; only attempt cleanup once a conversation id is on the URL.
            match = re.search(r"/chat/(\d+)", page.url)
            if match:
                conv_id = int(match.group(1))
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                except Exception:
                    pass
