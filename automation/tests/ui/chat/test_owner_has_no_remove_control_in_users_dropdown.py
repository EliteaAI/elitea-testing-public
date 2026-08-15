"""UI Test for ELITEA-2172 — Chat: Team Project, Conversation Owner Cannot
Be Removed from Participants List.

Verifies that the conversation owner's own row in the "Users" participants
dropdown never reveals a delete/"Remove user" control (hover or otherwise),
while every non-owner row's control DOES reveal on hover, in the SAME
dropdown instance — ruling out a stale-popover or timing artifact.

Spec: test-specs/chat-interface/l2_conversation-owner-has-no-remove-control-in-users-dropdown_ELITEA-2172.md

Mechanism note (AFS step 2 — not a case-text drift, a source-confirmed
clarification): the product does not carry an explicit "is conversation
owner" flag the UI reads for this check. ``UserMenu.jsx``'s per-row
``isSelectable = selectable && user.entity_meta?.id !== currentUserId``
implements "you cannot remove yourself", not a distinct owner role. In
this single-account testing environment (the dev-token account both
CREATES every conversation it opens AND IS the currently-logged-in
session) the two concepts are indistinguishable and produce identical,
case-text-satisfying behavior — asserting against the owner's row
faithfully verifies the case's own intent.

New page-object surface (this implementation, ``ChatPage``, additive —
no existing method or its caller is modified):
- ``hover_participant_user_row(user_id, timeout)`` — read-only sibling of
  ``open_remove_user_dialog()``: hovers a Users-dropdown row and returns
  its scoped "Remove user" button Locator WITHOUT clicking it, so the
  caller can assert visibility with a web-first ``expect()`` rather than
  clicking a control that, for the owner's row, is never actionable.

No new testids required — every handle this case needs (``chat-participants-
badge-button``, ``chat-participant-row-user_{userId}_``,
``chat-participant-remove-button``) already exists on ``origin/main``,
added by the merged ELITEA-2168 implementation (AFS § Concrete Handles,
fresh-fetch-verified this session).

Known defects: none. Live product behavior matches the case's expected
result exactly (AFS § Known Defects Found).
"""

import logging
import re

import allure
import pytest
from api import ConversationAPI
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds) — same values as the sibling chat suite
# (test_team_users_mention_and_remove_participants.py / test_invite_users_add_cancel_close.py)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 30_000

# Team project — the only project where "Invite Users" is offered at all
# (PlusChatButton.jsx's !isPrivateProject guard) — AFS § Preconditions.
TEAM_PROJECT_ID = "471"

# Non-owner participant seeded for this case's own positive control (AFS §
# Test Data — same name/query ELITEA-2168 already established for continuity).
NON_OWNER_QUERY, NON_OWNER_NAME = "sa", "Hrach Sargsyan"

SETUP_MESSAGE_TEXT = "setup message"


def _is_conversation_create_request(url: str) -> bool:
    """Match the POST that creates the conversation (AFS § Network Behavior)."""
    return bool(re.search(rf"/elitea_core/conversations/prompt_lib/{TEAM_PROJECT_ID}/?(\?|$)", url))


def _is_participants_persist_request(url: str) -> bool:
    """Match the POST that persists the queued invited user as a real participant
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

    Fires on "Add users" option selection — ``AutoCompleteDropDown.jsx``'s
    ``<CheckedIcon sx={...} />`` forwards an MUI ``sx`` prop onto a raw
    imported ``<svg>``, producing this React console warning. Re-confirmed
    live this session (AFS § Known Defects Found) — filtered here, not
    automated as a hard-fail."""
    text = msg.text
    return "Invalid value for prop" in text and "sx" in text and "svg" in text and "CheckedIcon" in text


def _open_blank_conversation(chat: ChatPage, timeout: int = NAVIGATION_TIMEOUT) -> None:
    """Click +Chat and confirm a genuinely blank, unsent conversation opened.

    Infrastructure-class flake guard (issue #1082, re-confirmed live per
    this feature's AFS): ``click_create_conversation()`` only waits for the
    message input to be visible, which is trivially true on ANY
    conversation — it does not itself prove navigation to a NEW
    conversation happened. Retries the click (real re-clicks, not a sleep)
    if the new-conversation greeting doesn't appear, OR if it appears but
    the conversation still has message history, OR if the URL already
    carries a numeric conversation id.

    Hardening beyond the sibling chat suite's own copy of this helper
    (confirmed live this implementation, on this heavily-used shared dev
    backend — issue #1082's own signature, worse under today's batch
    load): ``get_message_count()`` reads the message list SYNCHRONOUSLY
    (Playwright ``.count()``, no auto-wait), so it can transiently read 0
    on a landed STALE conversation whose message list simply hasn't
    finished its async fetch/render yet — a false "looks blank" that a
    moment later turns out not to be (reproduced live: the very
    conversation this hit, ``/chat/420`` "Review attached documents", is
    the SAME shared conversation the AFS's own exploration session used).
    The router URL has no such race — a genuinely fresh/draft conversation
    always stays on the bare ``/chat`` route (no id) until the first
    Send, while landing on ANY existing conversation immediately shows
    ``/chat/<id>`` in the URL — so it is checked as an ADDITIONAL,
    non-racy signal alongside the message-count check.
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


class TestOwnerHasNoRemoveControlInUsersDropdown:
    """ELITEA-2172: Chat – Team Project – Conversation Owner Cannot Be
    Removed from Participants List (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2172_chat-team-project-conversation-owner-cannot-be-removed-from-participants-list.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_owner_has_no_remove_control_in_users_dropdown(self, page, _browser_cookies):
        """Owner row never reveals a delete control; non-owner rows do.

        Steps (AFS
        test-specs/chat-interface/l2_conversation-owner-has-no-remove-control-in-users-dropdown_ELITEA-2172.md):
        Setup. Seed a conversation with the owner + 1 non-owner participant.
        1. Open USERS dropdown — both rows present.
        2. Identify the owner via the conversation API (``author_id`` match).
        3-4. Hover the owner's row — no "Remove user" icon reveals.
        5. Hover the non-owner's row (same dropdown) — icon DOES reveal.
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
                "Setup — switch to the Team project; open a genuinely blank "
                "conversation; seed 1 non-owner participant via Add users; "
                "send a message so owner + invited user both persist as "
                "real PARTICIPANTS and PARTICIPANTS badge reads '2'"
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
                chat.search_and_select_add_user_verified(
                    NON_OWNER_QUERY, NON_OWNER_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                chat.wait_for_add_users_chip(NON_OWNER_NAME, timeout=UI_ELEMENT_TIMEOUT)
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
                chat.wait_for_participants_badge_count("2", section="users", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 1 — Open a conversation, click avatar group to open "
                "USERS dropdown — dropdown shows all participants"
            ):
                popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper_text = popper.text_content() or ""
                assert NON_OWNER_NAME in popper_text, (
                    f"Popover should list {NON_OWNER_NAME!r}, got: {popper_text!r}"
                )
                # Left open deliberately (not dismissed here): confirmed live
                # this implementation that Escape has no effect on this
                # popper (see ChatPage.hover_participant_user_row's
                # docstring) — steps 3-4's own call closes it via a real
                # outside click before reopening, so no separate dismiss is
                # needed (or effective) here.

            with allure.step(
                "Step 2 — Identify the conversation owner via the "
                "conversation API (author_id match on the participants array)"
            ):
                # A bare "entity_name == 'user'" filter is ambiguous once a
                # non-owner user is also a real participant (both carry
                # entity_name == "user") — the sibling chat suite's own
                # ELITEA-2167 test documents this exact non-determinism.
                # Matching on entity_meta.id == author_id is the
                # deterministic resolution, and it doubles as this case's
                # own step-2 "identify the owner" verification.
                conv_data = team_conversation_api.get_conversation(conv_id)
                owner_id = conv_data.get("author_id")
                assert owner_id is not None, (
                    f"Expected a non-empty author_id from the conversation API, got: {conv_data!r}"
                )
                participants = conv_data.get("participants", [])
                owner_participant = next(
                    (
                        p for p in participants
                        if p.get("entity_name") == "user" and p.get("entity_meta", {}).get("id") == owner_id
                    ),
                    None,
                )
                assert owner_participant is not None, (
                    "Conversation API response should include a 'user' "
                    f"participant entry matching the owner (author_id={owner_id}), "
                    f"got participants: {participants!r}"
                )
                owner_name = owner_participant.get("meta", {}).get("user_name", "")
                assert owner_name, "Expected a non-empty owner display name from the API"
                assert owner_name in popper_text, (
                    f"Owner {owner_name!r} should have been listed in step 1's popover, got: {popper_text!r}"
                )

                non_owner_participant = next(
                    (
                        p for p in participants
                        if p.get("entity_name") == "user" and p.get("entity_meta", {}).get("id") != owner_id
                    ),
                    None,
                )
                assert non_owner_participant is not None, (
                    f"Expected a resolvable non-owner participant id, got participants: {participants!r}"
                )
                non_owner_id = non_owner_participant.get("entity_meta", {}).get("id")
                assert non_owner_id is not None, (
                    "Expected a resolvable entity_meta.id for the non-owner "
                    f"participant, got: {non_owner_participant!r}"
                )

            with allure.step(
                "Steps 3-4 — Hover the owner's row; verify no 'Remove user' "
                "icon appears — owner row has no delete control"
            ):
                owner_remove_button = chat.hover_participant_user_row(owner_id, timeout=UI_ELEMENT_TIMEOUT)
                # Web-first, polling assertion (AFS § Automation Hints — the
                # button is ALWAYS present in the DOM, only ever
                # `visibility: hidden` for the owner's row, so
                # `not_to_be_visible()` is the correct read, never
                # `to_have_count(0)`, which would pass vacuously if the row
                # itself failed to resolve).
                expect(owner_remove_button).not_to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                f"Step 5 — Hover {NON_OWNER_NAME!r}'s row (same dropdown "
                "instance) — verify the 'Remove user' icon DOES appear, "
                "contrasting directly with the owner row's absence above"
            ):
                non_owner_remove_button = chat.hover_participant_user_row(
                    non_owner_id, timeout=UI_ELEMENT_TIMEOUT,
                )
                expect(non_owner_remove_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                # Left open deliberately — same Escape-has-no-effect finding
                # as Step 1; the popper being open doesn't block the
                # side-channel check or the finally-block cleanup below
                # (sidebar context menu, unrelated region of the page).

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    f"Unexpected console errors: {[m.text for m in console_messages]!r}"
                )
        finally:
            if conv_id:
                try:
                    # A failure mid-flow can leave the "Add users" dialog
                    # (or another overlay) open, which blocks the sidebar
                    # hover below (same class already documented for the
                    # sibling chat suite's cleanup).
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
