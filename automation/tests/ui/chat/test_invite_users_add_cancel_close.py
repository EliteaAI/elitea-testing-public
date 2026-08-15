"""UI Test for ELITEA-2167 — Chat: Team Project, Create Conversation, Add
Users via Invite Users with Add/Cancel/Close.

Verifies the full "Add users" picker flow in a Team project: opening a new
conversation, the plus-menu's "Invite Users" item, searching/selecting two
users and confirming via Add (persisted), a third user dismissed via
Cancel (not persisted), a fourth dismissed via the dialog's X/Close (not
persisted), and that the invited users only actually reach the server once
the first message is sent (client-side queued state until then). Finishes
with the sidebar's Today-group multi-person icon check against a
negative-control single-owner conversation.

Spec: test-specs/chat-interface/l2_team-invite-users-add-cancel-close_ELITEA-2167.md

Test-data substitution (AFS § Test Data): the case's own "Admin Bot" example
does not exist in this environment — "Levon Dadayan" is used instead (both
match the case's own "ad" partial-search pattern).

New page-object surface (this implementation): ``ChatPage`` gained a
dedicated "Add users" modal surface (``open_add_users_modal`` /
``search_and_select_add_user`` / chip + option readers / Add / Cancel / X
close). Two testid commits landed on EliteaUI's ``automation/testids``
(see PR description): 8 testids on ``AddNewUserModal.jsx`` /
``AutoCompleteDropDown.jsx`` / ``ConversationItem.jsx`` /
``NewConversationView.jsx`` via EliteaAI/EliteaUI@dfc0d695, plus the
``chat-participants-badge-button``/``chat-participants-popper`` pair on
``UsersParticipantDropdown/index.jsx`` — the component this test's
``section="users"`` participants trigger/popover actually renders through —
via EliteaAI/EliteaUI@7ecc041d. The latter pair is on ``automation/testids``
ONLY, not on ``main``: the same testid strings pre-exist on ``main`` only in
the unrelated Agents-participants component (``CollapsedPerticapantsList.jsx``
/ ``CollapsedParticipantsDropdown.jsx``), which this test does not drive —
see the AFS § Concrete Handles PROVENANCE column (amended, this pass) for
the verified fresh-fetch ``git grep`` evidence. Also added: a testid-only
``data-has-icon`` state attribute on the conversation multi-person icon
wrapper (never a state-conditional testid, per the testid=identity/
state=data-* ruling).

Negative-control technique note (Phase 2 Explore decision, not a scope
change from the AFS's own Coverage Map, which commits to "icon container
non-empty, confirmed against an empty-icon single-owner conversation as a
negative control" for step 10): the AFS's own exploration session used a
pre-existing conversation ("HI Chat") left over from an EARLIER, unrelated
analyst session as its negative control. Relying on that specific
conversation persisting is fragile (this project's own prior-session memory
already documents a case where a stray leftover conversation caused a
DIFFERENT test to hang) — this test instead creates and cleans up its own
throwaway single-owner conversation, giving the same negative-control proof
with no dependency on ambient environment state.

Known defects (isolated, not automated as hard-fails — see AFS § Known
Defects Found): EliteaAI/elitea-testing-public#719 (MUI ``sx`` prop forwarded
onto a raw ``<svg>`` in the picker's checkmark icon — console warning only,
filed this session); EliteaAI/elitea-testing-public#694 (shared ``BaseModal``
``aria-labelledby`` id-mismatch, re-confirmed here, cross-referenced not
re-filed — a11y-only, does not affect testid-only automation).
"""

import logging
import re
import time

import allure
import pytest
from api import ConversationAPI
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds) — same values as the sibling chat suite
# (test_open_conversation_today_section.py / test_conversation_deletion_flow.py)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 30_000

# Team project — the only project where "Invite Users" is offered at all
# (PlusChatButton.jsx's !isPrivateProject guard) — AFS § Preconditions.
TEAM_PROJECT_ID = "471"

# Test data (AFS § Test Data — "sa"/"ad" partial-search pattern preserved
# from the case; "Levon Dadayan" substituted for the case's "Admin Bot",
# which does not exist live in this environment).
USER_1_QUERY, USER_1_NAME = "sa", "Hrach Sargsyan"
USER_2_QUERY, USER_2_NAME = "ad", "Levon Dadayan"
USER_3_QUERY, USER_3_NAME = "ma", "Mariam Hakobyan"
USER_4_QUERY, USER_4_NAME = "ta", "Tatiana Bontsevich"

MESSAGE_TEXT = "hi all"
CONTROL_MESSAGE_TEXT = "hi"


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
    ``test_open_conversation_today_section.py``'s equivalent filter).
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default/471" in (text + location_url)


def _is_known_version_validator_400(msg) -> bool:
    """Filter the pre-existing, unrelated ``version_validator`` 400 noise.

    Confirmed live (both by the analyst, AFS § Network Behavior, and during
    this implementation's own exploration) on navigation away from certain
    pre-existing conversations in this shared project — an artifact of an
    unrelated agent-versioning check, not caused by the Invite Users flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "400" in text and "version_validator/prompt_lib" in (text + location_url)


def _is_known_checkicon_sx_svg_warning_719(msg) -> bool:
    """Filter the already-filed, isolated console defect EliteaAI/elitea-testing-public#719.

    Fires on every "Add users" option selection (steps 4/5/7/8) —
    ``AutoCompleteDropDown.jsx``'s ``<CheckedIcon sx={...} />`` forwards an
    MUI ``sx`` prop onto a raw imported ``<svg>`` (not an MUI ``SvgIcon``),
    producing this React console warning. AFS § Known Defects Found /
    § Axis 2 explicitly classifies this as MINOR, already filed, and
    "not automated as a hard-fail assertion... flag for the implementer as
    an optional console-cleanliness guard, not a blocking check" — filtering
    it here (rather than failing the whole test on a known, non-blocking
    defect) is that guard, not defect masking: the filter is scoped to this
    exact, already-ticketed warning text/component, so any OTHER console
    error still fails the assertion below.
    """
    text = msg.text
    return "Invalid value for prop" in text and "sx" in text and "svg" in text and "CheckedIcon" in text


def _create_single_owner_control_conversation(chat: ChatPage) -> int:
    """Create a fresh, throwaway single-owner conversation (no invited users).

    Used as this test's own negative control for the step-10 multi-person
    icon check — see the module docstring's "Negative-control technique
    note". Returns the new conversation's numeric id.
    """
    _open_blank_conversation(chat, timeout=NAVIGATION_TIMEOUT)
    initial_count = chat.get_message_count()
    chat.send_message(CONTROL_MESSAGE_TEXT, use_enter=False)
    # Same router-commit race as step 9's send (see the inline comment
    # there) — wait for the URL itself rather than relying on incidental
    # timing from the AI-response waits below.
    chat.page.wait_for_url(re.compile(r"/chat/\d+"), timeout=NAVIGATION_TIMEOUT)
    chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
    chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)
    match = re.search(r"/chat/(\d+)", chat.page.url)
    assert match, (
        "Expected a conversation id in the URL after sending the control "
        f"conversation's message, got: {chat.page.url}"
    )
    return int(match.group(1))


def _open_blank_conversation(chat: ChatPage, timeout: int = NAVIGATION_TIMEOUT) -> None:
    """Click +Chat and confirm a genuinely blank, unsent conversation opened.

    Infrastructure-class flake guard (confirmed this session, on a shared
    dev backend where other sessions may concurrently change project 471's
    "last active conversation"): ``click_create_conversation()`` only waits
    for the message input to be visible, which is trivially true on ANY
    conversation (new or pre-existing) — it does not itself prove
    navigation to a NEW conversation happened. A click landing while the
    SPA is mid-settling a project switch can silently leave the previously
    active conversation on screen. Retries the click once (not a blind
    sleep — a real re-click) if the new-conversation greeting doesn't
    appear within a short window.
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


def _poll_blank_state_holds(
    chat: ChatPage,
    blank_url_pattern: "re.Pattern[str]",
    settle_ms: int = 1500,
    poll_interval_s: float = 0.25,
) -> tuple[bool, str]:
    """Poll message-count + URL at short intervals across *settle_ms*,
    instead of a fixed-latency sleep-then-recheck-once.

    Same idiom as ``ChatPage.wait_for_message_content_stable()``: sample the
    observed state on a short interval and only conclude "stable" once it
    has held for the whole window — here the value being watched for
    stability is "still blank" rather than "content stopped changing".
    Exits the instant either signal flips (a definitive, immediate result)
    rather than waiting out the full window and discovering the reversion
    only at the end.

    Returns ``(settled, reason)`` — ``settled`` is False (with a reason)
    the moment either signal flips during the window, True only if both
    signals held blank for the entire window.
    """
    deadline = time.monotonic() + settle_ms / 1000.0
    while time.monotonic() < deadline:
        time.sleep(poll_interval_s)
        count = chat.get_message_count()
        url = chat.page.url
        if count != 0 or not blank_url_pattern.search(url):
            return False, f"blank state reverted mid-settle (url={url!r}, message_count={count})"
    return True, ""


def _open_genuinely_blank_conversation(chat: ChatPage, timeout: int = NAVIGATION_TIMEOUT) -> None:
    """Stronger sibling of ``_open_blank_conversation()`` — additive, does
    NOT modify that function or its existing caller (Hard Rule 3).

    ``_open_blank_conversation()``'s single check (the new-conversation
    greeting is visible) is not sufficient on this shared dev backend:
    confirmed live this implementation (ELITEA-2175's own first run,
    reproduced identically 4 times running) that the SPA can restore the
    last-viewed conversation from browser/session storage (documented by
    ``ChatPage.navigate_to_chat()``'s own docstring: "the SPA may redirect
    to the last-viewed conversation stored in the browser session") AFTER
    the blank greeting and a momentary 0 message count were both already
    observed — the restore is a delayed effect, not synchronous with the
    +Chat click, so it silently wins a race against a check performed too
    early, snapping the URL back to a pre-existing conversation with real
    history (this environment's own EL-2091 "Review attached documents",
    id 420) a moment later. Confirmed via a parallel manual Playwright MCP
    session: the identical +Chat click reliably produced a genuinely blank
    conversation (bare ``/chat`` URL, no participants) when driven slowly
    with pauses between steps, but pytest's own faster, back-to-back
    action sequence consistently lost this race. Guards against it with a
    settle-and-recheck: poll BOTH the message count AND the URL at short
    intervals across the restore's own timing window (same idiom as
    ``ChatPage.wait_for_message_content_stable()`` — poll a value on a short
    interval, only proceed once it has held steady across the whole
    window), exiting the instant either signal flips instead of sleeping the
    full window blind and checking once. This stays condition-based even
    though there is no positive condition to await for "an effect did NOT
    fire": the condition polled for is continued stability of the observed
    state, checked repeatedly rather than assumed after a fixed delay.
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
                "(attempt %d) — retrying (see _open_genuinely_blank_conversation docstring)",
                attempt + 1,
            )
            continue
        if chat.get_message_count() != 0:
            last_reason = "greeting appeared but conversation has message history"
            logger.warning(
                "Landed on a non-blank conversation (attempt %d) — retrying "
                "(see _open_genuinely_blank_conversation docstring)",
                attempt + 1,
            )
            continue
        # Settle window for the delayed last-viewed-conversation restore
        # (see docstring) — poll both signals across the window instead of
        # a fixed sleep-then-recheck-once.
        settled, reason = _poll_blank_state_holds(chat, blank_url_pattern)
        if not settled:
            last_reason = reason
            logger.warning(
                "Blank conversation reverted to a restored one during "
                "settling (attempt %d) — retrying (see "
                "_open_genuinely_blank_conversation docstring)",
                attempt + 1,
            )
            continue
        return
    raise AssertionError(
        f"Could not open a genuinely blank conversation after 3 attempts: {last_reason}"
    )


class TestInviteUsersAddCancelClose:
    """ELITEA-2167: Chat – Team Project – Create Conversation and Add Users
    via Invite Users with Add Confirmation (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2167_chat-team-project-create-new-conversation-and-add-users-via-invite-users.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_invite_users_add_persists_cancel_and_close_discard(self, page, _browser_cookies):
        """Add users modal: Add persists selections, Cancel/X discard them.

        Steps (AFS
        test-specs/chat-interface/l2_team-invite-users-add-cancel-close_ELITEA-2167.md):
        1. Switch to the Team project; click + Chat; verify a new, blank
           conversation with no participants element.
        2. Click + menu; verify Invite Users is present among 6 items.
        3. Click Invite Users; verify the 'Add users' modal opens.
        4. Search 'sa', select Hrach Sargsyan; verify chip + Add enabled.
        5. Search 'ad', select Levon Dadayan; verify two chips.
        6. Click Add; verify modal closes, badge reads "2", popover lists
           both names, no persistence network call yet.
        7. Third user + Cancel; verify not added; excludedUserIds drops
           already-added participants from further searches.
        8. Fourth user + X close; verify not added.
        9. Send "hi all"; verify conversation created + participants
           persisted (network) + LLM responds; badge "2" -> "3", owner
           joins PARTICIPANTS USERS.
        10. Verify the conversation is under Today with a multi-person
            icon, confirmed against a single-owner negative control.
        """
        chat = ChatPage(page)
        # Same technique as test_open_conversation_today_section.py (ELITEA-2095)
        # Step 10 — a DOM-only "count went 2->3" read would not catch the
        # THIRD participant being anything other than the actual owner,
        # which is what AFS step 9's Expected Result + Coverage Map row
        # commit to ("popover shows owner + both invited users"). Cross-
        # checked via the API rather than hardcoding the dev-token user's
        # display name, since that's environment data, not a compile-time
        # constant (AFS metadata notes it renders as "Test Bot"/"TB" here).
        team_conversation_api = ConversationAPI(
            browser_cookies=_browser_cookies, project_id=TEAM_PROJECT_ID,
        )
        conv_id: int | None = None
        control_conv_id: int | None = None
        soft_failures: list[str] = []

        # Registered before Setup so console errors from every step (project
        # switch, +Chat seeding, all 10 case steps, the control conversation)
        # are captured — not just from a later step. Known, already-
        # documented noise (project-471 secrets 403; the unrelated
        # version_validator 400; the already-filed #719 sx-on-svg warning —
        # AFS § Known Defects Found classifies it MINOR/non-blocking) is
        # filtered so it can't mask a genuinely NEW error on the same flow.
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
                "Preconditions — logged in; switch to the Team project (471)"
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

            with allure.step(
                "Step 1 — Click + Chat; verify a new, blank conversation opens "
                "with no participants element (reverse-masking guard)"
            ):
                # Known defect: #1082 — the weaker _open_blank_conversation()
                # guard (greeting-visible only) does not protect against the
                # SPA's DELAYED restore-to-last-viewed-conversation effect
                # (see _open_genuinely_blank_conversation()'s own docstring),
                # confirmed live this session (2026-08-15, wave-10 gate
                # investigation): this exact call landed on the stale "HI
                # Chat" conversation (id 507), which already has both
                # USER_1_NAME/USER_2_NAME as participants — the modal's
                # excludedUserIds then silently drops them from every search,
                # so Step 4 timed out finding an option that legitimately
                # cannot appear. Same root cause as the already-soft-asserted
                # stale-badge symptom below, manifesting one step earlier via
                # a different observable. Swapped to the stronger sibling
                # already proven for ELITEA-2175/2176 in this same file —
                # additive only, does not touch the shared
                # _open_blank_conversation() (still used unmodified by
                # _create_single_owner_control_conversation() above).
                _open_genuinely_blank_conversation(chat, timeout=NAVIGATION_TIMEOUT)
                assert chat.new_conversation_greeting.is_visible(), (
                    "Blank-conversation greeting should be visible for a "
                    "brand-new, unsent conversation"
                )
                assert chat.message_input.is_visible() and chat.message_input.is_editable(), (
                    "Message input should be visible and editable on a fresh conversation"
                )
                assert chat.is_input_empty(), "Message input should start empty"
                # Case text says "PARTICIPANTS panel visible with empty USERS
                # section"; live behavior for a brand-new, zero-participant,
                # unsaved conversation is NO participants element at all
                # (matches the already-documented ELITEA-2095/ELITEA-2166
                # pattern) — asserting absence per is_participants_badge_visible's
                # own contract (the container disappears from the DOM entirely).
                # Known defect: #1082 — a test-isolation defect (project-switch
                # settling in a full-suite run can leave a stale/deleted
                # conversation on screen), confirmed deterministic 3/3 on this
                # branch, unrelated to this test's own logic; passes standalone.
                # Soft per the pytest-native soft_failures/pytest.fail() idiom
                # (mirrors test_pipeline_flow_editor_add_llm_node_from_chat_canvas.py's
                # #1039 handling) since the observable
                # (is_participants_badge_visible()) is a bool, not a bare
                # Locator/Page/APIResponse assertion that expect.soft() takes.
                if chat.is_participants_badge_visible(section="users", timeout=3000):
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1082: "
                        "a brand-new, zero-participant conversation should render no participants "
                        "badge/panel at all, but the badge was visible (test-isolation / "
                        "stale-conversation defect, reproduces only in a full-suite run)"
                    )

            with allure.step(
                "Step 2 — Click + menu; verify 'Invite Users' is present "
                "among exactly 6 menu items"
            ):
                chat.plus_menu_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                chat.plus_menu_button.click()
                chat.invite_users_menuitem.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.invite_users_menuitem.is_visible(), (
                    "'Invite Users' should be visible in the plus menu for a Team project"
                )
                assert chat.invite_users_menuitem.is_enabled(), "'Invite Users' should be enabled"
                menu_item_count = chat.get_open_plus_menu_item_count()
                assert menu_item_count == 6, (
                    "Expected 6 plus-menu items (Attach Files is a separate "
                    "button, not a menuitem) in a Team project, got "
                    f"{menu_item_count}"
                )
                # Menu is left open on purpose — Step 3 clicks Invite Users
                # directly from here (matching the case's own flow); closing
                # and immediately reopening the same MUI popper is a needless
                # extra toggle that races the popper's own open/close animation.

            with allure.step(
                "Step 3 — Click Invite Users; verify the 'Add users' modal "
                "opens with search field, Cancel, and a disabled Add button"
            ):
                chat.invite_users_menuitem.click()
                chat.add_users_dialog.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.add_users_dialog.is_visible(), "'Add users' dialog should be visible"
                assert chat.add_users_search_input.is_visible(), "Search field should be visible"
                assert chat.add_users_cancel_button.is_visible(), "Cancel button should be visible"
                assert chat.add_users_confirm_button.is_visible(), "Add button should be visible"
                assert not chat.is_add_users_confirm_enabled(), (
                    "Add button should be disabled — no users selected yet"
                )

            with allure.step(
                f"Step 4 — Search {USER_1_QUERY!r}, select {USER_1_NAME!r}; "
                "verify chip appears, modal stays open, Add becomes enabled"
            ):
                chat.search_and_select_add_user(USER_1_QUERY, USER_1_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chip_names = chat.get_add_users_chip_names()
                assert chip_names == [USER_1_NAME], (
                    f"Expected exactly one chip ({USER_1_NAME!r}), got {chip_names!r}"
                )
                assert chat.add_users_dialog.is_visible(), "Modal should stay open after selecting a user"
                assert chat.is_add_users_confirm_enabled(), "Add button should be enabled after a selection"

            with allure.step(
                f"Step 5 — Search {USER_2_QUERY!r}, select {USER_2_NAME!r} "
                "(AFS substitution for the case's 'Admin Bot'); verify two "
                "chips, modal stays open"
            ):
                chat.search_and_select_add_user(USER_2_QUERY, USER_2_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chip_names = chat.get_add_users_chip_names()
                assert chip_names == [USER_1_NAME, USER_2_NAME], (
                    f"Expected both chips in selection order, got {chip_names!r}"
                )
                assert chat.add_users_dialog.is_visible(), "Modal should stay open"
                assert chat.is_add_users_confirm_enabled(), "Add button should still be enabled"

            with allure.step(
                "Step 6 — Click Add; verify modal closes and both users are "
                "in PARTICIPANTS USERS"
            ):
                chat.click_add_users_confirm(timeout=UI_ELEMENT_TIMEOUT)
                chat.add_users_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_participants_badge_count("2", section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper_text = popper.text_content() or ""
                # DOM text is "Users" (title case) — the visually-uppercase
                # "USERS" the case text/AFS describe is a CSS
                # ``text-transform: uppercase`` rendering effect only
                # (``UsersParticipantDropdown``'s ``styles.title``), never
                # part of the actual textContent. Asserting the literal DOM
                # string is the live-contract read (reverse-masking guard);
                # confirmed live this session — ``text_content()`` returns
                # "Users@<names>@All users", never "USERS...".
                assert "Users" in popper_text, f"Popover should show a Users heading, got: {popper_text!r}"
                assert USER_1_NAME in popper_text and USER_2_NAME in popper_text, (
                    f"Popover should list both invited users, got: {popper_text!r}"
                )
                chat.dismiss_participants_popover()

            with allure.step(
                f"Step 7 — + menu, Invite Users, search+select {USER_3_NAME!r}, "
                "then Cancel; verify not added and excludedUserIds drops "
                f"{USER_1_NAME!r} from further searches"
            ):
                chat.open_add_users_modal(timeout=UI_ELEMENT_TIMEOUT)
                assert not chat.is_add_users_option_present(USER_1_NAME, timeout=2000), (
                    f"Already-added participant {USER_1_NAME!r} should be "
                    "excluded from a fresh search (excludedUserIds)"
                )
                chat.search_and_select_add_user(USER_3_QUERY, USER_3_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_add_users_cancel(timeout=UI_ELEMENT_TIMEOUT)
                chat.add_users_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                badge_count = chat.get_participants_badge_count(section="users", timeout=UI_ELEMENT_TIMEOUT)
                assert badge_count == "2", f"Badge should still read '2' after Cancel, got {badge_count!r}"
                popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper_text = popper.text_content() or ""
                assert USER_3_NAME not in popper_text, (
                    f"{USER_3_NAME!r} should NOT be added after Cancel, popover: {popper_text!r}"
                )
                chat.dismiss_participants_popover()

            with allure.step(
                f"Step 8 — + menu, Invite Users, search+select {USER_4_NAME!r}, "
                "then X (Close); verify not added"
            ):
                chat.open_add_users_modal(timeout=UI_ELEMENT_TIMEOUT)
                chat.search_and_select_add_user(USER_4_QUERY, USER_4_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_add_users_close(timeout=UI_ELEMENT_TIMEOUT)
                chat.add_users_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                badge_count = chat.get_participants_badge_count(section="users", timeout=UI_ELEMENT_TIMEOUT)
                assert badge_count == "2", f"Badge should still read '2' after X close, got {badge_count!r}"
                popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper_text = popper.text_content() or ""
                assert USER_4_NAME not in popper_text, (
                    f"{USER_4_NAME!r} should NOT be added after X close, popover: {popper_text!r}"
                )
                chat.dismiss_participants_popover()

            with allure.step(
                "Step 9 — Type 'hi all' and click Send; verify the "
                "conversation is created + queued users persisted as "
                "participants (network) + LLM responds"
            ):
                initial_count = chat.get_message_count()
                assert initial_count == 0, "Fresh conversation should have no messages yet"

                with page.expect_response(
                    lambda r: r.request.method == "POST" and _is_conversation_create_request(r.url)
                ) as create_info, page.expect_response(
                    lambda r: r.request.method == "POST" and _is_participants_persist_request(r.url)
                ) as participants_info:
                    chat.send_message(MESSAGE_TEXT, use_enter=False)

                create_response = create_info.value
                participants_response = participants_info.value
                assert create_response.status == 201, (
                    f"Conversation-create request should return 201, got "
                    f"{create_response.status} ({create_response.url})"
                )
                assert participants_response.status == 200, (
                    "Participants-persist request should return 200, got "
                    f"{participants_response.status} ({participants_response.url})"
                )

                # The URL only gains the conversation id once the SPA router
                # commits its own navigation — this fires as a LATER step in
                # the network sequence (AFS § Network Behavior:
                # .../select_conversation/... follows .../participants/...),
                # so reading ``page.url`` synchronously right after the
                # participants-persist response is a race (confirmed live
                # this session: still bare "/chat" at that exact instant).
                # ``page.wait_for_url`` is Playwright's own condition-based
                # wait for a URL pattern — not a sleep — so it waits out
                # exactly that router-commit gap.
                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=UI_ELEMENT_TIMEOUT)
                match = re.search(r"/chat/(\d+)", page.url)
                assert match, f"Conversation id should appear in the URL after Send, got: {page.url}"
                conv_id = int(match.group(1))

                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)

                chat.wait_for_participants_badge_count("3", section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper_text = popper.text_content() or ""
                assert USER_1_NAME in popper_text and USER_2_NAME in popper_text, (
                    f"Popover should still list both invited users after Send, got: {popper_text!r}"
                )
                # The badge going 2->3 only proves a THIRD participant exists,
                # not that it's the owner — AFS step 9 Expected Result +
                # Coverage Map row commit to "popover shows owner + both
                # invited users". Cross-verify via the API (same technique
                # as test_open_conversation_today_section.py Step 10,
                # ELITEA-2095) rather than trusting a hardcoded display
                # name.
                #
                # Unlike ELITEA-2095's single-owner conversation, THIS
                # conversation has THREE "user"-entity participants (owner +
                # both invited users — invited users are real platform
                # users too, so they carry ``entity_name == "user"`` just
                # like the owner does). Confirmed live this session: a bare
                # ``next(p for p in participants if entity_name == "user")``
                # non-deterministically grabbed an INVITED user's entry
                # instead of the owner's (`entity_meta={'id': 7}` — Levon
                # Dadayan — vs the real `author_id=659`), because dict/list
                # ordering from the API is not owner-first. The filter must
                # match the owner's `entity_meta.id` directly, not merely
                # the "user" entity type.
                conv_data = team_conversation_api.get_conversation(conv_id)
                owner_id = conv_data.get("author_id")
                owner_participant = next(
                    (
                        p for p in conv_data.get("participants", [])
                        if p.get("entity_name") == "user" and p.get("entity_meta", {}).get("id") == owner_id
                    ),
                    None,
                )
                assert owner_participant is not None, (
                    "Conversation API response should include a 'user' "
                    f"participant entry matching the owner (author_id={owner_id}), "
                    f"got participants: {conv_data.get('participants', [])!r}"
                )
                owner_name = owner_participant.get("meta", {}).get("user_name", "")
                assert owner_name, "Expected a non-empty owner display name from the API"
                assert owner_name in popper_text, (
                    f"Popover should include the owner {owner_name!r} in "
                    "PARTICIPANTS USERS alongside the two invited users "
                    f"after Send, got: {popper_text!r}"
                )
                chat.dismiss_participants_popover()

            with allure.step(
                "Step 10 — Verify the conversation is under Today with a "
                "multi-person icon, confirmed against a single-owner "
                "negative control"
            ):
                assert chat.is_conversation_in_group(conv_id, "today", timeout=UI_ELEMENT_TIMEOUT), (
                    f"Conversation {conv_id} should render under the Today group"
                )

                control_conv_id = _create_single_owner_control_conversation(chat)

                # Sidebar list items cache their own ``users_count`` at fetch
                # time (``ConversationItem.jsx``'s ``getConversationType()``)
                # and do NOT live-update it as participants change — confirmed
                # live this session: ``data-has-icon`` stayed "false" for
                # conv_id for 10s+ straight after Send, well after the
                # participants badge/popover already showed 3 users. Same
                # staleness CLASS (not the same field) as the already-
                # documented EliteaAI/elitea-testing-public#692 "stuck
                # active" sidebar defect.
                # Known defect: #989 — filed distinctly (not #692 — a
                # different field, same caching-not-live-updating class).
                # Reload stays the established fix in this suite
                # (test_open_conversation_today_section.py Step 2): it forces
                # a full client-state re-derivation, re-fetching the
                # conversation list with current data. The icon assertion
                # below stays a HARD assert (`expect().to_have_attribute()`
                # inside `wait_for_conversation_multi_user_icon` — see
                # chat_page.py) — the reload is a workaround for the known
                # defect's staleness window, not a mask of the assertion
                # itself.
                page.reload(wait_until="domcontentloaded")
                chat.wait_for_page_load()
                chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)

                chat.wait_for_conversation_multi_user_icon(
                    conv_id, expected_has_icon=True, timeout=UI_ELEMENT_TIMEOUT
                )
                chat.wait_for_conversation_multi_user_icon(
                    control_conv_id, expected_has_icon=False, timeout=UI_ELEMENT_TIMEOUT
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
                    "defect, not test/infrastructure — remaining steps "
                    "above passed cleanly):\n" + "\n".join(soft_failures)
                )

        finally:
            for cid in (conv_id, control_conv_id):
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


class TestRemovePreselectedUserViaChipX:
    """ELITEA-2175: Chat – Team Project – Remove Pre-Selected User from Add
    Users Modal by Clicking X on Chip (l3, medium).

    Extends the ELITEA-2167 covering file: that test only exercises
    Add/Cancel/X-close of the WHOLE modal, never removing a single
    already-selected chip before confirming. ``ChatPage.remove_add_users_chip()``
    already exists with one caller (ELITEA-2168's test, removing the LAST of
    4 chips) — this case's own data (3 users, X on the MIDDLE chip) is a
    genuinely distinct observable: it proves the removal is keyed by the
    clicked chip's own identity, not by array position, and that the two
    SURROUNDING selections survive a middle-item removal untouched.
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2175_chat-team-project-remove-pre-selected-user-from-add-users-modal-by-clicking-x-on-chip.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_remove_preselected_user_via_chip_x(self, page, _browser_cookies):
        """Removing the middle chip via its own X keeps the other two selected.

        Steps (AFS
        test-specs/chat-interface/l3_remove-preselected-user-via-chip-x_ELITEA-2175.md):
        1. Open a new, blank Team-project conversation; open Add users;
           select user_1, user_2, user_3 — verify three chips.
        2. Click X on user_2's chip; verify user_2 is gone and user_1/user_3
           remain, in order; Add stays enabled.
        3. Click Add; verify modal closes and user_1/user_3 (not user_2) are
           the queued PARTICIPANTS USERS.
        """
        chat = ChatPage(page)

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not (
                _is_known_project_471_secrets_403(msg)
                or _is_known_version_validator_400(msg)
                or _is_known_checkicon_sx_svg_warning_719(msg)
            ):
                console_messages.append(msg)

        page.on("console", _on_console)

        with allure.step("Preconditions — logged in; switch to the Team project (471)"):
            chat.navigate_to_chat()
            chat.wait_for_page_load()
            chat.switch_project(TEAM_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)
            chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 1 — Open a blank conversation; open Add users; select "
            f"{USER_1_NAME!r}, {USER_2_NAME!r}, {USER_3_NAME!r} — three chips"
        ):
            _open_genuinely_blank_conversation(chat, timeout=NAVIGATION_TIMEOUT)
            chat.open_add_users_modal(timeout=UI_ELEMENT_TIMEOUT)
            chat.search_and_select_add_user_verified(USER_1_QUERY, USER_1_NAME, timeout=UI_ELEMENT_TIMEOUT)
            chat.wait_for_add_users_chip(USER_1_NAME, timeout=UI_ELEMENT_TIMEOUT)
            chat.search_and_select_add_user_verified(USER_2_QUERY, USER_2_NAME, timeout=UI_ELEMENT_TIMEOUT)
            chat.wait_for_add_users_chip(USER_2_NAME, timeout=UI_ELEMENT_TIMEOUT)
            chat.search_and_select_add_user_verified(USER_3_QUERY, USER_3_NAME, timeout=UI_ELEMENT_TIMEOUT)
            chat.wait_for_add_users_chip(USER_3_NAME, timeout=UI_ELEMENT_TIMEOUT)

            chip_names = chat.get_add_users_chip_names()
            assert chip_names == [USER_1_NAME, USER_2_NAME, USER_3_NAME], (
                f"Expected three chips in selection order, got {chip_names!r}"
            )

        with allure.step(
            f"Step 2 — Click X on {USER_2_NAME!r}'s chip; verify "
            f"{USER_1_NAME!r}/{USER_3_NAME!r} remain, {USER_2_NAME!r} is gone"
        ):
            chat.remove_add_users_chip(USER_2_NAME, timeout=UI_ELEMENT_TIMEOUT)
            chip_names = chat.get_add_users_chip_names()
            assert chip_names == [USER_1_NAME, USER_3_NAME], (
                f"Expected only {USER_1_NAME!r}/{USER_3_NAME!r} to remain in "
                f"order after removing the middle chip, got {chip_names!r}"
            )
            assert chat.is_add_users_confirm_enabled(), (
                "Add button should stay enabled — 2 selections remain > 0"
            )

        with allure.step(
            "Step 3 — Click Add; verify modal closes and "
            f"{USER_1_NAME!r}/{USER_3_NAME!r} (not {USER_2_NAME!r}) are the "
            "queued PARTICIPANTS USERS"
        ):
            # Same blind-Escape-after-chip-removal gotcha ELITEA-2168's test
            # documents (ChatPage.remove_add_users_chip docstring) — removing
            # a chip can flip the results popper back open (the removed user
            # is no longer excluded), which would then intercept a plain
            # click_add_users_confirm()'s unconditional Escape-then-click.
            chat.add_users_confirm_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            if chat.is_add_users_results_open():
                chat.dismiss_add_users_dropdown()
            chat.add_users_confirm_button.click()
            chat.add_users_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

            chat.wait_for_participants_badge_count("2", section="users", timeout=UI_ELEMENT_TIMEOUT)
            popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
            popper_text = popper.text_content() or ""
            assert USER_1_NAME in popper_text and USER_3_NAME in popper_text, (
                f"Popover should list {USER_1_NAME!r} and {USER_3_NAME!r}, got: {popper_text!r}"
            )
            assert USER_2_NAME not in popper_text, (
                f"{USER_2_NAME!r} was removed via chip X before Add and "
                f"should NOT appear in PARTICIPANTS, got: {popper_text!r}"
            )
            chat.dismiss_participants_popover()

        with allure.step("Side-channel check — no unexpected console errors across the full flow"):
            assert not console_messages, f"Unexpected console errors: {[m.text for m in console_messages]!r}"

        # No conversation is created server-side until the first message is
        # sent (AFS § Network Behavior, same mechanism ELITEA-2167's own
        # test documents) — this case never sends one, so there is nothing
        # to clean up.


class TestCancelAddUsersModalAfterPreselectingUsers:
    """ELITEA-2176: Chat – Team Project – Cancel Add Users Modal After
    Pre-Selecting Users Does Not Add Anyone (l3, medium).

    Extends the ELITEA-2167 covering file: its own Cancel step (7) and
    ELITEA-2168's Cancel step (6) each discard only ONE pre-selected chip.
    This case's own data (select TWO users, THEN Cancel) is worth its own
    proof on an EXISTING conversation that already carries a real,
    persisted participant baseline — matching the case's own precondition
    ("Team project with an existing conversation") and its own step 1
    ("note current participants") rather than a fresh, participant-less one.
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2176_chat-team-project-cancel-add-users-modal-does-not-add-anyone.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_cancel_after_preselecting_two_users_adds_no_one(self, page, _browser_cookies):
        """Cancel with 2 chips selected discards both; baseline participants unchanged.

        Steps (AFS
        test-specs/chat-interface/l3_cancel-add-users-modal-after-preselecting-users_ELITEA-2176.md):
        Setup. Seed an existing conversation with one persisted participant
             (user_4) so PARTICIPANTS USERS has a real baseline to compare
             against — the case's own "existing conversation" precondition.
        1. Note current participants (badge count + popover names).
        2. Open Add users; select user_1 and user_2 — verify two chips.
        3. Click Cancel; verify modal closes.
        4. Verify PARTICIPANTS USERS is unchanged from the noted baseline.
        5. Verify user_1 and user_2 are NOT in PARTICIPANTS.
        """
        chat = ChatPage(page)
        conv_id: int | None = None

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
                "Setup — switch to the Team project; open a blank "
                "conversation; add user_4 and send so it persists as an "
                "existing conversation with one real participant"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.switch_project(TEAM_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)

                _open_genuinely_blank_conversation(chat, timeout=NAVIGATION_TIMEOUT)
                chat.open_add_users_modal(timeout=UI_ELEMENT_TIMEOUT)
                chat.search_and_select_add_user_verified(USER_4_QUERY, USER_4_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_add_users_chip(USER_4_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_add_users_confirm(timeout=UI_ELEMENT_TIMEOUT)
                chat.add_users_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

                initial_count = chat.get_message_count()
                assert initial_count == 0, "Fresh conversation should have no messages yet"

                with page.expect_response(
                    lambda r: r.request.method == "POST" and _is_conversation_create_request(r.url)
                ) as create_info, page.expect_response(
                    lambda r: r.request.method == "POST" and _is_participants_persist_request(r.url)
                ) as participants_info:
                    chat.send_message(CONTROL_MESSAGE_TEXT, use_enter=False)

                assert create_info.value.status == 201, (
                    f"Conversation-create request should return 201, got {create_info.value.status}"
                )
                assert participants_info.value.status == 200, (
                    "Participants-persist request should return 200, got "
                    f"{participants_info.value.status}"
                )

                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=UI_ELEMENT_TIMEOUT)
                match = re.search(r"/chat/(\d+)", page.url)
                assert match, f"Conversation id should appear in the URL after Send, got: {page.url}"
                conv_id = int(match.group(1))

                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_participants_badge_count("2", section="users", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 1 — Note current participants: badge '2' (owner + "
                f"{USER_4_NAME!r})"
            ):
                assert chat.is_participants_badge_visible(section="users", timeout=UI_ELEMENT_TIMEOUT), (
                    "PARTICIPANTS USERS badge should be visible on this "
                    "existing, one-participant conversation"
                )
                baseline_badge = chat.get_participants_badge_count(section="users", timeout=UI_ELEMENT_TIMEOUT)
                assert baseline_badge == "2", f"Expected baseline badge '2' (owner + 1), got {baseline_badge!r}"
                baseline_popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
                baseline_popper_text = baseline_popper.text_content() or ""
                assert USER_4_NAME in baseline_popper_text, (
                    f"Baseline popover should list {USER_4_NAME!r}, got: {baseline_popper_text!r}"
                )
                chat.dismiss_participants_popover()

            with allure.step(
                f"Step 2 — Open Add users; select {USER_1_NAME!r} and "
                f"{USER_2_NAME!r} — two chips shown"
            ):
                chat.open_add_users_modal(timeout=UI_ELEMENT_TIMEOUT)
                chat.search_and_select_add_user_verified(USER_1_QUERY, USER_1_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_add_users_chip(USER_1_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.search_and_select_add_user_verified(USER_2_QUERY, USER_2_NAME, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_add_users_chip(USER_2_NAME, timeout=UI_ELEMENT_TIMEOUT)

                chip_names = chat.get_add_users_chip_names()
                assert chip_names == [USER_1_NAME, USER_2_NAME], (
                    f"Expected both chips in selection order, got {chip_names!r}"
                )
                assert chat.is_add_users_confirm_enabled(), "Add button should be enabled with 2 selections"

            with allure.step("Step 3 — Click Cancel; verify modal closes"):
                chat.click_add_users_cancel(timeout=UI_ELEMENT_TIMEOUT)
                chat.add_users_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 4 — Verify PARTICIPANTS USERS is unchanged from the "
                "noted baseline (badge '2')"
            ):
                badge_after_cancel = chat.get_participants_badge_count(section="users", timeout=UI_ELEMENT_TIMEOUT)
                assert badge_after_cancel == baseline_badge, (
                    f"Badge should still read {baseline_badge!r} after "
                    f"Cancel, got {badge_after_cancel!r}"
                )

            with allure.step(
                f"Step 5 — Verify {USER_1_NAME!r} and {USER_2_NAME!r} are "
                "NOT in PARTICIPANTS"
            ):
                popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
                popper_text = popper.text_content() or ""
                assert USER_1_NAME not in popper_text and USER_2_NAME not in popper_text, (
                    f"{USER_1_NAME!r}/{USER_2_NAME!r} should NOT be added "
                    f"after Cancel, popover: {popper_text!r}"
                )
                assert USER_4_NAME in popper_text, (
                    f"Baseline participant {USER_4_NAME!r} should still be "
                    f"present, got: {popper_text!r}"
                )
                chat.dismiss_participants_popover()

            with allure.step("Side-channel check — no unexpected console errors across the full flow"):
                assert not console_messages, f"Unexpected console errors: {[m.text for m in console_messages]!r}"

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
