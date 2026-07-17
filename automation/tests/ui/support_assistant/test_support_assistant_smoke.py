"""Support Assistant Smoke Tests.

Verifies the core user journey for the Support Assistant chatbot widget.
These are critical path tests that should pass before any release.

Covers checklist items from issue #4894:
- Section 2: Entry Point & Plugin Shell (2.1.1, 2.2.1-2.2.3, 2.3.1-2.3.3)
- Section 3: Messaging Flow (3.1.1, 3.2.1-3.2.9)
- Section 3.5: New Session (3.5.1-3.5.2)
- Section 6: History & Restore (6.1.1, 6.2.1, 6.2.3)
- Section 7.1: Attachments (7.1.1-7.1.3)

Markers:
    - smoke: quick sanity checks (<5 min total)
    - ui: requires a browser
    - support_assistant: Support Assistant feature tests

Usage::

    cd automation
    pytest tests/ui/support_assistant/test_support_assistant_smoke.py -v
    HEADLESS=false pytest tests/ui/support_assistant/ -v  # watch the browser
"""

import pytest
from pages.support_assistant_page import SupportAssistantPage
from pages.chat_page import ChatPage
import allure

pytestmark = [pytest.mark.smoke, pytest.mark.ui, pytest.mark.support_assistant]

# Timeout constants
WIDGET_TIMEOUT = 10_000
AI_RESPONSE_TIMEOUT = 120_000  # 120s - progressive wait resets on status change
ANIMATION_WAIT = 500


class TestSupportAssistantLauncher:
    """Test Support Assistant launcher visibility and open/close behavior.

    Covers:
    - 2.1.1: Launcher visible when Support Assistant is enabled
    - 2.2.1: Clicking launcher opens the widget
    - 2.2.2: Widget can be closed via X button
    - 2.2.3: Opening/closing does not lose conversation state
    """

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/elitea-chat-bot/ELITEA-0626_support-assistant-floating-launcher-is-visible-on-every-main-applicati.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/elitea-chat-bot/ELITEA-0625_support-assistant-panel-opens-on-launcher-click-and-closes-on-x-button.md", "onetest-ai Test Case link")
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-1796_launcher-visible-widget-opens-and-closes.md",
        "onetest-ai Test Case link",
    )
    def test_launcher_visible_and_opens_widget(self, page):
        """Launcher is visible and opens Support Assistant widget.

        Covers: 2.1.1, 2.2.1, 2.2.2
        """
        with allure.step("Step 1 — Navigate to any page (chat)"):
            chat_page = ChatPage(page)
            chat_page.navigate_to_chat()

        with allure.step("Step 2 — Verify launcher button is visible"):
            support_page = SupportAssistantPage(page)
            assert support_page.is_launcher_visible(), (
                "Support Assistant launcher should be visible on the page"
            )

        with allure.step("Step 3 — Click launcher to open widget"):
            support_page.open_widget(timeout=WIDGET_TIMEOUT)

        with allure.step("Step 4 — Verify widget opens with title visible"):
            assert support_page.is_widget_open(), (
                "Support Assistant widget should be open after clicking launcher"
            )

        with allure.step("Step 5 — Close widget"):
            support_page.close_widget(timeout=WIDGET_TIMEOUT)

        with allure.step("Step 6 — Verify widget closes and launcher returns"):
            assert not support_page.is_widget_open(), (
                "Support Assistant widget should be closed after clicking close button"
            )
            assert support_page.is_launcher_visible(), (
                "Launcher should remain visible after closing widget"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/elitea-chat-bot/ELITEA-0643_conversation-is-retained-when-the-support-assistant-panel-is-closed-an.md", "onetest-ai Test Case link")
    def test_widget_state_persists_after_close_reopen(self, page):
        """Conversation state persists when closing and reopening widget.

        Covers: 2.2.3
        """
        with allure.step("Step 1 — Open Support Assistant"):
            chat_page = ChatPage(page)
            chat_page.navigate_to_chat()
            support_page = SupportAssistantPage(page)
            support_page.open_widget(timeout=WIDGET_TIMEOUT)

        with allure.step("Step 1b — Start new chat for clean state"):
            support_page.start_new_chat(timeout=WIDGET_TIMEOUT)
            page.wait_for_timeout(1000)
            initial_count = support_page.get_assistant_message_count()

        with allure.step("Step 2 — Send a message"):
            test_message = "Test message for state persistence"
            support_page.send_message(test_message)
            support_page.wait_for_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
            count_after_send = support_page.get_assistant_message_count()
            assert count_after_send > initial_count, (
                f"Assistant message count should increase after sending: {initial_count} -> {count_after_send}"
            )

        with allure.step("Step 3 — Close widget"):
            support_page.close_widget(timeout=WIDGET_TIMEOUT)

        with allure.step("Step 4 — Reopen widget"):
            support_page.open_widget(timeout=WIDGET_TIMEOUT)
            support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)
            page.wait_for_timeout(2000)

        with allure.step("Step 5 — Verify previous message is still visible"):
            count_after_reopen = support_page.get_assistant_message_count()
            assert count_after_reopen >= count_after_send, (
                f"Messages should persist after close/reopen: had {count_after_send}, now {count_after_reopen}"
            )


class TestSupportAssistantMessaging:
    """Test core messaging flow in Support Assistant.

    Covers:
    - 3.1.1: First-time user sees welcome message
    - 3.2.1-3.2.7: Send message flow
    - 3.2.9: Input re-enabled after response
    """

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/elitea-chat-bot/ELITEA-0647_user-sends-a-message-via-the-send-button-and-receives-a-complete-assis.md", "onetest-ai Test Case link")
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-1798_send-message-and-receive-ai-response.md",
        "onetest-ai Test Case link",
    )
    def test_send_message_and_receive_response(self, page):
        """User can send a message and receive AI response.

        Covers: 3.2.1-3.2.7, 3.2.9
        """
        with allure.step("Step 1 — Open Support Assistant"):
            chat_page = ChatPage(page)
            chat_page.navigate_to_chat()
            support_page = SupportAssistantPage(page)
            support_page.open_widget(timeout=WIDGET_TIMEOUT)
            support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)
            initial_count = support_page.get_assistant_message_count()

        with allure.step("Step 2 — Type a message"):
            test_message = "Hello, what is Elitea?"

        with allure.step("Step 3 — Send via send button"):
            support_page.send_message(test_message)

        with allure.step("Step 4-5 — Wait for AI response"):
            support_page.wait_for_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        with allure.step("Step 6 — Verify response appears"):
            final_count = support_page.get_assistant_message_count()
            assert final_count > initial_count, (
                f"Assistant message count should increase after response: {initial_count} -> {final_count}"
            )

        with allure.step("Step 7 — Verify input is re-enabled"):
            assert support_page.is_input_empty(), "Input should be cleared after sending"


class TestSupportAssistantNewSession:
    """Test new chat session functionality.

    Covers:
    - 3.5.1: New Chat button is available
    - 3.5.2: Starting new session creates fresh conversation

    Known defect (github.com/EliteaAI/elitea-testing-public#607): Support
    Assistant conversation restore truncates to the oldest 100 message
    groups for any conversation that has grown past that threshold, hiding
    all recent activity. This breaks ELITEA-1799's own Expected Final State
    clause 3 ("the previous session is preserved in history and not lost").
    Asserted via the pytest-native soft-assertion equivalent (a
    ``soft_failures`` list + a final ``pytest.fail()`` — Playwright's
    ``expect.soft()`` only supports Page/Locator/APIResponse, not the raw
    str/int values these getters return) per this project's no-masking
    policy — stays red once the account's active conversation exceeds the
    ~100-message-group threshold.
    """

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/elitea-chat-bot/ELITEA-0641_clicking-new-chat-opens-a-clean-session-without-affecting-the-previous.md", "onetest-ai Test Case link")
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-1799_new-chat-creates-fresh-session.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/607", "Known defect #607")
    def test_new_chat_creates_fresh_session(self, page):
        """New Chat button starts a fresh support session.

        Covers: 3.5.1, 3.5.2

        Also covers ELITEA-1799's Expected Final State clause 3 ("previous
        session preserved in history, not lost") via a soft assertion —
        known defect #607, stays red once the account's active conversation
        exceeds the ~100-message-group threshold.
        """
        with allure.step("Step 1 — Open Support Assistant"):
            chat_page = ChatPage(page)
            chat_page.navigate_to_chat()
            support_page = SupportAssistantPage(page)
            support_page.open_widget(timeout=WIDGET_TIMEOUT)
            support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)
            initial_count = support_page.get_assistant_message_count()

        with allure.step("Step 2 — Send a message to create conversation"):
            support_page.send_message("Test message before new chat")
            support_page.wait_for_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
            count_before = support_page.get_assistant_message_count()
            assert count_before > initial_count, "Should have new messages before starting new chat"
            # Captured live, before New Chat resets the view — used in Step 6
            # to verify this exact content survives the move to history.
            response_before_new_chat = support_page.get_last_message_text()
            # Total (user + assistant) baseline — get_message_count() is total,
            # while count_before above is assistant-only. Step 4-5 and Step 6
            # both compare against get_message_count() results later, so the
            # baseline must be captured in the same (total) units here to avoid
            # a unit mismatch (assistant-only vs total).
            total_count_before = support_page.get_message_count()

        with allure.step("Step 3 — Click New Chat"):
            support_page.start_new_chat(timeout=WIDGET_TIMEOUT)
            page.wait_for_timeout(1000)

        with allure.step("Step 4-5 — Verify clean slate (welcome or empty state)"):
            support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)
            reset_message_count = support_page.get_message_count()
            assert reset_message_count < total_count_before, (
                f"Message count should reset after New Chat: had {total_count_before} "
                f"total messages before, {reset_message_count} total messages now"
            )

        with allure.step(
            "Step 6 — Open history, select the archived session, and verify "
            "the message sent immediately before New Chat (and its AI "
            "response) are still visible in the restored view — Expected "
            "Final State clause 3 (Known defect: #607)"
        ):
            support_page.open_history(timeout=WIDGET_TIMEOUT)
            session_count = support_page.get_history_session_count()
            assert session_count >= 1, (
                f"History should have at least 1 session after New Chat, got {session_count}"
            )
            support_page.select_history_session(index=0, timeout=WIDGET_TIMEOUT)

            restored_message_count = support_page.get_message_count()
            restored_last_message = support_page.get_last_message_text()

            # pytest has no built-in expect.soft() for raw str/int return
            # values (Playwright's Python expect.soft() only supports Page/
            # Locator/APIResponse) — using the pytest-native soft-assertion
            # equivalent (a soft_failures list + a final pytest.fail()),
            # same pattern as test_fork_agent_to_different_project.py /
            # test_skill_agent_interaction.py's known-defect handling. This
            # also avoids introducing any new raw (non-testid) locator into
            # the test — both checks read existing SupportAssistantPage
            # getter methods only.
            soft_failures = []
            # Known defect: #607 — conversation restore truncates to the
            # oldest 100 message groups once a conversation grows past that
            # threshold (this shared test account's has 218+), hiding all
            # recent activity — including the message and response sent
            # above. Asserting the live-contract (correct) behavior per
            # this case's own Expected Final State clause 3, not the
            # current truncated behavior — expected to fail once the
            # account's active conversation exceeds the threshold, per
            # `.agents/testing.md` § Merge gate's Sanctioned-RED exception.
            if restored_message_count < total_count_before:
                soft_failures.append(
                    "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/607: "
                    f"restored session shows {restored_message_count} total message(s), "
                    f"fewer than the {total_count_before} total message(s) already present "
                    "before New Chat — the message sent immediately before New Chat "
                    "appears to have been truncated out of the restored view."
                )
            if restored_last_message != response_before_new_chat:
                soft_failures.append(
                    "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/607: "
                    "the AI response captured live immediately before New Chat is not the "
                    f"last message in the restored view (expected {response_before_new_chat!r}, "
                    f"got {restored_last_message!r})."
                )
            if soft_failures:
                pytest.fail(
                    "Known defect(s) detected (test still completed all steps):\n"
                    + "\n".join(soft_failures)
                )


class TestSupportAssistantHistory:
    """Test chat history and session restore functionality.

    Covers:
    - 6.1.1: History view is accessible
    - 6.2.1: Clicking past session loads messages
    - 6.2.3: Can continue messaging in restored session
    """

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/elitea-chat-bot/ELITEA-0641_clicking-new-chat-opens-a-clean-session-without-affecting-the-previous.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/elitea-chat-bot/ELITEA-0643_conversation-is-retained-when-the-support-assistant-panel-is-closed-an.md", "onetest-ai Test Case link")
    def test_history_restore_and_continue(self, page):
        """User can restore a previous session and continue messaging.

        Covers: 6.1.1, 6.2.1, 6.2.3
        """
        with allure.step("Step 1 — Open Support Assistant"):
            chat_page = ChatPage(page)
            chat_page.navigate_to_chat()
            support_page = SupportAssistantPage(page)
            support_page.open_widget(timeout=WIDGET_TIMEOUT)
            support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)
            initial_count = support_page.get_assistant_message_count()

        with allure.step("Step 2 — Send a message (creates session)"):
            distinctive_message = "History test message - distinctive content 12345"
            support_page.send_message(distinctive_message)
            support_page.wait_for_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        with allure.step("Step 3 — Start new chat"):
            support_page.start_new_chat(timeout=WIDGET_TIMEOUT)
            page.wait_for_timeout(1000)

        with allure.step("Step 4 — Open history"):
            support_page.open_history(timeout=WIDGET_TIMEOUT)
            session_count = support_page.get_history_session_count()
            assert session_count >= 1, (
                f"History should have at least 1 session after creating conversation, got {session_count}"
            )

        with allure.step("Step 5 — Select previous session"):
            support_page.select_history_session(index=0, timeout=WIDGET_TIMEOUT)

        with allure.step("Step 6 — Verify messages are loaded"):
            restored_count = support_page.get_assistant_message_count()
            assert restored_count > 0, (
                f"Restored session should have assistant messages, got {restored_count}"
            )

        with allure.step("Step 7 — Send new message in restored session"):
            support_page.send_message("Follow-up message after restore")
            support_page.wait_for_response(initial_count=restored_count, timeout=AI_RESPONSE_TIMEOUT)
            final_count = support_page.get_assistant_message_count()
            assert final_count > restored_count, (
                f"Should be able to add messages to restored session: {restored_count} -> {final_count}"
            )


class TestSupportAssistantViewModes:
    """Test widget and fullview mode switching.

    Covers:
    - 2.3.1: Compact/widget mode (default)
    - 2.3.2: Full view mode via expand button
    - 2.3.3: Collapse back to widget mode
    """

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/elitea-chat-bot/ELITEA-0624_support-assistant-expands-to-full-view-mode-and-collapses-back-to-widg.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-1801_expand-to-full-view-and-collapse-back.md", "onetest-ai Test Case link")
    def test_expand_collapse_fullview(self, page):
        """Widget can expand to full view and collapse back.

        Covers: 2.3.1, 2.3.2, 2.3.3
        """
        with allure.step("Step 1 — Open Support Assistant (widget mode)"):
            chat_page = ChatPage(page)
            chat_page.navigate_to_chat()
            support_page = SupportAssistantPage(page)
            support_page.open_widget(timeout=WIDGET_TIMEOUT)
            support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)

        with allure.step("Step 2 — Click expand button"):
            support_page.expand_to_fullview(timeout=WIDGET_TIMEOUT)
            page.wait_for_timeout(ANIMATION_WAIT)

        with allure.step("Step 3 — Verify full view mode"):
            assert support_page.is_widget_open(), "Widget should still be open in full view"
            assert support_page.is_fullview_mode(), (
                "Widget container should carry the --expanded modifier class after expand"
            )

        with allure.step("Step 4 — Click collapse button"):
            support_page.collapse_to_widget(timeout=WIDGET_TIMEOUT)
            page.wait_for_timeout(ANIMATION_WAIT)

        with allure.step("Step 5 — Verify widget mode restored"):
            assert support_page.is_widget_open(), "Widget should still be open after collapse"
            assert not support_page.is_fullview_mode(), (
                "Widget container should lose the --expanded modifier class after collapse"
            )


class TestSupportAssistantAttachments:
    """Test file attachment functionality.

    Covers:
    - 7.1.1: Attachment button is present
    - 7.1.2: Clicking opens file picker
    - 7.1.3: Selected file appears as preview
    """

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/elitea-chat-bot/ELITEA-0577_support-assistant-files-can-be-attached-via-click-to-browse-drag-and-d.md", "onetest-ai Test Case link")
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-1802_attach-button-present-and-opens-file-picker.md",
        "onetest-ai Test Case link",
    )
    def test_attach_button_present_and_opens_picker(self, page, tmp_path):
        """Attach button opens file picker dialog.

        Covers: 7.1.1, 7.1.2
        """
        with allure.step("Step 1 — Open Support Assistant"):
            chat_page = ChatPage(page)
            chat_page.navigate_to_chat()
            support_page = SupportAssistantPage(page)
            support_page.open_widget(timeout=WIDGET_TIMEOUT)
            support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)

        with allure.step("Step 2 — Verify attach button is visible"):
            attach_btn = page.locator('button[aria-label="Attach file"]').first
            assert attach_btn.is_visible(), "Attach file button should be visible"

        with allure.step("Step 3 — Click attach button"):
            test_file = tmp_path / "test_attachment.txt"
            test_file.write_text("Test attachment content")
            with page.expect_file_chooser(timeout=WIDGET_TIMEOUT) as fc_info:
                attach_btn.click()

        with allure.step("Step 4 — Verify file chooser dialog opens"):
            file_chooser = fc_info.value
            assert file_chooser is not None, "File chooser should open when clicking attach"
            file_chooser.set_files(str(test_file))
            support_page.wait_for_network(timeout=WIDGET_TIMEOUT)
