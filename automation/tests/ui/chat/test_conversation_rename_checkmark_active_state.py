"""UI Test for ELITEA-2105/2106/2107/2108/2109 — Chat: Conversation Rename —
Checkmark Active/Inactive States.

Family AFS covering five TMS cases that all drive the SAME ``isSaveEnabled``
gate on the SAME inline rename editor (``ConversationItem.jsx``), differing
only in the data/state fed into the input:

- ELITEA-2105: no changes made to an already-valid name -> checkmark stays
  disabled (fails the "changed" half of the gate).
- ELITEA-2106: field cleared to empty -> checkmark stays disabled (fails the
  "valid" half -- ``ConversationNameRegExp`` rejects an empty string).
- ELITEA-2107: exactly 1 character -> checkmark stays disabled (below the
  regex's 3-char floor).
- ELITEA-2108: exactly 2 characters -> checkmark stays disabled (still below
  the 3-char floor).
- ELITEA-2109: 2 characters (disabled) -> append 1 more to reach 3 characters
  (checkmark activates) -> click saves successfully.

Source-confirmed (``EliteaUI/src/[fsd]/features/chat/conversation-list/ui/
conversations/ConversationItem.jsx`` + ``src/common/constants.js``):
``ConversationNameRegExp = /^[a-zA-Z0-9_[\\].()][a-zA-Z0-9_[\\].() -]{2,63}$/``
(3-64 chars total) and ``isSaveEnabled = isConversationNameValid &&
(isNew || conversationName !== name)``. The confirm ``Box``'s
``onClick={isSaveEnabled ? (isNew ? onCreate : onSave) : null}`` -- when
disabled, ``onClick`` is literally ``null``, so a disabled-state click is a
genuine, un-intercepted browser no-op: this test asserts that no-op honestly
(no PUT request fires, the editor stays open, the sidebar keeps showing the
conversation's ORIGINAL persisted name) rather than only reading the DOM
state.

Spec:
test-specs/chat-interface/l3_conversation-rename-checkmark-active-inactive-states_ELITEA-2105_2106_2107_2108_2109.md

No new testids needed -- reuses ``chat-conversation-name-input`` /
``chat-conversation-name-confirm-button`` (``data-disabled`` state) /
``chat-conversation-name-cancel-button``, all added during ELITEA-2099's
implementation (``EliteaAI/EliteaUI@ff56e29d``).

No blocking product defects found -- all five cases pass end-to-end against
the live product exactly as their own case text expects; no case-text drift
(none of these five cases' steps describe the context-menu's content, only
the rename-editor's checkmark behavior, so the Rename-vs-Edit label drift
already documented for ELITEA-2099/2100/2114 does not recur here).
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

# A 25-char name that is itself VALID per ConversationNameRegExp, so
# ELITEA-2105's "no changes made" row isolates the "valid but unchanged"
# branch of isSaveEnabled from the "invalid" branch ELITEA-2106/2107/2108
# exercise.
ORIGINAL_NAME = "at_rename_checkmark_orig"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    A ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken (AFS § Network Behavior / same exclusion documented for
    ELITEA-2099/2100/2101/2102) -- unrelated to renaming.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestConversationRenameCheckmarkActiveState:
    """ELITEA-2105/2106/2107/2108/2109: Chat – Conversation Rename – Checkmark
    Active/Inactive States (l3, medium, all five)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2105_chat-conversation-rename-check-icon-inactive-when-no-changes-made.md",
        "onetest-ai Test Case link — ELITEA-2105",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2106_chat-conversation-rename-check-icon-inactive-when-name-field-is-empty.md",
        "onetest-ai Test Case link — ELITEA-2106",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2107_chat-conversation-rename-check-icon-inactive-for-1-character-input.md",
        "onetest-ai Test Case link — ELITEA-2107",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2108_chat-conversation-rename-check-icon-inactive-for-2-character-input.md",
        "onetest-ai Test Case link — ELITEA-2108",
    )
    @pytest.mark.p2
    @pytest.mark.parametrize(
        "case_id, action, expected_value",
        [
            pytest.param("ELITEA-2105", "no_change", ORIGINAL_NAME, id="ELITEA-2105-no-changes"),
            pytest.param("ELITEA-2106", "clear", "", id="ELITEA-2106-empty-field"),
            pytest.param("ELITEA-2107", "type", "A", id="ELITEA-2107-1-char"),
            pytest.param("ELITEA-2108", "type", "AB", id="ELITEA-2108-2-char"),
        ],
    )
    def test_rename_checkmark_inactive_click_has_no_effect(
        self, page, conversation_api, case_id, action, expected_value
    ):
        """Checkmark stays disabled for unchanged/empty/1-char/2-char input;
        clicking it while disabled is a genuine no-op.

        Steps (AFS
        test-specs/chat-interface/l3_conversation-rename-checkmark-active-inactive-states_ELITEA-2105_2106_2107_2108_2109.md,
        Shape A):
        1. Hover conv_target, click 3-dot, click Rename -> inline input
           editable, pre-filled with the current name.
        2. Apply the row's input action (no typing / clear / type N chars)
           -> input value matches exactly.
        3. Checkmark's data-disabled == "true".
        4. Click the checkmark -> no PUT fires, input stays open, sidebar
           still shows the ORIGINAL name.
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
                f"[{case_id}] Step 2 — Apply the row's input action "
                f"({action!r}); verify the input value matches exactly "
                f"{expected_value!r}"
            ):
                if action == "no_change":
                    pass  # leave the pre-filled original name untouched
                elif action == "clear":
                    chat.clear_conversation_name()
                elif action == "type":
                    chat.set_conversation_name(expected_value)
                else:  # pragma: no cover - guards against a typo in the param table
                    raise ValueError(f"Unknown action {action!r}")

                input_value = chat.conversation_name_input.input_value()
                assert input_value == expected_value, (
                    f"[{case_id}] Input value should be exactly "
                    f"{expected_value!r}, got {input_value!r}"
                )

            with allure.step(
                f"[{case_id}] Step 3 — Verify the checkmark icon is "
                'displayed in a disabled/inactive state (data-disabled == "true")'
            ):
                assert not chat.is_conversation_name_confirm_enabled(), (
                    f"[{case_id}] Checkmark should stay "
                    'data-disabled="true" for this input state'
                )

            with allure.step(
                f"[{case_id}] Step 4 — Attempt to click the checkmark icon; "
                "verify it has NO effect: no PUT request fires, the input "
                "remains open (per ConversationItem.jsx, the "
                "chat-conversation-item-{id} testid only renders when NOT "
                "editing, so the persisted name is read from the real "
                "backend — not a substitution, the system's own record)"
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
                assert chat.conversation_name_input.input_value() == expected_value, (
                    f"[{case_id}] Input should keep showing {expected_value!r} "
                    "after the no-op click, got "
                    f"{chat.conversation_name_input.input_value()!r}"
                )

                persisted = conversation_api.get_conversation(conv_target_id)
                assert persisted["name"] == ORIGINAL_NAME, (
                    f"[{case_id}] The conversation's persisted name should "
                    f"remain {ORIGINAL_NAME!r} (no save was triggered), got "
                    f"{persisted['name']!r}"
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
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2109_chat-conversation-rename-check-icon-becomes-active-at-3-characters.md",
        "onetest-ai Test Case link — ELITEA-2109",
    )
    @pytest.mark.p2
    def test_rename_checkmark_activates_at_three_characters(self, page, conversation_api):
        """ELITEA-2109: checkmark transitions inactive (2 chars) -> active (3
        chars), and a click at 3 characters saves successfully.

        Steps (AFS
        test-specs/chat-interface/l3_conversation-rename-checkmark-active-inactive-states_ELITEA-2105_2106_2107_2108_2109.md,
        Shape B):
        1. Hover conv_target, click 3-dot, click Rename -> inline input
           editable.
        2. Clear + type 2 characters ("AB") -> checkmark data-disabled ==
           "true".
        3. Append 1 more character ("C" -> "ABC", a genuine incremental
           keystroke, not a clear+retype) -> checkmark data-disabled ==
           "false".
        4. Click the checkmark -> input closes, sidebar shows "ABC", PUT
           .../conversation/... resolves 200.
        """
        case_id = "ELITEA-2109"
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
                f"[{case_id}] Step 2 — Clear the input and type exactly 2 "
                'characters ("AB"); verify the checkmark icon is inactive/'
                'greyed out (data-disabled == "true")'
            ):
                chat.set_conversation_name("AB")
                assert chat.conversation_name_input.input_value() == "AB", (
                    f"[{case_id}] Input value should be 'AB', got "
                    f"{chat.conversation_name_input.input_value()!r}"
                )
                assert not chat.is_conversation_name_confirm_enabled(), (
                    f"[{case_id}] Checkmark should stay disabled at 2 "
                    "characters"
                )

            with allure.step(
                f"[{case_id}] Step 3 — Type one more character to reach 3 "
                'characters ("C" appended -> "ABC"); verify the checkmark '
                'icon becomes active/enabled (data-disabled == "false")'
            ):
                chat.conversation_name_input.press_sequentially("C", delay=30)
                assert chat.conversation_name_input.input_value() == "ABC", (
                    f"[{case_id}] Input value should be 'ABC' after "
                    "appending one more character, got "
                    f"{chat.conversation_name_input.input_value()!r}"
                )
                assert chat.is_conversation_name_confirm_enabled(), (
                    f"[{case_id}] Checkmark should flip to "
                    'data-disabled="false" once the input reaches 3 '
                    "characters"
                )

            with allure.step(
                f"[{case_id}] Step 4 — Click the checkmark icon; verify the "
                "input closes, the sidebar shows the new name 'ABC', and "
                "the underlying PUT resolves 200"
            ):
                rename_put_requests = chat.capture_requests_matching(
                    "/conversation/prompt_lib", method="PUT"
                )
                chat.conversation_name_confirm_button.click()

                expect(chat.conversation_name_input).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
                expect(conv_target_item).to_contain_text("ABC", timeout=UI_ELEMENT_TIMEOUT)

                assert rename_put_requests, (
                    f"[{case_id}] A PUT to /conversation/prompt_lib/... "
                    "should have fired when the checkmark was clicked"
                )
                assert rename_put_requests[-1]["status"] == 200, (
                    f"[{case_id}] The rename PUT request should resolve "
                    f"200, got: {rename_put_requests[-1]}"
                )
                rename_put_requests.stop()

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
