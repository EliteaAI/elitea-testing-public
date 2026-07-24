"""UI Test for ELITEA-2170 — Chat: Team Project, Remove User from
Conversation via the USERS Dropdown + Confirm Dialog.

Verifies that a Team-project conversation's participant (invited via the
existing "Add users" modal flow) can be removed through the PARTICIPANTS
USERS dropdown: hovering a specific user's row reveals a trash-bin icon
with a "Remove user" tooltip, clicking it opens a "Remove user?" confirm
dialog with the exact live body text, and confirming removes the user from
both the popper and the participants badge count — with the removal
surviving a full page reload (real server-side persistence, not just
optimistic client state).

Spec: test-specs/chat-interface/l2_remove-user-from-conversation-confirm-dialog_ELITEA-2170.md

Test-data substitution (AFS § Test Data): the case's literal Test Data
value ``user_1`` does not exist as a real user in this environment —
"Hrach Sargsyan" (search "sa") is used as the user to remove instead
(same substitution pattern already logged for ELITEA-2167's "Admin Bot").
"Levon Dadayan" (search "da") is a second participant kept in the
conversation throughout, so both the "at least 2 added participants"
precondition and the post-removal "still >=1 other participant remains"
state are exercised.

New page-object surface (this implementation): ``ChatPage`` gained
``get_user_participant_row()`` / ``get_user_participant_remove_button()``,
mirroring ``remove_agent_participant()``'s row-scoping + hover-reveal
technique for the "Users" participant type, decomposed into per-step
methods so this case's own hover/click/confirm-dialog states can each be
asserted (rather than one opaque call). One testid commit landed on
EliteaUI's ``automation/testids`` (see PR description): the
``chat-participant-row-{uniqueId}`` testid on ``UserMenu.jsx``'s row
container (EliteaAI/EliteaUI@8bd06e9a) — a one-line mirror of the
already-shipped ``ExpandedParticipants/ParticipantItem.jsx`` sibling
pattern, resolving the AFS-specced testid collision (every row's
``chat-participant-remove-button`` was otherwise identical and
unscopable once 2+ users were listed).

Reverse-masking guard (AFS step 4 / issue #1020): the case's literal text
says the confirm dialog reads "...from conversation?"; the live product
consistently says "...from chat" (same wording as the rest of the
``DeleteEntityModal`` family — title "Remove user?", confirm "Remove").
This test asserts the LIVE wording, not the stale case text.

Known defects (isolated, not automated as hard-fails — see AFS § Known
Defects Found): EliteaAI/elitea-testing-public#719 (MUI ``sx`` prop
forwarded onto a raw ``<svg>`` in the "Add users" picker's checkmark icon
— console warning only, reproduced again during this test's SETUP, not
the removal flow under test).
"""

import logging
import re

import allure
import pytest
from api import ConversationAPI
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

# Team project — the only project where the USERS participants section
# renders at all (AFS § Preconditions — !isPrivateProject guard).
TEAM_PROJECT_ID = "471"

# Test data (AFS § Test Data — "sa"/"da" partial-search pattern; "Hrach
# Sargsyan" substituted for the case's non-existent "user_1" placeholder).
USER_1_QUERY, USER_1_NAME = "sa", "Hrach Sargsyan"
USER_2_QUERY, USER_2_NAME = "da", "Levon Dadayan"

# The dev-token user's display name on localhost (AFS metadata — auth_state
# bypasses Keycloak via VITE_DEV_TOKEN, which renders as "Test Bot"/"TB").
OWNER_NAME = "Test Bot"

MESSAGE_TEXT = "hi all"


def _is_known_project_471_secrets_403(msg) -> bool:
    """Filter the pre-existing, already-documented project-471 ``secrets`` 403.

    Fires on every page load in this project regardless of any action taken
    (same idiom as ``test_invite_users_add_cancel_close.py``'s equivalent
    filter).
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default/471" in (text + location_url)


def _is_known_version_validator_400(msg) -> bool:
    """Filter the pre-existing, unrelated ``version_validator`` 400 noise
    (same idiom as ``test_invite_users_add_cancel_close.py``)."""
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "400" in text and "version_validator/prompt_lib" in (text + location_url)


def _is_known_checkicon_sx_svg_warning_719(msg) -> bool:
    """Filter the already-filed, isolated console defect
    EliteaAI/elitea-testing-public#719 (fires on every "Add users" option
    selection during this test's SETUP — same filter as
    ``test_invite_users_add_cancel_close.py``, re-confirmed by this case's
    AFS during its own setup phase)."""
    text = msg.text
    return "Invalid value for prop" in text and "sx" in text and "svg" in text and "CheckedIcon" in text


def _open_blank_conversation(chat: ChatPage, timeout: int = NAVIGATION_TIMEOUT) -> None:
    """Click +Chat and confirm a genuinely blank, unsent conversation opened.

    Same infrastructure-class flake guard as
    ``test_invite_users_add_cancel_close.py``'s helper of the same name —
    ``click_create_conversation()`` only waits for the message input to be
    visible, which is trivially true on ANY conversation, so a click
    landing while the SPA is mid-settling a project switch can silently
    leave the previously active conversation on screen. Retries the click
    once (a real re-click, not a sleep) if the new-conversation greeting
    doesn't appear within a short window.
    """
    for attempt in range(2):
        chat.click_create_conversation(timeout=timeout)
        try:
            chat.new_conversation_greeting.wait_for(state="visible", timeout=5000)
            return
        except Exception:
            if attempt == 0:
                logger.warning(
                    "New-conversation greeting not visible after +Chat click "
                    "— retrying once (see _open_blank_conversation docstring)"
                )
                continue
            raise


class TestRemoveUserFromConversationConfirmDialog:
    """ELITEA-2170: Chat – Team Project – Remove User from Conversation via
    Confirm Dialog (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2170_chat-team-project-remove-user-from-conversation-via-confirm-dialog.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_remove_user_from_conversation_via_confirm_dialog(self, page, _browser_cookies):
        """Remove a Team-project participant via the USERS popper + confirm dialog.

        Steps (AFS
        test-specs/chat-interface/l2_remove-user-from-conversation-confirm-dialog_ELITEA-2170.md):
        1. Open the conversation; click the avatar group in the
           PARTICIPANTS USERS section; verify the dropdown lists all
           participants plus an "All users" footer item.
        2. Hover Hrach Sargsyan's row; verify a trash-bin icon appears with
           a "Remove user" tooltip.
        3. Click the trash-bin icon; verify the "Remove user?" confirm
           modal appears.
        4. Verify the modal body text (reverse-masking guard — live text
           says "from chat", not the case's "from conversation").
        5. Click Remove; verify the modal closes, the user disappears from
           the still-open popper and the badge count decrements, and the
           removal survives a full page reload.
        """
        chat = ChatPage(page)
        team_conversation_api = ConversationAPI(
            browser_cookies=_browser_cookies, project_id=TEAM_PROJECT_ID,
        )
        conv_id: int | None = None

        # Registered before Setup so console errors from every step (project
        # switch, +Chat seeding, invite-two-users setup, all 5 case steps)
        # are captured — not just from a later step. Known, already-
        # documented noise (project-471 secrets 403; the unrelated
        # version_validator 400; the already-filed #719 sx-on-svg warning —
        # AFS § Known Defects Found classifies it as re-confirmed, not
        # re-filed) is filtered so it can't mask a genuinely NEW error.
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
                "Preconditions — logged in; switch to the Team project (471); "
                "create a new conversation and invite two users, then send "
                "the first message to persist them as real participants"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.switch_project(TEAM_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)
                selected_project_text = chat.get_selected_project_text()
                assert "Elitea Testing Team" in selected_project_text, (
                    "Project selector should show 'Elitea Testing Team' after "
                    f"switching, got: {selected_project_text!r}"
                )

                _open_blank_conversation(chat, timeout=NAVIGATION_TIMEOUT)

                chat.open_add_users_modal(timeout=UI_ELEMENT_TIMEOUT)
                chat.search_and_select_add_user(USER_1_QUERY, USER_1_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.search_and_select_add_user(USER_2_QUERY, USER_2_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_add_users_confirm(timeout=UI_ELEMENT_TIMEOUT)
                chat.add_users_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_participants_badge_count("2", section="users", timeout=UI_ELEMENT_TIMEOUT)

                initial_count = chat.get_message_count()
                chat.send_message(MESSAGE_TEXT, use_enter=False)
                # Router-commit race (same as the invite-users precedent test):
                # the URL only gains the conversation id once the SPA router
                # commits its own navigation, a later step than the
                # participants-persist network response — wait for the URL
                # itself rather than incidental timing.
                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=UI_ELEMENT_TIMEOUT)
                match = re.search(r"/chat/(\d+)", page.url)
                assert match, f"Conversation id should appear in the URL after Send, got: {page.url}"
                conv_id = int(match.group(1))

                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_participants_badge_count("3", section="users", timeout=UI_ELEMENT_TIMEOUT)

                # Resolve Hrach Sargsyan's numeric platform id via the API —
                # ground truth, not a DOM scrape — matching on the display
                # name (own-memory finding: a bare "entity_name == 'user'"
                # filter is non-deterministic once 2+ 'user'-entity rows
                # exist; matching on the specific participant's own field
                # avoids that ambiguity entirely).
                conv_data = team_conversation_api.get_conversation(conv_id)
                target_participant = next(
                    (
                        p for p in conv_data.get("participants", [])
                        if p.get("entity_name") == "user" and p.get("meta", {}).get("user_name") == USER_1_NAME
                    ),
                    None,
                )
                assert target_participant is not None, (
                    f"Conversation API response should include a 'user' participant "
                    f"named {USER_1_NAME!r}, got participants: {conv_data.get('participants', [])!r}"
                )
                user_1_id = target_participant["entity_meta"]["id"]

            with allure.step(
                "Step 1 — Open the PARTICIPANTS USERS dropdown; verify it "
                "lists all three participants plus an 'All users' footer item"
            ):
                popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper_text = popper.text_content() or ""
                assert "Users" in popper_text, f"Popover should show a Users heading, got: {popper_text!r}"
                assert USER_1_NAME in popper_text and USER_2_NAME in popper_text and OWNER_NAME in popper_text, (
                    f"Popover should list all three participants, got: {popper_text!r}"
                )
                assert "All users" in popper_text, (
                    f"Popover should show an 'All users' footer item, got: {popper_text!r}"
                )

            with allure.step(
                f"Step 2 — Hover {USER_1_NAME!r}'s row; verify a trash-bin "
                "icon appears with a 'Remove user' tooltip"
            ):
                remove_btn = chat.get_user_participant_remove_button(user_1_id, timeout=UI_ELEMENT_TIMEOUT)
                assert remove_btn.is_visible(), (
                    f"Trash-bin remove button should be visible after hovering {USER_1_NAME!r}'s row"
                )
                # Static aria-label MUI's Tooltip clones onto the button
                # itself (describeChild defaults False, so it's set
                # unconditionally whenever the title is a string) — same
                # no-hover-required tooltip-text technique already
                # established for other MUI tooltips in this codebase
                # (artifacts_page.py's get_delete_button_tooltip_text()).
                tooltip_text = remove_btn.get_attribute("aria-label") or ""
                assert tooltip_text == "Remove user", (
                    f"Remove button's tooltip text should read 'Remove user', got: {tooltip_text!r}"
                )

            with allure.step(
                "Step 3 — Click the trash-bin icon; verify the 'Remove "
                "user?' confirm modal appears"
            ):
                remove_btn.click(force=True)
                chat.delete_confirm_dialog.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                title_text = (chat.delete_confirm_title.text_content() or "").strip()
                assert title_text == "Remove user?", (
                    f"Confirm modal title should read 'Remove user?', got: {title_text!r}"
                )

            with allure.step(
                "Step 4 — Verify the modal body text (reverse-masking "
                "guard: live text says 'from chat', case text says "
                "'from conversation' — issue #1020)"
            ):
                message_text = (chat.delete_confirm_message.text_content() or "").strip()
                expected_message = f"Are you sure to remove the {USER_1_NAME} user from chat?"
                assert message_text == expected_message, (
                    f"Confirm modal body should read {expected_message!r}, got: {message_text!r}"
                )

            with allure.step(
                "Step 5 — Click Remove; verify the modal closes, the user "
                "disappears from the still-open popper and the badge "
                "decrements, and the removal persists across a page reload"
            ):
                chat.delete_confirm_button.click()
                chat.delete_confirm_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_participants_badge_count("2", section="users", timeout=UI_ELEMENT_TIMEOUT)

                popper_text = chat.participants_popper.text_content() or ""
                assert USER_1_NAME not in popper_text, (
                    f"{USER_1_NAME!r} should be removed from the still-open popper, got: {popper_text!r}"
                )
                assert USER_2_NAME in popper_text and OWNER_NAME in popper_text, (
                    f"Remaining participants should still be listed, got: {popper_text!r}"
                )
                chat.dismiss_participants_popover()

                # Persistence check — a full reload re-fetches participants
                # from the server, proving this is a real server-side
                # effect and not merely an optimistic client-state splice
                # (AFS Axis 2 addition / § Expected Results).
                page.reload(wait_until="domcontentloaded")
                chat.wait_for_page_load()
                chat.wait_for_participants_badge_count("2", section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper_after_reload = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper_text_after_reload = popper_after_reload.text_content() or ""
                assert USER_1_NAME not in popper_text_after_reload, (
                    f"{USER_1_NAME!r} should not reappear after reload, got: {popper_text_after_reload!r}"
                )
                assert USER_2_NAME in popper_text_after_reload and OWNER_NAME in popper_text_after_reload, (
                    f"Remaining participants should survive reload, got: {popper_text_after_reload!r}"
                )
                chat.dismiss_participants_popover()

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    f"Unexpected console errors: {[m.text for m in console_messages]!r}"
                )

        finally:
            if conv_id:
                try:
                    chat.open_conversation_context_menu(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                    chat.click_conversation_menu_item("delete", timeout=UI_ELEMENT_TIMEOUT)
                    delete_response = chat.confirm_delete_conversation(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                    assert delete_response.status in (200, 204), (
                        f"DELETE for conversation {conv_id} should succeed, got {delete_response.status}"
                    )
                    logger.info("Cleaned up conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Failed to clean up conversation %s: %s", conv_id, exc)
