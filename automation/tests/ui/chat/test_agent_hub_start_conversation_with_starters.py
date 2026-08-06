"""Agent Hub — E2E start conversation with a starters-bearing agent, use a
starter to send a message, receive reply (ELITEA-2369).

Opens a Catalog agent that HAS predefined conversation starters and a
configured welcome message, verifies the preview modal's CHAT STARTERS
section (multiple starter items) and Welcome Message text, starts a chat via
"Start Chat", verifies the SAME starters render as clickable tiles in the
chat area plus the agent chip + Participants panel entry, clicks a starter
tile to populate (not auto-send) the composer, sends it, and verifies the
user message, the "Thought for N secs" processing indicator with tool-call
chips, and the AI reply.

Spec: test-specs/agent-hub/l3_agent-hub-start-conversation-with-starters_ELITEA-2369.md

Reuses ``AgentHubPage`` (Catalog listing + preview modal, ELITEA-2356/2075)
and ``ChatPage`` (composer, participants panel, message history —
ELITEA-2075/2167/2168) as-is, PLUS two new locators added this dispatch
(``AgentHubPage.get_modal_starter_items()`` / ``ChatPage.get_chat_starter_tiles()``
+ ``ChatPage.click_chat_starter_tile()``) backed by two new testids:
``catalog-agent-modal-starter-item`` (``AgentConversationStarterItem.jsx``,
feature-scoped, hardcoded) and ``chat-conversation-starter-tile`` (a new
caller-supplied ``testId`` prop on the SHARED ``EllipsisTextWithTooltip``,
wired ONLY at ``NewConversationView.jsx``'s call site — the new-conversation
landing view this case's flow actually renders through, confirmed via live
exploration (AFS Known Defects amendment corrects the AFS's original,
mistaken call site). Its sibling call site in ``ChatConversationStarters.jsx``
(consumed only by the embedded ``ChatBox.jsx`` surface) is a different,
not-yet-analysed flow and is intentionally left unwired per canon ruling #511).

Case-text drifts (CLARIFICATION, already tracked, not re-filed — AFS §
Known Defects Found): "CONVERSATION STARTERS" / "Start conversation" ->
live product reads "CHAT STARTERS" / "Start Chat"; "WELCOME MESSAGE"
(all-caps) -> live product reads "Welcome Message" (title-case). Tracked in
EliteaAI/elitea-testing-public#1042, which explicitly names ELITEA-2369 as
an affected sibling.

Known defect (already tracked, not re-filed — same #1043 as ELITEA-2368):
clicking "Start Chat" before the modal's async ``agentDetails`` fetch commits
throws an uncaught TypeError and silently no-ops — mitigated with the same
documented 1s wait immediately before the click.

Apostrophe caveat (AFS § Test Data): the live starter text uses a
typographic ("curly") apostrophe the case text's own literal example doesn't.
Assertions below deliberately avoid hardcoding the apostrophe character —
filtering/matching uses an apostrophe-free substring, and the populated-input
assertion (step 12) compares against the EXACT text read off the clicked
tile rather than a literal.
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

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 90_000  # live LLM completion w/ tool calls — AFS Automation Hints (30-90s)

CATALOG_AGENT_NAME = "API Testing Buddy"
CATALOG_AGENT_DESCRIPTION_SNIPPET = "Tests API by Provided swagger or postman collection"
WELCOME_MESSAGE_AGENT_SNIPPET = "your API Testing Buddy"
WELCOME_MESSAGE_INTENT_SNIPPET = "ready to validate documentation"
EXPECTED_STARTER_COUNT = 4

# Apostrophe-free substring — avoids the straight-vs-curly-apostrophe drift
# documented in the AFS (Test Data) when filtering by has_text.
STARTER_MATCH_TEXT = "uploaded a Swagger spec"


class TestAgentHubStartConversationWithStarters:
    """ELITEA-2369: Agent Hub — start conversation with a starters-bearing agent (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2369_agent-hub-e2e-start-conversation-with-agent-that-has-convers.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_agent_hub_start_conversation_with_starters(self, page: Page, _browser_cookies):
        """A starters-bearing Catalog agent can be opened, its starters used to
        populate and send a message via "Start Chat", and the send produces a
        visible "Thought for N secs" processing indicator with tool-call chips
        plus a reply."""
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
                f"Step 2 — Click on the {CATALOG_AGENT_NAME!r} agent card (has predefined chat starters)"
            ):
                assert agent_hub.get_agent_card(CATALOG_AGENT_NAME).first.is_visible(), (
                    f"Agent card {CATALOG_AGENT_NAME!r} should be visible on the Catalog page"
                )
                # open_agent_by_name() waits on the agent-details GET response
                # (.../public_application/prompt_lib/{id} -> 200) — deterministic
                # ready-signal, avoids known defect #1043's race class (AFS Axis 2).
                agent_hub.open_agent_by_name(CATALOG_AGENT_NAME, timeout=NAVIGATION_TIMEOUT)
                assert not console_errors, f"Unexpected console errors while opening the modal: {console_errors}"

            with allure.step("Step 3 — Verify the detail modal opens displaying agent name and description"):
                assert agent_hub.modal_agent_name.text_content().strip() == CATALOG_AGENT_NAME, (
                    f"Preview modal should show the agent name {CATALOG_AGENT_NAME!r}"
                )
                description_text = agent_hub.modal_description.text_content() or ""
                assert CATALOG_AGENT_DESCRIPTION_SNIPPET in description_text, (
                    f"Expected description to contain {CATALOG_AGENT_DESCRIPTION_SNIPPET!r}, got: {description_text!r}"
                )
                assert not console_errors, f"Unexpected console errors while reading the modal: {console_errors}"

            with allure.step(
                'Step 4 — Verify the CHAT STARTERS section displays multiple predefined starter options '
                '(case text: "CONVERSATION STARTERS" — drift, tracked EliteaAI/elitea-testing-public#1042)'
            ):
                assert agent_hub.modal_chat_starters_section.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "CHAT STARTERS section should be visible in the preview modal"
                )
                # AgentModal.jsx's CHAT STARTERS section renders from
                # `agentDetails?.version_details?.conversation_starters` (the async
                # fetch state) with NO synchronous `agent`-prop fallback (confirmed
                # via source) — the SAME agentDetails-not-yet-committed race as known
                # defect #1043 (AFS § Known Defects), here manifesting as a transient
                # "No predefined chat starters" empty state instead of a TypeError.
                # open_agent_by_name()'s wait on modal_show_instructions_link is not a
                # sufficient ready-signal for THIS data either (that link renders
                # unconditionally) — wait for a real starter item instead of reading
                # the section immediately.
                agent_hub.get_modal_starter_items().first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                modal_starter_count = agent_hub.get_modal_starter_items().count()
                assert modal_starter_count == EXPECTED_STARTER_COUNT, (
                    f"Expected {EXPECTED_STARTER_COUNT} starter items in the modal, got {modal_starter_count}"
                )

            with allure.step(
                'Step 5 — Verify the Welcome Message section displays the agent\'s configured welcome text '
                '(case text: "WELCOME MESSAGE" all-caps — same #1042 drift)'
            ):
                assert agent_hub.modal_welcome_message_section.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "Welcome Message section should be visible in the preview modal"
                )
                welcome_text = agent_hub.modal_welcome_message_section.text_content() or ""
                assert "Welcome!" in welcome_text, (
                    f"Expected welcome text to contain 'Welcome!', got: {welcome_text!r}"
                )
                assert WELCOME_MESSAGE_AGENT_SNIPPET in welcome_text, (
                    f"Expected welcome text to contain {WELCOME_MESSAGE_AGENT_SNIPPET!r}, got: {welcome_text!r}"
                )
                assert WELCOME_MESSAGE_INTENT_SNIPPET in welcome_text, (
                    f"Expected welcome text to contain {WELCOME_MESSAGE_INTENT_SNIPPET!r}, got: {welcome_text!r}"
                )
                assert not console_errors, f"Unexpected console errors while reading the modal: {console_errors}"

            with allure.step(
                'Step 6 — Click "Start Chat" (case text: "Start conversation" — same #1042 drift)'
            ):
                # Known defect EliteaAI/elitea-testing-public#1043 (already tracked,
                # explicitly names ELITEA-2369 as an affected sibling — same root
                # cause the no-starters sibling ELITEA-2368 hit): AgentModal.jsx's
                # "Start Chat" button reads `agentDetails.version_details.*` from a
                # `useState(null)` populated by an async fetch; the modal's visible
                # content (incl. CHAT STARTERS/Welcome Message) renders from the
                # synchronously-available `agent` prop, so it LOOKS ready before
                # `agentDetails` actually commits — clicking in that window throws
                # an uncaught TypeError and silently no-ops (confirmed live this
                # dispatch: deterministic success at >=1s post-modal-open). Test
                # synchronization for an unobservable async gap, not defect
                # masking — the underlying product gap stays tracked on #1043.
                page.wait_for_timeout(1000)
                agent_hub.click_start_chat(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 7 — Verify a new chat is created and the user is redirected to the Chat interface"):
                page.wait_for_url(re.compile(r"/chat"), timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_page_load()
                assert not failed_responses, f"Unexpected 4xx/5xx responses: {failed_responses}"

            with allure.step(
                "Step 8 — Verify the conversation starters are displayed as clickable tiles in the chat area"
            ):
                # New-conversation content (starters, composer, participants) loads
                # asynchronously after the /chat redirect — ChatPage.wait_for_page_load()'s
                # message_input-visible signal can resolve while the chat pane is still on
                # its loading spinner (confirmed live this dispatch). Wait for a real
                # starter tile rather than trusting the generic page-load signal alone —
                # same "wait for real content" pattern as step 4's agentDetails race.
                chat.get_chat_starter_tiles().first.wait_for(state="visible", timeout=NAVIGATION_TIMEOUT)
                chat_tile_count = chat.get_chat_starter_tiles().count()
                assert chat_tile_count == EXPECTED_STARTER_COUNT, (
                    f"Expected {EXPECTED_STARTER_COUNT} starter tiles in the chat area, got {chat_tile_count}"
                )

            with allure.step(
                f"Step 9 — Verify the agent chip for {CATALOG_AGENT_NAME!r} v1.1 is visible in the message input bar"
            ):
                assert chat.is_agent_participant_in_composer(CATALOG_AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Composer should show {CATALOG_AGENT_NAME!r} as the active agent participant"
                )
                assert chat.chat_version_selector_trigger.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "Version selector chip should be visible next to the agent chip in the composer"
                )
                version_text = chat.chat_version_selector_trigger.text_content() or ""
                assert "v1.1" in version_text, f"Expected version chip to read 'v1.1', got: {version_text!r}"

            with allure.step("Step 10 — Verify the agent appears under the AGENTS section in the Participants panel"):
                chat.expand_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)
                participant_row = chat.get_participant_row_by_name(CATALOG_AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT)
                row_text = (participant_row.text_content() or "").strip()
                assert CATALOG_AGENT_NAME in row_text, (
                    f"PARTICIPANTS panel row should show {CATALOG_AGENT_NAME!r}, got: {row_text!r}"
                )
                assert not console_errors, (
                    f"Unexpected console errors after opening the Participants panel: {console_errors}"
                )

            initial_count = chat.get_message_count()

            with allure.step(
                "Step 11 — Click one of the conversation starter tiles "
                "(the Swagger-spec starter, matched apostrophe-tolerantly)"
            ):
                starter_text = chat.click_chat_starter_tile(STARTER_MATCH_TEXT, timeout=UI_ELEMENT_TIMEOUT)
                assert starter_text, "Clicked starter tile should have non-empty text"

            with allure.step("Step 12 — Verify the selected starter text is populated into the message input field"):
                assert chat.message_input.input_value() == starter_text, (
                    f"Message input should be populated with the clicked starter's exact text {starter_text!r}, "
                    f"got: {chat.message_input.input_value()!r}"
                )

            with allure.step("Step 13 — Verify the send button becomes active"):
                assert chat.is_send_button_enabled(), (
                    "Send button should become enabled once the starter text populates the input"
                )

            with allure.step("Step 14 — Click the send button"):
                chat.send_button.click(force=True)
                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=NAVIGATION_TIMEOUT)
                match = re.search(r"/chat/(\d+)", page.url)
                assert match, f"Conversation id should appear in the URL after Send, got: {page.url}"
                conv_id = int(match.group(1))

            with allure.step("Step 15 — Verify the message is sent and displayed in the chat"):
                chat.wait_for_message_count(initial_count + 1, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_message_count() > initial_count, (
                    "Message count should increase once the starter message is sent"
                )
                # Read the SPECIFIC user-message slot (initial_count), not `.last` — a
                # transient AI placeholder ("Waking the agent…") can already occupy
                # `.last` by the time this reads, confirmed live this dispatch.
                assert chat.get_message_text_at(initial_count).strip() == starter_text, (
                    "The user's sent message should be the exact starter text that was sent"
                )

            with allure.step(
                'Step 16 — Verify the agent begins processing ("Thought for X secs" indicator is shown) '
                "and tools used are visible"
            ):
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                thought_text = chat.answer_thought_accordion.text_content() or ""
                assert "Thought for" in thought_text, f"Expected 'Thought for N secs' text, got: {thought_text!r}"

                tool_chip_count = chat.answer_tool_chip.count()
                assert tool_chip_count >= 1, (
                    f"Expected at least 1 tool-call chip in the Thought accordion, got {tool_chip_count}"
                )

                reply_text = chat.get_last_message_text()
                assert reply_text.strip(), "Agent reply text should be non-empty"
                assert not console_errors, f"Unexpected console errors during the AI exchange: {console_errors}"

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
