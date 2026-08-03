"""UI Test for ELITEA-2168 — Chat: Team Project, Add Multiple Users
(Deselect via Chip), USERS Avatar Overflow, Mention User/@Everyone, Remove
Users from Conversation.

Verifies, on an existing Team-project conversation that already has
participants: adding four users via the "Add users" modal with one
deselected via its own chip delete icon before confirming, the expanded
PARTICIPANTS panel's 5-avatar-plus-overflow-indicator view, re-selecting
and Cancel-discarding a user, mentioning a specific participant via the
composer's typed-"@" popper (no LLM response), removing a user via the
Users dropdown's Remove/Cancel confirmation flow, and the composer's
"Everyone" mention path (no LLM response) — including a confirmed,
isolated product defect (#1119) in the dropdown's own "All users" footer
item, which is soft-asserted rather than masked.

Spec: test-specs/chat-interface/l2_team-users-mention-and-remove-participants_ELITEA-2168.md

Test-data substitutions (AFS § Test Data): the case's own "user_1..4"
placeholders map to Hrach Sargsyan / Levon Dadayan / Mariam Hakobyan /
Tatiana Bontsevich (same four names ELITEA-2167 already established for
this environment); the case's literal mention target "Test Bot" is the
dev-token owner's OWN display name (self-mention is excluded by the
composer's mention list) — substituted "Hrach Sargsyan" instead, already
a real participant by that point.

New page-object surface (this implementation, ``ChatPage``, all additive —
no existing method or its caller is modified):
- ``remove_add_users_chip(name)`` — clicks a selected chip's own delete
  icon in the "Add users" modal.
- ``open_remove_user_dialog(user_id)`` — generalizes
  ``remove_agent_participant()``'s row-resolution/hover-reveal mechanism
  to the "user" entity type, returning the confirmation dialog for the
  caller to confirm or cancel.
- ``expand_participants_panel_via_toggle()`` / ``collapse_participants_panel_via_toggle()``
  — deterministic, testid-backed replacements (for this case's own use)
  of the pre-existing raw-JS-heuristic ``expand_participants_panel()`` /
  ``collapse_participants_panel()`` (the latter failed live during
  analysis — AFS § Concrete Handles).
- ``open_user_mention_popper()`` / ``select_user_mention(name_or_everyone)``
  — composer's typed-"@" user-mention popper, mirroring the existing
  ``open_mention_skill_popper()`` for skills.

Testid gaps filled this implementation (``add-data-testid``, pushed to
``automation/testids``):
- ``add-users-remove-chip-{userId}`` on the "Add users" modal's per-chip
  delete icon (``AutoCompleteDropDown.jsx``'s new ``chipDeleteTestId``
  prop) — renamed from the AFS's originally-proposed
  ``add-users-chip-remove-{userId}`` to avoid a prefix collision with the
  already-merged ``ADD_USERS_CHIP_PREFIX`` (see AFS § Concrete Handles
  amendment; commits EliteaAI/EliteaUI@16fb99e3 / @d688dec1).
- ``chat-participant-row-user_{userId}_{projectId}`` on the Users
  participants dropdown's per-user row (``UserMenu.jsx``), via the
  existing ``getChatParticipantUniqueId()`` helper — same
  ``PARTICIPANT_ROW`` template family ELITEA-1793 established for
  Agents/Pipelines/Toolkits/MCP rows.
- ``chat-participants-panel-toggle-button`` (+ ``data-expanded``
  attribute) on the Participants panel's own expand/collapse
  ``IconButton`` (``Participants.jsx``).
- ``chat-participants-users-overflow-count`` on the expanded USERS
  section's "+N" ``Typography`` (``ExpandedParticipantsList.jsx``).
- ``chat-user-mention-list`` (container) + ``chat-user-mention-item-{id}``
  (dynamic per-row, including the literal ``@everyone`` id) on the
  composer's typed-"@" mention popper (``UserMentionList.jsx`` — had ZERO
  testids before this implementation).
- ``chat-participants-all-users-button`` on the Users dropdown's "All
  users" footer item (``DropdownFooter.jsx``) — an implementer addition
  not identified by analyst exploration, needed to exercise/confirm
  step 11's defect.
All via EliteaAI/EliteaUI@16fb99e3, @d688dec1, @11ba9c72 on
``automation/testids``.

Known defects (AFS § Known Defects Found):
- EliteaAI/elitea-testing-public#1119 (NOVEL, filed by the analyst this
  case) — clicking "All users" in the Participants dropdown does not
  insert an @Everyone mention (silently no-ops). Isolated, soft-asserted
  below (step 11); the case's own INTENDED "@Everyone, no LLM response"
  observable is separately verified via the confirmed-working
  composer-"@" path (step 12).
- EliteaAI/elitea-testing-public#719 (re-confirmed, not re-filed) — the
  "Add users" picker's checkmark-icon ``sx``-on-raw-``<svg>`` console
  warning, same as ELITEA-2167. Filtered below, not automated as a
  hard-fail.
- EliteaAI/elitea-testing-public#1082 (re-confirmed, not re-filed) — an
  unguarded ``click_create_conversation()`` can land on a stale
  conversation. Worked around via the same retry-guarded
  ``_open_blank_conversation()`` ELITEA-2167's test already implements.
"""

import logging
import re

import allure
import pytest
from api import ConversationAPI
from components.mui import Dialog
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds) — same values as the sibling chat suite
# (test_invite_users_add_cancel_close.py / test_open_conversation_today_section.py)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 30_000

# Team project — the only project where "Invite Users" is offered at all
# (PlusChatButton.jsx's !isPrivateProject guard) — AFS § Preconditions.
TEAM_PROJECT_ID = "471"

# Precondition/setup users (NOT part of the case's own numbered steps) —
# added once during setup, sent-and-persisted, never touched again.
SETUP_USER_1_QUERY, SETUP_USER_1_NAME = "chambyl", "Daniyar Chambylov"
SETUP_USER_2_QUERY, SETUP_USER_2_NAME = "bylitsk", "Ihar Bylitski"

# Case's own user_1-4 (AFS § Test Data — same four names ELITEA-2167 already
# established for this environment).
USER_1_QUERY, USER_1_NAME = "sa", "Hrach Sargsyan"
USER_2_QUERY, USER_2_NAME = "ad", "Levon Dadayan"
USER_3_QUERY, USER_3_NAME = "ma", "Mariam Hakobyan"
USER_4_QUERY, USER_4_NAME = "ta", "Tatiana Bontsevich"

# Mention target substitution (AFS § Test Data — "Test Bot" is the
# dev-token owner's own display name; self-mention is excluded).
MENTION_TARGET_NAME = USER_1_NAME

SETUP_MESSAGE_TEXT = "setup message"
MENTION_MESSAGE_SUFFIX = "hi"


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
    (AFS § Network Behavior; same idiom as
    ``test_invite_users_add_cancel_close.py``'s equivalent filter).
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default/471" in (text + location_url)


def _is_known_version_validator_400(msg) -> bool:
    """Filter the pre-existing, unrelated ``version_validator`` 400 noise.

    Confirmed live on navigation away from certain pre-existing
    conversations in this shared project — an artifact of an unrelated
    agent-versioning check, not caused by this flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "400" in text and "version_validator/prompt_lib" in (text + location_url)


def _is_known_checkicon_sx_svg_warning_719(msg) -> bool:
    """Filter the already-filed, isolated console defect EliteaAI/elitea-testing-public#719.

    Fires on every "Add users" option selection — ``AutoCompleteDropDown.jsx``'s
    ``<CheckedIcon sx={...} />`` forwards an MUI ``sx`` prop onto a raw
    imported ``<svg>``, producing this React console warning. Re-confirmed
    live this session (AFS § Known Defects Found) — filtered here, not
    automated as a hard-fail.
    """
    text = msg.text
    return "Invalid value for prop" in text and "sx" in text and "svg" in text and "CheckedIcon" in text


def _open_blank_conversation(chat: ChatPage, timeout: int = NAVIGATION_TIMEOUT) -> None:
    """Click +Chat and confirm a genuinely blank, unsent conversation opened.

    Infrastructure-class flake guard (issue #1082, re-confirmed live this
    session per AFS § Known Defects Found): ``click_create_conversation()``
    only waits for the message input to be visible, which is trivially
    true on ANY conversation — it does not itself prove navigation to a
    NEW conversation happened. Retries the click (real re-clicks, not a
    sleep) if the new-conversation greeting doesn't appear, OR if it
    appears but the conversation still has message history — this
    stronger, message-count check is this test's own hardening on top of
    ELITEA-2167's original helper: this test's OWN prior pytest-rerun
    attempt can leave a REAL, non-empty "Setup message" conversation
    behind (its cleanup runs in a ``finally`` block that can itself be
    blocked by a still-open dialog on the failure that triggered the
    rerun — confirmed live this implementation), and the greeting alone
    was observed to report a false positive when the SPA briefly shows it
    before settling back onto that leftover conversation.
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


class TestTeamUsersMentionAndRemoveParticipants:
    """ELITEA-2168: Chat – Team Project – Add Multiple Users, Mention User,
    View User List and Remove Users from Conversation (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2168_chat-team-project-add-multiple-users-mention-user-view-user-list-and-remove-users-from-conversation.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_team_users_mention_and_remove_participants(self, page, _browser_cookies):
        """Add-with-deselect, avatar overflow, mention/@Everyone, remove-user flow.

        Steps (AFS
        test-specs/chat-interface/l2_team-users-mention-and-remove-participants_ELITEA-2168.md):
        Setup. Seed a conversation with 2 participants (owner + 2 users),
             establishing the "existing conversation with participants"
             precondition the case's own step 1 requires.
        1. Verify PARTICIPANTS USERS section visible, badge "3".
        2. Open Invite Users, select user_1..4 — four chips in order.
        3. Click X on user_4's chip — 3 chips remain.
        4. Click Add (directly — blind-Escape-after-chip-removal gotcha) —
           badge "3" -> "6", popover lists all 6 + "All users" footer.
        5. Expand PARTICIPANTS panel — 5 avatars + "+1"; collapse again.
        6. Open Invite Users, select user_4, Cancel — not added; badge
           stays "6"; excludedUserIds still drops already-added users.
        7. Mention a specific participant via composer "@" — sent, no LLM
           response (message count +1 not +2).
        8. Open Users dropdown, hover, delete icon — "Remove user?" modal.
        9. Click Remove — removed from dropdown and PARTICIPANTS (6 -> 5).
        10. Hover another user, delete, Cancel — not removed (stays 5).
        11. Click "All users" footer — KNOWN DEFECT #1119: no @Everyone
            inserted (soft-asserted).
        12. Via the composer's own "@" -> "Everyone" path (confirmed
            working): sent, no LLM response (message count +1 not +2).
        """
        chat = ChatPage(page)
        team_conversation_api = ConversationAPI(
            browser_cookies=_browser_cookies, project_id=TEAM_PROJECT_ID,
        )
        conv_id: int | None = None
        soft_failures: list[str] = []

        # Registered before Setup so console errors from every step are
        # captured. Known, already-documented noise is filtered so it
        # can't mask a genuinely NEW error on the same flow.
        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not (
                _is_known_project_471_secrets_403(msg)
                or _is_known_version_validator_400(msg)
                or _is_known_checkicon_sx_svg_warning_719(msg)
            ):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — switch to the Team project; open a genuinely blank "
                "conversation; seed 2 participants via Add users; send a "
                "message so they persist and PARTICIPANTS badge reads '3'"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.switch_project(TEAM_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)

                _open_blank_conversation(chat, timeout=NAVIGATION_TIMEOUT)

                chat.open_add_users_modal(timeout=UI_ELEMENT_TIMEOUT)
                # Residual real-mouse hover on the plus-menu button (its own
                # click sequence never moves the mouse away) can leave its
                # MUI Tooltip ("Add files, agents, toolkits and more...")
                # rendered ON TOP of the modal's search field, intermittently
                # intercepting the very next click (confirmed live this
                # implementation — same hover-residue CLASS already
                # documented for participant-row removal, now confirmed to
                # also affect the Add users modal's own open sequence).
                page.mouse.move(0, 0)
                chat.search_and_select_add_user_verified(
                    SETUP_USER_1_QUERY, SETUP_USER_1_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                # Settle each selection's re-render before the next search —
                # back-to-back search_and_select_add_user() calls otherwise
                # race the shared onClickOption callback that both adds the
                # chip AND resets the search input (see
                # ChatPage.wait_for_add_users_chip docstring).
                chat.wait_for_add_users_chip(SETUP_USER_1_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.search_and_select_add_user_verified(
                    SETUP_USER_2_QUERY, SETUP_USER_2_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                chat.wait_for_add_users_chip(SETUP_USER_2_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_add_users_confirm(timeout=UI_ELEMENT_TIMEOUT)
                chat.add_users_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

                initial_count = chat.get_message_count()
                assert initial_count == 0, "Fresh conversation should have no messages yet"

                with page.expect_response(
                    lambda r: r.request.method == "POST" and _is_conversation_create_request(r.url)
                ) as create_info, page.expect_response(
                    lambda r: r.request.method == "POST" and _is_participants_persist_request(r.url)
                ) as participants_info:
                    chat.send_message(SETUP_MESSAGE_TEXT, use_enter=False)

                assert create_info.value.status == 201, (
                    f"Conversation-create request should return 201, got {create_info.value.status}"
                )
                assert participants_info.value.status == 200, (
                    f"Participants-persist request should return 200, got {participants_info.value.status}"
                )

                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=UI_ELEMENT_TIMEOUT)
                match = re.search(r"/chat/(\d+)", page.url)
                assert match, f"Conversation id should appear in the URL after Send, got: {page.url}"
                conv_id = int(match.group(1))

                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_participants_badge_count("3", section="users", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 1 — Verify PARTICIPANTS USERS section is visible on "
                "the existing/precondition conversation"
            ):
                assert chat.is_participants_badge_visible(section="users", timeout=UI_ELEMENT_TIMEOUT), (
                    "PARTICIPANTS USERS badge should be visible on a "
                    "conversation that already has participants"
                )
                badge_count = chat.get_participants_badge_count(section="users", timeout=UI_ELEMENT_TIMEOUT)
                assert badge_count == "3", f"Expected badge '3' (owner + 2 seed users), got {badge_count!r}"

            with allure.step(
                f"Step 2 — Open Invite Users; select {USER_1_NAME!r}, "
                f"{USER_2_NAME!r}, {USER_3_NAME!r}, {USER_4_NAME!r} — four "
                "chips shown, in selection order"
            ):
                chat.open_add_users_modal(timeout=UI_ELEMENT_TIMEOUT)
                # Residual real-mouse hover on the plus-menu button (its own
                # click sequence never moves the mouse away) can leave its
                # MUI Tooltip ("Add files, agents, toolkits and more...")
                # rendered ON TOP of the modal's search field, intermittently
                # intercepting the very next click (confirmed live this
                # implementation — same hover-residue CLASS already
                # documented for participant-row removal, now confirmed to
                # also affect the Add users modal's own open sequence).
                page.mouse.move(0, 0)
                chat.search_and_select_add_user_verified(USER_1_QUERY, USER_1_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_add_users_chip(USER_1_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.search_and_select_add_user_verified(USER_2_QUERY, USER_2_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_add_users_chip(USER_2_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.search_and_select_add_user_verified(USER_3_QUERY, USER_3_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_add_users_chip(USER_3_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.search_and_select_add_user_verified(USER_4_QUERY, USER_4_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_add_users_chip(USER_4_NAME, timeout=UI_ELEMENT_TIMEOUT)

                chip_names = chat.get_add_users_chip_names()
                assert chip_names == [USER_1_NAME, USER_2_NAME, USER_3_NAME, USER_4_NAME], (
                    f"Expected four chips in selection order, got {chip_names!r}"
                )
                assert chat.is_add_users_confirm_enabled(), "Add button should be enabled with 4 selections"

            with allure.step(
                f"Step 3 — Click X on {USER_4_NAME!r}'s chip to deselect — "
                f"{USER_1_NAME!r}/{USER_2_NAME!r}/{USER_3_NAME!r} remain, in order"
            ):
                chat.remove_add_users_chip(USER_4_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chip_names = chat.get_add_users_chip_names()
                assert chip_names == [USER_1_NAME, USER_2_NAME, USER_3_NAME], (
                    f"Expected the remaining three chips in order, got {chip_names!r}"
                )
                assert chat.is_add_users_confirm_enabled(), (
                    "Add button should stay enabled — 3 selections remain > 0"
                )

            with allure.step(
                f"Step 4 — Click Add (directly — no preceding blind "
                f"dropdown-dismiss, AFS gotcha); verify {USER_1_NAME!r}/"
                f"{USER_2_NAME!r}/{USER_3_NAME!r} added to PARTICIPANTS"
            ):
                # Deliberately NOT the unconditional click_add_users_confirm()
                # — it presses Escape unconditionally first, which closes the
                # WHOLE dialog (not a results popper) when nothing is open to
                # dismiss right after a chip-removal action (AFS §
                # Automation Hints — blind-Escape-after-chip-removal gotcha).
                # But removing a chip can ALSO flip the results popper back
                # OPEN (the removed user is no longer excluded, so an empty
                # query matches again — confirmed live this implementation),
                # which then intercepts the Add button click. Dismiss ONLY
                # if the popper is actually visible.
                chat.add_users_confirm_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                if chat.is_add_users_results_open():
                    chat.dismiss_add_users_dropdown()
                chat.add_users_confirm_button.click()
                chat.add_users_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

                chat.wait_for_participants_badge_count("6", section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper_text = popper.text_content() or ""
                for name in (USER_1_NAME, USER_2_NAME, USER_3_NAME, SETUP_USER_1_NAME, SETUP_USER_2_NAME):
                    assert name in popper_text, f"Popover should list {name!r}, got: {popper_text!r}"
                assert "All users" in popper_text, f"Popover should show the 'All users' footer, got: {popper_text!r}"
                chat.dismiss_participants_popover()

                # Resolve the numeric platform user ids needed for steps
                # 8-10's dropdown-row removal — the "Users" dropdown's row
                # testid is keyed by entity_meta.id, which callers don't
                # know ahead of time (only the display name searched for).
                # Step 8 targets user_2 (Levon Dadayan); step 10 targets
                # user_1 (Hrach Sargsyan) per the case's own literal text
                # ("Hover over user_1") and this AFS's own § Test Data
                # mapping — fix round 1 corrected an undocumented drift
                # that had targeted user_3 (Mariam Hakobyan) instead.
                conv_data = team_conversation_api.get_conversation(conv_id)
                participant_id_by_name = {
                    p.get("meta", {}).get("user_name"): p.get("entity_meta", {}).get("id")
                    for p in conv_data.get("participants", [])
                    if p.get("entity_name") == "user"
                }
                for name in (USER_1_NAME, USER_2_NAME):
                    assert participant_id_by_name.get(name) is not None, (
                        f"Expected a resolvable participant id for {name!r} via the "
                        f"conversation API, got participants: {conv_data.get('participants', [])!r}"
                    )

            with allure.step(
                "Step 5 — Expand PARTICIPANTS panel; verify 5 avatars + "
                "'+1' overflow indicator; collapse again"
            ):
                chat.expand_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)
                chat.participants_users_avatar.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                avatar_count = chat.participants_users_avatar.count()
                assert avatar_count == 5, f"Expected exactly 5 avatars with 6 total users, got {avatar_count}"
                overflow_text = (chat.participants_users_overflow_count.text_content() or "").strip()
                assert overflow_text == "+1", f"Expected the overflow indicator to read '+1', got {overflow_text!r}"

                # The collapsed 'chat-participants-badge-users' testid later
                # steps depend on is not rendered at all while expanded
                # (AFS § Concrete Handles panel-state gotcha) — restore it.
                chat.collapse_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                f"Step 6 — Open Invite Users, select {USER_4_NAME!r} again, "
                "then Cancel; verify not added and excludedUserIds still "
                "drops already-added participants"
            ):
                chat.open_add_users_modal(timeout=UI_ELEMENT_TIMEOUT)
                # Residual real-mouse hover on the plus-menu button (its own
                # click sequence never moves the mouse away) can leave its
                # MUI Tooltip ("Add files, agents, toolkits and more...")
                # rendered ON TOP of the modal's search field, intermittently
                # intercepting the very next click (confirmed live this
                # implementation — same hover-residue CLASS already
                # documented for participant-row removal, now confirmed to
                # also affect the Add users modal's own open sequence).
                page.mouse.move(0, 0)
                assert not chat.is_add_users_option_present(USER_1_NAME, timeout=2000), (
                    f"Already-added participant {USER_1_NAME!r} should be "
                    "excluded from a fresh search (excludedUserIds)"
                )
                chat.search_and_select_add_user_verified(USER_4_QUERY, USER_4_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_add_users_cancel(timeout=UI_ELEMENT_TIMEOUT)
                chat.add_users_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

                badge_count = chat.get_participants_badge_count(section="users", timeout=UI_ELEMENT_TIMEOUT)
                assert badge_count == "6", f"Badge should still read '6' after Cancel, got {badge_count!r}"
                popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper_text = popper.text_content() or ""
                assert USER_4_NAME not in popper_text, (
                    f"{USER_4_NAME!r} should NOT be added after Cancel, popover: {popper_text!r}"
                )
                chat.dismiss_participants_popover()

            with allure.step(
                f"Step 7 — Mention {MENTION_TARGET_NAME!r} via composer '@' "
                "and send; verify sent with no LLM response"
            ):
                initial_count = chat.get_message_count()
                chat.open_user_mention_popper(timeout=UI_ELEMENT_TIMEOUT)
                chat.select_user_mention(MENTION_TARGET_NAME, timeout=UI_ELEMENT_TIMEOUT)

                composer_text = chat.message_input.text_content() or ""
                assert composer_text == f"@{MENTION_TARGET_NAME} ", (
                    f"Expected the mention to replace '@' with "
                    f"'@{MENTION_TARGET_NAME} ', got: {composer_text!r}"
                )

                chat.message_input.click()
                chat.message_input.press("End")
                chat.message_input.press_sequentially(MENTION_MESSAGE_SUFFIX, delay=50)
                chat.send_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                chat.send_button.click(force=True)

                chat.wait_for_message_count(initial_count + 1, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_network(timeout=AI_RESPONSE_TIMEOUT)
                message_count = chat.get_message_count()
                assert message_count == initial_count + 1, (
                    "A to-user mention send should add exactly ONE message "
                    f"(no LLM response) — expected {initial_count + 1}, got {message_count}"
                )

            with allure.step(
                f"Step 8 — Open Users dropdown, hover {USER_2_NAME!r}, "
                "click delete icon — 'Remove user?' modal appears"
            ):
                dialog = chat.open_remove_user_dialog(
                    participant_id_by_name[USER_2_NAME], timeout=UI_ELEMENT_TIMEOUT,
                )
                dialog_text = (dialog.text_content() or "").strip()
                expected_dialog_text = (
                    f"Remove user?Are you sure to remove the {USER_2_NAME} user from chat?CancelRemove"
                )
                assert dialog_text == expected_dialog_text, (
                    f"Expected dialog text {expected_dialog_text!r}, got {dialog_text!r}"
                )

            with allure.step(
                f"Step 9 — Click Remove; verify {USER_2_NAME!r} removed "
                "from dropdown and PARTICIPANTS (6 -> 5)"
            ):
                Dialog.click_button(dialog, "Remove")
                Dialog.wait_for_hidden(page, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_participants_badge_count("5", section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper_text = popper.text_content() or ""
                assert USER_2_NAME not in popper_text, (
                    f"{USER_2_NAME!r} should no longer be listed, got: {popper_text!r}"
                )
                chat.dismiss_participants_popover()

            with allure.step(
                f"Step 10 — Hover {USER_1_NAME!r} (case's own literal "
                "'user_1'), click delete, then Cancel; verify not removed "
                "(stays 5)"
            ):
                dialog = chat.open_remove_user_dialog(
                    participant_id_by_name[USER_1_NAME], timeout=UI_ELEMENT_TIMEOUT,
                )
                Dialog.click_button(dialog, "Cancel")
                Dialog.wait_for_hidden(page, timeout=UI_ELEMENT_TIMEOUT)

                badge_count = chat.get_participants_badge_count(section="users", timeout=UI_ELEMENT_TIMEOUT)
                assert badge_count == "5", f"Badge should still read '5' after Cancel, got {badge_count!r}"
                popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper_text = popper.text_content() or ""
                assert USER_1_NAME in popper_text, (
                    f"{USER_1_NAME!r} should still be listed after Cancel, got: {popper_text!r}"
                )

            with allure.step(
                "Step 11 — Click 'All users' footer; verify @Everyone is "
                "inserted (KNOWN DEFECT #1119 — soft-asserted)"
            ):
                chat.participants_all_users_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                chat.participants_all_users_button.click()
                composer_text_after_click = chat.message_input.text_content() or ""
                if composer_text_after_click != "@Everyone ":
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1119: "
                        "clicking 'All users' in the Participants dropdown should insert "
                        f"'@Everyone ' into the composer, got: {composer_text_after_click!r}"
                    )
                chat.dismiss_participants_popover()
                # Reset the composer regardless of the defect's outcome so
                # step 12 starts from a known-empty state.
                chat.message_input.click()
                chat.message_input.press("Control+a")
                chat.message_input.press("Backspace")

            with allure.step(
                "Step 12 — Via the composer's own '@' -> 'Everyone' path "
                "(confirmed working); type 'hi' and send — no LLM response"
            ):
                initial_count = chat.get_message_count()
                chat.open_user_mention_popper(timeout=UI_ELEMENT_TIMEOUT)
                chat.select_user_mention("Everyone", timeout=UI_ELEMENT_TIMEOUT)

                composer_text = chat.message_input.text_content() or ""
                assert composer_text == "@Everyone ", (
                    f"Expected the mention to insert '@Everyone ', got: {composer_text!r}"
                )

                chat.message_input.click()
                chat.message_input.press("End")
                chat.message_input.press_sequentially(MENTION_MESSAGE_SUFFIX, delay=50)
                chat.send_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                chat.send_button.click(force=True)

                chat.wait_for_message_count(initial_count + 1, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_network(timeout=AI_RESPONSE_TIMEOUT)
                message_count = chat.get_message_count()
                assert message_count == initial_count + 1, (
                    "A to-everyone mention send should add exactly ONE "
                    f"message (no LLM response) — expected {initial_count + 1}, got {message_count}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    f"Unexpected console errors: {[m.text for m in console_messages]!r}"
                )

            if soft_failures:
                pytest.fail(
                    "Soft assertion(s) failed (known isolated product "
                    "defect, not test/infrastructure — the add/mention/"
                    "remove flow above passed cleanly):\n" + "\n".join(soft_failures)
                )
        finally:
            if conv_id:
                try:
                    # A failure mid-flow can leave the "Add users" dialog (or
                    # another overlay) open, which blocks the sidebar hover
                    # below and would otherwise leave conv_id orphaned for
                    # the next pytest-rerun attempt to stumble onto
                    # (confirmed live this implementation — see
                    # _open_blank_conversation's docstring).
                    page.keyboard.press("Escape")
                    chat.open_conversation_context_menu(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                    chat.click_conversation_menu_item("delete", timeout=UI_ELEMENT_TIMEOUT)
                    delete_response = chat.confirm_delete_conversation(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                    assert delete_response.status in (200, 204), (
                        f"DELETE for conversation {conv_id} should succeed, got {delete_response.status}"
                    )
                    logger.info("Cleaned up conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Failed to clean up conversation %s: %s", conv_id, exc)
