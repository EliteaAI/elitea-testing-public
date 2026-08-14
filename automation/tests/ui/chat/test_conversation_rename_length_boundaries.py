"""UI Test for ELITEA-2101/ELITEA-2102 — Chat: Conversation Rename — Save with
49/50-Character Names (Length Boundaries).

Family AFS covering two TMS cases that differ only in data: a 49-character
name (ELITEA-2101) and an exactly-50-character name (ELITEA-2102, the
product's ``MAX_CONVERSATION_LENGTH`` boundary). Both are expected to be
accepted WITHOUT truncation and saved successfully via the checkmark — 50 is
the boundary at which truncation would first apply to a *51st* character,
not to the 50th itself (``EliteaUI/src/common/constants.js:74`` +
``ConversationItem.jsx``'s ``onChangeConversationName`` slice, both
source-confirmed in the AFS).

Spec:
test-specs/chat-interface/l3_conversation-rename-length-boundaries_ELITEA-2101_2102.md

Sibling of ``test_conversation_rename_basic_via_edit_option.py`` (ELITEA-2099,
merged) and ``test_conversation_rename_cancel_discards_changes.py``
(ELITEA-2100, merged to this batch's trunk): same page object, same
Rename-menu-item / inline-input / checkmark helpers. This test exercises the
SAVE half of the editor (like ELITEA-2099) at two specific data points the
2099 test never covers (its name is a fixed short string, never near the
length boundary).

No blocking product defects found — both cases pass end-to-end against the
live product exactly as their own case text expects; no case-text drift for
either case (unlike ELITEA-2099/2100/2114, whose Step-2 menu-item-label
drift doesn't recur here since neither case's steps describe the menu's
content, only the Rename flow itself).

Also holds ELITEA-2103/ELITEA-2104 — Chat: Conversation Rename — Cannot
Type/Paste Beyond 50 Characters (the truncation boundary these two cases
never trigger: 49/50-char names never reach the 51st character). Two
separate, non-parametrized test functions (differ in ACTION — per-keystroke
typing vs a real clipboard paste — not just data, per each case's own AFS).
Both source-confirm and live-confirm the SAME
``ConversationItem.jsx``'s ``onChangeConversationName`` handler
(``event.target.value.slice(0, MAX_CONVERSATION_LENGTH)``) truncates
regardless of how the 51st+ character reaches the DOM.

Specs:
test-specs/chat-interface/l3_conversation-rename-cannot-type-beyond-50-chars_ELITEA-2103.md
test-specs/chat-interface/l3_conversation-rename-cannot-paste-beyond-50-chars_ELITEA-2104.md
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

ORIGINAL_NAME = "at_rename_len_orig"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    A ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken (AFS § Network Behavior / same exclusion documented for
    ELITEA-2099/2100/2114) — unrelated to renaming. Matched on both the
    message text and the request location URL, same idiom as the sibling
    chat tests.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestConversationRenameLengthBoundaries:
    """ELITEA-2101/ELITEA-2102: Chat – Conversation Rename – Save with
    49/50-Character Names (Length Boundaries) (l3, medium, both)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2101_chat-conversation-rename-save-with-49-character-name.md",
        "onetest-ai Test Case link — ELITEA-2101",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2102_chat-conversation-rename-save-with-50-character-name.md",
        "onetest-ai Test Case link — ELITEA-2102",
    )
    @pytest.mark.p2
    @pytest.mark.parametrize(
        "case_id, name_length",
        [
            pytest.param("ELITEA-2101", 49, id="ELITEA-2101-49-chars"),
            pytest.param("ELITEA-2102", 50, id="ELITEA-2102-50-chars"),
        ],
    )
    def test_rename_conversation_length_boundary(self, page, conversation_api, case_id, name_length):
        """Rename a conversation to an exactly-N-character name (N=49 or 50).

        Steps (AFS
        test-specs/chat-interface/l3_conversation-rename-length-boundaries_ELITEA-2101_2102.md):
        1. Hover conv_target, click 3-dot, click Rename -> inline input
           editable.
        2. Clear + type exactly N characters -> input value length == N
           (no truncation at 49 or 50); checkmark data-disabled == "false".
        3. Explicit click on the checkmark -> input closes, sidebar shows
           the new N-character name, PUT .../conversation/... resolves 200.
        4. No error toast / no NEW console errors.
        """
        new_name = "A" * name_length
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
                f"[{case_id}] Step 2 — Clear the input and type exactly "
                f"{name_length} characters; verify the input value's length "
                "== N (no truncation) and the checkmark's data-disabled "
                'flips to "false"'
            ):
                chat.set_conversation_name(new_name)
                input_value = chat.conversation_name_input.input_value()
                assert len(input_value) == name_length, (
                    f"[{case_id}] Input value should hold exactly "
                    f"{name_length} characters (no truncation), got "
                    f"{len(input_value)}: {input_value!r}"
                )
                assert input_value == new_name, (
                    f"[{case_id}] Input value should be exactly {new_name!r}, "
                    f"got {input_value!r}"
                )
                assert chat.is_conversation_name_confirm_enabled(), (
                    f"[{case_id}] Checkmark should flip to "
                    'data-disabled="false" once the name changed and '
                    "passes ConversationNameRegExp"
                )

            with allure.step(
                f"[{case_id}] Step 3 — Explicit click on the checkmark "
                "(save) icon; verify the input closes, the sidebar shows "
                f"the new {name_length}-character name, and the underlying "
                "PUT resolves 200"
            ):
                rename_put_requests = chat.capture_requests_matching(
                    "/conversation/prompt_lib", method="PUT"
                )
                chat.conversation_name_confirm_button.click()

                expect(chat.conversation_name_input).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
                expect(conv_target_item).to_contain_text(new_name, timeout=UI_ELEMENT_TIMEOUT)

                assert rename_put_requests, (
                    f"[{case_id}] A PUT to /conversation/prompt_lib/... "
                    "should have fired when the checkmark was clicked"
                )
                assert rename_put_requests[-1]["status"] == 200, (
                    f"[{case_id}] The rename PUT request should resolve "
                    f"200, got: {rename_put_requests[-1]}"
                )
                rename_put_requests.stop()

            with allure.step(
                f"[{case_id}] Step 4 — Verify no error message is shown: "
                "no error toast, no NEW console errors (pre-existing "
                "secrets/403 noise excluded)"
            ):
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

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2103_chat-conversation-rename-cannot-type-beyond-50-characters.md",
        "onetest-ai Test Case link — ELITEA-2103",
    )
    @pytest.mark.p2
    def test_rename_conversation_type_beyond_max_length_truncates(self, page, conversation_api):
        """ELITEA-2103: Chat – Conversation Rename – Cannot Type Beyond 50 Characters.

        Typing a 51-character string character-by-character results in
        exactly the first 50 characters landing in the field — the 51st
        keystroke is silently dropped by the product's own ``onChange``
        handler (client-side ``slice(0, 50)``), not by any test-side
        interception. The checkmark then saves the resulting 50-character
        name successfully.

        Spec:
        test-specs/chat-interface/l3_conversation-rename-cannot-type-beyond-50-chars_ELITEA-2103.md

        Steps (AFS):
        1. Hover conv_target, click 3-dot, click Rename -> inline input
           editable.
        2. Clear + type 51 characters via per-keystroke simulation
           (``press_sequentially``, NOT ``fill()``) -> input value length
           == 50 (51st char dropped); value == "A"*50; checkmark
           data-disabled == "false".
        3. Verify the character count does not exceed 50 (same read as
           step 2 — no separate character-count element exists on this
           editor).
        4. Explicit click on the checkmark -> input closes, sidebar shows
           the new 50-character name, PUT .../conversation/... resolves
           200, no error toast, no new console errors.
        """
        case_id = "ELITEA-2103"
        new_name = "A" * 51
        expected_name = "A" * 50
        chat = ChatPage(page)
        conv_target_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(f"[{case_id}] Setup — create conv_target via API; navigate to chat"):
                conv_target = conversation_api.create_conversation("at_rename_type51_orig")
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
                f"[{case_id}] Step 2 — Clear the input and attempt to TYPE 51 "
                "characters via per-keystroke simulation; verify only the "
                "first 50 land (51st silently dropped) and the checkmark's "
                'data-disabled flips to "false"'
            ):
                chat.set_conversation_name(new_name)
                input_value = chat.conversation_name_input.input_value()
                assert len(input_value) == 50, (
                    f"[{case_id}] Input value should hold exactly 50 "
                    f"characters (51st dropped), got {len(input_value)}: "
                    f"{input_value!r}"
                )
                assert input_value == expected_name, (
                    f"[{case_id}] Input value should be exactly "
                    f"{expected_name!r} (left-slice truncation), got "
                    f"{input_value!r}"
                )
                assert chat.is_conversation_name_confirm_enabled(), (
                    f"[{case_id}] Checkmark should flip to "
                    'data-disabled="false" once the truncated 50-char '
                    "value passes ConversationNameRegExp"
                )

            with allure.step(
                f"[{case_id}] Step 3 — Verify the character count does not "
                "exceed 50 (same input-length read as step 2 — no separate "
                "character counter exists on this editor)"
            ):
                assert len(chat.conversation_name_input.input_value()) <= 50, (
                    f"[{case_id}] Input value must never exceed 50 characters"
                )

            with allure.step(
                f"[{case_id}] Step 4 — Explicit click on the checkmark (save) "
                "icon; verify the input closes, the sidebar shows the new "
                "50-character name, the underlying PUT resolves 200, no "
                "error toast, no new console errors"
            ):
                rename_put_requests = chat.capture_requests_matching(
                    "/conversation/prompt_lib", method="PUT"
                )
                chat.conversation_name_confirm_button.click()

                expect(chat.conversation_name_input).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
                expect(conv_target_item).to_contain_text(expected_name, timeout=UI_ELEMENT_TIMEOUT)

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

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2104_chat-conversation-rename-cannot-paste-more-than-50-characters.md",
        "onetest-ai Test Case link — ELITEA-2104",
    )
    @pytest.mark.p2
    def test_rename_conversation_paste_beyond_max_length_truncates(self, page, conversation_api):
        """ELITEA-2104: Chat – Conversation Rename – Cannot Paste More Than 50 Characters.

        Pasting a 60-character clipboard string via a REAL OS/browser
        clipboard write + a genuine Control+V/Meta+V keypress results in
        exactly the first 50 characters landing in the field — characters
        51-60 are silently dropped by the product's own ``onChange``
        handler (client-side ``slice(0, 50)``), reached via the SAME code
        path as typing (ELITEA-2103) since no separate ``onPaste`` handler
        exists on the input. The checkmark then saves the resulting
        50-character name successfully.

        Spec:
        test-specs/chat-interface/l3_conversation-rename-cannot-paste-beyond-50-chars_ELITEA-2104.md

        Steps (AFS):
        1. Hover conv_target, click 3-dot, click Rename -> inline input
           editable.
        2. Clear the input -> value empty (length 0).
        3. Write a 60-char string to the REAL system clipboard
           (``navigator.clipboard.writeText``) and paste it via a real
           Control+V/Meta+V keypress -> input value length == 50 (chars
           51-60 dropped); value == first 50 chars of the source string;
           checkmark data-disabled == "false".
        4. Verify the 51st character and beyond are not present (same
           length/content read as step 3).
        5. Explicit click on the checkmark -> input closes, sidebar shows
           the new 50-character name, PUT .../conversation/... resolves
           200, no error toast, no new console errors.
        """
        case_id = "ELITEA-2104"
        source_string = "A" * 60
        expected_name = "A" * 50
        chat = ChatPage(page)
        conv_target_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(f"[{case_id}] Setup — create conv_target via API; navigate to chat"):
                conv_target = conversation_api.create_conversation("at_rename_paste60_orig")
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

            with allure.step(f"[{case_id}] Step 2 — Clear the input; verify the value is empty"):
                chat.clear_conversation_name()
                expect(chat.conversation_name_input).to_have_value("", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                f"[{case_id}] Step 3 — Write a 60-character string to the "
                "REAL system clipboard and paste it via Control+V/Meta+V; "
                "verify only the first 50 characters land and the "
                "checkmark's data-disabled flips to \"false\""
            ):
                chat.paste_conversation_name(source_string)
                expect(chat.conversation_name_input).to_have_value(
                    expected_name, timeout=UI_ELEMENT_TIMEOUT
                )
                input_value = chat.conversation_name_input.input_value()
                assert len(input_value) == 50, (
                    f"[{case_id}] Input value should hold exactly 50 "
                    f"characters (chars 51-60 dropped), got "
                    f"{len(input_value)}: {input_value!r}"
                )
                assert chat.is_conversation_name_confirm_enabled(), (
                    f"[{case_id}] Checkmark should flip to "
                    'data-disabled="false" once the truncated 50-char '
                    "value passes ConversationNameRegExp"
                )

            with allure.step(
                f"[{case_id}] Step 4 — Verify the 51st character and beyond "
                "are not present (same length/content read as step 3)"
            ):
                current_value = chat.conversation_name_input.input_value()
                assert current_value == expected_name, (
                    f"[{case_id}] Input value should be exactly "
                    f"{expected_name!r} (left-slice truncation, no "
                    "reordered/dropped-from-the-middle corruption), got "
                    f"{current_value!r}"
                )

            with allure.step(
                f"[{case_id}] Step 5 — Explicit click on the checkmark (save) "
                "icon; verify the input closes, the sidebar shows the new "
                "50-character name, the underlying PUT resolves 200, no "
                "error toast, no new console errors"
            ):
                rename_put_requests = chat.capture_requests_matching(
                    "/conversation/prompt_lib", method="PUT"
                )
                chat.conversation_name_confirm_button.click()

                expect(chat.conversation_name_input).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
                expect(conv_target_item).to_contain_text(expected_name, timeout=UI_ELEMENT_TIMEOUT)

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
