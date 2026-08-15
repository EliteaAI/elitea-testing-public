"""UI Test for ELITEA-2188 — Chat: Team Project, Public Conversation Marked
with Green People Icon in Chat List.

Verifies, in a Team project: making a fresh conversation public via the
existing "Make public" context-menu action turns its sidebar multi-user
icon GREEN (asserted via the new ``data-conversation-type="public"`` state
attribute, not a raw SVG fill read); a private conversation WITH
participants shows the SAME icon wrapper but never green (the sharper
negative control the case's own wording — "private conversations" — calls
for, not merely a no-icon-at-all single-owner conversation); and the
now-public conversation's full message history, input, and PARTICIPANTS
USERS section remain fully functional after the publicness change.

Spec: test-specs/chat-interface/l3_public-conversation-green-icon-in-chat-list_ELITEA-2188.md

New page-object surface (this implementation, ``ChatPage``, all additive —
no existing method or its caller is modified):
- ``wait_for_conversation_type()`` — sibling of the pre-existing
  ``wait_for_conversation_multi_user_icon()``, asserts the sidebar item's
  ``data-conversation-type`` state attribute (new this pass) instead of
  the presence-only ``data-has-icon`` (which is ``"true"`` for BOTH
  ``public`` and ``private_with_users`` and cannot distinguish them).
- ``confirm_make_public()`` — clicks the make-public-confirm button and
  returns the underlying ``PUT .../conversation/prompt_lib/...`` response,
  same "network response proves server persistence" idiom as the
  pre-existing ``confirm_delete_conversation()``.
- ``make_public_confirm_dialog`` / ``make_public_confirm_button`` /
  ``make_public_cancel_button`` — new ``LocatorDescriptor`` fields for the
  "Make public" confirmation dialog, which previously carried ZERO
  testids at all (AFS § Concrete Handles gap #1).

Testid gaps filled this implementation (``add-data-testid``, pushed to
``automation/testids``, EliteaAI/EliteaUI@7292e18f):
- ``chat-conversation-make-public-confirm-dialog`` /
  ``chat-conversation-make-public-confirm-button`` /
  ``chat-conversation-make-public-cancel-button`` — threaded through
  ``DotMenu.jsx``'s shared ``Modal.BaseModal`` confirm-dialog branch via
  new caller-supplied ``dialogTestId``/``confirmButtonTestId``/
  ``cancelButtonTestId`` props (``ConversationItem.jsx``'s "make-public"
  menu item is the only call site that sets them — same
  caller-supplied-prop precedent as the pre-existing ``submenuTestId``).
- ``data-conversation-type`` — new state attribute (existing
  ``conversation-multi-user-icon`` testid, identity unchanged) on
  ``ConversationItem.jsx``, one-line JSX addition per the
  testid=identity/state=data-* ruling (AFS § Concrete Handles gap #2).

No NEW product defects found (AFS § Known Defects Found — both testid gaps
above are additions, not defects; the underlying publicness behavior works
correctly). One PRE-EXISTING, already-filed defect re-confirmed during this
implementation (not re-filed, filtered per the established idiom):
- EliteaAI/elitea-testing-public#719 — the "Add users" picker's checkmark-icon
  ``sx``-on-raw-``<svg>`` console warning, same as ELITEA-2167/2168's own
  conversation-B-setup Add-users flow. Filtered below, not automated as a
  hard-fail.

Infrastructure-class races found and fixed during implementation (not product
defects — all three are test-side timing, confirmed via live exploration):
- ``_open_blank_conversation()`` needed the "genuinely blank" settle-and-retry
  guard (same EliteaAI/elitea-testing-public#1082 race class
  ``test_invite_users_add_cancel_close.py`` already documents) — a bare
  "+Chat click -> greeting visible" check is not sufficient on this shared dev
  backend for a SECOND back-to-back +Chat click in one test.
- The "Add users" modal's own MUI close transition can still be resolving
  when the very next action targets the composer's send button; waiting for
  ``add_users_dialog`` to reach ``state="hidden"`` before sending removes the race.
- Known, already-documented sidebar staleness defect
  (EliteaAI/elitea-testing-public#989, same class first hit in
  ``test_invite_users_add_cancel_close.py`` Step 10): the sidebar's cached
  ``conversationType``/``users_count`` does not live-update on a participant
  or publicness change — a ``page.reload()`` (the suite's established fix)
  is required before re-reading ``conversation-multi-user-icon``'s state.
"""

import logging
import re
import time

import allure
import pytest
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.p3, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds) — same values as the sibling chat suite
# (test_invite_users_add_cancel_close.py / test_team_users_mention_and_remove_participants.py)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 30_000

# Team project — the only project where "Make public" / "Invite Users" are
# offered at all (AFS § Preconditions).
TEAM_PROJECT_ID = "471"

# Second participant for conversation B, the private-with-participants
# negative control (AFS § Test Data — same environment user the sibling
# ELITEA-2167/2168 tests already established via this "sa" partial search).
SECOND_PARTICIPANT_QUERY, SECOND_PARTICIPANT_NAME = "sa", "Hrach Sargsyan"

CONVERSATION_A_MESSAGE = "hello"
CONVERSATION_B_MESSAGE = "hi"

# ``ConversationItem.jsx``'s own ``getConversationType()`` values — asserted
# via the new ``data-conversation-type`` attribute (AFS § Concrete Handles
# gap #2; ``ChatPage.wait_for_conversation_type()``).
CONVERSATION_TYPE_PUBLIC = "public"
CONVERSATION_TYPE_PRIVATE_WITH_USERS = "private_with_users"


def _is_known_project_471_secrets_403(msg) -> bool:
    """Filter the pre-existing, already-documented project-471 ``secrets`` 403.

    Fires on every page load in this project regardless of any action taken
    (AFS § Network Behavior; same idiom as
    ``test_invite_users_add_cancel_close.py``'s equivalent filter).
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default/471" in (text + location_url)


def _is_known_checkicon_sx_svg_warning_719(msg) -> bool:
    """Filter the already-filed, isolated console defect EliteaAI/elitea-testing-public#719.

    Fires on every "Add users" option selection — ``AutoCompleteDropDown.jsx``'s
    ``<CheckedIcon sx={...} />`` forwards an MUI ``sx`` prop onto a raw
    imported ``<svg>`` (not an MUI ``SvgIcon``), producing this React console
    warning. Confirmed live this implementation on this test's own conversation
    B setup (Step 2's Add-users flow) — already filed and filtered by this
    exact idiom in ``test_invite_users_add_cancel_close.py`` /
    ``test_team_users_mention_and_remove_participants.py``; scoped to this
    exact, already-ticketed warning text/component so any OTHER console error
    still fails the assertion below.
    """
    text = msg.text
    return "Invalid value for prop" in text and "sx" in text and "svg" in text and "CheckedIcon" in text


def _poll_blank_state_holds(
    chat: ChatPage,
    blank_url_pattern: "re.Pattern[str]",
    settle_ms: int = 1500,
    poll_interval_s: float = 0.25,
) -> tuple[bool, str]:
    """Poll message-count + URL at short intervals across *settle_ms*,
    instead of a fixed-latency sleep-then-recheck-once.

    Same idiom as ``test_invite_users_add_cancel_close.py``'s identically-
    named helper: exits the instant either signal flips (a definitive,
    immediate result) rather than waiting out the full window and
    discovering the reversion only at the end.
    """
    deadline = time.monotonic() + settle_ms / 1000.0
    while time.monotonic() < deadline:
        time.sleep(poll_interval_s)
        count = chat.get_message_count()
        url = chat.page.url
        if count != 0 or not blank_url_pattern.search(url):
            return False, f"blank state reverted mid-settle (url={url!r}, message_count={count})"
    return True, ""


def _open_blank_conversation(chat: ChatPage, timeout: int = NAVIGATION_TIMEOUT) -> None:
    """Click +Chat and confirm a GENUINELY blank, unsent conversation opened
    (no stale/restored conversation silently left on screen).

    Known, filed defect class (EliteaAI/elitea-testing-public#1082, first
    documented in ``test_invite_users_add_cancel_close.py``): a bare
    "greeting visible" check is not sufficient on this shared dev backend
    — the SPA can restore the last-viewed conversation from browser/session
    storage AFTER the blank greeting was already observed, a DELAYED
    effect that wins a race against a check performed too early. Confirmed
    live this implementation: this exact race hit conversation B's setup
    (the second back-to-back +Chat click in one test), landing back on
    conversation A instead of a fresh blank one and causing the Add-users
    + Send flow to silently target the wrong conversation. Guards with a
    settle-and-recheck across a short window (same idiom as
    ``ChatPage.wait_for_message_content_stable()``), retried up to 3 times.
    """
    blank_url_pattern = re.compile(r"/chat/?(?:\?.*)?$")
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
        settled, reason = _poll_blank_state_holds(chat, blank_url_pattern)
        if not settled:
            last_reason = reason
            logger.warning(
                "Blank conversation reverted to a restored one during "
                "settling (attempt %d) — retrying (see "
                "_open_blank_conversation docstring)",
                attempt + 1,
            )
            continue
        return
    raise AssertionError(
        f"Could not open a genuinely blank conversation after 3 attempts: {last_reason}"
    )


def _send_message_and_get_id(chat: ChatPage, message: str) -> int:
    """Send *message* in the currently-open (already-blank) conversation,
    return its numeric id once persisted.

    Deliberately does NOT open a blank conversation itself (unlike a
    combined "open+send" helper would) — conversation B's flow needs to
    queue an invited participant (``open_add_users_modal()`` /
    ``search_and_select_add_user()``) on the SAME blank conversation
    BEFORE the first Send, which is what actually persists the queued
    participant server-side (AFS § Network Behavior). Re-opening a blank
    conversation between the invite and the Send would discard the queue.
    """
    initial_count = chat.get_message_count()
    chat.send_message(message, use_enter=False)
    chat.page.wait_for_url(re.compile(r"/chat/\d+"), timeout=NAVIGATION_TIMEOUT)
    chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
    chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)
    match = re.search(r"/chat/(\d+)", chat.page.url)
    assert match, f"Expected a conversation id in the URL after sending, got: {chat.page.url}"
    return int(match.group(1))


class TestPublicConversationGreenIcon:
    """ELITEA-2188: Chat – Team Project – Public Conversation Marked with
    Green People Icon in Chat List (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2188_chat-team-project-public-conversation-marked-with-green-people-icon-in-chat-list.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_public_conversation_shows_green_icon_in_chat_list(self, page, _browser_cookies):
        """Making a conversation public turns its sidebar icon green;
        private-with-participants conversations never show green.

        Steps (AFS
        test-specs/chat-interface/l3_public-conversation-green-icon-in-chat-list_ELITEA-2188.md):
        1. Switch to the Team project; confirm the conversation list loads.
        2. Create conversation A (to be made public) and conversation B
           (private control, with a second participant).
        3. Make conversation A public via the context menu; confirm; verify
           the PUT request returns 200.
        4. Re-read conversation A's sidebar row; verify its icon settles to
           ``data-conversation-type="public"`` (green).
        5. Compare against conversation B; verify it stays
           ``"private_with_users"`` (never ``"public"``).
        6. Click conversation A; verify full message history renders.
        7. Verify the message input and PARTICIPANTS USERS section.
        """
        chat = ChatPage(page)
        conv_a_id: int | None = None
        conv_b_id: int | None = None

        # Registered before Setup so console errors from every step are
        # captured — not just from a later one. The known, already-
        # documented project-471 secrets 403 (AFS § Network Behavior) is
        # filtered so it can't mask a genuinely new error on this flow.
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
                "Step 1 — Switch to the Team project; confirm the conversations "
                "list loads"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.switch_project(TEAM_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)
                selected_project_text = chat.get_selected_project_text()
                assert "Elitea Testing Team" in selected_project_text, (
                    "Project selector should show 'Elitea Testing Team' after "
                    f"switching, got: {selected_project_text!r}"
                )
                assert chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT), (
                    "Conversations list should populate after switching to the "
                    "Team project"
                )

            with allure.step(
                "Step 2 — Create conversation A (to be made public) and "
                "conversation B (private control, WITH a second participant)"
            ):
                _open_blank_conversation(chat, timeout=NAVIGATION_TIMEOUT)
                conv_a_id = _send_message_and_get_id(chat, CONVERSATION_A_MESSAGE)
                assert chat.is_conversation_in_group(conv_a_id, "today", timeout=UI_ELEMENT_TIMEOUT), (
                    f"Conversation A ({conv_a_id}) should render under the Today group"
                )

                _open_blank_conversation(chat, timeout=NAVIGATION_TIMEOUT)
                chat.open_add_users_modal(timeout=UI_ELEMENT_TIMEOUT)
                chat.search_and_select_add_user(
                    SECOND_PARTICIPANT_QUERY, SECOND_PARTICIPANT_NAME, timeout=UI_ELEMENT_TIMEOUT,
                )
                chat.click_add_users_confirm(timeout=UI_ELEMENT_TIMEOUT)
                # Infrastructure-class flake guard (confirmed live this
                # implementation): the 'Add users' modal's own MUI Dialog
                # close transition can still be resolving when the very
                # next action targets the composer's send button —
                # send_button.click(force=True, ...) bypasses actionability
                # waits, so it can fire during that transition and be lost.
                # Waiting for the dialog to genuinely leave the DOM (a real
                # framework wait, not a sleep) removes the race.
                chat.add_users_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                conv_b_id = _send_message_and_get_id(chat, CONVERSATION_B_MESSAGE)
                assert chat.is_conversation_in_group(conv_b_id, "today", timeout=UI_ELEMENT_TIMEOUT), (
                    f"Conversation B ({conv_b_id}) should render under the Today group"
                )
                # Conversation B has a second participant besides the owner —
                # this is the case's own step-3 negative control (a
                # WITH-PARTICIPANTS private conversation), sharper than a
                # single-owner one: it proves the distinguishing factor is
                # PUBLICNESS, not mere icon presence (AFS § Test Data).
                #
                # Known, already-documented defect class (EliteaAI/elitea-
                # testing-public#989, first hit in
                # test_invite_users_add_cancel_close.py Step 10): sidebar
                # list items cache their own users_count/conversationType at
                # fetch time and do NOT live-update as participants change —
                # confirmed live this session, ``data-conversation-type``
                # stayed "private_without_users" straight after Send, well
                # after the server had actually persisted the participant
                # (verified by reloading and re-reading the same element).
                # Reload is the established fix in this suite (same idiom):
                # forces a full client-state re-derivation. The icon
                # assertion itself stays a HARD assert — the reload is a
                # workaround for the known staleness window, not a mask.
                page.reload(wait_until="domcontentloaded")
                chat.wait_for_page_load()
                chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_conversation_multi_user_icon(
                    conv_b_id, expected_has_icon=True, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 3 — Make conversation A public via the context menu; "
                "confirm; verify the PUT request returns 200"
            ):
                chat.open_conversation_context_menu(conv_a_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_conversation_menu_item("make-public", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.make_public_confirm_dialog.is_visible(), (
                    "'Make public' confirmation dialog should be visible"
                )
                make_public_response = chat.confirm_make_public(conv_a_id, timeout=UI_ELEMENT_TIMEOUT)
                assert make_public_response.status == 200, (
                    "PUT .../conversation/prompt_lib/.../{id} should return 200 "
                    f"on make-public confirm, got {make_public_response.status}"
                )

            with allure.step(
                "Step 4 — Re-read conversation A's sidebar row; verify its icon "
                "settles to data-conversation-type=\"public\" (green)"
            ):
                # Same known staleness class (#989) as Step 2 above — the
                # sidebar's cached conversationType does not live-update on
                # a publicness change either (confirmed live this session);
                # reload forces the same full client-state re-derivation.
                page.reload(wait_until="domcontentloaded")
                chat.wait_for_page_load()
                chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_conversation_type(
                    conv_a_id, CONVERSATION_TYPE_PUBLIC, timeout=UI_ELEMENT_TIMEOUT
                )
                chat.wait_for_conversation_multi_user_icon(
                    conv_a_id, expected_has_icon=True, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 5 — Compare against conversation B; verify it stays "
                "private_with_users, never public"
            ):
                chat.wait_for_conversation_type(
                    conv_b_id, CONVERSATION_TYPE_PRIVATE_WITH_USERS, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 6 — Click the public conversation; verify full history"):
                chat.click_conversation_in_group(conv_a_id, "today", timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_conversation_url(str(conv_a_id), timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_page_load()
                chat.wait_for_message_count(2, timeout=UI_ELEMENT_TIMEOUT)
                message_count = chat.get_message_count()
                assert message_count == 2, (
                    f"Expected 2 messages (user + AI response) in conversation A, got {message_count}"
                )
                user_body = ChatPage._extract_message_body(chat.messages_container.nth(0))
                assert CONVERSATION_A_MESSAGE in user_body, (
                    f"Message 0 should be the seeded user message, got: {user_body!r}"
                )
                ai_body = ChatPage._extract_message_body(chat.messages_container.nth(1))
                assert ai_body.strip(), "Message 1 (AI response) should be non-empty"

            with allure.step(
                "Step 7 — Verify the message input and PARTICIPANTS USERS section"
            ):
                assert chat.message_input.is_visible() and chat.message_input.is_editable(), (
                    "Message input should be visible and editable on the now-"
                    "public conversation"
                )
                badge_count = chat.get_participants_badge_count(
                    section="users", timeout=UI_ELEMENT_TIMEOUT
                )
                popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper_text = popper.text_content() or ""
                assert "Users" in popper_text, (
                    f"Participants popover should show a 'Users' heading, got: {popper_text!r}"
                )
                # The heading text alone is STATIC —
                # UsersParticipantDropdown/index.jsx renders it
                # unconditionally, above the dynamic participant-row list —
                # so it proves the popover opened, never that any
                # participant is actually listed (reviewer finding, PR
                # #1562 round 1). Assert the DYNAMIC row content itself via
                # the same PARTICIPANT_ROW_PREFIX template
                # ELITEA-2167/2168/2095's remove/mention flows already
                # resolve rows through, and cross-check against the
                # collapsed badge's own independently-rendered count (AFS
                # § step 7 — "lists the conversation's participants (owner
                # at minimum)").
                participant_rows = popper.locator(chat.PARTICIPANT_ROW_PREFIX)
                participant_rows.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                row_count = participant_rows.count()
                assert row_count >= 1, (
                    "Users popover should list at least the owner as a "
                    f"participant, got {row_count} rows"
                )
                assert str(row_count) == badge_count, (
                    f"Popover row count ({row_count}) should match the "
                    f"collapsed badge's own count ({badge_count!r})"
                )
                chat.dismiss_participants_popover()

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    f"Unexpected console errors: {[m.text for m in console_messages]!r}"
                )

        finally:
            for cid in (conv_a_id, conv_b_id):
                if not cid:
                    continue
                try:
                    chat.open_conversation_context_menu(cid, timeout=UI_ELEMENT_TIMEOUT)
                    chat.click_conversation_menu_item("delete", timeout=UI_ELEMENT_TIMEOUT)
                    delete_response = chat.confirm_delete_conversation(cid, timeout=UI_ELEMENT_TIMEOUT)
                    assert delete_response.status in (200, 204), (
                        f"DELETE for conversation {cid} should succeed, got {delete_response.status}"
                    )
                    logger.info("Cleaned up conversation %s", cid)
                except Exception as exc:
                    logger.warning("Failed to clean up conversation %s: %s", cid, exc)
