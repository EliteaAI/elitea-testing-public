"""UI Test for ELITEA-2095 — Open Existing Conversation from Today Section.

Verifies that clicking a conversation from the Today section displays the
full message history with scroll, an active input field, the correct
model/agent name, Context Budget counters, and the correct PARTICIPANTS
panel participant.

Spec: test-specs/chat-interface/l3_open-existing-conversation-today-section_ELITEA-2095.md

Environment note (AFS § Preconditions — reverse-masking guard): the Team
project ("Elitea Testing Team", id 471) is used rather than the default
Private project (399) — CollapsedPerticapantsList.jsx's
``showUsersSection = !isPrivateProject`` unconditionally omits the whole
Users/owner badge for the account's own Private project, so case step 8
("PARTICIPANTS panel shows the correct participant") is only genuinely
assertable for a plain default-LLM conversation in a non-Private project.

No product defects were found during analysis. During implementation, two
genuine product defects were found and filed:

- EliteaAI/elitea-testing-public#691 — sending the first UI message to a
  conversation that exists server-side with ZERO messages silently creates
  a brand-new conversation instead of using the existing one. Worked around
  by seeding the test conversation via the UI's own "+Chat" flow instead of
  ``ConversationAPI.create_conversation()`` (see AFS § Test Data "AMENDED"
  note).
- EliteaAI/elitea-testing-public#692 — a conversation created via "+Chat"
  stays permanently marked "active" in the sidebar after navigating away,
  silently no-op'ing any later click back onto it. Worked around with a
  ``page.reload()`` right after navigating away (Step 2).

Everything else was a missing testid (added via ``add-data-testid``, see
PR description).
"""

import logging
import re
import time

import allure
import pytest
from api import ConversationAPI
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
AI_RESPONSE_TIMEOUT = 30_000
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Team project — the ONLY environment where a plain default-LLM conversation's
# PARTICIPANTS panel shows a USERS section for the account's own identity
# (see module docstring / AFS § Preconditions).
TEAM_PROJECT_ID = "471"

FIRST_MESSAGE = "Give me a short 5-item numbered list of fun facts about octopuses."
SECOND_MESSAGE = "Thanks! Now give me 5 more facts, this time about jellyfish."


def _is_known_project_471_secrets_403(msg) -> bool:
    """Filter the pre-existing, already-documented project-471 ``secrets`` 403.

    Project 471 ("Elitea Testing Team") surfaces a ``403 Forbidden`` on
    ``GET .../secrets/secrets/default/471`` on every page load, regardless
    of any action taken — an environment/permission-scoping artifact of
    that specific project, not a symptom of anything this case's
    automation touches. Already documented in the ``ELITEA-1893`` AFS
    § Test Data / § Handles Reference and reconfirmed live in this case's
    own AFS § Network Behavior. Matched on both the message text and the
    request location URL (same idiom as ``test_credential_create.py``'s
    ``_is_known_554_warning``) so a genuinely NEW 403 elsewhere isn't
    accidentally swallowed by a text-only match.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default/471" in (text + location_url)


def _expected_initials(name: str) -> str:
    """Replicate EliteaUI's getInitials() (src/common/utils.jsx) for cross-check.

    First letter of the first word + first letter of the last word,
    uppercased (e.g. "Test Bot" -> "TB").
    """
    parts = name.split(" ")
    return (parts[0][0] + parts[-1][0]).upper()


class TestOpenConversationFromTodaySection:
    """ELITEA-2095: Open Existing Conversation from Today Section (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2095_open-existing-conversation-from-today-section.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_open_conversation_from_today_section(self, page, _browser_cookies):
        """Open an existing conversation from the Today section and verify
        full history, active input, model name, Context Budget, and the
        correct PARTICIPANTS panel participant.

        Steps (AFS
        test-specs/chat-interface/l3_open-existing-conversation-today-section_ELITEA-2095.md):
        1. Navigate to chat; confirm default project; switch to the Team
           project (471).
        2. Navigate away from the freshly-seeded conversation so the
           subsequent click is a genuine "open EXISTING conversation" action.
        3. Locate the Today heading; verify it and the conversation render
           under it specifically.
        4. Click the conversation from the Today list; verify URL + title.
        5. Verify full message history (4 messages, in original order).
        6. Verify genuine scroll (scrollHeight > clientHeight + real scroll).
        7. Verify the message input is active/ready.
        8. Verify the model name is displayed.
        9. Verify the Context Budget widget (tokens, Messages=4, Summaries=0).
        10. Verify the PARTICIPANTS panel shows the correct (single) user.
        """
        team_conversation_api = ConversationAPI(
            browser_cookies=_browser_cookies, project_id=TEAM_PROJECT_ID,
        )
        conv_id = None
        conv_name = None
        other_conv_id = None
        chat = ChatPage(page)

        # Registered before Step 1 so console errors from every step
        # (project switch, +Chat seeding, navigation, all 10 case steps)
        # are captured — not just from a later step. AFS Expected Results
        # require "no console errors specific to this flow"; the known,
        # already-documented project-471 secrets 403 (AFS § Network
        # Behavior) is filtered so it can't mask a genuinely NEW error on
        # the same project.
        #
        # `page.on("console", ...)` alone is NOT sufficient — established
        # the same day on the sibling ELITEA-2094 PR (#688): an UNCAUGHT
        # JS exception never reaches the "console" event, only
        # `page.on("pageerror", ...)` does. Both are wired here for the
        # same reason: "console" for the repo's established side-channel
        # idiom, "pageerror" so a genuine uncaught exception anywhere in
        # this flow isn't silently missed. The known project-471 secrets
        # 403 is a console/network log, not a pageerror, so it needs no
        # filtering on the pageerror side.
        console_messages = []
        page_errors: list[str] = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_project_471_secrets_403(msg):
                console_messages.append(msg)

        def _on_pageerror(exc):
            page_errors.append(str(exc))

        page.on("console", _on_console)
        page.on("pageerror", _on_pageerror)

        try:
            with allure.step(
                "Step 1 — Navigate to chat; confirm default project; "
                "switch to the Team project (471)"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                default_project_text = chat.get_selected_project_text()
                assert default_project_text, (
                    "Project selector should show a non-empty default/"
                    "last-active project before switching"
                )

                chat.switch_project(TEAM_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)

                switched_project_text = chat.get_selected_project_text()
                assert "Elitea Testing Team" in switched_project_text, (
                    "Project selector should show 'Elitea Testing Team' "
                    f"after switching, got: {switched_project_text!r}"
                )

            # ------------------------------------------------------------------
            # Setup — seed a second, throwaway conversation via the API so
            # Step 2 (navigate away) has a real OTHER conversation to click
            # to, independent of whatever ambient conversations may or may
            # not already exist in project 471. click_first_other_
            # conversation() only needs to find ANY conversation besides the
            # one under test — confirmed live (test_navigate_between_
            # conversations in test_conversation_management.py) that an
            # API-created, zero-message conversation renders in the sidebar
            # and is clickable. No message is ever sent to it, so defect
            # #691 (which fires only on SENDING the first message to a
            # zero-message conversation, never on creating/clicking one)
            # does not apply here. Cleaned up in the same `finally` block as
            # the seeded conversation under test.
            # ------------------------------------------------------------------
            other_conversation = team_conversation_api.create_conversation(
                f"autotest_2095_other_{int(time.time())}"
            )
            other_conv_id = other_conversation["id"]
            assert other_conv_id, "Expected a numeric id for the throwaway 'other' conversation"

            # ------------------------------------------------------------------
            # Setup — seed a fresh conversation + real message history entirely
            # via the UI's own "+Chat" flow (NOT via ConversationAPI.create_
            # conversation() — confirmed live, 4/4 attempts, that sending the
            # first UI message to a conversation that exists server-side with
            # ZERO messages silently creates a BRAND-NEW conversation instead
            # of using the existing one; filed as
            # EliteaAI/elitea-testing-public#691. See AFS § Test Data
            # "AMENDED" note). Two exchanges (4 messages) is the minimum
            # confirmed live to reliably overflow the default viewport for the
            # Step 6 scroll assertion.
            # ------------------------------------------------------------------
            chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
            assert chat.is_input_empty(), (
                "Message input should be empty right after starting a fresh "
                "conversation via +Chat"
            )

            initial_count = chat.get_message_count()
            chat.send_message(FIRST_MESSAGE, use_enter=True)
            chat.wait_for_input_ready(timeout=NAVIGATION_TIMEOUT)
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
            chat.wait_for_message_content_stable(timeout=AI_RESPONSE_TIMEOUT)
            # Same race as documented below for the second send:
            # wait_for_message_content_stable() is a text-heuristic and the
            # app's own internal streaming/nav-blocking flag can trail it
            # briefly — confirmed live (PR #693 review round 2): the SECOND
            # send_message()'s fill()/type call can time out on a
            # still-disabled input while the first AI response is still
            # finishing. wait_for_generation_complete() is the authoritative
            # "safe to send again" signal, so it's applied here too, not
            # just before Step 2.
            chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)

            match = re.search(r"/chat/(\d+)", page.url)
            assert match, (
                f"Conversation id should appear in the URL after the first "
                f"send, got: {page.url}"
            )
            conv_id = int(match.group(1))

            second_initial_count = chat.get_message_count()
            chat.send_message(SECOND_MESSAGE, use_enter=True)
            chat.wait_for_input_ready(timeout=NAVIGATION_TIMEOUT)
            chat.wait_for_ai_response(initial_count=second_initial_count, timeout=AI_RESPONSE_TIMEOUT)
            chat.wait_for_message_content_stable(timeout=AI_RESPONSE_TIMEOUT)
            # wait_for_message_content_stable() is a text-heuristic; the app's
            # own internal streaming/nav-blocking flag can trail it briefly —
            # confirmed live: a conversation-switch click issued right after
            # content-stable (but before generation is marked complete) is
            # silently swallowed (no navigation). wait_for_generation_complete()
            # is the authoritative "safe to navigate" signal Step 2 needs.
            chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)

            seeded_count = chat.get_message_count()
            assert seeded_count == 4, (
                "Expected 4 seeded messages (2 user + 2 AI) before re-opening "
                f"the conversation from Today, got {seeded_count}"
            )

            conv_data = team_conversation_api.get_conversation(conv_id)
            conv_name = conv_data.get("name", "")
            assert conv_name, "Seeded conversation should have a (server-assigned) name"

            with allure.step(
                "Step 2 — Navigate away from the seeded conversation so the "
                "subsequent click is a genuine 'open an EXISTING conversation' action"
            ):
                # Bare "/chat" auto-redirects back to the last-viewed
                # conversation (SPA "resume" behavior, confirmed live) — a
                # DIFFERENT real conversation must be opened instead to
                # genuinely leave this one.
                chat.click_first_other_conversation(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                # Known defect EliteaAI/elitea-testing-public#692: the seeded
                # (+Chat-created) conversation's sidebar entry stays stuck
                # "active" after this navigation, silently no-op'ing any
                # later click back onto it. A reload here (landing on the
                # OTHER conversation's URL) forces a full client-state
                # re-derivation that clears the stale flag — confirmed live.
                # Test-side plumbing, not a case step.
                page.reload(wait_until="domcontentloaded")
                chat.wait_for_page_load()
                assert f"/chat/{conv_id}" not in page.url, (
                    "Should have genuinely navigated away from the seeded "
                    f"conversation, but URL still shows it: {page.url}"
                )

            with allure.step(
                "Step 3 — Locate the Today heading; verify the conversation "
                "renders under it specifically"
            ):
                assert chat.is_conversation_group_visible("today", timeout=UI_ELEMENT_TIMEOUT), (
                    "'Today' date-group heading should be visible in the sidebar"
                )
                assert chat.is_conversation_in_group(conv_id, "today", timeout=UI_ELEMENT_TIMEOUT), (
                    f"Conversation {conv_id} should render under the Today "
                    "group specifically (not merely exist somewhere on the page)"
                )

            with allure.step("Step 4 — Click the conversation from the Today list; verify URL + title"):
                chat.click_conversation_in_group(conv_id, "today", timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_conversation_url(str(conv_id), timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_page_load()
                assert f"/chat/{conv_id}" in page.url, (
                    f"URL should contain the conversation id {conv_id}, got: {page.url}"
                )
                assert conv_name in page.title(), (
                    "Browser tab title should show the conversation's title "
                    f"{conv_name!r}, got: {page.title()!r}"
                )

            with allure.step("Step 5 — Verify full message history (4 messages) in original order"):
                chat.wait_for_message_count(4, timeout=UI_ELEMENT_TIMEOUT)
                message_count = chat.get_message_count()
                assert message_count == 4, (
                    f"Expected 4 messages in the reopened conversation, got {message_count}"
                )

                bodies = [
                    ChatPage._extract_message_body(chat.messages_container.nth(i))
                    for i in range(4)
                ]
                assert FIRST_MESSAGE in bodies[0], (
                    f"Message 0 should be the first seeded user message, got: {bodies[0]!r}"
                )
                assert bodies[1].strip(), "Message 1 (AI response to the first message) should be non-empty"
                assert SECOND_MESSAGE in bodies[2], (
                    "Message 2 should be the SECOND seeded user message (order "
                    f"preserved, not re-shuffled), got: {bodies[2]!r}"
                )
                assert bodies[3].strip(), "Message 3 (AI response to the second message) should be non-empty"

            with allure.step("Step 6 — Verify the messages region is genuinely scrollable"):
                assert chat.is_messages_scrollable(), (
                    "Messages scroll container should overflow (scrollHeight > "
                    "clientHeight) given 4 seeded messages"
                )
                before, after = chat.scroll_messages_container(delta_y=200)
                assert after != before, (
                    "scrollTop should change after a real scroll interaction "
                    f"(not just a CSS-overflow read): before={before}, after={after}"
                )

            with allure.step("Step 7 — Verify the message input is active/ready"):
                assert chat.message_input.is_visible(), "Message input should be visible"
                assert chat.message_input.is_editable(), "Message input should be editable (not disabled)"
                assert chat.is_input_empty(), "Message input should be empty on a freshly-opened conversation"

            with allure.step("Step 8 — Verify the model name is displayed in the composer"):
                model_text = chat.get_selected_model()
                assert model_text, "Model selector should show a non-empty model name"

            with allure.step("Step 9 — Verify the Context Budget widget (tokens, Messages, Summaries)"):
                chat.wait_for_context_budget_panel(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_context_budget_panel_visible(), "Context Budget panel should be visible"

                tokens_text = chat.get_context_budget_tokens_text()
                assert re.search(r"\d+\s*/\s*[\d\s]+tokens", tokens_text), (
                    f"Context Budget tokens text should match 'N / M tokens', got: {tokens_text!r}"
                )

                # The counters update asynchronously shortly after the panel
                # becomes visible — a one-shot read can race ahead of that
                # update (confirmed live: PR #693 review round 2 reproduced
                # a failure reading '0' where the failure screenshot,
                # captured moments later, already showed '4' rendered).
                # Wait for the expected value first, mirroring the
                # wait_for_message_count() + get_message_count() pattern.
                chat.wait_for_context_budget_messages_count("4", timeout=UI_ELEMENT_TIMEOUT)
                messages_count = chat.get_context_budget_messages_count()
                assert messages_count == "4", (
                    "Context Budget Messages counter should read '4' (matching "
                    f"the 4 seeded messages), got: {messages_count!r}"
                )

                chat.wait_for_context_budget_summaries_count("0", timeout=UI_ELEMENT_TIMEOUT)
                summaries_count = chat.get_context_budget_summaries_count()
                assert summaries_count == "0", (
                    "Context Budget Summaries counter should read '0' (no "
                    f"summarization triggered at this token volume), got: {summaries_count!r}"
                )

            with allure.step("Step 10 — Verify the PARTICIPANTS panel shows the correct participant"):
                chat.expand_participants_panel(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.participants_users_avatar.count() == 1, (
                    "Expanded PARTICIPANTS panel should show exactly one USERS avatar"
                )
                avatar_text = chat.get_participants_user_avatar_text(timeout=UI_ELEMENT_TIMEOUT)
                assert avatar_text, "USERS avatar should show non-empty initials"

                # Cross-check via the API — a DOM-only "some avatar renders"
                # check would not catch the panel showing the WRONG
                # participant, which is literally what case step 8 asks for.
                conv_data = team_conversation_api.get_conversation(int(conv_id))
                owner_id = conv_data.get("author_id")
                user_participant = next(
                    (
                        p for p in conv_data.get("participants", [])
                        if p.get("entity_name") == "user"
                    ),
                    None,
                )
                assert user_participant is not None, (
                    "Conversation API response should include a 'user' participant entry"
                )
                assert user_participant.get("entity_meta", {}).get("id") == owner_id, (
                    "The conversation's 'user' participant should be its actual "
                    f"owner (author_id={owner_id}), got participant "
                    f"entity_meta={user_participant.get('entity_meta')!r}"
                )
                owner_name = user_participant.get("meta", {}).get("user_name", "")
                assert avatar_text == _expected_initials(owner_name), (
                    f"DOM avatar initials {avatar_text!r} should match the "
                    f"conversation's actual owner {owner_name!r} (expected "
                    f"{_expected_initials(owner_name)!r})"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors or "
                "uncaught exceptions across the full flow"
            ):
                # Known artifact: the project-471 secrets 403 is filtered by
                # _is_known_project_471_secrets_403() above (already
                # documented, unrelated — see AFS § Network Behavior). Any
                # OTHER console error, or any uncaught JS exception
                # (pageerror — console alone would miss it, see the
                # listener registration comment above), still fails this
                # check for real.
                assert not console_messages and not page_errors, (
                    f"Unexpected side-channel errors: "
                    f"console={[m.text for m in console_messages]!r} "
                    f"page_errors={page_errors!r}"
                )

        finally:
            if conv_id:
                try:
                    team_conversation_api.delete_conversation(int(conv_id))
                    logger.info("Cleaned up conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_id, exc)
            if other_conv_id:
                try:
                    team_conversation_api.delete_conversation(int(other_conv_id))
                    logger.info("Cleaned up other conversation %s", other_conv_id)
                except Exception as exc:
                    logger.warning(
                        "Failed to delete other conversation %s: %s", other_conv_id, exc
                    )
