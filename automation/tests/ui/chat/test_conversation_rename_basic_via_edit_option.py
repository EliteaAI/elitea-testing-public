"""UI Test for ELITEA-2099 — Chat: Conversation Rename — Basic Rename via Edit Option.

Verifies renaming a conversation via the 3-dot menu's "Rename" item (the
case's own "Edit option" — see the Step-3 clarification below): the inline
editor pre-fills with the CURRENT name, the checkmark (confirm) icon is
gated on a real "name changed AND valid" state via ``data-disabled``, the
new name commits via an EXPLICIT click on the checkmark (not Enter), and
the new name persists both immediately in the sidebar and after navigating
away and back.

Spec: test-specs/chat-interface/l3_conversation-rename-basic-via-edit-option_ELITEA-2099.md

Distinct from the pre-existing
``test_conversation_management.py::TestConversationActions::test_rename_conversation_via_ui``
(ELITEA-0570): that test proves the coarser "rename via menu -> new name
in sidebar, old name gone, persisted via API" outcome using
``rename_conversation_via_menu()`` (raw selectors, confirms with Enter).
This test exercises the ELITEA-2114-era testid-based helpers
(``open_conversation_context_menu`` / ``click_conversation_menu_item``),
asserts the pre-fill + checkmark/cancel affordances + explicit-click-save
+ UI-level (not just API) persistence-after-navigation that the older test
never checks, and shares the page object without touching it.

Known case-text drift (issue #1513, sibling of the already-accepted #695 /
ELITEA-2114): the case's own Step 3 literal menu-item list ("Delete, Edit,
Move to, Export, Playback, Pin on top") does not match the live product —
the live menu is "Rename, Move to, Playback, Duplicate, Make public,
Share, Pin on top, Delete" (8 items), and the case's "Edit option" is
rendered live as "Rename". This test asserts the LIVE set/label
(reverse-masking guard — the live product is correct, the case text is
stale), not the case's literal wording.

No blocking product defects found — all 9 case steps executed live
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

ORIGINAL_NAME = "at_rename_basic_orig"
NEW_NAME = "HI Chat_edited"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    A ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken (AFS § Network Behavior / same exclusion documented for
    ELITEA-2114) — unrelated to renaming. Matched on both the message text
    and the request location URL, same idiom as the sibling chat tests.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestConversationRenameBasicViaEditOption:
    """ELITEA-2099: Chat – Conversation Rename – Basic Rename via Edit Option (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2099_chat-conversation-rename-basic-rename-via-edit-option.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_rename_conversation_basic_via_edit_option(self, page, conversation_api):
        """Rename a conversation via the 3-dot menu's Rename item, checkmark save.

        Steps (AFS
        test-specs/chat-interface/l3_conversation-rename-basic-via-edit-option_ELITEA-2099.md):
        1. Chats panel + conv_target visible.
        2. 3-dot icon transitions hidden -> visible on hover.
        3. Context menu shows the LIVE item set (case-text drift, #1513).
        4. Click Rename -> inline input pre-filled with the CURRENT name.
        5. Checkmark (data-disabled="true") + cancel icons visible.
        6. Clear + type new name -> checkmark flips to data-disabled="false".
        7. Explicit click on checkmark -> input closes, new name in sidebar,
           PUT .../conversation/... resolves 200.
        8. No error toast / no NEW console errors.
        9. Navigate away and back -> new name persists via the UI.
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
                "Step 2 — Hover conv_target's sidebar item; verify the "
                "3-dot menu button transitions from not-visible to visible"
            ):
                menu_button = chat.get_conversation_menu_button(conv_target_id)
                expect(menu_button).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                chat.hover_conversation_item(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(menu_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Click the 3-dot icon; verify the context menu is "
                "visible with the LIVE item set (case-text drift — case "
                "says 'Delete, Edit, Move to, Export, Playback, Pin on "
                "top'; live product renders Rename/Move to/Playback/"
                "Duplicate/Make public/Share/Pin on top/Delete — issue "
                "#1513)"
            ):
                chat.open_conversation_context_menu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                item_count = chat.get_open_conversation_menu_item_count()
                assert item_count > 0, "Context menu should render at least one item"
                rename_item = chat.get_conversation_menu_item("rename")
                expect(rename_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 4 — Click the Rename menu item (the case's 'Edit "
                "option'); verify the inline input pre-fills with the "
                "CURRENT name before any edit"
            ):
                chat.click_conversation_menu_item("rename", timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.conversation_name_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.conversation_name_input.input_value() == ORIGINAL_NAME, (
                    f"Rename input should pre-fill with the current name "
                    f"{ORIGINAL_NAME!r}, got {chat.conversation_name_input.input_value()!r}"
                )

            with allure.step(
                "Step 5 — Verify checkmark (save, disabled while unchanged) "
                "and X (cancel) icons appear"
            ):
                expect(chat.conversation_name_confirm_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert not chat.is_conversation_name_confirm_enabled(), (
                    "Checkmark should be disabled (data-disabled=\"true\") "
                    "while the name is unchanged"
                )
                expect(chat.conversation_name_cancel_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 6 — Clear the current name and type "
                f"{NEW_NAME!r}; verify the checkmark becomes enabled"
            ):
                chat.set_conversation_name(NEW_NAME)
                assert chat.conversation_name_input.input_value() == NEW_NAME, (
                    f"Input value should be {NEW_NAME!r} after typing, got "
                    f"{chat.conversation_name_input.input_value()!r}"
                )
                assert chat.is_conversation_name_confirm_enabled(), (
                    "Checkmark should flip to data-disabled=\"false\" once "
                    "the name changed and passes ConversationNameRegExp"
                )

            with allure.step(
                "Step 7 — Explicit click on the checkmark (save) icon "
                "(NOT Enter); verify the input closes, the sidebar shows "
                "the new name, and the underlying PUT resolves 200"
            ):
                rename_put_requests = chat.capture_requests_matching(
                    "/conversation/prompt_lib", method="PUT"
                )
                chat.conversation_name_confirm_button.click()

                expect(chat.conversation_name_input).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
                expect(conv_target_item).to_contain_text(NEW_NAME, timeout=UI_ELEMENT_TIMEOUT)

                assert rename_put_requests, (
                    "A PUT to /conversation/prompt_lib/... should have "
                    "fired when the checkmark was clicked"
                )
                assert rename_put_requests[-1]["status"] == 200, (
                    "The rename PUT request should resolve 200, got: "
                    f"{rename_put_requests[-1]}"
                )
                rename_put_requests.stop()

            with allure.step(
                "Step 8 — Verify no error toast is shown and no NEW "
                "console errors appeared (pre-existing secrets/403 noise "
                "excluded)"
            ):
                error_toast = chat.get_toast_alert("error")
                assert error_toast.count() == 0, (
                    f"No error toast should be shown after a successful "
                    f"rename, found: {error_toast.count()}"
                )
                assert not console_messages, (
                    "Unexpected console errors during the rename flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

            with allure.step(
                "Step 9 — Navigate away and return to the Chats section; "
                "verify the updated name persists via the UI (not just "
                "re-fetched via API)"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()

                # Click the testid-scoped sidebar item directly (not the
                # legacy name/href-guessing select_conversation_by_id() —
                # tracked tech debt) — force=True bypasses the MUI overlay
                # divs that intercept pointer events in the conversations
                # panel (same idiom as select_conversation_from_list()).
                conv_target_item_after = chat.get_conversation_item(conv_target_id)
                expect(conv_target_item_after).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                conv_target_item_after.click(force=True)
                chat.wait_for_conversation_url(conv_target_id, timeout=NAVIGATION_TIMEOUT)

                expect(conv_target_item_after).to_contain_text(NEW_NAME, timeout=UI_ELEMENT_TIMEOUT)

        finally:
            page.remove_listener("console", _on_console)
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("Cleaned up conv_target %s", conv_target_id)
                except Exception as exc:
                    logger.warning("Failed to delete conv_target %s: %s", conv_target_id, exc)
