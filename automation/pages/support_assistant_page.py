"""Support Assistant page object for Elitea chatbot widget.

Provides locators and methods for interacting with the Support Assistant
floating widget that provides platform-wide support to users.

The Support Assistant is a reusable chatbot plugin that:
- Appears as a floating launcher button on all pages
- Opens as a widget/panel with messaging capabilities
- Supports conversation history and session restore
- Can expand to full view mode
"""

import logging
import time
from playwright.sync_api import Page
from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.support_assistant")


class SupportAssistantPage(BasePage):
    """Page object for Support Assistant floating widget.

    The Support Assistant is a global chatbot widget accessible from any page.
    It provides support functionality separate from the main Chat interface.

    Key UI elements:
    - Launcher button (floating, bottom-right)
    - Widget panel (compact mode)
    - Full view mode (expanded)
    - Message input and history
    - Session management (new chat, history)
    """

    # ------------------------------------------------------------------
    # Launcher button (always visible when assistant is enabled)
    # ------------------------------------------------------------------

    launcher_button = LocatorDescriptor(
        testid="support-assistant-launcher",
        fallback=lambda page: page.locator('button.elitea-assistant-button, button[aria-label="Support Assistant"]'),
        description="Support Assistant floating launcher button"
    )

    # ------------------------------------------------------------------
    # Widget header controls
    # ------------------------------------------------------------------

    close_button = LocatorDescriptor(
        testid="support-assistant-close",
        fallback=lambda page: page.locator('button[aria-label="Close chat"], button:has-text("Close chat")').first,
        description="Close the Support Assistant widget"
    )

    new_chat_button = LocatorDescriptor(
        testid="support-assistant-new-chat",
        fallback=lambda page: page.locator('button[aria-label="New chat"], button:has-text("New chat")').first,
        description="Start a new support session"
    )

    history_button = LocatorDescriptor(
        testid="support-assistant-history",
        fallback=lambda page: page.locator('button[aria-label="Chat history"], button:has-text("Chat history")').first,
        description="Open chat history panel"
    )

    expand_button = LocatorDescriptor(
        testid="support-assistant-expand",
        fallback=lambda page: page.locator('button[aria-label="Expand chat"], button:has-text("Expand chat")').first,
        description="Expand widget to full view mode"
    )

    collapse_button = LocatorDescriptor(
        testid="support-assistant-collapse",
        fallback=lambda page: page.locator('button[aria-label="Collapse chat"], button[aria-label="Minimize chat"], button[aria-label="Shrink chat"]').first,
        description="Collapse from full view to widget mode"
    )

    widget_title = LocatorDescriptor(
        testid="support-assistant-title",
        fallback=lambda page: page.locator('h2:has-text("ELITEA Support"), h2:has-text("Support")').first,
        description="Widget header title"
    )

    # ------------------------------------------------------------------
    # Message input area
    # ------------------------------------------------------------------

    message_input = LocatorDescriptor(
        testid="support-assistant-input",
        fallback=lambda page: page.locator('textbox[placeholder*="Type a message"], input[placeholder*="Type a message"]').first,
        description="Message input textbox"
    )

    send_button = LocatorDescriptor(
        testid="support-assistant-send",
        fallback=lambda page: page.locator('button[aria-label="Send message"], button:has-text("Send message")').first,
        description="Send message button"
    )

    attach_button = LocatorDescriptor(
        testid="support-assistant-attach",
        fallback=lambda page: page.locator('button[aria-label="Attach file"], button:has-text("Attach file")').first,
        description="Attach file button"
    )

    # ------------------------------------------------------------------
    # Widget container
    # ------------------------------------------------------------------

    widget_container = LocatorDescriptor(
        testid="support-assistant-widget",
        fallback=lambda page: page.locator('.elitea-assistant-widget, [class*="support-assistant"], [class*="chatbot-widget"]').first,
        description="Support Assistant widget container"
    )

    # ------------------------------------------------------------------
    # Messages area
    # ------------------------------------------------------------------

    messages_container = LocatorDescriptor(
        testid="support-assistant-messages",
        fallback=lambda page: page.locator('.elitea-assistant-widget [class*="messages"], .elitea-assistant-widget > div > div').nth(1),
        description="Messages container area"
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def is_launcher_visible(self) -> bool:
        """Check if the Support Assistant launcher button is visible.

        Returns:
            True if launcher is visible on the page
        """
        try:
            return self.launcher_button.is_visible()
        except Exception:
            return False

    def is_widget_open(self) -> bool:
        """Check if the Support Assistant widget is currently open.

        Returns:
            True if widget is visible/open
        """
        try:
            return self.widget_title.is_visible()
        except Exception:
            return False

    @action("Open Support Assistant")
    def open_widget(self, timeout: int = 5000):
        """Click the launcher to open the Support Assistant widget.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Opening Support Assistant widget")

        # Use JavaScript click since the button may be a custom element
        self.page.evaluate("""() => {
            const btn = document.querySelector('button.elitea-assistant-button, button[aria-label="Support Assistant"]');
            if (btn) btn.click();
        }""")

        # Wait for widget to appear
        self.widget_title.wait_for(state="visible", timeout=timeout)
        logger.info("Support Assistant widget opened")

    @action("Close Support Assistant")
    def close_widget(self, timeout: int = 5000):
        """Close the Support Assistant widget.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Closing Support Assistant widget")
        self.close_button.click()

        # Wait for widget to close (title disappears)
        self.widget_title.wait_for(state="hidden", timeout=timeout)
        logger.info("Support Assistant widget closed")

    @action("Send message")
    def send_message(self, text: str, timeout: int = 5000):
        """Send a message in the Support Assistant.

        Args:
            text: Message text to send
            timeout: Maximum wait time for send button to enable
        """
        logger.info(f"Sending message: {text[:50]}...")

        # Find and fill the message input
        input_locator = self.page.locator('textbox[placeholder*="Type a message"]').first
        if input_locator.count() == 0:
            input_locator = self.page.get_by_placeholder("Type a message...")

        input_locator.fill(text)

        # Wait for send button to be enabled
        send_btn = self.page.locator('button[aria-label="Send message"]').first
        self.page.wait_for_function(
            """() => {
                const btn = document.querySelector('button[aria-label="Send message"]');
                return btn && !btn.disabled;
            }""",
            timeout=timeout
        )

        send_btn.click()
        logger.info("Message sent")

    def wait_for_response(self, initial_count: int = 0, timeout: int = 30000):
        """Wait for the assistant to respond to a message.

        Waits for a new assistant message to appear in the conversation.
        The assistant message contains a "Copy to clipboard" button.

        Args:
            initial_count: Number of "Copy to clipboard" buttons before sending
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Waiting for assistant response (initial_count=%d)...", initial_count)

        # Wait for a new assistant message (identified by Copy to clipboard button)
        # Assistant messages have this button, user messages don't
        # Widget container class is 'elitea-assistant-container'
        self.page.wait_for_function(
            f"""(expectedCount) => {{
                const widget = document.querySelector('.elitea-assistant-container, [class*="elitea-assistant"]');
                if (!widget) return false;
                const copyButtons = widget.querySelectorAll('button[aria-label="Copy to clipboard"]');
                return copyButtons.length > expectedCount;
            }}""",
            arg=initial_count,
            timeout=timeout
        )
        # Additional wait for content to stabilize
        self.page.wait_for_timeout(1000)
        logger.info("Assistant response complete")

    def get_message_count(self) -> int:
        """Get the count of message blocks in the conversation.

        Returns:
            Number of message blocks (user + assistant)
        """
        # Count messages by looking for assistant messages (with Copy to clipboard button)
        # Widget container class is 'elitea-assistant-container'
        widget = self.page.locator('.elitea-assistant-container, [class*="elitea-assistant"]').first
        if widget.count() == 0:
            return 0

        # Count Copy to clipboard buttons (assistant messages)
        count = widget.locator('button[aria-label="Copy to clipboard"]').count()
        logger.info(f"Assistant message count: {count}")
        return count

    def get_assistant_message_count(self) -> int:
        """Get the count of assistant response messages.

        Assistant messages have a "Copy to clipboard" button.

        Returns:
            Number of assistant messages
        """
        widget = self.page.locator('.elitea-assistant-container, [class*="elitea-assistant"]').first
        if widget.count() == 0:
            return 0

        count = widget.locator('button[aria-label="Copy to clipboard"]').count()
        logger.info(f"Assistant message count: {count}")
        return count

    def get_last_message_text(self) -> str:
        """Get the text content of the last message.

        Returns:
            Text of the last message body
        """
        # Find paragraphs in the last message block
        paragraphs = self.page.locator('.elitea-assistant-widget p')
        if paragraphs.count() > 0:
            text = paragraphs.last.text_content() or ""
            logger.info(f"Last message: {text[:50]}...")
            return text
        return ""

    @action("Start new chat")
    def start_new_chat(self, timeout: int = 5000):
        """Click New Chat to start a fresh support session.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Starting new chat session")
        self.new_chat_button.click()
        self.page.wait_for_timeout(1000)  # Wait for session to initialize
        self.wait_for_network(timeout=timeout)
        logger.info("New chat session started")

    @action("Open chat history")
    def open_history(self, timeout: int = 5000):
        """Open the chat history panel.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Opening chat history")
        self.history_button.click()
        self.page.wait_for_timeout(500)  # Wait for panel transition
        logger.info("History panel opened")

    def get_history_session_count(self) -> int:
        """Get the count of sessions in the history panel.

        Must be called after open_history().

        Returns:
            Number of history sessions
        """
        # History sessions are typically list items or buttons
        sessions = self.page.locator('[class*="history"] button, [class*="session-list"] > div')
        count = sessions.count()
        logger.info(f"History session count: {count}")
        return count

    @action("Select history session")
    def select_history_session(self, index: int = 0, timeout: int = 5000):
        """Select a session from the history panel.

        Args:
            index: Index of session to select (0 = most recent)
            timeout: Maximum wait time in milliseconds
        """
        logger.info(f"Selecting history session at index {index}")
        sessions = self.page.locator('[class*="history"] button, [class*="session-list"] > div')
        sessions.nth(index).click()
        self.wait_for_network(timeout=timeout)
        logger.info("History session loaded")

    @action("Expand to full view")
    def expand_to_fullview(self, timeout: int = 5000):
        """Expand the widget to full view mode.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Expanding to full view mode")
        self.expand_button.click()
        self.page.wait_for_timeout(500)  # Wait for animation
        logger.info("Widget expanded to full view")

    @action("Collapse to widget")
    def collapse_to_widget(self, timeout: int = 5000):
        """Collapse from full view back to widget mode.

        Note: The expand/collapse button is a toggle - the aria-label
        stays "Expand chat" in both states. We use the same button to toggle.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Collapsing to widget mode")
        # The expand button is a toggle - click it again to collapse
        self.expand_button.click()
        self.page.wait_for_timeout(500)  # Wait for animation
        logger.info("Widget collapsed")

    def is_send_button_enabled(self) -> bool:
        """Check if the send button is enabled.

        Returns:
            True if send button is enabled (not disabled)
        """
        send_btn = self.page.locator('button[aria-label="Send message"]').first
        return send_btn.is_enabled()

    def is_input_empty(self) -> bool:
        """Check if the message input is empty.

        Returns:
            True if input is empty
        """
        input_locator = self.page.locator('textbox[placeholder*="Type a message"]').first
        if input_locator.count() == 0:
            input_locator = self.page.get_by_placeholder("Type a message...")
        value = input_locator.input_value()
        return len(value.strip()) == 0

    @action("Attach file")
    def attach_file(self, file_path: str, timeout: int = 10000):
        """Attach a file to the message.

        Args:
            file_path: Path to the file to attach
            timeout: Maximum wait time in milliseconds
        """
        logger.info(f"Attaching file: {file_path}")
        with self.page.expect_file_chooser(timeout=timeout) as fc_info:
            self.attach_button.click()
        file_chooser = fc_info.value
        file_chooser.set_files(file_path)
        self.wait_for_network(timeout=timeout)
        logger.info("File attached")

    def wait_for_widget_ready(self, timeout: int = 10000):
        """Wait for the Support Assistant widget to be fully loaded.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Waiting for widget to be ready...")
        self.widget_title.wait_for(state="visible", timeout=timeout)
        # Wait for input to be ready
        input_locator = self.page.locator('textbox[placeholder*="Type a message"]').first
        if input_locator.count() == 0:
            input_locator = self.page.get_by_placeholder("Type a message...")
        input_locator.wait_for(state="visible", timeout=timeout)
        logger.info("Widget ready")
