"""Chat — add/remove an agent participant mid-conversation, conversation
starters render/clear, click-a-starter-to-send (ELITEA-2177/2178/2465).

Three separate cases sharing one `/chat/{id}` existing-conversation surface
(NOT the Agent Hub / embedded-agent-detail surfaces ELITEA-2369/1886 already
cover — different entry point: the composer's "+ → Agents" flow on an
already-open conversation):

- ELITEA-2177 (l2, medium): add an agent with starters, hover a truncated
  starter for its tooltip, click a starter to populate (not send), edit,
  send, verify the agent's reply + Thinking accordion + model chip.
- ELITEA-2178 (l2, medium): removing that agent clears its starter tiles,
  restores the default LLM, drops the Agents section from PARTICIPANTS, and
  leaves prior conversation history untouched — verified live AND after a
  full reload.
- ELITEA-2465 (l1, high): the same underlying add-agent-and-send-via-starter
  flow as ELITEA-2177, decomposed into 15 fine-grained verification points
  (default LLM before add, gear+X icons, PARTICIPANTS Agents-section row,
  processing indicator as its own check, LLM label as its own check).

Specs:
- test-specs/chat-interface/l2_add-agent-with-starters-to-conversation_ELITEA-2177.md
- test-specs/chat-interface/l2_remove-agent-clears-conversation-starters_ELITEA-2178.md
- test-specs/chat-interface/l1_add-agent-with-starters-and-send-via-starter_ELITEA-2465.md

Case-text drifts (CLARIFICATION, not filed — AFS § Test Data / § Known
Defects, live-confirmed by the analyst):
- The case-family's own example agent name "Claude B" does not exist in
  this environment — a disposable per-test agent is created instead
  (`AgentAPI.create_agent_full()`).
- ELITEA-2178's "Remove agent?" dialog reads "...agent from **chat**?" —
  the case text says "...from **conversation**?". Live wording is correct/
  current; asserted below as-is.
- The case-family's own short example starter ("here is your task: Explain
  Exponential Backoff", 48 chars) does NOT visually truncate at this
  environment's tile width, so it never triggers the hover tooltip — a
  second, deliberately long throwaway starter is used for the
  tooltip-specific assertion (AFS § Test Data).

Test-data payload note (implementer decision, not a scope/observable
change): the disposable agent's `llm_settings.reasoning_effort` uses the
already-proven "medium" value (same shape as `api.client._default_llm_settings()`)
rather than omitting the field as the AFS's own literal Test Data snippet
shows. Both routes avoid the AFS's documented gotcha (`reasoning_effort:
"none"` 400s the participants-ADD endpoint though agent-CREATE accepts it
silently) — "medium" is additionally the value
`test_agent_embedded_chat_conversation_starter_chips.py` (ELITEA-1886)
already documents as live-confirmed-safe for an actual chat/predict round
trip (that file's own docstring: "none" leaves the composer populated but
the Send POST never fires for a real predict), which THIS case's flow also
exercises (Send → real agent reply), so it is the more proven choice here.

New page-object surface added this dispatch (all additive, ``ChatPage``):
- ``hover_agent_participant_row(agent_id)`` — read-only sibling of
  ``remove_agent_participant()``, stops after the hover so the caller can
  assert the revealed "Remove agent" button's accessible name before ever
  clicking it (ELITEA-2178 step 2). Mirrors the existing
  ``hover_participant_user_row()`` vs ``open_remove_user_dialog()`` shape.
- ``hover_chat_starter_tile(match_text)`` — read-only sibling of
  ``click_chat_starter_tile()``, for the hover-tooltip assertion.
- ``chat_switch_to_model_button`` — new ``LocatorDescriptor`` for the
  composer's "X" icon (case step 4, ELITEA-2465's own subject).
- ``chat_starter_tile_tooltip_content`` — new ``LocatorDescriptor`` for the
  starter tile's hover tooltip popper content.

Testid gaps filled this implementation (``add-data-testid``, pushed to
``automation/testids``):
- ``chat-switch-to-model-button`` on `AgentEditorPanel.jsx`'s "switch to
  model" `IconButton` (both render branches) — a genuine gap, confirmed via
  source (EliteaAI/EliteaUI@c1905706).
- ``chat-conversation-starter-tile-tooltip`` on the starter tile's MUI
  Tooltip popper content, via a new `slotProps.tooltip` wire on the shared
  `EllipsisTextWithTooltip` (`src/components/ConversationStarters.jsx`) —
  the compliant MUI `slotProps` channel; a raw `[role="tooltip"]` selector
  is not a sanctioned #579 exception for our own MUI usage
  (EliteaAI/EliteaUI@c7e7f88e).
- ``chat-conversation-starter-tile`` itself needed NO new wiring — it
  already renders on this `/chat/{id}` mid-conversation-add surface
  (`ChatConversationStarters.jsx`'s call site, wired ELITEA-1886/
  EliteaAI/EliteaUI@afb48435), confirmed live. A stale in-repo comment
  claiming that call site was "intentionally left unwired" (written before
  the ELITEA-1886 dispatch) was corrected in `chat_page.py` this dispatch.
"""

import logging
import re
import uuid

import allure
import pytest
from components.mui import Dialog
from config import settings
from pages.chat_page import ChatPage
from playwright.sync_api import Page, expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000

# Case-family's own literal example starter (portable, agent-identity-independent).
CASE_STARTER_TEXT = "here is your task: Explain Exponential Backoff"

# Deliberately long (>150 chars) — forces genuine visual truncation at this
# environment's tile width (AFS § Test Data: the short literal above does
# NOT truncate) so the hover-tooltip assertion has a real truncated tile to
# hover over and verify against.
LONG_STARTER_TEXT = (
    "This is a deliberately long conversation starter text, crafted "
    "specifically to overflow the starter tile's rendered width in this "
    "environment so the hover tooltip assertion has a genuinely truncated "
    "tile to hover over and verify the full text against."
)

SETUP_MESSAGE_TEXT = "setup message"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as the sibling chat tests' equivalent filter (e.g.
    ``test_chat_folder_creation_custom_name_and_cancel.py``) — a
    ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken, unrelated to this flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


def _starters_agent_payload(name: str, starters: list[str]) -> dict:
    """Disposable starters-bearing agent payload shared by all three cases.

    See module docstring's "Test-data payload note" for why
    ``reasoning_effort: "medium"`` is used instead of the AFS's own literal
    snippet (which omits the field).
    """
    return {
        "name": name[:32],
        "description": f"Auto-created for test {name}",
        "type": "interface",
        "versions": [{
            "name": "base",
            "tags": [],
            "instructions": "You are a test agent. Answer briefly, in one short sentence.",
            "variables": [],
            "tools": [],
            "llm_settings": {
                "max_tokens": -1,
                "temperature": None,
                "reasoning_effort": "medium",
                "model_name": settings.default_model_name,
                "model_project_id": settings.default_model_project_id,
            },
            "conversation_starters": starters,
            "agent_type": "openai",
            "welcome_message": "",
            "meta": {"step_limit": 25},
        }],
    }


def _open_new_conversation(chat: ChatPage, timeout: int = NAVIGATION_TIMEOUT) -> None:
    """Click +Chat and confirm a genuinely NEW conversation opened.

    Infrastructure-class flake guard (issue #1082) — same idiom as the
    sibling chat suite's own ``_open_blank_conversation()``
    (`test_team_users_mention_and_remove_participants.py`; per-file
    duplication is this suite's established pattern for this helper, not a
    shared cross-file import).
    """
    last_reason = "unknown"
    for attempt in range(3):
        chat.click_create_conversation(timeout=timeout)
        try:
            chat.new_conversation_greeting.wait_for(state="visible", timeout=5000)
            return
        except Exception:
            last_reason = "greeting never appeared"
            logger.warning(
                "New-conversation greeting not visible after +Chat click "
                "(attempt %d) — retrying (see _open_new_conversation docstring)",
                attempt + 1,
            )
    raise AssertionError(f"Could not open a new conversation after 3 attempts: {last_reason}")


def _conv_id_from_url(page: Page) -> int | None:
    match = re.search(r"/chat/(\d+)", page.url)
    return int(match.group(1)) if match else None


class TestChatAddAgentWithStartersToConversation:
    """ELITEA-2177: Chat – Add Agent with Conversation Starters to Conversation (l2, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2177_chat-add-agent-with-conversation-starters-to-conversation.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_add_agent_with_starters_to_conversation(self, page: Page, agent_api, conversation_api):
        """Add a starters-bearing agent mid-conversation, hover a truncated
        starter for its tooltip, click a starter to populate (not send),
        edit, send, verify the reply + Thinking accordion + model chip.

        Steps (AFS
        test-specs/chat-interface/l2_add-agent-with-starters-to-conversation_ELITEA-2177.md):
        1. + → Agents → select the disposable agent — chip/badge/starters shown.
        2. Hover a genuinely-truncated starter — tooltip shows full text.
        3. Click the case's own literal starter — populates the input.
        4. Text editable; agent chip/version still shown.
        5. Click Send.
        6. Agent responds with Thinking accordion + model chip.
        """
        chat = ChatPage(page)
        agent_id: int | None = None
        conv_id: int | None = None

        console_messages = []
        page_errors: list[str] = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        def _on_pageerror(exc):
            page_errors.append(str(exc))

        page.on("console", _on_console)
        page.on("pageerror", _on_pageerror)

        try:
            with allure.step(
                "Setup — create a disposable agent with conversation starters; open a new conversation"
            ):
                agent_name = f"autotest_2177_{uuid.uuid4().hex[:8]}"
                agent = agent_api.create_agent_full(
                    _starters_agent_payload(agent_name, [CASE_STARTER_TEXT, LONG_STARTER_TEXT])
                )
                agent_id = agent["id"]
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                _open_new_conversation(chat, timeout=NAVIGATION_TIMEOUT)
                conv_id = _conv_id_from_url(page)

            with allure.step(
                "Step 1 — Navigate to Chats, open a conversation, click +, select Agents, select the agent"
            ):
                chat.add_agent_participant(agent_name, timeout=UI_ELEMENT_TIMEOUT)
                if conv_id is None:
                    conv_id = _conv_id_from_url(page)
                expect(chat.switch_participant_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.switch_participant_button).to_contain_text(agent_name)
                expect(chat.chat_version_selector_trigger).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_participants_badge_visible(section="agents", timeout=UI_ELEMENT_TIMEOUT), (
                    "PARTICIPANTS panel's Agents badge should appear once the agent is added"
                )
                assert chat.get_participants_badge_count(section="agents") == "1", (
                    "Agents badge should read '1' after adding one agent participant"
                )
                chat.get_chat_starter_tiles().first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                tile_count = chat.get_chat_starter_tiles().count()
                assert 1 <= tile_count <= 4, (
                    f"Expected 1-4 conversation starter tiles above the input (case: max 4), got {tile_count}"
                )
                assert not console_messages, f"Unexpected console errors: {console_messages}"
                assert not page_errors, f"Unexpected page errors: {page_errors}"

            with allure.step(
                "Step 2 — Verify starters are clickable pills; hover a genuinely-truncated "
                "starter and confirm the tooltip shows the full text"
            ):
                tooltip_source_text = chat.hover_chat_starter_tile(
                    LONG_STARTER_TEXT[:30], timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.chat_starter_tile_tooltip_content).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                tooltip_text = (chat.chat_starter_tile_tooltip_content.text_content() or "").strip()
                assert tooltip_text == tooltip_source_text, (
                    f"Tooltip should show the full (untruncated) starter text, expected "
                    f"{tooltip_source_text!r}, got {tooltip_text!r}"
                )
                # Reset residual hover so it can't interfere with step 3's click.
                page.mouse.move(0, 0)

            initial_count = chat.get_message_count()

            with allure.step(f"Step 3 — Click the conversation starter {CASE_STARTER_TEXT!r}"):
                starter_text = chat.click_chat_starter_tile(CASE_STARTER_TEXT, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 4 — Verify text is editable and agent name/version still shown in input bar"):
                assert chat.message_input.input_value() == starter_text, (
                    f"Message input should be populated with the clicked starter's exact text "
                    f"{starter_text!r}, got {chat.message_input.input_value()!r}"
                )
                assert chat.is_send_button_enabled(), (
                    "Send button should become enabled once the starter text populates the input"
                )
                expect(chat.switch_participant_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.chat_version_selector_trigger).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 5 — Click Send"):
                # Plain (non-force) click — a force=True click right after a
                # starter populates the composer can silently no-op: the
                # participant-add + composer-populate settle asynchronously,
                # and force=True bypasses Playwright's own actionability wait
                # that would otherwise line up with that settle (memory:
                # chat_send_button_force_click_race.md, ELITEA-2093).
                chat.send_button.click()
                chat.wait_for_message_count(initial_count + 1, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_message_text_at(initial_count).strip() == starter_text, (
                    "The user's sent message should be the exact starter text that was clicked"
                )
                sent_message_full_text = chat.messages_container.nth(initial_count).text_content() or ""
                assert agent_name in sent_message_full_text, (
                    f"Sent message should be directed 'to {agent_name}', got: {sent_message_full_text!r}"
                )

            with allure.step("Step 6 — Verify agent responds with reasoning/Thinking section and LLM model label"):
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                thought_text = chat.answer_thought_accordion.text_content() or ""
                assert "Thought for" in thought_text, f"Expected 'Thought for N secs' text, got: {thought_text!r}"
                model_chip_text = (chat.answer_model_chip.text_content() or "").strip()
                assert model_chip_text, "LLM model chip should show a non-empty model name"
                reply_text = chat.get_last_message_text()
                assert reply_text.strip(), "Agent reply text should be non-empty"

            with allure.step("Side-channel check — zero console/page errors across the whole flow"):
                assert not console_messages, f"Unexpected console errors: {console_messages}"
                assert not page_errors, f"Unexpected page errors: {page_errors}"
        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                    logger.info("Cleaned up conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Failed to clean up conversation %s: %s", conv_id, exc)
            if agent_id:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleaned up agent %s", agent_id)
                except Exception as exc:
                    logger.warning("Failed to clean up agent %s: %s", agent_id, exc)


class TestChatRemoveAgentClearsConversationStarters:
    """ELITEA-2178: Chat – Remove Agent from Conversation Clears Conversation Starters (l2, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2178_chat-remove-agent-from-conversation-clears-conversation-starters.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_remove_agent_clears_conversation_starters(self, page: Page, agent_api, conversation_api):
        """Removing an agent participant clears its starter tiles, restores
        the default LLM, drops the Agents section from PARTICIPANTS, and
        leaves prior conversation history untouched (verified live AND
        after a full reload).

        Steps (AFS
        test-specs/chat-interface/l2_remove-agent-clears-conversation-starters_ELITEA-2178.md):
        Setup. Seed a conversation with one prior message exchange, then add
             the starters-bearing agent — establishes the case's own step 1
             precondition ("agent in the conversation with starters visible").
        1. Verify agent chip + starters visible.
        2. Hover the trash bin icon — 'Remove agent' accessible name revealed.
        3. Click it — 'Remove agent?' modal appears.
        4. Verify modal text (live wording: "...agent from chat?" — case text
           drift, CLARIFICATION).
        5. Click Remove — modal closes, AGENTS section removed, default LLM
           restored.
        6. Starters gone.
        7. Conversation history intact (incl. after a full reload).
        """
        chat = ChatPage(page)
        agent_id: int | None = None
        conv_id: int | None = None

        console_messages = []
        page_errors: list[str] = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        def _on_pageerror(exc):
            page_errors.append(str(exc))

        page.on("console", _on_console)
        page.on("pageerror", _on_pageerror)

        try:
            with allure.step(
                "Setup — create a disposable agent with a conversation starter; open a new "
                "conversation and send one message so there is prior history to protect"
            ):
                agent_name = f"autotest_2178_{uuid.uuid4().hex[:8]}"
                agent = agent_api.create_agent_full(
                    _starters_agent_payload(agent_name, [CASE_STARTER_TEXT])
                )
                agent_id = agent["id"]
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                _open_new_conversation(chat, timeout=NAVIGATION_TIMEOUT)

                chat.send_message(SETUP_MESSAGE_TEXT)
                chat.wait_for_ai_response(initial_count=0, timeout=AI_RESPONSE_TIMEOUT)
                # The conversation only gets a real id once the first message
                # is sent (bare /chat until then) — capture it AFTER send.
                conv_id = _conv_id_from_url(page)
                pre_removal_count = chat.get_message_count()
                pre_removal_messages = [
                    chat.get_message_text_at(i).strip() for i in range(pre_removal_count)
                ]

            with allure.step(
                "Step 1 — Add the agent (with starters) as a participant; verify agent "
                "chip and starters visible"
            ):
                chat.add_agent_participant(agent_name, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.switch_participant_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.switch_participant_button).to_contain_text(agent_name)
                chat.get_chat_starter_tiles().first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_chat_starter_tiles().count() >= 1, (
                    "At least one starter tile should render after the agent is added"
                )

            with allure.step(
                "Step 2 — In the PARTICIPANTS AGENTS section, hover over the trash bin icon next to the agent"
            ):
                remove_btn = chat.hover_agent_participant_row(agent_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(remove_btn).to_have_accessible_name("Remove agent")

            with allure.step("Step 3 — Click the trash bin icon"):
                remove_btn.click(force=True)
                dialog = Dialog.wait_for(page, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 4 — Verify modal text (live wording: '...agent from chat?' — case text "
                "says '...from conversation?', CLARIFICATION not a defect)"
            ):
                dialog_text = (dialog.text_content() or "").strip()
                expected_body = f"Are you sure to remove the {agent_name} agent from chat?"
                assert expected_body in dialog_text, (
                    f"Expected dialog to contain {expected_body!r}, got: {dialog_text!r}"
                )

            with allure.step(
                "Step 5 — Click Remove; verify AGENTS section removed from PARTICIPANTS "
                "and default LLM restored"
            ):
                Dialog.click_button(dialog, "Remove")
                chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
                dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                # Genuine wait for the negative transition — a bare
                # `not is_participants_badge_visible()` right after a click
                # can read "still visible" a moment before the DOM update
                # lands (positive-existence wait can't assert a negative
                # transition).
                chat.wait_for_participants_badge_absent(section="agents", timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.model_selector_name).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert (chat.model_selector_name.text_content() or "").strip(), (
                    "Default LLM label should be non-empty again after the agent is removed"
                )

            with allure.step("Step 6 — Verify conversation starters no longer displayed"):
                assert chat.get_chat_starter_tiles().count() == 0, (
                    "No starter tiles should remain once the agent is removed"
                )

            with allure.step(
                "Step 7 — Verify conversation history intact, including after a full page reload"
            ):
                post_removal_messages = [
                    chat.get_message_text_at(i).strip() for i in range(chat.get_message_count())
                ]
                assert post_removal_messages == pre_removal_messages, (
                    "Prior conversation history should be unchanged immediately after agent removal"
                )
                page.reload()
                chat.wait_for_page_load()
                assert chat.get_message_count() == pre_removal_count, (
                    "Message count should still match the pre-agent-add baseline after reload"
                )
                chat.wait_for_participants_badge_absent(section="agents", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_chat_starter_tiles().count() == 0, (
                    "No starter tiles should remain after a full reload"
                )

            with allure.step("Side-channel check — zero console/page errors across the whole flow"):
                assert not console_messages, f"Unexpected console errors: {console_messages}"
                assert not page_errors, f"Unexpected page errors: {page_errors}"
        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                    logger.info("Cleaned up conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Failed to clean up conversation %s: %s", conv_id, exc)
            if agent_id:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleaned up agent %s", agent_id)
                except Exception as exc:
                    logger.warning("Failed to clean up agent %s: %s", agent_id, exc)


class TestChatAddAgentWithStartersAndSendViaStarter:
    """ELITEA-2465: Chat – Add agent with conversation starters and use a starter to send message (l1, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2465_chat-add-agent-with-conversation-starters-and-use-a-starter-to-send-message.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_add_agent_with_starters_and_send_via_starter(self, page: Page, agent_api, conversation_api):
        """Same underlying flow as ELITEA-2177, at finer granularity (15
        case steps): default LLM visible pre-add; agent+version chips, gear
        icon, and X icon all visible post-add; PARTICIPANTS panel's Agents
        section shows the participant; starters render (<=4) with
        truncation-conditional tooltips; clicking a starter pre-fills (not
        auto-sends) an editable field; sending produces a "to {agent}"
        message, a processing/Thinking indicator, an LLM model label, and a
        full, error-free response.

        Steps (AFS
        test-specs/chat-interface/l1_add-agent-with-starters-and-send-via-starter_ELITEA-2465.md):
        1. Navigate to Chats, open/create a conversation.
        2. Default LLM shown in the input bar (pre-add).
        3. + → Agents → select the disposable agent.
        4. Input bar shows agent name+version, gear icon, X icon.
        5. PARTICIPANTS panel's AGENTS section shows the agent.
        6. Starter tiles shown, max 4.
        7. Hover a truncated starter — tooltip shows full text.
        8. Click a conversation starter.
        9. Full starter text inserted, editable.
        10. Click Send.
        11. Message sent, directed "to [Agent Name]".
        12. Agent begins processing — generation indicator shown.
        13. LLM model label shown on the response.
        14. "Thinking" section visible and expanding (same element as step 12).
        15. Full response received, no error.
        """
        chat = ChatPage(page)
        agent_id: int | None = None
        conv_id: int | None = None

        console_messages = []
        page_errors: list[str] = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        def _on_pageerror(exc):
            page_errors.append(str(exc))

        page.on("console", _on_console)
        page.on("pageerror", _on_pageerror)

        try:
            with allure.step(
                "Setup — create a disposable agent with conversation starters"
            ):
                agent_name = f"autotest_2465_{uuid.uuid4().hex[:8]}"
                agent = agent_api.create_agent_full(
                    _starters_agent_payload(agent_name, [CASE_STARTER_TEXT, LONG_STARTER_TEXT])
                )
                agent_id = agent["id"]

            with allure.step("Step 1 — Navigate to the Chats section and open/create a conversation"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                _open_new_conversation(chat, timeout=NAVIGATION_TIMEOUT)
                conv_id = _conv_id_from_url(page)

            with allure.step("Step 2 — Verify the default LLM is shown in the input bar"):
                expect(chat.model_selector_name).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert (chat.model_selector_name.text_content() or "").strip(), (
                    "Default LLM label should be non-empty before any agent is added"
                )

            with allure.step(
                "Step 3 — Click + and select Agents, then select the disposable agent with "
                "conversation starters configured"
            ):
                chat.add_agent_participant(agent_name, timeout=UI_ELEMENT_TIMEOUT)
                if conv_id is None:
                    conv_id = _conv_id_from_url(page)
                assert not console_messages, f"Unexpected console errors: {console_messages}"
                assert not page_errors, f"Unexpected page errors: {page_errors}"

            with allure.step(
                "Step 4 — Verify the input bar shows the agent name and version, a gear icon, and an X icon"
            ):
                expect(chat.switch_participant_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.switch_participant_button).to_contain_text(agent_name)
                expect(chat.chat_version_selector_trigger).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.chat_version_selector_trigger).to_contain_text("base")
                expect(chat.chat_participant_settings_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.chat_switch_to_model_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 5 — Verify the PARTICIPANTS panel shows the AGENTS section with the agent"):
                popper = chat.open_participants_popover(section="agents", timeout=UI_ELEMENT_TIMEOUT)
                assert "Agents" in (popper.text_content() or ""), (
                    "Participants popover should show an 'Agents' heading"
                )
                unique_id = f"application_{agent_id}_{settings.elitea_project_id}"
                row = popper.locator(chat.PARTICIPANT_ROW.format(unique_id))
                # The row renders a "Participant Name" loading-skeleton
                # placeholder before its real content settles — a one-shot
                # `wait_for(visible)` + `text_content()` read can catch that
                # placeholder. `to_contain_text` is a web-first assertion
                # that retries until the REAL name lands (or times out).
                expect(row).to_contain_text(agent_name, timeout=UI_ELEMENT_TIMEOUT)
                chat.dismiss_participants_popover()

            with allure.step("Step 6 — Verify conversation starter buttons are displayed, maximum 4"):
                chat.get_chat_starter_tiles().first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                tile_count = chat.get_chat_starter_tiles().count()
                assert 1 <= tile_count <= 4, (
                    f"Expected 1-4 conversation starter tiles (case: max 4), got {tile_count}"
                )

            with allure.step(
                "Step 7 — Hover a starter button with truncated text and verify the tooltip shows the full text"
            ):
                tooltip_source_text = chat.hover_chat_starter_tile(
                    LONG_STARTER_TEXT[:30], timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.chat_starter_tile_tooltip_content).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                tooltip_text = (chat.chat_starter_tile_tooltip_content.text_content() or "").strip()
                assert tooltip_text == tooltip_source_text, (
                    f"Tooltip should show the full (untruncated) starter text, expected "
                    f"{tooltip_source_text!r}, got {tooltip_text!r}"
                )
                page.mouse.move(0, 0)

            initial_count = chat.get_message_count()

            with allure.step(f"Step 8 — Click on the conversation starter {CASE_STARTER_TEXT!r}"):
                starter_text = chat.click_chat_starter_tile(CASE_STARTER_TEXT, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 9 — Verify the full starter text is inserted and the field is editable"):
                assert chat.message_input.input_value() == starter_text, (
                    f"Message input should be populated with the clicked starter's exact text "
                    f"{starter_text!r}, got {chat.message_input.input_value()!r}"
                )
                assert chat.is_send_button_enabled(), (
                    "Send button should become enabled once the starter text populates the input"
                )

            with allure.step("Step 10 — Click the Send button"):
                # Plain (non-force) click — see the Step 5 comment in the
                # ELITEA-2177 test above (same race, same fix).
                chat.send_button.click()
                chat.wait_for_message_count(initial_count + 1, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 11 — Verify the message is sent and directed 'to [Agent Name]'"):
                assert chat.get_message_text_at(initial_count).strip() == starter_text, (
                    "The user's sent message should be the exact starter text that was clicked"
                )
                sent_message_full_text = chat.messages_container.nth(initial_count).text_content() or ""
                assert agent_name in sent_message_full_text, (
                    f"Sent message should be directed 'to {agent_name}', got: {sent_message_full_text!r}"
                )

            with allure.step("Step 12 — Verify the agent begins processing with a response generation indicator"):
                chat.answer_thought_accordion.wait_for(state="visible", timeout=AI_RESPONSE_TIMEOUT)
                # MUI's Accordion root (this testid) carries the global state
                # class "Mui-expanded" while expanded — `aria-expanded` itself
                # lives on the nested AccordionSummary button, a different
                # element, so the class check is the correct signal on THIS
                # testid'd element (confirmed via @mui/material source:
                # generateUtilityClass's globalStateClasses map).
                expect(chat.answer_thought_accordion).to_have_class(
                    re.compile(r"Mui-expanded"), timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 13 — Verify the LLM model label is shown on the agent's response"):
                model_chip_text = (chat.answer_model_chip.text_content() or "").strip()
                assert model_chip_text, "LLM model chip should show a non-empty model name"

            with allure.step('Step 14 — Verify the "Thinking" section is visible and expanding during generation'):
                # Same live element as step 12 (`chat-answer-thought-accordion`) —
                # case text's "Thinking section" = this project's "Thought for N
                # secs" accordion (AFS Automation Hints). Re-assert both the text
                # and the same "Mui-expanded" class signal step 12 used.
                thought_text = chat.answer_thought_accordion.text_content() or ""
                assert "Thought for" in thought_text, f"Expected 'Thought for N secs' text, got: {thought_text!r}"
                expect(chat.answer_thought_accordion).to_have_class(
                    re.compile(r"Mui-expanded"), timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 15 — Verify the agent's full response is received and displayed with no error"):
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                reply_text = chat.get_last_message_text()
                assert reply_text.strip(), "Agent reply text should be non-empty"
                assert not console_messages, f"Unexpected console errors: {console_messages}"
                assert not page_errors, f"Unexpected page errors: {page_errors}"
        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                    logger.info("Cleaned up conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Failed to clean up conversation %s: %s", conv_id, exc)
            if agent_id:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleaned up agent %s", agent_id)
                except Exception as exc:
                    logger.warning("Failed to clean up agent %s: %s", agent_id, exc)
