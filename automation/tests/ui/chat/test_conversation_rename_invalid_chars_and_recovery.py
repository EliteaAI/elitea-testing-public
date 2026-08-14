"""UI Test for ELITEA-2110/2112/2113/2111 — Chat: Conversation Rename — Invalid
Characters / Leading Space / Recovery After Invalid Input / Tooltip Validation
Message Content.

Family AFS covering three TMS cases that all drive the SAME
``isSaveEnabled``/``ConversationNameRegExp`` gate on the SAME inline rename
editor (``ConversationItem.jsx``) as the sibling ELITEA-2105/2106/2107/2108/2109
family, but exercise the CHARSET and FIRST-CHAR branches of the regex instead
of the length branch:

- ELITEA-2110: special characters (``"HI Chat$$%"``) -> checkmark stays
  disabled, hovering shows the exact validation-message tooltip, click is a
  no-op.
- ELITEA-2112: a leading space (``" ab"``, typed as real sequential
  keystrokes: Space, then "a", then "b") -> checkmark stays disabled (the
  regex's first-character class excludes space/hyphen even though the later
  class allows both).
- ELITEA-2113: type invalid characters (checkmark inactive) -> clear and
  type a fully valid name ("Chat 01 (test).") -> checkmark activates -> click
  saves successfully with no error shown.
- ELITEA-2111 (extend-existing, added this session): "$ % @"-flavoured invalid
  characters -> hovering the inactive checkmark shows the EXACT
  ConversationNameWarningMessage tooltip text -> recovering to a valid name
  makes the tooltip disappear and the checkmark activate. Steps 1-4 are a new
  parametrize row on the Shape-A test (own literal invalid-char data, same
  method body as ELITEA-2110/2112); step 5 is a coverage-tag-only addition on
  the ELITEA-2113 test, whose existing Step 3 already asserts exactly that
  outcome. AFS:
  test-specs/chat-interface/lextend_conversation-rename-tooltip-validation-message-content_ELITEA-2111.md

Source-confirmed (``EliteaUI/src/[fsd]/features/chat/conversation-list/ui/
conversations/ConversationItem.jsx`` + ``src/common/constants.js``):
``ConversationNameRegExp = /^[a-zA-Z0-9_[\\].()][a-zA-Z0-9_[\\].() -]{2,63}$/``
(first-char class excludes space/hyphen; later-char class allows both) and
``ConversationNameWarningMessage`` (the single static validation-tooltip
string shown for ANY regex-failure reason — charset, first-char, or length).

Spec:
test-specs/chat-interface/l3_conversation-rename-invalid-chars-leading-space-and-recovery_ELITEA-2110_2112_2113.md
test-specs/chat-interface/lextend_conversation-rename-tooltip-validation-message-content_ELITEA-2111.md

New testid added originally (ELITEA-2110/2112/2113 session): ``chat-conversation-name-confirm-tooltip-content``
(``EliteaAI/EliteaUI@888dac13`` on ``automation/testids``) — mirrors the
pre-existing ``chat-folder-name-confirm-tooltip-content`` (ELITEA-2458) exactly;
the conversation-rename confirm button's validation tooltip had no testid on
its popper content before this. No new testid needed for ELITEA-2111 — reuses
the same handle.

No blocking product defects found -- all four cases pass end-to-end against
the live product exactly as their own case text expects; no case-text drift.
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
NETWORK_SETTLE_TIMEOUT = 5_000

# A 23-char name that is itself VALID per ConversationNameRegExp, so the
# "invalid" assertions below test the CHARSET/first-char branch, not an
# unrelated "unchanged" branch.
ORIGINAL_NAME = "at_rename_invalid_orig"

# The exact validation-tooltip string (source: EliteaUI/src/common/constants.js
# ConversationNameWarningMessage) — asserted verbatim, not a substring guess.
EXPECTED_TOOLTIP_TEXT = (
    "The chat name should be 3 to 64 characters long. It can include letters "
    "(a-z, A-Z), numbers (0-9), underscores (_), brackets ([]), parentheses "
    "(()), dots (.), hyphen(-), and spaces. Please note that the first "
    "character should not be a space."
)


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    A ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken (AFS § Network Behavior / same exclusion documented for the
    2099-2109 conversation-rename family) -- unrelated to renaming.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestConversationRenameInvalidCharsAndRecovery:
    """ELITEA-2110/2112/2113/2111: Chat – Conversation Rename – Invalid
    Characters / Leading Space / Recovery After Invalid Input / Tooltip
    Validation Message Content (l3, medium, all four)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2110_chat-conversation-rename-check-icon-inactive-when-name-contains-special-characters.md",
        "onetest-ai Test Case link — ELITEA-2110",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2112_chat-conversation-rename-first-character-cannot-be-a-space.md",
        "onetest-ai Test Case link — ELITEA-2112",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2111_chat-conversation-rename-tooltip-validation-message-content.md",
        "onetest-ai Test Case link — ELITEA-2111",
    )
    @pytest.mark.p2
    @pytest.mark.parametrize(
        "case_id, invalid_name",
        [
            pytest.param("ELITEA-2110", "HI Chat$$%", id="ELITEA-2110-special-characters"),
            pytest.param("ELITEA-2112", " ab", id="ELITEA-2112-leading-space"),
            pytest.param("ELITEA-2111", "Ch$t %@name", id="ELITEA-2111-dollar-percent-at-characters"),
        ],
    )
    def test_rename_checkmark_inactive_for_invalid_input_shows_tooltip(
        self, page, conversation_api, case_id, invalid_name
    ):
        """Checkmark stays disabled for a charset-invalid / leading-space
        name; hovering shows the exact validation tooltip; clicking is a
        genuine no-op.

        Steps (AFS
        test-specs/chat-interface/l3_conversation-rename-invalid-chars-leading-space-and-recovery_ELITEA-2110_2112_2113.md,
        Shape A):
        1. Hover conv_target, click 3-dot, click Rename -> inline input
           editable, pre-filled with the current name.
        2. Clear and type the row's invalid name (real sequential keystrokes)
           -> input value matches exactly.
        3. Hover the checkmark -> exact ConversationNameWarningMessage
           tooltip text; data-disabled == "true".
        4. Click the checkmark -> no PUT fires, input stays open, sidebar/API
           still show the ORIGINAL name.
        """
        chat = ChatPage(page)
        conv_target_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(f"[{case_id}] Setup — create conv_target via API; navigate to chat"):
                conv_target = conversation_api.create_conversation(ORIGINAL_NAME)
                conv_target_id = conv_target["id"]

                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step(
                f"[{case_id}] Step 1 — Hover conv_target's sidebar item, click "
                "the 3-dot icon, click the Rename menu item; verify the "
                "conversation name becomes an editable inline input "
                "pre-filled with the current name"
            ):
                conv_target_item = chat.get_conversation_item(conv_target_id)
                expect(conv_target_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

                chat.hover_conversation_item(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.open_conversation_context_menu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                rename_item = chat.get_conversation_menu_item("rename")
                expect(rename_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                chat.click_conversation_menu_item("rename", timeout=UI_ELEMENT_TIMEOUT)

                expect(chat.conversation_name_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.conversation_name_input.input_value() == ORIGINAL_NAME, (
                    f"[{case_id}] Rename input should pre-fill with the "
                    f"current name {ORIGINAL_NAME!r}, got "
                    f"{chat.conversation_name_input.input_value()!r}"
                )

            with allure.step(
                f"[{case_id}] Step 2 — Clear the input and type the invalid "
                f"name {invalid_name!r} as real sequential keystrokes; "
                "verify the input value matches exactly"
            ):
                chat.set_conversation_name(invalid_name)

                input_value = chat.conversation_name_input.input_value()
                assert input_value == invalid_name, (
                    f"[{case_id}] Input value should be exactly "
                    f"{invalid_name!r}, got {input_value!r}"
                )

            with allure.step(
                f"[{case_id}] Step 3 — Hover the checkmark icon; verify the "
                "exact validation-rule tooltip text appears and the "
                'checkmark is disabled/inactive (data-disabled == "true")'
            ):
                tooltip_text = chat.get_conversation_name_confirm_tooltip_text(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert tooltip_text == EXPECTED_TOOLTIP_TEXT, (
                    f"[{case_id}] Validation tooltip text should match "
                    f"ConversationNameWarningMessage verbatim, got "
                    f"{tooltip_text!r}"
                )
                assert not chat.is_conversation_name_confirm_enabled(), (
                    f"[{case_id}] Checkmark should stay "
                    'data-disabled="true" for invalid input '
                    f"{invalid_name!r}"
                )

            with allure.step(
                f"[{case_id}] Step 4 — Attempt to click the checkmark icon; "
                "verify it has NO effect: no PUT request fires, the input "
                "remains open, and the conversation's persisted name (read "
                "from the real backend) is unchanged"
            ):
                no_op_put_requests = chat.capture_requests_matching(
                    "/conversation/prompt_lib", method="PUT"
                )
                chat.conversation_name_confirm_button.click()

                # Give any would-be async mutation a chance to register
                # before asserting its absence (framework-native networkidle
                # wait, not a raw sleep — .claude/rules/ui-tests.md).
                chat.wait_for_network(timeout=NETWORK_SETTLE_TIMEOUT)

                assert not no_op_put_requests, (
                    f"[{case_id}] Clicking a disabled checkmark should not "
                    "fire any PUT request to /conversation/prompt_lib/..., "
                    f"captured: {list(no_op_put_requests)!r}"
                )
                no_op_put_requests.stop()

                expect(chat.conversation_name_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.conversation_name_input.input_value() == invalid_name, (
                    f"[{case_id}] Input should keep showing {invalid_name!r} "
                    "after the no-op click, got "
                    f"{chat.conversation_name_input.input_value()!r}"
                )

                persisted = conversation_api.get_conversation(conv_target_id)
                assert persisted["name"] == ORIGINAL_NAME, (
                    f"[{case_id}] The conversation's persisted name should "
                    f"remain {ORIGINAL_NAME!r} (no save was triggered), got "
                    f"{persisted['name']!r}"
                )

                assert not console_messages, (
                    f"[{case_id}] Unexpected console errors while testing "
                    f"invalid input {invalid_name!r}: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            page.remove_listener("console", _on_console)
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("[%s] Cleaned up conv_target %s", case_id, conv_target_id)
                except Exception as exc:
                    logger.warning(
                        "[%s] Failed to delete conv_target %s: %s", case_id, conv_target_id, exc
                    )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2113_chat-conversation-rename-valid-characters-are-accepted-and-saved-after-invalid-value.md",
        "onetest-ai Test Case link — ELITEA-2113",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2111_chat-conversation-rename-tooltip-validation-message-content.md",
        "onetest-ai Test Case link — ELITEA-2111 (step 5: tooltip disappears + checkmark"
        " activates on recovery — coverage-tag only, same assertion below)",
    )
    @pytest.mark.p2
    def test_rename_recovers_and_saves_after_invalid_value_replaced(self, page, conversation_api):
        """ELITEA-2113: checkmark inactive for invalid chars -> replacing
        with a fully valid name activates the checkmark -> click saves
        successfully with no error shown.

        Also covers ELITEA-2111 step 5 ("Remove the invalid characters and
        replace with a valid name of at least 3 characters" -> "Tooltip
        disappears; checkmark becomes active") verbatim via Step 3 below —
        coverage-tag only, no new assertion code (data-value-agnostic: the
        check is against the CURRENT state after replacement, not tied to
        which invalid string preceded it). See AFS
        test-specs/chat-interface/lextend_conversation-rename-tooltip-validation-message-content_ELITEA-2111.md.

        Steps (AFS
        test-specs/chat-interface/l3_conversation-rename-invalid-chars-leading-space-and-recovery_ELITEA-2110_2112_2113.md,
        Shape B):
        1. Hover conv_target, click 3-dot, click Rename -> inline input
           editable.
        2. Clear + type invalid characters ("$$%%") -> checkmark
           data-disabled == "true".
        3. Clear + type "Chat 01 (test)." -> checkmark data-disabled ==
           "false".
        4. Click the checkmark -> input closes, sidebar shows the new name,
           PUT .../conversation/... resolves 200.
        5. No error toast shown.
        """
        case_id = "ELITEA-2113"
        valid_name = "Chat 01 (test)."
        chat = ChatPage(page)
        conv_target_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(f"[{case_id}] Setup — create conv_target via API; navigate to chat"):
                conv_target = conversation_api.create_conversation(ORIGINAL_NAME)
                conv_target_id = conv_target["id"]

                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step(
                f"[{case_id}] Step 1 — Hover conv_target's sidebar item, click "
                "the 3-dot icon, click the Rename menu item; verify the "
                "conversation name becomes an editable inline input"
            ):
                conv_target_item = chat.get_conversation_item(conv_target_id)
                expect(conv_target_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

                chat.hover_conversation_item(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.open_conversation_context_menu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                rename_item = chat.get_conversation_menu_item("rename")
                expect(rename_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                chat.click_conversation_menu_item("rename", timeout=UI_ELEMENT_TIMEOUT)

                expect(chat.conversation_name_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                f"[{case_id}] Step 2 — Clear the name and type invalid "
                'characters ("$$%%"); verify the checkmark icon is inactive '
                '(data-disabled == "true")'
            ):
                chat.set_conversation_name("$$%%")
                assert chat.conversation_name_input.input_value() == "$$%%", (
                    f"[{case_id}] Input value should be '$$%%', got "
                    f"{chat.conversation_name_input.input_value()!r}"
                )
                assert not chat.is_conversation_name_confirm_enabled(), (
                    f"[{case_id}] Checkmark should stay disabled for "
                    "invalid characters"
                )

            with allure.step(
                f"[{case_id}] Step 3 — Clear the invalid input and type "
                f'{valid_name!r}; verify the checkmark icon becomes active '
                '(data-disabled == "false") with no validation error shown'
            ):
                chat.set_conversation_name(valid_name)
                assert chat.conversation_name_input.input_value() == valid_name, (
                    f"[{case_id}] Input value should be {valid_name!r}, got "
                    f"{chat.conversation_name_input.input_value()!r}"
                )
                assert chat.is_conversation_name_confirm_enabled(), (
                    f"[{case_id}] Checkmark should flip to "
                    'data-disabled="false" for a fully valid name'
                )
                # No validation tooltip should mount for a valid name — the
                # source's title prop is '' when isConversationNameValid,
                # so MUI renders no popper (get_..._tooltip_text() returns
                # "" on timeout, which IS the expected/passing outcome here).
                tooltip_text = chat.get_conversation_name_confirm_tooltip_text(timeout=1500)
                assert tooltip_text == "", (
                    f"[{case_id}] No validation tooltip should appear for "
                    f"a valid name, got {tooltip_text!r}"
                )

            with allure.step(
                f"[{case_id}] Step 4 — Click the checkmark icon; verify the "
                f"input closes, the sidebar shows the new name {valid_name!r}, "
                "and the underlying PUT resolves 200"
            ):
                rename_put_requests = chat.capture_requests_matching(
                    "/conversation/prompt_lib", method="PUT"
                )
                chat.conversation_name_confirm_button.click()

                expect(chat.conversation_name_input).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
                expect(conv_target_item).to_contain_text(valid_name, timeout=UI_ELEMENT_TIMEOUT)

                assert rename_put_requests, (
                    f"[{case_id}] A PUT to /conversation/prompt_lib/... "
                    "should have fired when the checkmark was clicked"
                )
                assert rename_put_requests[-1]["status"] == 200, (
                    f"[{case_id}] The rename PUT request should resolve "
                    f"200, got: {rename_put_requests[-1]}"
                )
                rename_put_requests.stop()

            with allure.step(f"[{case_id}] Step 5 — Verify no error message is shown"):
                error_toast = chat.get_toast_alert("error")
                assert error_toast.count() == 0, (
                    f"[{case_id}] No error toast should be shown after a "
                    f"successful rename, found: {error_toast.count()}"
                )
                assert not console_messages, (
                    f"[{case_id}] Unexpected console errors during the "
                    f"rename flow: {[m.text for m in console_messages]!r}"
                )

        finally:
            page.remove_listener("console", _on_console)
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("[%s] Cleaned up conv_target %s", case_id, conv_target_id)
                except Exception as exc:
                    logger.warning(
                        "[%s] Failed to delete conv_target %s: %s", case_id, conv_target_id, exc
                    )
