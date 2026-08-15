"""UI Test for ELITEA-2173/ELITEA-2174 — Chat: Team Project, Mention User(s)
by Clicking Name(s) in the Users Participants Dropdown.

Family AFS covering two TMS cases that differ only in how many participant
names are clicked before Send: ELITEA-2173 mentions ONE user, ELITEA-2174
mentions TWO users (with an explicit dropdown-reopen between clicks — the
case's own literal step 2). Both assert the SAME mechanism: clicking a
participant's NAME row inside the "Users" participants dropdown
(``UserMenu.jsx``/``onSelectParticipant``→``onSelectThisParticipant``→
``NewChat.jsx``'s ``onSelectParticipant(foundParticipant, false)``) inserts
an ``@<DisplayName> `` mention into the composer — a genuinely different
code path than ELITEA-2168's composer-own typed-``"@"`` mention popper
(``UserMentionList``/``onSelectUserMention``), which that case's own test
never exercises via a dropdown row's name (only its delete icon, or the
dropdown footer's "All users" item).

Spec:
test-specs/chat-interface/l2_participants-dropdown-click-name-inserts-mention_ELITEA-2173.md

New page-object surface (this implementation, ``ChatPage``, additive — no
existing method or its caller is modified):
- ``mention_user_via_participants_dropdown(user_id, timeout)`` — opens the
  Users popover and clicks a participant's name row directly (reuses the
  existing ``PARTICIPANT_ROW`` testid template ``open_remove_user_dialog()``/
  ``hover_participant_user_row()`` already resolve; no hover needed — the
  row's own ``onClick`` fires on the whole row, and the hover-only delete
  icon is ``visibility: hidden`` by default so it never intercepts the
  click).

Zero new testids required — every element this family touches already
carries a testid ELITEA-2167/2168 added, present on both ``main`` and
``automation/testids`` (AFS § Concrete Handles).

Known defects: none on either case's own subject. ELITEA-2173's own case
text (step 3, "mention is highlighted/formatted") does NOT hold — the
inserted mention is plain, unstyled text (same as the composer's own
typed-``"@"`` mention path). Classified as case-text drift (reverse-masking
guard), filed as CLARIFICATION
https://github.com/EliteaAI/elitea-testing-public/issues/1558 — NOT
asserted here (the composer's exact TEXT content is asserted instead, per
AFS § Known Defects Found).

Both cases' recipient-notification expected-result half ("user_1 receives
notification" / "both users notified") is NOT independently assertable in
this single-account localhost environment (same limitation ELITEA-2168
already documents for its own composer-mention steps) — the structural
"no LLM response" proxy (message count +1, not +2) is asserted instead.
"""

import logging
import re

import allure
import pytest
from api import ConversationAPI
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds) — same values as the sibling chat suite
# (test_team_users_mention_and_remove_participants.py / test_owner_has_no_remove_control_in_users_dropdown.py)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 30_000

# Team project — the only project where "Invite Users" is offered at all
# (PlusChatButton.jsx's !isPrivateProject guard) — AFS § Preconditions.
TEAM_PROJECT_ID = "471"

# Case's own user_1/user_2 (AFS § Test Data — same two names ELITEA-2168
# already established for this environment).
USER_1_QUERY, USER_1_NAME = "sa", "Hrach Sargsyan"
USER_2_QUERY, USER_2_NAME = "ad", "Levon Dadayan"

# Case's own literal Test Data message suffix — the composer already ends
# with a trailing space after a mention insert (`mentionUser('@<name> ')`),
# so appending "hi" (no leading space) via press("End") +
# press_sequentially() reproduces the case's own literal
# "@user_1 hi"/"@user_1 @user_2 hi" text (same idiom ELITEA-2168's test
# already established for its own composer-mention send step).
MENTION_MESSAGE_SUFFIX = "hi"

SETUP_MESSAGE_TEXT = "setup message"


def _is_conversation_create_request(url: str) -> bool:
    """Match the POST that creates the conversation (AFS § Network Behavior)."""
    return bool(re.search(rf"/elitea_core/conversations/prompt_lib/{TEAM_PROJECT_ID}/?(\?|$)", url))


def _is_participants_persist_request(url: str) -> bool:
    """Match the POST that persists the queued invited users as real participants
    (AFS § Network Behavior — fires only at first Send, not at the Add-button click)."""
    return bool(re.search(rf"/elitea_core/participants/prompt_lib/{TEAM_PROJECT_ID}/\d+", url))


def _is_known_project_471_secrets_403(msg) -> bool:
    """Filter the pre-existing, already-documented project-471 ``secrets`` 403.

    Fires on every page load in this project regardless of any action taken
    (AFS § Network Behavior; same idiom as the sibling chat suite's
    equivalent filter)."""
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default/471" in (text + location_url)


def _is_known_checkicon_sx_svg_warning_719(msg) -> bool:
    """Filter the already-filed, isolated console defect EliteaAI/elitea-testing-public#719.

    Fires on every "Add users" option selection — ``AutoCompleteDropDown.jsx``'s
    ``<CheckedIcon sx={...} />`` forwards an MUI ``sx`` prop onto a raw
    imported ``<svg>``, producing this React console warning. Re-confirmed
    live this session (AFS § Known Defects Found) — filtered here, not
    automated as a hard-fail."""
    text = msg.text
    return "Invalid value for prop" in text and "sx" in text and "svg" in text and "CheckedIcon" in text


def _open_blank_conversation(chat: ChatPage, timeout: int = NAVIGATION_TIMEOUT) -> None:
    """Click +Chat and confirm a genuinely blank, unsent conversation opened.

    Infrastructure-class flake guard (issue #1082, re-confirmed live per
    this feature's AFS) — same idiom as the sibling chat suite's own copy
    of this helper (``test_team_users_mention_and_remove_participants.py``/
    ``test_owner_has_no_remove_control_in_users_dropdown.py``):
    ``click_create_conversation()`` only waits for the message input to be
    visible, which is trivially true on ANY conversation. Retries if the
    new-conversation greeting doesn't appear, OR if it appears but the
    conversation still has message history, OR if the URL already carries a
    numeric conversation id (a genuinely fresh/draft conversation always
    stays on the bare ``/chat`` route until the first Send).
    """
    last_reason = "unknown"
    for attempt in range(3):
        chat.click_create_conversation(timeout=timeout)
        try:
            chat.new_conversation_greeting.wait_for(state="visible", timeout=5000)
        except Exception:
            last_reason = "greeting never appeared"
            logger.warning(
                "New-conversation greeting not visible after +Chat click "
                "(attempt %d) — retrying (see _open_blank_conversation docstring)",
                attempt + 1,
            )
            continue
        if re.search(r"/chat/\d+", chat.page.url):
            last_reason = f"landed on an existing conversation URL ({chat.page.url})"
            logger.warning(
                "Landed on a non-blank conversation URL (attempt %d) — "
                "retrying (see _open_blank_conversation docstring)",
                attempt + 1,
            )
            continue
        if chat.get_message_count() != 0:
            last_reason = "greeting appeared but conversation has message history"
            logger.warning(
                "Landed on a non-blank conversation (attempt %d) — retrying "
                "(see _open_blank_conversation docstring)",
                attempt + 1,
            )
            continue
        return
    raise AssertionError(
        f"Could not open a genuinely blank conversation after 3 attempts: {last_reason}"
    )


class TestParticipantsDropdownClickNameInsertsMention:
    """ELITEA-2173/ELITEA-2174: Chat – Team Project – Mention User(s) by
    Clicking Name(s) in Participants Dropdown (l2, medium, both)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/"
        "ELITEA-2173_chat-team-project-mention-single-user-by-clicking-name-in-participants-dropdown.md",
        "onetest-ai Test Case link — ELITEA-2173",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/"
        "ELITEA-2174_chat-team-project-mention-two-users-by-clicking-their-names.md",
        "onetest-ai Test Case link — ELITEA-2174",
    )
    @pytest.mark.p2
    @pytest.mark.parametrize(
        "case_id, target_users, badge_count_after_setup",
        [
            pytest.param(
                "ELITEA-2173",
                ((USER_1_QUERY, USER_1_NAME),),
                "2",
                id="ELITEA-2173-single-mention",
            ),
            pytest.param(
                "ELITEA-2174",
                ((USER_1_QUERY, USER_1_NAME), (USER_2_QUERY, USER_2_NAME)),
                "3",
                id="ELITEA-2174-two-mentions",
            ),
        ],
    )
    def test_click_participant_name_inserts_mention(
        self, page, _browser_cookies, case_id, target_users, badge_count_after_setup,
    ):
        """Click one/two participant name row(s) in the Users dropdown — mention(s) inserted, sent, no LLM reply.

        Steps (AFS
        test-specs/chat-interface/l2_participants-dropdown-click-name-inserts-mention_ELITEA-2173.md):
        Setup. Seed a Team-project conversation with the case's own target
              user(s) already added as Users participants.
        1. Verify the PARTICIPANTS USERS section is visible.
        2. Open the Users dropdown, click the target user's name row —
           composer text becomes "@<DisplayName> " (ELITEA-2174: repeats
           for a SECOND user via an explicit dropdown reopen — composer
           text appends, not replaces).
        3. Type 'hi' and send — message count goes N -> N+1 (no LLM
           response).
        4. Recipient notification — not independently assertable in this
           single-account environment (AFS § Cluster execution log).
        """
        chat = ChatPage(page)
        team_conversation_api = ConversationAPI(
            browser_cookies=_browser_cookies, project_id=TEAM_PROJECT_ID,
        )
        conv_id: int | None = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not (
                _is_known_project_471_secrets_403(msg)
                or _is_known_checkicon_sx_svg_warning_719(msg)
            ):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                f"[{case_id}] Setup — switch to the Team project; open a "
                "genuinely blank conversation; seed the target user(s) via "
                "Add users; send a message so they persist and the USERS "
                f"badge reads {badge_count_after_setup!r}"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.switch_project(TEAM_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)

                _open_blank_conversation(chat, timeout=NAVIGATION_TIMEOUT)

                chat.open_add_users_modal(timeout=UI_ELEMENT_TIMEOUT)
                # Residual real-mouse hover on the plus-menu button (its own
                # click sequence never moves the mouse away) can leave its
                # MUI Tooltip rendered ON TOP of the modal's search field,
                # intermittently intercepting the very next click (same
                # hover-residue class already documented for the sibling
                # chat suite's "Add users" open sequence).
                page.mouse.move(0, 0)
                for query, name in target_users:
                    chat.search_and_select_add_user_verified(query, name, timeout=UI_ELEMENT_TIMEOUT)
                    chat.wait_for_add_users_chip(name, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_add_users_confirm(timeout=UI_ELEMENT_TIMEOUT)
                chat.add_users_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

                initial_setup_count = chat.get_message_count()
                assert initial_setup_count == 0, f"[{case_id}] Fresh conversation should have no messages yet"

                with page.expect_response(
                    lambda r: r.request.method == "POST" and _is_conversation_create_request(r.url)
                ) as create_info, page.expect_response(
                    lambda r: r.request.method == "POST" and _is_participants_persist_request(r.url)
                ) as participants_info:
                    chat.send_message(SETUP_MESSAGE_TEXT, use_enter=False)

                assert create_info.value.status == 201, (
                    f"[{case_id}] Conversation-create request should return 201, got {create_info.value.status}"
                )
                assert participants_info.value.status == 200, (
                    f"[{case_id}] Participants-persist request should return 200, got {participants_info.value.status}"
                )

                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=UI_ELEMENT_TIMEOUT)
                match = re.search(r"/chat/(\d+)", page.url)
                assert match, f"[{case_id}] Conversation id should appear in the URL after Send, got: {page.url}"
                conv_id = int(match.group(1))

                chat.wait_for_ai_response(initial_count=initial_setup_count, timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_participants_badge_count(
                    badge_count_after_setup, section="users", timeout=UI_ELEMENT_TIMEOUT,
                )

                # Resolve the numeric platform user ids needed for step 2's
                # dropdown-row clicks — the row's testid is keyed by
                # entity_meta.id, which callers don't know ahead of time
                # (only the display name searched for).
                conv_data = team_conversation_api.get_conversation(conv_id)
                participant_id_by_name = {
                    p.get("meta", {}).get("user_name"): p.get("entity_meta", {}).get("id")
                    for p in conv_data.get("participants", [])
                    if p.get("entity_name") == "user"
                }
                for _, name in target_users:
                    assert participant_id_by_name.get(name) is not None, (
                        f"[{case_id}] Expected a resolvable participant id for {name!r} via "
                        f"the conversation API, got participants: {conv_data.get('participants', [])!r}"
                    )

            with allure.step(
                f"[{case_id}] Step 1 — Verify PARTICIPANTS USERS section is "
                "visible on the seeded conversation"
            ):
                assert chat.is_participants_badge_visible(section="users", timeout=UI_ELEMENT_TIMEOUT), (
                    f"[{case_id}] PARTICIPANTS USERS badge should be visible on a "
                    "conversation that already has participants"
                )

            expected_prefix = ""
            for step_index, (_, name) in enumerate(target_users, start=1):
                reopen_note = " (reopen the dropdown)" if step_index > 1 else ""
                with allure.step(
                    f"[{case_id}] Step 2.{step_index} — Open the Users dropdown"
                    f"{reopen_note} and click {name!r}'s name row; verify the "
                    "mention is inserted/appended into the composer"
                ):
                    chat.mention_user_via_participants_dropdown(
                        participant_id_by_name[name], timeout=UI_ELEMENT_TIMEOUT,
                    )
                    expected_prefix += f"@{name} "
                    composer_text = chat.message_input.text_content() or ""
                    assert composer_text == expected_prefix, (
                        f"[{case_id}] Expected the composer to read {expected_prefix!r} "
                        f"after mentioning {name!r}, got: {composer_text!r}"
                    )

            with allure.step(
                f"[{case_id}] Step 3 — Type {MENTION_MESSAGE_SUFFIX!r} and "
                "send; verify sent with no LLM response (message count "
                "N -> N+1, not N+2)"
            ):
                initial_count = chat.get_message_count()
                chat.message_input.click()
                chat.message_input.press("End")
                chat.message_input.press_sequentially(MENTION_MESSAGE_SUFFIX, delay=50)

                expected_final_text = expected_prefix + MENTION_MESSAGE_SUFFIX
                composer_text_before_send = chat.message_input.text_content() or ""
                assert composer_text_before_send == expected_final_text, (
                    f"[{case_id}] Expected the composer to read {expected_final_text!r} "
                    f"before Send, got: {composer_text_before_send!r}"
                )

                chat.send_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                chat.send_button.click(force=True)

                chat.wait_for_message_count(initial_count + 1, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_network(timeout=AI_RESPONSE_TIMEOUT)
                message_count = chat.get_message_count()
                assert message_count == initial_count + 1, (
                    f"[{case_id}] A to-user mention send should add exactly ONE "
                    f"message (no LLM response) — expected {initial_count + 1}, got {message_count}"
                )

            # Step 4 (recipient notification) is NOT independently
            # assertable in this single-account environment — AFS § Cluster
            # execution log / § Coverage Map. The structural "no LLM
            # response" proof above is the correct single-account proxy.

            with allure.step(
                f"[{case_id}] Side-channel check — no unexpected console "
                "errors across the full flow"
            ):
                assert not console_messages, (
                    f"[{case_id}] Unexpected console errors: {[m.text for m in console_messages]!r}"
                )
        finally:
            page.remove_listener("console", _on_console)
            if conv_id:
                try:
                    # A failure mid-flow can leave the "Add users" dialog (or
                    # another overlay) open, which blocks the sidebar hover
                    # below (same class already documented for the sibling
                    # chat suite's cleanup).
                    page.keyboard.press("Escape")
                    chat.open_conversation_context_menu(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                    chat.click_conversation_menu_item("delete", timeout=UI_ELEMENT_TIMEOUT)
                    delete_response = chat.confirm_delete_conversation(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                    assert delete_response.status in (200, 204), (
                        f"[{case_id}] DELETE for conversation {conv_id} should succeed, got {delete_response.status}"
                    )
                    logger.info("[%s] Cleaned up conversation %s", case_id, conv_id)
                except Exception as exc:
                    logger.warning("[%s] Failed to clean up conversation %s: %s", case_id, conv_id, exc)
