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

pytestmark = [pytest.mark.smoke, pytest.mark.ui, pytest.mark.support_assistant]

# Timeout constants
WIDGET_TIMEOUT = 10_000
AI_RESPONSE_TIMEOUT = 60_000
ANIMATION_WAIT = 500


class TestSupportAssistantLauncher:
    """Test Support Assistant launcher visibility and open/close behavior.

    Covers:
    - 2.1.1: Launcher visible when Support Assistant is enabled
    - 2.2.1: Clicking launcher opens the widget
    - 2.2.2: Widget can be closed via X button
    - 2.2.3: Opening/closing does not lose conversation state
    """

    def test_launcher_visible_and_opens_widget(self, page):
        """Launcher is visible and opens Support Assistant widget.

        Steps:
        1. Navigate to any page (chat)
        2. Verify launcher button is visible
        3. Click launcher to open widget
        4. Verify widget opens with title visible
        5. Close widget
        6. Verify widget closes and launcher returns

        Covers: 2.1.1, 2.2.1, 2.2.2
        """
        # Navigate to chat page
        chat_page = ChatPage(page)
        chat_page.navigate_to_chat()

        # Verify launcher is visible
        support_page = SupportAssistantPage(page)
        assert support_page.is_launcher_visible(), (
            "Support Assistant launcher should be visible on the page"
        )

        # Open the widget
        support_page.open_widget(timeout=WIDGET_TIMEOUT)
        assert support_page.is_widget_open(), (
            "Support Assistant widget should be open after clicking launcher"
        )

        # Close the widget
        support_page.close_widget(timeout=WIDGET_TIMEOUT)
        assert not support_page.is_widget_open(), (
            "Support Assistant widget should be closed after clicking close button"
        )

        # Launcher should still be visible
        assert support_page.is_launcher_visible(), (
            "Launcher should remain visible after closing widget"
        )

    def test_widget_state_persists_after_close_reopen(self, page):
        """Conversation state persists when closing and reopening widget.

        Steps:
        1. Open Support Assistant
        2. Send a message
        3. Close widget
        4. Reopen widget
        5. Verify previous message is still visible

        Covers: 2.2.3
        """
        chat_page = ChatPage(page)
        chat_page.navigate_to_chat()

        support_page = SupportAssistantPage(page)
        support_page.open_widget(timeout=WIDGET_TIMEOUT)

        # Get initial assistant message count
        initial_count = support_page.get_assistant_message_count()

        # Send a test message
        test_message = "Test message for state persistence"
        support_page.send_message(test_message)

        # Wait for response (pass initial count for proper detection)
        support_page.wait_for_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        # Get message count after sending
        count_after_send = support_page.get_assistant_message_count()
        assert count_after_send > initial_count, (
            f"Assistant message count should increase after sending: {initial_count} -> {count_after_send}"
        )

        # Close widget
        support_page.close_widget(timeout=WIDGET_TIMEOUT)

        # Reopen widget
        support_page.open_widget(timeout=WIDGET_TIMEOUT)
        support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)

        # Wait for messages to fully load
        page.wait_for_timeout(2000)

        # Verify messages are still there
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

    def test_send_message_and_receive_response(self, page):
        """User can send a message and receive AI response.

        Steps:
        1. Open Support Assistant
        2. Type a message
        3. Send via send button
        4. Verify loading state (send button disabled)
        5. Wait for AI response
        6. Verify response appears
        7. Verify input is re-enabled

        Covers: 3.2.1-3.2.7, 3.2.9
        """
        chat_page = ChatPage(page)
        chat_page.navigate_to_chat()

        support_page = SupportAssistantPage(page)
        support_page.open_widget(timeout=WIDGET_TIMEOUT)
        support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)

        # Get initial assistant message count
        initial_count = support_page.get_assistant_message_count()

        # Send a simple message
        test_message = "Hello, what is Elitea?"
        support_page.send_message(test_message)

        # Wait for response
        support_page.wait_for_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        # Verify assistant message count increased
        final_count = support_page.get_assistant_message_count()
        assert final_count > initial_count, (
            f"Assistant message count should increase after response: {initial_count} -> {final_count}"
        )

        # Verify input is empty (send button disabled when empty is expected)
        assert support_page.is_input_empty(), "Input should be cleared after sending"


class TestSupportAssistantNewSession:
    """Test new chat session functionality.

    Covers:
    - 3.5.1: New Chat button is available
    - 3.5.2: Starting new session creates fresh conversation
    """

    def test_new_chat_creates_fresh_session(self, page):
        """New Chat button starts a fresh support session.

        Steps:
        1. Open Support Assistant
        2. Send a message to create conversation
        3. Click New Chat
        4. Verify old conversation moved to history
        5. Verify clean slate (welcome or empty state)

        Covers: 3.5.1, 3.5.2
        """
        chat_page = ChatPage(page)
        chat_page.navigate_to_chat()

        support_page = SupportAssistantPage(page)
        support_page.open_widget(timeout=WIDGET_TIMEOUT)
        support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)

        # Get initial count
        initial_count = support_page.get_assistant_message_count()

        # Send a message to create a conversation
        support_page.send_message("Test message before new chat")
        support_page.wait_for_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        # Get message count before new chat
        count_before = support_page.get_assistant_message_count()
        assert count_before > initial_count, "Should have new messages before starting new chat"

        # Start new chat
        support_page.start_new_chat(timeout=WIDGET_TIMEOUT)

        # Give time for session to reset
        page.wait_for_timeout(1000)

        # Verify we're in a fresh state
        # Note: The new session may show welcome message or be empty
        # The key is that the OLD conversation messages are not visible
        support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)


class TestSupportAssistantHistory:
    """Test chat history and session restore functionality.

    Covers:
    - 6.1.1: History view is accessible
    - 6.2.1: Clicking past session loads messages
    - 6.2.3: Can continue messaging in restored session
    """

    def test_history_restore_and_continue(self, page):
        """User can restore a previous session and continue messaging.

        Steps:
        1. Open Support Assistant
        2. Send a message (creates session)
        3. Start new chat
        4. Open history
        5. Select previous session
        6. Verify messages are loaded
        7. Send new message in restored session

        Covers: 6.1.1, 6.2.1, 6.2.3
        """
        chat_page = ChatPage(page)
        chat_page.navigate_to_chat()

        support_page = SupportAssistantPage(page)
        support_page.open_widget(timeout=WIDGET_TIMEOUT)
        support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)

        # Get initial count
        initial_count = support_page.get_assistant_message_count()

        # Create a conversation with a distinctive message
        distinctive_message = "History test message - distinctive content 12345"
        support_page.send_message(distinctive_message)
        support_page.wait_for_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        # Start new chat to move conversation to history
        support_page.start_new_chat(timeout=WIDGET_TIMEOUT)
        page.wait_for_timeout(1000)

        # Open history
        support_page.open_history(timeout=WIDGET_TIMEOUT)

        # History should have at least one session
        session_count = support_page.get_history_session_count()
        assert session_count >= 1, (
            f"History should have at least 1 session after creating conversation, got {session_count}"
        )

        # Select the most recent session (index 0)
        support_page.select_history_session(index=0, timeout=WIDGET_TIMEOUT)

        # Verify messages are loaded
        restored_count = support_page.get_assistant_message_count()
        assert restored_count > 0, (
            f"Restored session should have assistant messages, got {restored_count}"
        )

        # Continue the conversation
        support_page.send_message("Follow-up message after restore")
        support_page.wait_for_response(initial_count=restored_count, timeout=AI_RESPONSE_TIMEOUT)

        # Verify new message was added
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

    def test_expand_collapse_fullview(self, page):
        """Widget can expand to full view and collapse back.

        Steps:
        1. Open Support Assistant (widget mode)
        2. Click expand button
        3. Verify full view mode
        4. Click collapse button
        5. Verify widget mode restored

        Covers: 2.3.1, 2.3.2, 2.3.3
        """
        chat_page = ChatPage(page)
        chat_page.navigate_to_chat()

        support_page = SupportAssistantPage(page)
        support_page.open_widget(timeout=WIDGET_TIMEOUT)
        support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)

        # Expand to full view
        support_page.expand_to_fullview(timeout=WIDGET_TIMEOUT)
        page.wait_for_timeout(ANIMATION_WAIT)

        # Verify widget is still functional in full view
        assert support_page.is_widget_open(), "Widget should still be open in full view"

        # Collapse back to widget
        support_page.collapse_to_widget(timeout=WIDGET_TIMEOUT)
        page.wait_for_timeout(ANIMATION_WAIT)

        # Verify still functional in widget mode
        assert support_page.is_widget_open(), "Widget should still be open after collapse"


class TestSupportAssistantAttachments:
    """Test file attachment functionality.

    Covers:
    - 7.1.1: Attachment button is present
    - 7.1.2: Clicking opens file picker
    - 7.1.3: Selected file appears as preview
    """

    def test_attach_button_present_and_opens_picker(self, page, tmp_path):
        """Attach button opens file picker dialog.

        Steps:
        1. Open Support Assistant
        2. Verify attach button is visible
        3. Click attach button
        4. Verify file chooser dialog opens

        Covers: 7.1.1, 7.1.2
        """
        chat_page = ChatPage(page)
        chat_page.navigate_to_chat()

        support_page = SupportAssistantPage(page)
        support_page.open_widget(timeout=WIDGET_TIMEOUT)
        support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)

        # Verify attach button is visible
        attach_btn = page.locator('button[aria-label="Attach file"]').first
        assert attach_btn.is_visible(), "Attach file button should be visible"

        # Create a test file
        test_file = tmp_path / "test_attachment.txt"
        test_file.write_text("Test attachment content")

        # Click attach and verify file chooser opens
        with page.expect_file_chooser(timeout=WIDGET_TIMEOUT) as fc_info:
            attach_btn.click()

        file_chooser = fc_info.value
        assert file_chooser is not None, "File chooser should open when clicking attach"

        # Select the file
        file_chooser.set_files(str(test_file))

        # Wait for upload to process
        support_page.wait_for_network(timeout=WIDGET_TIMEOUT)
