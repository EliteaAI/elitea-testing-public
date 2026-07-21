"""UI Test for ELITEA-2114 — Chat: Conversation Deletion.

Verifies the full conversation-deletion flow on the ACTIVE conversation:
date-grouped sidebar list, hover-reveal of the 3-dot menu, full context-menu
enumeration, the delete-confirmation dialog (body text, both buttons),
Cancel-then-Delete as one continuous flow on the SAME conversation, the
underlying DELETE network call, sidebar removal, and next-conversation
auto-selection + main-panel refresh.

Spec: test-specs/chat-interface/l2_conversation-deletion_ELITEA-2114.md

Relationship to existing coverage: ``test_conversation_management.py``'s
``TestConversationActions.test_delete_conversation_with_confirmation`` and
``test_delete_conversation_cancel`` already cover isolated cancel/delete
flows, but neither (a) runs cancel-then-delete on the SAME conversation as
one continuous flow, nor (b) opens the target conversation as the ACTIVE
one first (required for next-conversation auto-selection to trigger at
all — see ``useDeleteConversation.js``'s ``findNextConversation``). Per the
AFS's own Automation Hints, this ships as a THIRD, separate test rather than
folding the two existing ones in — additive-only, no existing merged test
touched (see PR description for the full reasoning).

AFS-drift discovered during implementation (documented in the AFS as
CLARIFICATION-2, amended in-PR): the case's default test project
(``${ELITEA_PROJECT_ID}``, the account's own Private project) only shows 5 of
the AFS's originally-claimed 7 context-menu items — "Make public" and
"Share" are intentionally hidden for a user's own private-project
conversations (``ConversationItem.jsx``'s ``menuItems`` ``display`` filter).
This test asserts the live, correct 5-item set for the project it actually
runs against, not the case's or the AFS's original (7-item) claim.

Known defect BUG #694 (``BaseModal`` ``aria-labelledby``/``#alert-dialog-title``
id mismatch) is isolated and out of scope here — this test's title assertion
uses the NEW ``delete-confirm-title`` testid (added this implementation),
which does not depend on the broken id wiring.
"""

import logging
import re
import time

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Live-verified for the default test project (${ELITEA_PROJECT_ID}, Private) —
# see CLARIFICATION-2 in the AFS. "Make public"/"Share" are absent by design.
EXPECTED_MENU_ITEM_KEYS = ("rename", "move-to", "playback", "pin", "delete")


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    A ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken (AFS § Automation Hints) — an unrelated toolkit/secrets
    panel probe, not caused by the delete flow. Matched on both the message
    text and the request location URL (same idiom as
    ``test_open_conversation_today_section.py``'s equivalent filter) so a
    genuinely NEW 403 elsewhere isn't accidentally swallowed.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestConversationDeletionFlow:
    """ELITEA-2114: Chat – Conversation Deletion (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2114_chat-conversation-deletion.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_conversation_deletion_cancel_then_delete_active_conversation(
        self, page, conversation_api,
    ):
        """Cancel preserves the active conversation; Delete removes it and
        auto-selects the next remaining conversation.

        Steps (AFS
        test-specs/chat-interface/l2_conversation-deletion_ELITEA-2114.md):
        1. Navigate to chat with conv_target active; verify sidebar list
           grouped by date (Today) with conv_target under it.
        2. Hover conv_target; verify the 3-dot menu button transitions
           hidden -> visible.
        3. Click the 3-dot button; verify the context menu shows exactly
           the live 5-item set for this project (see CLARIFICATION-2).
        4. Click Delete; verify the confirmation dialog appears.
        5. Verify the dialog body text.
        6. Verify both dialog buttons are present.
        7. Click Cancel; verify the dialog closes and conv_target remains
           active.
        8. Reopen the menu, click Delete again; verify the dialog reopens
           cleanly (no stale-modal residue from the prior Cancel).
        9. Click the Delete (confirm) button; verify the dialog closes and
           the underlying DELETE request resolves 204.
        10. Verify conv_target is gone from the sidebar.
        11. Verify no new console errors and the next conversation is
            auto-selected (URL moves off conv_target, data-active reflects
            the new conversation).
        12. Verify the main chat panel no longer shows conv_target content.
        """
        chat = ChatPage(page)
        conv_target_id = None
        conv_sibling_id = None

        # Registered before setup so console errors from every step are
        # captured (side-channel discipline — silent errors are the worst
        # bugs). The known, environment-wide secrets 403 noise (see
        # _is_known_secrets_403) is filtered so it can't mask a genuinely
        # new error.
        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — create conv_sibling then conv_target via API; "
                "open conv_target so it becomes the ACTIVE conversation"
            ):
                # conv_sibling first so the app has a deterministic "other"
                # conversation for step 11's auto-select to land on (AFS
                # § Test Data — without a second conversation, deleting the
                # only/active conversation falls back to an empty state
                # instead of exercising next-conversation selection).
                ts = int(time.time())
                sibling = conversation_api.create_conversation(f"autotest_2114_sibling_{ts}")
                conv_sibling_id = sibling["id"]
                target = conversation_api.create_conversation(f"autotest_2114_target_{ts}")
                conv_target_id = target["id"]
                target_name = target["name"]

                # This single navigation satisfies both the AFS's Setup
                # step 0 (open conv_target so it becomes active — required
                # for step 11's auto-select to trigger at all) and case
                # step 1 (navigate to chat, sidebar list renders).
                chat.navigate_to_chat(conversation_id=conv_target_id)
                chat.wait_for_page_load()
                assert chat.is_conversation_active(conv_target_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"conv_target {conv_target_id} should be the active "
                    "conversation right after navigating to it"
                )

            with allure.step(
                "Step 1 — Verify the sidebar conversation list renders "
                "under the Today date-group heading, with conv_target "
                "under it specifically"
            ):
                assert chat.is_conversation_group_visible("today", timeout=UI_ELEMENT_TIMEOUT), (
                    "'Today' date-group heading should be visible in the sidebar"
                )
                assert chat.is_conversation_in_group(conv_target_id, "today", timeout=UI_ELEMENT_TIMEOUT), (
                    f"conv_target {conv_target_id} should render under the "
                    "Today group specifically"
                )

            with allure.step(
                "Step 2 — Hover conv_target; verify the 3-dot menu button "
                "transitions from not-visible to visible"
            ):
                expect(chat.get_conversation_menu_button(conv_target_id)).to_be_hidden(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                chat.hover_conversation_item(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_conversation_menu_button(conv_target_id)).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 3 — Click the 3-dot button; verify the context menu "
                "shows exactly the live item set for this project "
                "(CLARIFICATION-2: 5 items, not the case's/AFS's original "
                "7 — Make public/Share are hidden for a Private-project "
                "conversation)"
            ):
                chat.open_conversation_context_menu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                for key in EXPECTED_MENU_ITEM_KEYS:
                    expect(chat.get_conversation_menu_item(key)).to_be_visible(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                item_count = chat.get_open_conversation_menu_item_count()
                assert item_count == len(EXPECTED_MENU_ITEM_KEYS), (
                    f"Expected exactly {len(EXPECTED_MENU_ITEM_KEYS)} context-menu "
                    f"items ({EXPECTED_MENU_ITEM_KEYS}), found {item_count}"
                )

            with allure.step("Step 4 — Click Delete; verify the confirmation dialog appears"):
                chat.click_conversation_menu_item("delete", timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.delete_confirm_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                # Fresh, correct handle (ELITEA-2114) — does NOT depend on
                # the broken #alert-dialog-title wiring (BUG #694,
                # isolated/out of scope here). Text checked (not just
                # visibility) to match the AFS's Concrete Handles table
                # (live-verified "Delete confirmation") — same pattern as
                # the step-5 body-text assertion below.
                expect(chat.delete_confirm_title).to_have_text(
                    "Delete confirmation", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 5 — Verify the dialog body text"):
                expected_message = f"Are you sure to delete the {target_name} chat? It can't be restored."
                expect(chat.delete_confirm_message).to_have_text(
                    expected_message, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 6 — Verify both dialog buttons are present"):
                expect(chat.delete_confirm_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.delete_confirm_cancel_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 7 — Click Cancel; verify the dialog closes and "
                "conv_target remains present, active, and open"
            ):
                chat.delete_confirm_cancel_button.click()
                expect(chat.delete_confirm_dialog).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_conversation_in_group(conv_target_id, "today", timeout=UI_ELEMENT_TIMEOUT), (
                    "conv_target should still be present in the sidebar after Cancel"
                )
                assert f"/chat/{conv_target_id}" in page.url, (
                    f"URL should still show conv_target {conv_target_id} after "
                    f"Cancel, got: {page.url}"
                )

            with allure.step(
                "Step 8 — Hover conv_target again, reopen the menu, click "
                "Delete again; verify the dialog reopens cleanly (no stale "
                "residue from the prior Cancel)"
            ):
                chat.open_conversation_context_menu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_conversation_menu_item("delete", timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.delete_confirm_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.delete_confirm_dialog.count() == 1, (
                    "Exactly one delete-confirmation dialog should be mounted — "
                    "a stale/duplicate portal instance would indicate residue "
                    "from the prior Cancel"
                )

            with allure.step(
                "Step 9 — Click the Delete (confirm) button; verify the "
                "dialog closes and the underlying DELETE request resolves 204"
            ):
                delete_response = chat.confirm_delete_conversation(
                    conv_target_id, timeout=NAVIGATION_TIMEOUT,
                )
                assert delete_response.status == 204, (
                    f"DELETE conversation request should resolve 204, got "
                    f"{delete_response.status} for {delete_response.url}"
                )
                expect(chat.delete_confirm_dialog).to_be_hidden(timeout=NAVIGATION_TIMEOUT)

            with allure.step("Step 10 — Verify conv_target is gone from the sidebar"):
                assert not chat.is_conversation_in_group(
                    conv_target_id, "today", timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_target {conv_target_id} should no longer be in the Today group"

            with allure.step(
                "Step 11 — Verify no unexpected console errors and the next "
                "conversation is auto-selected"
            ):
                chat.wait_for_conversation_url_change(conv_target_id, timeout=NAVIGATION_TIMEOUT)
                match = re.search(r"/chat/(\d+)", page.url)
                assert match, (
                    f"URL should point at a numeric conversation id after "
                    f"delete, got: {page.url}"
                )
                next_id = match.group(1)
                assert next_id != str(conv_target_id), (
                    "The app should have navigated to a DIFFERENT conversation, "
                    f"not conv_target itself: {page.url}"
                )

                # Cross-check via the API that the selected id is a real,
                # still-existing conversation (not a stale/dangling id).
                next_conv = conversation_api.get_conversation(int(next_id))
                assert next_conv.get("id") == int(next_id), (
                    f"Auto-selected conversation {next_id} should resolve via the API"
                )

                # The AFS's own Automation Hints flag that the "most recent
                # other conversation" pick isn't guaranteed to be
                # conv_sibling if the project accumulates stray
                # conversations — so this asserts generically ("some valid
                # remaining conversation is now active"), not a hardcoded id.
                assert chat.is_conversation_active(next_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"The auto-selected conversation {next_id} should carry "
                    'data-active="true" in the sidebar'
                )

                assert not console_messages, (
                    "Unexpected console errors during the delete flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

            with allure.step(
                "Step 12 — Verify the main chat panel no longer shows "
                "conv_target content"
            ):
                # conv_target and conv_sibling are both API-created with
                # zero messages (AFS § Automation Hints — creating test
                # data via a real chat-send is unnecessarily slow/costly),
                # so there is no conv_target-distinguishing message text to
                # check for absence. The assertable structural fact is that
                # the panel now reflects an empty, freshly-loaded
                # conversation (the newly-active one) rather than any
                # lingering conv_target state.
                assert chat.get_message_count() == 0, (
                    "Main chat panel should show an empty message list for "
                    "the newly-active (also empty) conversation, not any "
                    "lingering conv_target content"
                )

        finally:
            # conv_target is already removed by the test's own delete
            # action; conv_sibling needs explicit cleanup. Both wrapped in
            # try/except per .claude/rules/ui-tests.md § Test Data Lifecycle
            # — cleanup must not mask the real test result.
            if conv_sibling_id:
                try:
                    conversation_api.delete_conversation(conv_sibling_id)
                except Exception as exc:
                    logger.warning("Cleanup failed for conv_sibling %s: %s", conv_sibling_id, exc)
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                except Exception as exc:
                    logger.debug(
                        "conv_target %s cleanup no-op (already deleted by the "
                        "test itself): %s", conv_target_id, exc,
                    )
