"""UI Test for ELITEA-2092 — Create New Conversation via Agent HUB — Start
Conversation (No Conversation Starters).

Verifies that starting a conversation from the Agent HUB with an agent that
has no predefined conversation starters opens the chat with the agent
pre-loaded, the agent responds correctly, and the new conversation is
auto-named under "Today".

Spec: test-specs/hubs/l2_agent-hub-start-conversation-no-starters_ELITEA-2092.md

Case-text drift (clarification `#1042`, not a product defect): the case's
step 3 ("CONVERSATION STARTERS" section) and step 4 ("Start conversation"
button) literal text don't match live product copy ("CHAT STARTERS" /
"Start Chat") — this test asserts the live copy (reverse-masking guard).

Known defect `#1043` (does not block this case — non-deterministic timing
race, confirmed live during implementation, still open): the Agent HUB
"Start Chat" button reads `agentDetails.version_details` from React state
that an async `useEffect`-triggered fetch populates, with no loading guard
and no DOM-observable "still loading" signal (the empty conversation-
starters state renders identically whether or not the fetch has resolved —
`AgentModal.jsx`'s `agentDetails?.version_details?.conversation_starters ||
[]`). Clicking in that window throws an uncaught `TypeError: Cannot read
properties of null (reading 'version_details')` and silently no-ops (no
navigation, modal stays open). `CatalogPage.click_start_chat()` retries the
click itself, gated on the actual outcome (the modal closing) rather than a
guessed delay — see its docstring for the declared-improvisation reasoning
and the empirical evidence ruling out a fixed-wait fix. The resulting
`pageerror` is filtered from this test's own side-channel check (below) the
same way `test_open_conversation_today_section.py` filters its own
pre-existing, already-documented artifact — this is a KNOWN, filed,
non-blocking race, not a masked new defect.

No product defects were found beyond `#1043` (pre-existing) during this
implementation. No new testids were required — all 7 handles this case
touches landed on `automation/testids` during analysis
(EliteaAI/EliteaUI@ae7d2703, plus pre-existing chat composer/conversation
testids).
"""

import logging
import re

import allure
import pytest
from pages.catalog_page import CatalogPage
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.agent_hub")

pytestmark = [pytest.mark.ui, pytest.mark.agent_hub, pytest.mark.chat, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 30_000
NAMING_TIMEOUT = 10_000

# Test data (AFS § Test Data — reuse-existing): a stable, published agent
# with NO conversation_starters configured, and a fixed first message.
AGENT_NAME = "Business Analyst"
FIRST_MESSAGE = "hi"


def _is_known_1043_race(text: str) -> bool:
    """Filter the pre-existing, already-filed `#1043` race's uncaught
    exception text (see module docstring). `CatalogPage.click_start_chat()`
    retries past it — this only stops it from also failing the test's
    generic side-channel check when it fires on a recovered attempt.
    """
    return "version_details" in text and "Cannot read properties of null" in text


class TestAgentHubStartConversationNoStarters:
    """ELITEA-2092: Create New Conversation via Agent HUB — Start
    Conversation (No Conversation Starters) (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2092_agent-hub-start-conversation-no-starters.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_start_conversation_from_agent_hub_no_starters(self, page):
        """Start a conversation from the Agent HUB with an agent that has no
        conversation starters; verify the agent pre-loads, responds, and the
        conversation is auto-named under Today.

        Steps (AFS
        test-specs/hubs/l2_agent-hub-start-conversation-no-starters_ELITEA-2092.md):
        1. Navigate to chat, then to the Agent HUB via the sidebar "Catalog" entry.
        2. Click the "Business Analyst" agent card; verify the detail modal.
        3. Verify the "CHAT STARTERS" section shows the no-starters empty state.
        4. Click "Start Chat"; verify the modal closes and chat opens.
        5. Verify the composer shows the agent name + version + clear button.
        6. Send "hi"; verify the AI reply with the agent shown as respondent.
        7. Verify the new conversation is auto-named under "Today".
        """
        chat = ChatPage(page)
        catalog = CatalogPage(page)

        # Registered before Step 1 so console errors from the whole flow are
        # captured. The known, filed `#1043` race (module docstring) is
        # filtered — CatalogPage.click_start_chat() already retries past it,
        # so it must not ALSO fail this generic side-channel check; any
        # OTHER page error still fails it for real.
        console_messages = []
        page_errors: list[str] = []

        def _on_console(msg):
            if msg.type == "error":
                console_messages.append(msg)

        def _on_pageerror(exc):
            text = str(exc)
            if not _is_known_1043_race(text):
                page_errors.append(text)

        page.on("console", _on_console)
        page.on("pageerror", _on_pageerror)

        with allure.step(
            "Step 1 — Navigate to chat, then to the Agent HUB via the "
            "sidebar 'Catalog' entry"
        ):
            chat.navigate_to_chat()
            catalog.navigate_to_agent_hub(timeout=NAVIGATION_TIMEOUT)
            assert "/elitea-catalog" in page.url, (
                f"Expected the Agent HUB URL after clicking 'Catalog', got: {page.url}"
            )

        with allure.step(
            "Step 2 — Click the 'Business Analyst' agent card; verify the "
            "detail modal opens"
        ):
            card = catalog.find_agent_card_by_name(AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT).first
            agent_id = catalog.get_agent_id_from_card(card)
            assert agent_id, f"Could not resolve a numeric agent id for {AGENT_NAME!r}"

            catalog.open_agent_detail_modal(agent_id, timeout=UI_ELEMENT_TIMEOUT)
            assert catalog.agent_detail_modal.is_visible(), (
                "Agent detail modal should be visible after clicking the agent card"
            )
            modal_text = catalog.agent_detail_modal.text_content() or ""
            assert AGENT_NAME in modal_text, (
                f"Agent detail modal should show the agent name {AGENT_NAME!r}, "
                f"got: {modal_text[:200]!r}"
            )

        with allure.step(
            "Step 3 — Verify the 'CHAT STARTERS' section shows the "
            "no-predefined-starters empty state (case text: "
            "'CONVERSATION STARTERS' — clarification #1042)"
        ):
            assert catalog.modal_starters_header.is_visible(), (
                "Conversation-starters section header should be visible in the modal"
            )
            header_text = catalog.modal_starters_header.text_content() or ""
            assert "CHAT STARTERS" in header_text, (
                f"Starters section header should read 'CHAT STARTERS' (live "
                f"copy), got: {header_text!r}"
            )

            assert catalog.modal_starters_empty.is_visible(), (
                "No-predefined-starters empty-state message should be visible "
                "for an agent with no conversation starters"
            )
            empty_text = catalog.modal_starters_empty.text_content() or ""
            assert "No predefined conversation starters" in empty_text, (
                f"Empty-state message should announce no predefined starters, "
                f"got: {empty_text!r}"
            )

        with allure.step(
            "Step 4 — Click 'Start Chat' (case text: 'Start conversation' — "
            "same clarification #1042); verify the modal closes and chat opens"
        ):
            catalog.click_start_chat(timeout=NAVIGATION_TIMEOUT)
            assert "/chat" in page.url, (
                f"Expected to land back on /chat after 'Start Chat', got: {page.url}"
            )
            assert not catalog.agent_detail_modal.is_visible(), (
                "Agent detail modal should be closed after 'Start Chat'"
            )
            chat.wait_for_page_load()

        with allure.step(
            "Step 5 — Verify the composer shows the agent name, version, "
            "and clear-participant button"
        ):
            chat.switch_participant_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            participant_text = chat.switch_participant_button.text_content() or ""
            assert AGENT_NAME in participant_text, (
                f"Composer active-participant button should show {AGENT_NAME!r}, "
                f"got: {participant_text!r}"
            )

            assert chat.chat_version_selector_trigger.is_visible(), (
                "Composer version-selector trigger should be visible once an "
                "agent participant with versions is active"
            )
            version_text = chat.chat_version_selector_trigger.text_content() or ""
            assert version_text.strip(), (
                "Composer version-selector trigger should show a non-empty version"
            )

            assert chat.chat_clear_participant_button.is_visible(), (
                "Composer clear-participant ('x') button should be visible "
                "next to the active-participant chip"
            )

        with allure.step('Step 6 — Type "hi" and click Send; verify the AI reply'):
            initial_count = chat.get_message_count()
            chat.send_message(FIRST_MESSAGE, use_enter=False)
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
            chat.wait_for_message_content_stable(timeout=AI_RESPONSE_TIMEOUT)

            message_count = chat.get_message_count()
            assert message_count >= initial_count + 2, (
                f"Expected at least a user message + an AI reply after Send "
                f"(started at {initial_count}, now {message_count})"
            )

            ai_message = chat.messages_container.nth(initial_count + 1)
            ai_message_text = ai_message.text_content() or ""
            assert AGENT_NAME in ai_message_text, (
                f"AI reply should show {AGENT_NAME!r} as the respondent, "
                f"got: {ai_message_text[:200]!r}"
            )
            ai_body = ChatPage._extract_message_body(ai_message)
            assert ai_body.strip(), "AI reply body should be non-empty"

        with allure.step(
            "Step 7 — Verify a new conversation entry appears under 'Today', "
            "auto-named via the naming spinner's present-then-resolved transition"
        ):
            match = re.search(r"/chat/(\d+)", page.url)
            assert match, (
                f"Conversation id should appear in the URL after sending the "
                f"first message, got: {page.url}"
            )
            conv_id = match.group(1)

            assert chat.is_conversation_group_visible("today", timeout=UI_ELEMENT_TIMEOUT), (
                "'Today' date-group heading should be visible in the sidebar"
            )
            assert chat.is_conversation_in_group(conv_id, "today", timeout=UI_ELEMENT_TIMEOUT), (
                f"New conversation {conv_id} should render under the Today "
                "group specifically"
            )

            # The spinner may already have resolved by the time we check (the
            # naming call is fast on DEV — confirmed live ~1.5-2s) — only
            # assert the presence check when we actually catch it, then always
            # assert the resolved, non-placeholder final state.
            try:
                chat.wait_for_conversation_naming_spinner(timeout=2000)
                logger.info("Caught the naming spinner while transient")
            except Exception:
                logger.info("Naming spinner already resolved by check time")

            chat.wait_for_conversation_naming_spinner_to_resolve(timeout=NAMING_TIMEOUT)

            final_title = chat.get_conversation_item_text(conv_id, timeout=UI_ELEMENT_TIMEOUT)
            assert final_title and final_title != "Naming", (
                f"New conversation should resolve to a non-empty, non-placeholder "
                f"auto-generated title, got: {final_title!r}"
            )

        with allure.step(
            "Side-channel check — no unexpected console errors or uncaught "
            "exceptions across the full flow"
        ):
            assert not console_messages and not page_errors, (
                f"Unexpected side-channel errors: "
                f"console={[m.text for m in console_messages]!r} "
                f"page_errors={page_errors!r}"
            )
