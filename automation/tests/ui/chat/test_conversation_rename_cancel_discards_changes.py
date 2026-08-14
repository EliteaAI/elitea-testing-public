"""UI Test for ELITEA-2100 — Chat: Conversation Rename — Cancel Discards Changes.

Verifies clicking the X (cancel) icon during the inline rename editor
discards the typed change WITHOUT issuing any network mutation and WITHOUT
changing the conversation's stored name — including across a
navigate-away-and-back round trip.

Spec: test-specs/chat-interface/l3_conversation-rename-cancel-discards-changes_ELITEA-2100.md

Sibling of ``test_conversation_rename_basic_via_edit_option.py`` (ELITEA-2099,
merged to this batch's trunk): that test proves the *save* half of the same
inline rename editor (explicit checkmark click -> PUT 200 -> new name
persists). This test exercises the opposite (**cancel/discard**) branch of
the SAME editor and asserts a different observable — that clicking the X
icon closes the editor WITHOUT any network mutation and the original name
survives, including after navigating away and back. Distinct steps
(discard vs save), so this is a separate spec/test, not an extension of
ELITEA-2099's.

Known case-text drift (issue #1513, sibling of the already-accepted #695 /
ELITEA-2114 — same drift already accepted for ELITEA-2099): the case's own
Step 2 says "click Edit"; the live menu item is labelled "Rename". This test
asserts the LIVE label (reverse-masking guard — the live product is
correct, the case text is stale).

No blocking product defects found — all 6 case steps executed live
end-to-end and matched expected results (modulo the case-text drift above).
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

ORIGINAL_NAME = "at_rename_cancel_orig"
DISCARDED_NAME = "Renamed Chat"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    A ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken (AFS § Network Behavior / same exclusion documented for
    ELITEA-2099/ELITEA-2114) — unrelated to renaming. Matched on both the
    message text and the request location URL, same idiom as the sibling
    chat tests.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestConversationRenameCancelDiscardsChanges:
    """ELITEA-2100: Chat – Conversation Rename – Cancel Discards Changes (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2100_chat-conversation-rename-cancel-discards-changes.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_rename_conversation_cancel_discards_changes(self, page, conversation_api):
        """Clicking the cancel (X) icon discards the typed rename, no PUT fires.

        Steps (AFS
        test-specs/chat-interface/l3_conversation-rename-cancel-discards-changes_ELITEA-2100.md):
        1. Chats panel + conv_target visible.
        2. 3-dot icon -> Rename item (case's own "Edit", live label drift
           #1513) -> inline input pre-filled with the CURRENT name;
           checkmark (disabled) + X icons visible.
        3. Clear + type 'Renamed Chat' -> new name in field, no PUT fires
           from typing alone.
        4. Click the X (cancel) icon -> input closes, NO PUT fires at all.
        5. Sidebar item still shows the ORIGINAL name.
        6. No error toast / no NEW console errors; original name survives
           a navigate-away-and-back round trip through the UI.
        """
        chat = ChatPage(page)
        conv_target_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step("Setup — create conv_target via API; navigate to chat"):
                conv_target = conversation_api.create_conversation(ORIGINAL_NAME)
                conv_target_id = conv_target["id"]

                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step(
                "Step 1 — Verify the Chats/Conversations panel is displayed"
            ):
                expect(chat.conversations_panel_heading).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                conv_target_item = chat.get_conversation_item(conv_target_id)
                expect(conv_target_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 2 — Hover conv_target's sidebar item, click the "
                "3-dot icon, click the Rename item (the case's own 'Edit "
                "option'; live label drift #1513, same clarification "
                "accepted for ELITEA-2099); verify the inline input "
                "pre-fills with the CURRENT name and both checkmark "
                "(disabled) and X icons are visible"
            ):
                chat.hover_conversation_item(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.open_conversation_context_menu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                rename_item = chat.get_conversation_menu_item("rename")
                expect(rename_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                chat.click_conversation_menu_item("rename", timeout=UI_ELEMENT_TIMEOUT)

                expect(chat.conversation_name_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.conversation_name_input.input_value() == ORIGINAL_NAME, (
                    f"Rename input should pre-fill with the current name "
                    f"{ORIGINAL_NAME!r}, got {chat.conversation_name_input.input_value()!r}"
                )
                expect(chat.conversation_name_confirm_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert not chat.is_conversation_name_confirm_enabled(), (
                    "Checkmark should be disabled (data-disabled=\"true\") "
                    "while the name is unchanged"
                )
                expect(chat.conversation_name_cancel_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Clear the current name and type "
                f"{DISCARDED_NAME!r}; verify the new name appears in the "
                "field and no PUT fires from typing alone"
            ):
                typing_put_requests = chat.capture_requests_matching(
                    "/conversation/prompt_lib", method="PUT"
                )
                chat.set_conversation_name(DISCARDED_NAME)
                assert chat.conversation_name_input.input_value() == DISCARDED_NAME, (
                    f"Input value should be {DISCARDED_NAME!r} after "
                    f"typing, got {chat.conversation_name_input.input_value()!r}"
                )
                assert chat.is_conversation_name_confirm_enabled(), (
                    "Checkmark should flip to data-disabled=\"false\" once "
                    "the name changed and passes ConversationNameRegExp"
                )
                assert not typing_put_requests, (
                    "Typing a new name alone should not fire any PUT "
                    f"request, captured: {list(typing_put_requests)!r}"
                )
                typing_put_requests.stop()

            with allure.step(
                "Step 4 — Click the X (cancel) icon; verify the input "
                "field closes WITHOUT saving and NO PUT request fires at "
                "all (the case's central assertion — a true client-side "
                "discard, not a save-then-revert round trip)"
            ):
                cancel_put_requests = chat.capture_requests_matching(
                    "/conversation/prompt_lib", method="PUT"
                )
                chat.conversation_name_cancel_button.click()

                expect(chat.conversation_name_input).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

                assert not cancel_put_requests, (
                    "Clicking cancel should not fire any PUT request to "
                    f"/conversation/prompt_lib/..., captured: {list(cancel_put_requests)!r}"
                )
                cancel_put_requests.stop()

            with allure.step(
                "Step 5 — Verify the conversation still displays its "
                "ORIGINAL name (not the discarded 'Renamed Chat')"
            ):
                expect(conv_target_item).to_contain_text(ORIGINAL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                expect(conv_target_item).not_to_contain_text(DISCARDED_NAME)

            with allure.step(
                "Step 6 — Verify no changes were applied: no error toast, "
                "no NEW console errors (pre-existing secrets/403 noise "
                "excluded); original name survives a navigate-away-and-"
                "back round trip through the UI"
            ):
                error_toast = chat.get_toast_alert("error")
                assert error_toast.count() == 0, (
                    f"No error toast should be shown after cancelling a "
                    f"rename, found: {error_toast.count()}"
                )
                assert not console_messages, (
                    "Unexpected console errors during the cancel-rename "
                    f"flow: {[m.text for m in console_messages]!r}"
                )

                chat.navigate_to_chat()
                chat.wait_for_page_load()

                conv_target_item_after = chat.get_conversation_item(conv_target_id)
                expect(conv_target_item_after).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                conv_target_item_after.click(force=True)
                chat.wait_for_conversation_url(conv_target_id, timeout=NAVIGATION_TIMEOUT)

                expect(conv_target_item_after).to_contain_text(ORIGINAL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                expect(conv_target_item_after).not_to_contain_text(DISCARDED_NAME)

        finally:
            page.remove_listener("console", _on_console)
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("Cleaned up conv_target %s", conv_target_id)
                except Exception as exc:
                    logger.warning("Failed to delete conv_target %s: %s", conv_target_id, exc)
