"""UI Test for ELITEA-2117 — Chat: Deletion of the Last Remaining Conversation
in a Project.

Verifies that deleting the sole remaining conversation in a project empties
the sidebar and transitions the main panel to the exact same welcome/greeting
component the blank ``+Chat`` state uses, with the message input and
``+Chat`` button both remaining available.

Spec: test-specs/chat-interface/l2_deletion-of-last-remaining-conversation_ELITEA-2117.md

Uses project 400 ("UI Testing") — REQUIRED for this case specifically: the
empty-panel/welcome-state observable can only be honestly reached by
genuinely emptying a project's conversation list, and 400 is a dedicated
sandbox confirmed live to normally hold zero conversations (unlike the
shared Team/Private projects other analyses reuse). See AFS § Automation
Hints for the full isolation rationale.

**Isolated known defect, filed EliteaAI/elitea-testing-public#1523**: the
browser URL does not clear/update after deleting the last remaining
conversation within the same SPA session (only a reload fixes it) — every
OTHER observable in this case (empty sidebar, welcome state, active input,
no error banners, +Chat available) is unaffected and asserted as a hard
check. The URL check is specced as a soft failure per the no-masking
decision tree (`.agents/testing.md` § Merge gate) — this test is expected to
run RED (sanctioned) until #1523 ships a fix.
"""

import logging

import allure
import pytest
from api.client import ConversationAPI
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

SANDBOX_PROJECT_ID = "400"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as ``test_conversation_deletion_flow.py``'s identically named
    filter — unrelated to the delete flow under test here.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


def _is_known_stale_url_400(msg) -> bool:
    """Filter the two delayed 400s that are a DIRECT, deterministic
    consequence of Known defect #1523 (the URL not clearing after the last
    conversation is deleted) — NOT a second, independent defect.

    Live-confirmed (AFS § Known Defects Found): ~1.5s after the delete, the
    stale URL's leftover conversation id causes two background refetch
    attempts to fire against the now-nonexistent conversation:
    ``GET .../conversation/prompt_lib/{project}/{id}?...`` and
    ``GET .../select_conversation/prompt_lib/{project}/{id}``, both 400.
    Excluded here so step 9's "no unexpected console errors" check isn't a
    second, redundant symptom of the SAME already-linked defect — a genuinely
    NEW/unrelated error still fails this check.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    haystack = text + location_url
    return "400" in text and (
        f"/conversation/prompt_lib/{SANDBOX_PROJECT_ID}/" in haystack
        or f"/select_conversation/prompt_lib/{SANDBOX_PROJECT_ID}/" in haystack
    )


class TestLastRemainingConversationDeletion:
    """ELITEA-2117: Chat – Deletion of the Last Remaining Conversation in a Project (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2117_chat-deletion-of-the-last-remaining-conversation-in-a-project.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1523",
        "Known defect — URL doesn't clear after last-conversation delete",
    )
    @pytest.mark.p2
    def test_delete_last_remaining_conversation_shows_welcome_state(self, page, _browser_cookies):
        """Deleting the sole conversation empties the panel and shows the
        new-chat welcome state; +Chat stays available.

        Steps (AFS
        test-specs/chat-interface/l2_deletion-of-last-remaining-conversation_ELITEA-2117.md):
        1. Verify exactly one conversation exists; no others.
        2. Click it to open — active, input ready.
        3. Hover, 3-dot, Delete — confirmation dialog appears.
        4. Verify modal body text.
        5. Click Delete — resolves 204, no error.
        6. Left panel empty, no date groups.
        7. Main panel shows the welcome/greeting state.
        8. Message input visible and active.
        9. No error banners/toasts; no new console errors.
        10. URL no longer references the deleted conversation — SOFT
            (Known defect #1523).
        11. + Chat button remains available.
        """
        sandbox_api = ConversationAPI(browser_cookies=_browser_cookies, project_id=SANDBOX_PROJECT_ID)
        chat = ChatPage(page)
        conv_id = None
        soft_failures: list[str] = []

        console_messages = []

        def _on_console(msg):
            if (
                msg.type == "error"
                and not _is_known_secrets_403(msg)
                and not _is_known_stale_url_400(msg)
            ):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — switch to the sandbox project (400, confirmed "
                "empty); seed the SOLE conversation via the API"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.switch_project(SANDBOX_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)
                assert chat.get_conversation_link_count() == 0, (
                    "Sandbox project 400 should be empty before seeding — "
                    "this test requires exclusive use of it"
                )

                conv = sandbox_api.create_conversation("autotest_2117_last_conv")
                conv_id = conv["id"]

                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step(
                "Step 1 — Verify exactly one conversation exists in the left "
                "panel; no others"
            ):
                # Wait for the sidebar's own render of conv_id FIRST — a bare
                # count() read races the SPA's post-navigation list render
                # (confirmed live: navigate_to_chat() can return before the
                # sidebar list has re-populated).
                expect(chat.get_conversation_item(conv_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_conversation_link_count() == 1, (
                    f"Expected exactly 1 conversation, got {chat.get_conversation_link_count()}"
                )

            with allure.step(
                "Step 2 — Click the conversation to open it; verify it's "
                "active and the input is ready"
            ):
                chat.click_conversation_item(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_conversation_url(str(conv_id), timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_conversation_active(conv_id, active=True, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Hover, click 3-dot, click Delete; verify the "
                "confirmation dialog appears"
            ):
                chat.open_conversation_context_menu(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_conversation_menu_item("delete", timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.delete_confirm_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 4 — Verify the modal body text"):
                expected_message = f"Are you sure to delete the {conv['name']} chat? It can't be restored."
                expect(chat.delete_confirm_message).to_have_text(
                    expected_message, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 5 — Click the Delete (confirm) button; verify the "
                "dialog closes without error and the DELETE request resolves 204"
            ):
                delete_response = chat.confirm_delete_conversation(conv_id, timeout=NAVIGATION_TIMEOUT)
                assert delete_response.status == 204, (
                    f"DELETE conversation request should resolve 204, got {delete_response.status}"
                )
                expect(chat.delete_confirm_dialog).to_be_hidden(timeout=NAVIGATION_TIMEOUT)

            with allure.step(
                "Step 7 — Verify the main panel transitions to the new-chat "
                "welcome/greeting state (waited on FIRST — this is the "
                "deterministic condition that proves the delete's client-side "
                "state update has landed, gating every check below)"
            ):
                expect(chat.new_conversation_greeting).to_be_visible(timeout=NAVIGATION_TIMEOUT)

            with allure.step(
                "Step 6 — Verify the left panel conversation list is empty — "
                "no conversations under any date group"
            ):
                assert chat.get_conversation_link_count() == 0, (
                    "Left panel should be empty after deleting the last conversation"
                )
                for group in ("today", "this_week", "older"):
                    assert not chat.is_conversation_group_visible(group, timeout=1000), (
                        f"No date-group heading ({group}) should be visible when the "
                        "project has zero conversations"
                    )

            with allure.step("Step 8 — Verify the message input is visible and active"):
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.message_input.is_editable(), (
                    "Message input should be editable in the welcome state"
                )

            with allure.step(
                "Step 9 — Verify no error banners/toasts and no new console errors"
            ):
                expect(chat.toast_message).to_have_count(0, timeout=1000)
                assert not console_messages, (
                    f"Unexpected console errors during the delete flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

            with allure.step(
                "Step 10 — Verify the page URL no longer references the "
                "deleted conversation — SOFT, Known defect: #1523"
            ):
                if f"/chat/{conv_id}" in chat.page.url:
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1523: "
                        f"page URL still references the deleted conversation {conv_id} "
                        f"after deleting the last remaining conversation: {chat.page.url}"
                    )

            with allure.step("Step 11 — Verify the + Chat button remains available"):
                expect(chat.create_conversation_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.create_conversation_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

            if soft_failures:
                pytest.fail(
                    "Soft assertion(s) failed (known isolated product "
                    "defect, not test/infrastructure — every other "
                    "observable in this case passed cleanly):\n"
                    + "\n".join(soft_failures)
                )

        finally:
            try:
                if conv_id:
                    sandbox_api.delete_conversation(conv_id)
            except Exception as exc:
                logger.debug(
                    "conv_id %s cleanup no-op (already deleted by the test "
                    "itself): %s", conv_id, exc,
                )
            sandbox_api.close()
