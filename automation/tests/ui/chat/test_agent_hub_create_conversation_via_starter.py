"""Agent Hub — create a new conversation by clicking a conversation starter
INSIDE the preview modal (ELITEA-2093).

Opens a Catalog agent that has predefined conversation starters, verifies the
preview modal's CHAT STARTERS section, clicks a starter tile INSIDE the modal
(NOT the "Start Chat" button), verifies the modal closes and the user lands
directly on `/chat` with the composer pre-populated with the clicked starter's
text, verifies the agent chip + version + all three starter tiles render in
the chat area, sends the pre-populated message, verifies the reply, and
verifies the new conversation auto-names and appears under the sidebar's
"Today" date-group.

Spec: test-specs/agent-hub/l2_agent-hub-create-conversation-via-starter_ELITEA-2093.md

Reuses ``AgentHubPage`` (Catalog listing + preview modal, ELITEA-2356/2075)
and ``ChatPage`` (composer, sidebar date-groups, message history —
ELITEA-2075/2091/2167/2168) as-is, PLUS one new page-object METHOD added this
dispatch: ``AgentHubPage.click_modal_starter_item()`` — no new testid, the
underlying ``catalog-agent-modal-starter-item`` testid already exists
(``chat-conversation-starter-tile`` in the chat area likewise pre-existing,
both added by the ELITEA-2369 dispatch).

Case-text drift (CLARIFICATION, already tracked, not re-filed — AFS §
Known Defects Found): "CONVERSATION STARTERS" -> live product reads
"CHAT STARTERS". Tracked in EliteaAI/elitea-testing-public#1042, which
already names the ELITEA-2368/2369 siblings as affected — this case hits the
identical drift on the identical component (``AgentConversationStarters.jsx``).

Unlike the ELITEA-2368/2369 siblings' "Start Chat" button click, clicking a
starter tile INSIDE the modal needs NO known-defect-#1043 timing workaround:
``AgentConversationStarterItem`` only renders once the modal's async
``agentDetails`` fetch has committed, so this test's own step 3 (waiting for
a starter item to become visible) already clears that same async gap before
step 4's click ever fires.
"""

import logging
import re

import allure
import pytest
from api import ConversationAPI
from pages.agent_hub_page import AgentHubPage
from pages.chat_page import ChatPage
from playwright.sync_api import Page, expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 90_000  # live LLM completion — AFS Automation Hints (well under 60s observed)

CATALOG_AGENT_NAME = "Assistant for ELITEA Documentation"
STARTER_TEXT = "Tell me about Elitea"
EXPECTED_STARTER_COUNT = 3
EXPECTED_VERSION_TEXT = "v1.0"


class TestAgentHubCreateConversationViaStarter:
    """ELITEA-2093: Agent Hub — create new conversation via a modal conversation starter (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2093_create-new-conversation-via-agent-hub-using-a-conversation-starter.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_agent_hub_create_conversation_via_starter(self, page: Page, _browser_cookies):
        """Clicking a conversation-starter tile inside the Catalog agent preview
        modal closes the modal, navigates straight to a new chat with the
        starter pre-populated, and the agent + starters render correctly in
        the chat area before send."""
        agent_hub = AgentHubPage(page)
        chat = ChatPage(page)
        conversation_api = ConversationAPI(browser_cookies=_browser_cookies)
        conv_id: int | None = None

        console_errors = agent_hub.capture_console_errors()
        failed_responses: list[int] = []
        page.on("response", lambda resp: failed_responses.append(resp.status) if resp.status >= 400 else None)

        try:
            with allure.step("Step 1 — Navigate to Agent HUB from the left sidebar"):
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
                # ready-signal (AFS Axis 2).
                agent_hub.open_agent_by_name(CATALOG_AGENT_NAME, timeout=NAVIGATION_TIMEOUT)
                assert not console_errors, f"Unexpected console errors while opening the modal: {console_errors}"

            with allure.step(
                'Step 3 — Verify the CHAT STARTERS section shows clickable starter buttons '
                '(case text: "CONVERSATION STARTERS" — drift, tracked EliteaAI/elitea-testing-public#1042)'
            ):
                assert agent_hub.modal_chat_starters_section.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "CHAT STARTERS section should be visible in the preview modal"
                )
                # AgentModal.jsx's CHAT STARTERS section renders from the async
                # `agentDetails` fetch state — waiting for a real starter item
                # (rather than reading the section immediately) both proves
                # "multiple options display" AND clears the same async gap known
                # defect #1043 has to work around separately for the Start Chat
                # button click (AFS step 4 note) — no extra wait needed at step 4.
                agent_hub.get_modal_starter_items().first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                modal_starter_count = agent_hub.get_modal_starter_items().count()
                assert modal_starter_count == EXPECTED_STARTER_COUNT, (
                    f"Expected {EXPECTED_STARTER_COUNT} starter items in the modal, got {modal_starter_count}"
                )

            with allure.step(f'Step 4 — Click the {STARTER_TEXT!r} starter button'):
                agent_hub.click_modal_starter_item(STARTER_TEXT, timeout=UI_ELEMENT_TIMEOUT)
                # AgentModal.jsx's onSelectStarter fires navigate() + onClose()
                # synchronously off this single click — modal closes AND the
                # user lands on /chat, no separate "Start Chat" click involved.
                agent_hub.modal_dialog.wait_for(state="hidden", timeout=NAVIGATION_TIMEOUT)
                page.wait_for_url(re.compile(r"/chat"), timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_page_load()
                assert not failed_responses, f"Unexpected 4xx/5xx responses: {failed_responses}"

            with allure.step("Step 5 — Verify the selected starter text is pre-populated in the message input field"):
                # NewConversationView.jsx populates the composer from a
                # setTimeout(..., 100) inside a useEffect (onSendStarter() ->
                # chatInput.current.setValue(starter)) — a synchronous read right
                # after wait_for_page_load() (which only waits for the input to be
                # visible+editable, not for this delayed state update) races an
                # empty value (confirmed live this dispatch: reproduced deterministically
                # with a bare .input_value() read). Playwright's auto-retrying
                # to_have_value() polls past the ~100ms window instead of reading once.
                expect(chat.message_input).to_have_value(STARTER_TEXT, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 6 — Verify the agent name and version are in the input bar and all three "
                "starter prompts are displayed as clickable suggestions"
            ):
                assert chat.is_agent_participant_in_composer(CATALOG_AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Composer should show {CATALOG_AGENT_NAME!r} as the active agent participant"
                )
                assert chat.chat_version_selector_trigger.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "Version selector chip should be visible next to the agent chip in the composer"
                )
                version_text = chat.chat_version_selector_trigger.text_content() or ""
                assert EXPECTED_VERSION_TEXT in version_text, (
                    f"Expected version chip to read {EXPECTED_VERSION_TEXT!r}, got: {version_text!r}"
                )
                # NewConversationView.jsx renders the SAME conversation_starters list
                # as the modal — same content-ready caveat as step 3 (wait for a real
                # tile, not the generic page-load signal).
                chat.get_chat_starter_tiles().first.wait_for(state="visible", timeout=NAVIGATION_TIMEOUT)
                chat_tile_count = chat.get_chat_starter_tiles().count()
                assert chat_tile_count == EXPECTED_STARTER_COUNT, (
                    f"Expected {EXPECTED_STARTER_COUNT} starter tiles in the chat area, got {chat_tile_count}"
                )
                assert not console_errors, (
                    f"Unexpected console errors after landing on the pre-populated chat: {console_errors}"
                )

            initial_count = chat.get_message_count()

            with allure.step("Step 7 — Click the Send button"):
                # Auto-retrying wait rather than a single is_enabled() read — the
                # composer's disabledSend prop depends on selectedParticipant state
                # that settles asynchronously (same 100ms setTimeout window as step
                # 5's message_input race), so a single synchronous read can catch it
                # mid-flap even though the button is visibly rendered.
                expect(chat.send_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)
                # Deliberately NOT force=True here (unlike the ELITEA-2368/2369
                # siblings' Send click): force bypasses Playwright's actionability
                # wait, and this flow's disabledSend can still be mid-flap for a
                # brief window right after the starter click lands (participant +
                # starter both populate off the SAME 100ms setTimeout, unlike the
                # siblings where the agent had already settled well before Send was
                # clicked). Confirmed live this dispatch: force=True clicked a
                # button that visually read enabled but silently no-op'd
                # (sendQuestion()'s own `!disabledSend` guard still gated it),
                # reproduced deterministically; a plain (non-force) click, which
                # waits for the element to be actionable/stable, sent correctly on
                # every live retry.
                chat.send_button.click()
                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=NAVIGATION_TIMEOUT)
                match = re.search(r"/chat/(\d+)", page.url)
                assert match, f"Conversation id should appear in the URL after Send, got: {page.url}"
                conv_id = int(match.group(1))

                chat.wait_for_message_count(initial_count + 1, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_message_text_at(initial_count).strip() == STARTER_TEXT, (
                    "The user's sent message should be the exact pre-populated starter text"
                )

                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                reply_text = chat.get_last_message_text()
                assert reply_text.strip(), "Agent reply text should be non-empty"
                assert not console_errors, f"Unexpected console errors during the AI exchange: {console_errors}"

            with allure.step(
                'Step 8 — Verify a new entry appears in Today, resolving to a real (non-"Naming") title'
            ):
                chat.wait_for_naming_label_to_resolve()
                assert chat.is_conversation_in_group(conv_id, group="today", timeout=UI_ELEMENT_TIMEOUT), (
                    f"Conversation {conv_id} should appear under the sidebar's 'Today' date-group"
                )
                title_text = (chat.get_conversation_item_in_group(conv_id, group="today").text_content() or "").strip()
                assert title_text, "Sidebar conversation entry should have a non-empty title"
                assert "Naming" not in title_text, (
                    f"Conversation title should have resolved past the 'Naming' placeholder, got: {title_text!r}"
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
