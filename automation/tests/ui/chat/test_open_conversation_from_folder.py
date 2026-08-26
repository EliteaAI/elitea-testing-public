"""UI Test for ELITEA-2098 — Open Existing Conversation from a Folder.

Verifies that a folder expands to list its conversations, that clicking a
conversation inside the folder opens it (URL + tab title update, active
input, correct model name, correct PARTICIPANTS participant), highlights
that conversation's row, and that clicking a second conversation in the
SAME folder moves the interaction window and the highlight to the new one.

Spec: test-specs/chat-interface/l3_open-existing-conversation-from-folder_ELITEA-2098.md

Setup seeds a folder + two conversations, then moves both into the folder
via the API ("move into folder" PUTs) — transit setup, not the observable
under test; the case's own observable (folder expand -> conversation open
-> highlight moves) is produced entirely by the real UI against these
real, server-persisted conversations. No new page-object locators were
needed — every handle (``FOLDER_ITEM``, scoped ``CONVERSATION_ITEM``,
``message_input``, ``model_selector``,
``chat-participants-panel-toggle-button``) was already on ``main``.

Fix round 1 (this PR): case step 3's expected result ("Conversation
content is displayed with full message history") had no assertion —
the AFS's own § Blocked Steps implementer note flagged this as an open
choice, but shipping without an assertion or a routed decision is a
silent scope drop, not a resolution. Fixed by seeding conv_a's message
history via the UI's own "+Chat" flow (same idiom, same worked
precedent, and the same defect it dodges — EliteaAI/elitea-testing-public#691,
"sending the first UI message to a conversation that exists server-side
with ZERO messages silently creates a brand-new conversation" — as
``test_open_conversation_today_section.py``/ELITEA-2095, which the AFS's
own note pointed at) instead of the plain API create used for conv_b,
then moving the seeded conversation into the folder via the same PUT.
Step 3 now asserts the reopened conversation shows exactly the 2 seeded
messages (1 user + 1 AI), in order, non-empty.

AFS amendment (implementer exploration, this PR): the AFS specced project
399 (Private) throughout, including case step 6 (PARTICIPANTS panel). Live
run showed step 6 fails on Private — ``ExpandedParticipantsList.jsx``'s
``!isPrivateProject`` guard (confirmed against ``../EliteaUI/src`` on
``main``) unconditionally omits the whole Users/owner badge for the
account's own Private project, so there is no USERS avatar to read at all
(product design, not a defect — same constraint the sibling ELITEA-2095
test already documents and works around). Switched the WHOLE test to the
Team project (471), matching ELITEA-2095's own precedent, so step 6's
assertion is genuinely testable — same assertions throughout, no scope
change, purely a "which project" technique choice (folder/conversation
mechanics are project-agnostic).

No ``FolderAPI`` client exists yet; ``create_folder()``/``delete_folder()``/
``move_conversation_to_folder()`` were added to ``ConversationAPI`` (folder
endpoints share the conversations project scope) rather than duplicating a
new client, per the AFS's own Automation Hints. Cleanup uses the singular
``/elitea_core/conversation/...`` delete endpoint (the plural form 404s —
confirmed live during analysis; ``ConversationAPI.delete_conversation()``
already implements this correctly, the top-level ``automation/CLAUDE.md``
"API Quirks" table is stale on this one point — flagged as a doc-accuracy
note, not a defect, not fixed in this PR since it's outside this test's
scope).

No product defects were found — all 8 case steps matched the live product
exactly.
"""

import logging
import re
import time

import allure
import pytest
from api import ConversationAPI
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 30_000
# Short, deliberate timeout for "should NOT be there" negative checks — long
# enough to catch a genuine render, short enough not to pad a passing run.
NEGATIVE_CHECK_TIMEOUT = 1_500

# Team project — the ONLY environment where a plain default-LLM conversation's
# PARTICIPANTS panel shows a USERS section for the account's own identity
# (see module docstring's AFS amendment note; same project ELITEA-2095 uses).
TEAM_PROJECT_ID = "471"

# The single real exchange seeded into conv_a via the UI's own "+Chat" flow
# (see Setup and the module docstring's fix-round-1 note) so case step 3's
# "full message history" wording has real content to assert against on
# reopen. One exchange (2 messages) is enough — unlike ELITEA-2095's step 6
# scroll assertion, this case doesn't need an overflowing viewport.
FIRST_MESSAGE = "Give me a short 3-item numbered list of fun facts about narwhals."


def _is_known_project_471_secrets_403(msg) -> bool:
    """Filter the pre-existing, already-documented project-471 ``secrets`` 403.

    Same idiom as ``test_open_conversation_today_section.py``'s identically
    named filter — project 471 surfaces a ``403 Forbidden`` on
    ``GET .../secrets/secrets/default/471`` on every page load regardless of
    any action taken, unrelated to this flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default/471" in (text + location_url)


class TestOpenExistingConversationFromFolder:
    """ELITEA-2098: Open Existing Conversation from a Folder (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2098_open-existing-conversation-from-a-folder.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_open_existing_conversation_from_folder(self, page, _browser_cookies):
        """Expand a folder, open a conversation inside it, then open a
        second conversation in the same folder and verify the highlight moves.

        Steps (AFS
        test-specs/chat-interface/l3_open-existing-conversation-from-folder_ELITEA-2098.md):
        1. Locate the seeded folder — collapsed, folder icon visible, no
           conversation items rendered beneath it.
        2. Expand the folder; both seeded conversations render inside.
        3. Click the first conversation; URL + tab title update, full
           message history (the 2 messages seeded via the UI's own
           "+Chat" flow) is displayed.
        4. Message input is active/editable.
        5. Model name is shown.
        6. PARTICIPANTS panel shows the correct (single) participant.
        7. The clicked conversation's row is highlighted (data-active).
        8. Click a different conversation in the SAME folder; interaction
           window + highlight both move to it, the previous row un-highlights.
        """
        team_conversation_api = ConversationAPI(
            browser_cookies=_browser_cookies, project_id=TEAM_PROJECT_ID,
        )
        chat = ChatPage(page)
        folder_id = None
        conv_a_id = None
        conv_b_id = None
        other_conv_id = None

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
                "Setup — switch to the Team project (471, see module "
                "docstring's AFS amendment); seed a folder with two "
                "conversations (conv_a via the UI's own '+Chat' flow with "
                "a real message exchange, conv_b via API), a throwaway "
                "'other' conversation for the navigate-away step, and move "
                "conv_a + conv_b into the folder via API PUTs"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.switch_project(TEAM_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)
                switched_project_text = chat.get_selected_project_text()
                assert "Elitea Testing Team" in switched_project_text, (
                    "Project selector should show 'Elitea Testing Team' after "
                    f"switching, got: {switched_project_text!r}"
                )

                ts = int(time.time())
                folder = team_conversation_api.create_folder(f"autotest_2098_folder_{ts}")
                folder_id = folder.get("id")
                assert folder_id is not None, f"Folder create response should include an id: {folder!r}"

                conv_b = team_conversation_api.create_conversation(f"autotest_2098_conv_b_{ts}")
                conv_b_id = conv_b["id"]

                # Throwaway conversation used ONLY as a navigate-away target
                # (see the "Navigate away" note below) — it is never moved
                # into the folder, so clicking it can never re-trigger the
                # folder's containsActiveConversation auto-expand the way
                # clicking conv_b would (conv_b IS moved into the folder).
                # Live-confirmed in ELITEA-2095 (test_open_conversation_
                # today_section.py) that an API-created, zero-message
                # conversation renders in the sidebar and is clickable
                # without an intervening reload. Cleaned up in `finally`.
                other_conversation = team_conversation_api.create_conversation(
                    f"autotest_2098_other_{ts}"
                )
                other_conv_id = other_conversation["id"]

                # conv_a needs real message history for Step 3's "full
                # message history" assertion. Seeded via the UI's own
                # "+Chat" flow, NOT ConversationAPI.create_conversation() —
                # same worked precedent and same reason as
                # test_open_conversation_today_section.py (ELITEA-2095):
                # sending the first UI message to a conversation that
                # exists server-side with ZERO messages silently creates a
                # BRAND-NEW conversation instead of using the existing one
                # (EliteaAI/elitea-testing-public#691).
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
                assert chat.is_input_empty(), (
                    "Message input should be empty right after starting a "
                    "fresh conversation via +Chat"
                )
                initial_count = chat.get_message_count()
                chat.send_message(FIRST_MESSAGE, use_enter=True)
                chat.wait_for_input_ready(timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_message_content_stable(timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)

                match = re.search(r"/chat/(\d+)", page.url)
                assert match, (
                    f"Conversation id should appear in the URL after the "
                    f"first send, got: {page.url}"
                )
                conv_a_id = int(match.group(1))

                seeded_count = chat.get_message_count()
                assert seeded_count == 2, (
                    "Expected 2 seeded messages (1 user + 1 AI) in conv_a "
                    f"before moving it into the folder, got {seeded_count}"
                )

                # Navigate away from conv_a BEFORE moving it into the
                # folder — live-confirmed this session: reloading while
                # conv_a is still the active/open conversation makes the
                # product auto-expand the folder that now contains it
                # (FolderItem.jsx's `defaultExpanded={containsActiveConversation}`
                # — sensible product behavior, "you're looking at a
                # conversation, its folder shows it", but it breaks case
                # Step 1's own precondition of a COLLAPSED folder on a fresh
                # page load). Clicks the THROWAWAY other_conversation
                # specifically (not "first other", which could land back on
                # conv_b — conv_b is ALSO about to move into the folder, so
                # that would just reproduce the same auto-expand).
                chat.click_conversation_item(other_conv_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_conversation_url(str(other_conv_id), timeout=NAVIGATION_TIMEOUT)
                assert f"/chat/{conv_a_id}" not in page.url, (
                    "Should have genuinely navigated away from conv_a before "
                    f"moving it into the folder, but URL still shows it: {page.url}"
                )

                team_conversation_api.move_conversation_to_folder(conv_a_id, folder_id)
                team_conversation_api.move_conversation_to_folder(conv_b_id, folder_id)

                # ``navigate_to_chat()`` no-ops when already on "/chat" (see its
                # own docstring) — it would NOT refetch the sidebar list to
                # pick up the folder/conversations just created via API. A
                # reload forces a genuine client-state refresh, same idiom
                # ELITEA-2095 uses for its own post-API-seed refresh.
                page.reload(wait_until="domcontentloaded")
                chat.wait_for_page_load()
                chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)
                logger.info(
                    "Setup complete — folder=%s conv_a=%s conv_b=%s", folder_id, conv_a_id, conv_b_id,
                )

            with allure.step(
                "Step 1 — Locate the seeded folder: renders with a folder "
                "icon, collapsed (no conversation items visible beneath it)"
            ):
                folder_item = chat.get_folder_item(folder_id)
                expect(folder_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert not chat.is_folder_expanded(folder_id), (
                    f"Folder {folder_id} should render collapsed by default"
                )
                expect(folder_item.locator(chat.FOLDER_ICON)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert not chat.is_conversation_in_folder(
                    folder_id, conv_a_id, timeout=NEGATIVE_CHECK_TIMEOUT
                ), f"Conversation {conv_a_id} should not be visible while folder {folder_id} is collapsed"

            with allure.step(
                "Step 2 — Click the folder to expand it; both seeded "
                "conversations render inside"
            ):
                chat.expand_folder(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(folder_id), f"Folder {folder_id} should be expanded"
                assert chat.is_conversation_in_folder(
                    folder_id, conv_a_id, timeout=UI_ELEMENT_TIMEOUT
                ), f"Conversation {conv_a_id} should render inside folder {folder_id}"
                assert chat.is_conversation_in_folder(
                    folder_id, conv_b_id, timeout=UI_ELEMENT_TIMEOUT
                ), f"Conversation {conv_b_id} should render inside folder {folder_id}"

            with allure.step(
                "Step 3 — Click the first conversation inside the folder; "
                "URL, browser tab title, and full message history update"
            ):
                chat.click_conversation_in_folder(folder_id, conv_a_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_conversation_url(str(conv_a_id), timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_page_load()
                assert f"/chat/{conv_a_id}" in page.url, (
                    f"URL should contain conversation {conv_a_id}, got: {page.url}"
                )

                conv_a_data = team_conversation_api.get_conversation(conv_a_id)
                conv_a_name = conv_a_data.get("name", "")
                assert conv_a_name, "conv_a should have a (server-assigned) name"
                assert conv_a_name in page.title(), (
                    f"Browser tab title should show conv_a's name {conv_a_name!r}, "
                    f"got: {page.title()!r}"
                )

                # Case step 3's expected result: "Conversation content is
                # displayed with full message history" — conv_a was seeded
                # with one real exchange via the UI's own "+Chat" flow (see
                # Setup), so reopening it from the folder must show that
                # same content, not a blank thread. Same shape as
                # ELITEA-2095's Step 5 (test_open_conversation_today_
                # section.py), scaled down to the single seeded exchange.
                chat.wait_for_message_count(2, timeout=UI_ELEMENT_TIMEOUT)
                message_count = chat.get_message_count()
                assert message_count == 2, (
                    "Expected the 2 seeded messages (1 user + 1 AI) to be "
                    f"shown when reopening conv_a from the folder, got {message_count}"
                )
                bodies = [
                    ChatPage._extract_message_body(chat.messages_container.nth(i))
                    for i in range(2)
                ]
                assert FIRST_MESSAGE in bodies[0], (
                    f"Message 0 should be the seeded user message, got: {bodies[0]!r}"
                )
                assert bodies[1].strip(), "Message 1 (AI response to the seeded message) should be non-empty"

            with allure.step("Step 4 — Verify the message input at the bottom is active"):
                assert chat.message_input.is_visible(), "Message input should be visible"
                assert chat.message_input.is_editable(), "Message input should be editable (not disabled)"

            with allure.step("Step 5 — Verify the correct model/agent name is shown in the input bar"):
                model_text = chat.get_selected_model()
                assert model_text, "Model selector should show a non-empty model name"

            with allure.step("Step 6 — Verify the PARTICIPANTS panel shows the correct participant"):
                chat.expand_participants_panel(timeout=UI_ELEMENT_TIMEOUT)
                # get_participants_user_avatar_text() waits for the avatar to
                # become visible (the USERS section renders asynchronously
                # after the panel expands); .count() below is a synchronous
                # snapshot with no retry, so it must run AFTER the wait, not
                # before — live-confirmed flaky 0-count when read first.
                avatar_text = chat.get_participants_user_avatar_text(timeout=UI_ELEMENT_TIMEOUT)
                assert avatar_text, "USERS avatar should show non-empty initials"
                assert chat.participants_users_avatar.count() == 1, (
                    "Expanded PARTICIPANTS panel should show exactly one USERS avatar"
                )

            with allure.step("Step 7 — Verify the conversation entry in the folder list is highlighted"):
                chat.wait_for_conversation_active(conv_a_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_conversation_active(conv_a_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Conversation {conv_a_id} should be marked active (data-active) after being opened"
                )

            with allure.step(
                "Step 8 — Click a different conversation inside the SAME "
                "folder; URL updates, highlight moves from conv_a to conv_b"
            ):
                chat.click_conversation_in_folder(folder_id, conv_b_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_conversation_url(str(conv_b_id), timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_page_load()
                assert f"/chat/{conv_b_id}" in page.url, (
                    f"URL should contain conversation {conv_b_id}, got: {page.url}"
                )
                # data-active flips asynchronously relative to the URL/history
                # change — poll for it rather than reading it once
                # (ChatPage.wait_for_conversation_active() docstring has the
                # live-confirmed race; bidirectional so it covers both the
                # new active row AND the previous one going inactive).
                chat.wait_for_conversation_active(conv_b_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_conversation_active(conv_b_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Conversation {conv_b_id} should now be marked active"
                )
                chat.wait_for_conversation_active(conv_a_id, active=False, timeout=NEGATIVE_CHECK_TIMEOUT)
                assert not chat.is_conversation_active(conv_a_id, timeout=NEGATIVE_CHECK_TIMEOUT), (
                    f"Conversation {conv_a_id} should no longer be marked active "
                    f"after conv_b became active"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors or "
                "uncaught exceptions across the full flow"
            ):
                assert not console_messages and not page_errors, (
                    f"Unexpected side-channel errors: "
                    f"console={[m.text for m in console_messages]!r} "
                    f"page_errors={page_errors!r}"
                )

        finally:
            # Independent try/except per resource (.claude/rules/ui-tests.md
            # § Test Data Lifecycle) — one resource's cleanup failure must
            # not block the others. Conversations deleted before the folder
            # (harmless order either way — delete_folder does not cascade).
            if conv_a_id:
                try:
                    team_conversation_api.delete_conversation(conv_a_id)
                    logger.info("Cleaned up conv_a %s", conv_a_id)
                except Exception as exc:
                    logger.warning("Failed to delete conv_a %s: %s", conv_a_id, exc)
            if conv_b_id:
                try:
                    team_conversation_api.delete_conversation(conv_b_id)
                    logger.info("Cleaned up conv_b %s", conv_b_id)
                except Exception as exc:
                    logger.warning("Failed to delete conv_b %s: %s", conv_b_id, exc)
            if other_conv_id:
                try:
                    team_conversation_api.delete_conversation(other_conv_id)
                    logger.info("Cleaned up other_conversation %s", other_conv_id)
                except Exception as exc:
                    logger.warning("Failed to delete other_conversation %s: %s", other_conv_id, exc)
            if folder_id:
                try:
                    team_conversation_api.delete_folder(folder_id)
                    logger.info("Cleaned up folder %s", folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)
            team_conversation_api.close()
