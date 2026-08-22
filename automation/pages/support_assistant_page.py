"""Support Assistant page object for Elitea chatbot widget.

Provides locators and methods for interacting with the Support Assistant
floating widget that provides platform-wide support to users.

The Support Assistant is a reusable chatbot plugin that:
- Appears as a floating launcher button on all pages
- Opens as a widget/panel with messaging capabilities
- Supports conversation history and session restore
- Can expand to full view mode
"""

import base64
import logging
import mimetypes
import time
from pathlib import Path
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
        fallback=lambda page: page.locator('button.elitea-assistant-button, button[aria-label="Support Assistant"]'),
        description="Support Assistant floating launcher button"
    )

    # ------------------------------------------------------------------
    # Widget header controls
    # ------------------------------------------------------------------

    close_button = LocatorDescriptor(
        fallback=lambda page: page.locator('button[aria-label="Close chat"], button:has-text("Close chat")').first,
        description="Close the Support Assistant widget"
    )

    new_chat_button = LocatorDescriptor(
        fallback=lambda page: page.locator('button[aria-label="New chat"], button:has-text("New chat")').first,
        description="Start a new support session"
    )

    history_button = LocatorDescriptor(
        fallback=lambda page: page.locator('button[aria-label="Chat history"], button:has-text("Chat history")').first,
        description="Open chat history panel"
    )

    expand_button = LocatorDescriptor(
        fallback=lambda page: page.locator('button[aria-label="Expand chat"], button:has-text("Expand chat")').first,
        description="Expand widget to full view mode"
    )

    collapse_button = LocatorDescriptor(
        fallback=lambda page: page.locator('button[aria-label="Collapse chat"], button[aria-label="Minimize chat"], button[aria-label="Shrink chat"]').first,
        description="Collapse from full view to widget mode"
    )

    widget_title = LocatorDescriptor(
        fallback=lambda page: page.locator('.elitea-assistant-header-title').first,
        description="Widget header title"
    )

    # ------------------------------------------------------------------
    # Message input area
    # ------------------------------------------------------------------

    message_input = LocatorDescriptor(
        fallback=lambda page: page.locator('.elitea-assistant-input').first,
        description="Message input textbox"
    )

    send_button = LocatorDescriptor(
        fallback=lambda page: page.locator('button[aria-label="Send message"], button:has-text("Send message")').first,
        description="Send message button"
    )

    attach_button = LocatorDescriptor(
        fallback=lambda page: page.locator('button[aria-label="Attach file"]').first,
        description="Attach file button"
    )

    # ------------------------------------------------------------------
    # Widget container
    # ------------------------------------------------------------------

    widget_container = LocatorDescriptor(
        fallback=lambda page: page.locator('.elitea-assistant-window').first,
        description="Support Assistant widget container"
    )

    # ------------------------------------------------------------------
    # Messages area
    # ------------------------------------------------------------------

    messages_container = LocatorDescriptor(
        fallback=lambda page: page.locator('.elitea-assistant-messages').first,
        description="Messages container area"
    )

    # ------------------------------------------------------------------
    # Testid-only locators (policy-compliant — .agents/testing.md § Locator
    # policy). Added for ELITEA-2418; the ``fallback=`` fields above are
    # pre-policy tech debt (#25/#42) kept for their existing callers.
    #
    # Testid provenance: ``sidebar-support-assistant-button`` lives in
    # EliteaUI (``src/[fsd]/widgets/sidebar-root/ui/SidebarBody.jsx``); the
    # ``support-assistant-*`` ones live in the connected first-party repo
    # ``EliteaAI/elitea_assistant`` (canon #705), aliased into the local dev
    # server by ``VITE_ASSISTANT_LOCAL=1``.
    # ------------------------------------------------------------------

    sidebar_launcher = LocatorDescriptor(
        testid="sidebar-support-assistant-button",
        description="Sidebar Support Assistant launcher (the element owning onClick)"
    )

    widget = LocatorDescriptor(
        testid="support-assistant-widget",
        description="Support Assistant widget window"
    )

    widget_header_title = LocatorDescriptor(
        testid="support-assistant-widget-title",
        description="Support Assistant widget header title"
    )

    message_input_field = LocatorDescriptor(
        testid="support-assistant-message-input",
        description="Support Assistant message input textarea"
    )

    send_message_button = LocatorDescriptor(
        testid="support-assistant-send-button",
        description="Support Assistant Send message button"
    )

    message_items = LocatorDescriptor(
        testid="support-assistant-message-item",
        description="Support Assistant conversation message items (repeated)"
    )

    # ELITEA-2419 — copy-to-clipboard affordance on assistant responses.
    # Testids live in the connected first-party repo EliteaAI/elitea_assistant
    # (EliteaAI/elitea_assistant@216da01 on its ``automation/testids`` branch).
    message_copy_buttons = LocatorDescriptor(
        testid="support-assistant-message-copy-button",
        description="Copy-to-clipboard button on a completed assistant response bubble"
    )

    message_bubbles = LocatorDescriptor(
        testid="support-assistant-message-bubble",
        description="Message bubble (user or assistant) inside a message item"
    )

    # Scoped / state-filtered forms of the testids above. UPPER_CASE class
    # constants are the sanctioned shape for a selector that must be composed
    # at call time (.agents/testing.md § Locator policy) — the copied state is
    # a ``data-*`` attribute, never a second testid value.
    MESSAGE_COPY_BUTTON = '[data-testid="support-assistant-message-copy-button"]'
    MESSAGE_COPY_BUTTON_COPIED = '[data-testid="support-assistant-message-copy-button"][data-copied="true"]'
    MESSAGE_COPY_BUTTON_IDLE = '[data-testid="support-assistant-message-copy-button"][data-copied="false"]'
    ASSISTANT_MESSAGE_ITEM = '[data-testid="support-assistant-message-item"][data-role="assistant"]'
    USER_MESSAGE_ITEM = '[data-testid="support-assistant-message-item"][data-role="user"]'
    MESSAGE_BUBBLE = '[data-testid="support-assistant-message-bubble"]'

    # ELITEA-2423 — conversation-history panel. Testids live in the connected
    # first-party repo EliteaAI/elitea_assistant
    # (EliteaAI/elitea_assistant@7413180 on its ``automation/testids`` branch),
    # ``src/components/chat/ChatHeader.tsx``.
    history_toggle_button = LocatorDescriptor(
        testid="support-assistant-history-button",
        description="Support Assistant conversation-history toggle button"
    )

    history_dropdown = LocatorDescriptor(
        testid="support-assistant-history-dropdown",
        description="Support Assistant conversation-history dropdown panel"
    )

    history_items = LocatorDescriptor(
        testid="support-assistant-history-item",
        description="Support Assistant conversation-history entries (repeated)"
    )

    # ELITEA-2421 — file attachments. Testids live in the connected first-party
    # repo EliteaAI/elitea_assistant (EliteaAI/elitea_assistant@1960c8e on its
    # ``automation/testids`` branch), ``src/components/chat/MessageInput.tsx``
    # and ``src/components/chat/attachments/AttachmentChip.tsx``.
    attach_file_button = LocatorDescriptor(
        testid="support-assistant-attach-button",
        description="Support Assistant Attach file button (opens the file picker)"
    )

    attachment_chips = LocatorDescriptor(
        testid="support-assistant-attachment-chip",
        description="Attachment chips staged in the composer (repeated)"
    )

    # ELITEA-2420 — drag-and-drop attachment. Testids live in the connected
    # first-party repo EliteaAI/elitea_assistant
    # (EliteaAI/elitea_assistant@e134bfc on its ``automation/testids`` branch),
    # ``src/components/chat/MessageInput.tsx``.
    #
    # The drop zone is the ALWAYS-MOUNTED input-area div that owns
    # ``onDragEnter``/``onDragOver``/``onDragLeave``/``onDrop`` — its testid is
    # stable identity; the drag-over state stays a CSS modifier class, never a
    # second testid value (PR #581 ruling).
    drop_zone = LocatorDescriptor(
        testid="support-assistant-drop-zone",
        description="Composer input area that owns the drag-and-drop handlers"
    )

    # The overlay is rendered only while ``isDragOver`` is true
    # (``{isDragOver && <div …>Drop files here</div>}``). Its own MOUNT encodes
    # the state, so presence/absence is the assertion and no extra ``data-*``
    # attribute is added — same accepted shape as
    # ``support-assistant-history-dropdown``.
    drop_overlay = LocatorDescriptor(
        testid="support-assistant-drop-overlay",
        description='"Drop files here" affordance shown while a file drag is over the composer'
    )

    # An item is rendered ``disabled`` exactly when it IS the currently-open
    # conversation (``ChatHeader.tsx``:
    # ``disabled={conversation.uuid === currentConversationId}``). The native
    # attribute already encodes that state, so no second testid and no extra
    # ``data-*`` attribute is needed — filter on it from a class constant
    # (.agents/testing.md § Locator policy).
    HISTORY_ITEM_OPENABLE = '[data-testid="support-assistant-history-item"]:not([disabled])'

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

    def is_fullview_mode(self) -> bool:
        """Check if the widget is currently in full-view (expanded) mode.

        Mode-specific signal, complementary to is_widget_open(): the widget
        container gains the --expanded modifier class (and resizes
        460x480 -> 720x678) when expanded via the header toggle button.
        is_widget_open() alone cannot distinguish compact from full-view,
        since it only checks title visibility (true in both modes).

        Returns:
            True if the widget container has the --expanded modifier class.
        """
        try:
            class_attr = self.widget_container.get_attribute("class") or ""
            return "elitea-assistant-window--expanded" in class_attr
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

    def wait_for_response(self, initial_count: int = 0, timeout: int = 120000):
        """Wait for the assistant to respond to a message with progressive timeout.

        Uses a progressive wait strategy: the timeout resets each time the status
        changes (e.g., "sending" -> "thinking" -> "receiving text"). This handles
        slow AI responses where processing takes time but progress is being made.

        Completion is detected by:
        1. A new "Copy to clipboard" button (message fully rendered)
        2. A new assistant message wrapper with no active spinner

        Args:
            initial_count: Number of assistant messages before sending
            timeout: Maximum time (ms) to wait WITHOUT status change (default 120s)
        """
        logger.info("Waiting for assistant response (initial_count=%d, timeout=%dms)...", initial_count, timeout)

        deadline = time.time() + timeout / 1000
        last_status = None
        last_status_change = time.time()
        poll_interval = 0.5  # seconds

        while time.time() < deadline:
            # Check if response is complete
            is_complete = self.page.evaluate(
                """(expectedCount) => {
                    // Primary signal: new copy button means message fully done
                    const copyButtons = document.querySelectorAll('button[aria-label="Copy to clipboard"]');
                    if (copyButtons.length > expectedCount) return { done: true };

                    // Secondary: new assistant wrapper with no active spinner
                    const assistantWrappers = document.querySelectorAll(
                        '.elitea-assistant-message-wrapper--assistant'
                    );
                    if (assistantWrappers.length > expectedCount) {
                        const activeSpinner = document.querySelector(
                            '.elitea-assistant-status-chip--active'
                        );
                        if (!activeSpinner) return { done: true };
                    }

                    // Get current status text for progress tracking
                    // Status chip shows: "Sending...", "Thinking...", "Receiving text...", etc.
                    const statusChip = document.querySelector('.elitea-assistant-status-chip');
                    const statusText = statusChip ? statusChip.textContent.trim() : '';

                    // Also track message content length as progress indicator
                    const lastWrapper = assistantWrappers[assistantWrappers.length - 1];
                    const contentLength = lastWrapper ? (lastWrapper.textContent || '').length : 0;

                    return {
                        done: false,
                        status: statusText,
                        wrapperCount: assistantWrappers.length,
                        contentLength: contentLength
                    };
                }""",
                initial_count
            )

            if is_complete.get("done"):
                logger.info("Assistant response complete")
                self.page.wait_for_timeout(1000)  # Stabilize
                return

            # Build current state signature for change detection
            current_status = f"{is_complete.get('status', '')}|{is_complete.get('wrapperCount', 0)}|{is_complete.get('contentLength', 0)}"

            if current_status != last_status:
                # Progress detected - reset the deadline
                logger.info(
                    "Status change: %s -> %s (resetting timeout)",
                    last_status or "(none)", current_status
                )
                last_status = current_status
                last_status_change = time.time()
                deadline = time.time() + timeout / 1000

            # Check if we've been stuck without progress for too long
            time_since_change = time.time() - last_status_change
            if time_since_change > timeout / 1000:
                raise TimeoutError(
                    f"Support Assistant response timed out after {timeout}ms without status change. "
                    f"Last status: {last_status}"
                )

            self.page.wait_for_timeout(int(poll_interval * 1000))

        raise TimeoutError(
            f"Support Assistant response timed out after {timeout}ms. "
            f"Last status: {last_status}"
        )

    def get_message_count(self) -> int:
        """Get the count of message blocks in the conversation.

        Returns:
            Number of message blocks (user + assistant)
        """
        # Count all message wrappers (both user and assistant)
        all_wrappers = self.page.locator('.elitea-assistant-message-wrapper')
        count = all_wrappers.count()
        logger.info(f"Total message count: {count}")
        return count

    def get_assistant_message_count(self) -> int:
        """Get the count of assistant response messages.

        Uses the assistant message wrapper elements which are always present
        (even during streaming), falling back to Copy to clipboard button count
        for completed messages.

        Returns:
            Number of assistant messages
        """
        # Use assistant message wrapper count — present for all assistant messages
        # including those still streaming
        wrappers = self.page.locator('.elitea-assistant-message-wrapper--assistant')
        count = wrappers.count()
        if count > 0:
            logger.info(f"Assistant message count (wrappers): {count}")
            return count

        # Fallback: count copy buttons (only on completed messages)
        copy_buttons = self.page.locator('button[aria-label="Copy to clipboard"]')
        count = copy_buttons.count()
        logger.info(f"Assistant message count (copy buttons): {count}")
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

        The history dropdown renders items as BUTTON.elitea-assistant-history-item
        inside DIV.elitea-assistant-history-dropdown-scroll.

        Returns:
            Number of history sessions
        """
        # History items are BUTTON.elitea-assistant-history-item inside the dropdown
        sessions = self.page.locator('button.elitea-assistant-history-item')
        count = sessions.count()
        logger.info(f"History session count: {count}")
        return count

    @action("Select history session")
    def select_history_session(self, index: int = 0, timeout: int = 5000):
        """Select a session from the history panel.

        The history dropdown renders session items as BUTTON.elitea-assistant-history-item.
        The selector [class*="history"] button was too broad and matched the 'Chat history'
        header button (index 0) before the actual session items, causing the wrong element
        to be clicked and toggling the dropdown closed.

        After clicking a session, the widget shows skeleton placeholder rows
        (DIV.elitea-assistant-skeleton-row) while loading. We must wait for
        skeleton rows to disappear and actual message wrappers to appear.

        Args:
            index: Index of session to select (0 = most recent)
            timeout: Maximum wait time in milliseconds
        """
        logger.info(f"Selecting history session at index {index}")
        sessions = self.page.locator('button.elitea-assistant-history-item')
        sessions.nth(index).click()

        # Wait for skeleton loading indicators to disappear
        skeleton = self.page.locator('.elitea-assistant-skeleton-row')
        try:
            # Skeleton may appear briefly — wait for it to disappear
            skeleton.first.wait_for(state="hidden", timeout=timeout)
        except Exception:
            pass  # Skeleton may not appear at all if load is instant

        # Wait for actual messages to appear
        try:
            self.page.locator('.elitea-assistant-message-wrapper').first.wait_for(
                state="visible", timeout=timeout
            )
        except Exception:
            pass  # Messages may not exist in empty session

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

    # ------------------------------------------------------------------
    # Testid-based helpers (ELITEA-2418) — additive; the legacy helpers above
    # keep their existing callers byte-identical.
    # ------------------------------------------------------------------

    @action("Open Support Assistant via sidebar launcher")
    def open_widget_via_sidebar(self, timeout: int = 10000):
        """Open the widget with a REAL pointer click on the sidebar launcher.

        Distinct from :meth:`open_widget`, which JS-clicks the floating button.
        A native click on ``button.elitea-assistant-button`` is intercepted by
        the MUI Tooltip clone; the sidebar wrapper is the element that actually
        carries ``onClick={onToggleAssistant}``, so clicking it is the genuine
        user-equivalent gesture (no ``page.evaluate``).

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Opening Support Assistant widget via sidebar launcher")
        self.sidebar_launcher.click()
        self.widget_header_title.wait_for(state="visible", timeout=timeout)
        self.message_input_field.wait_for(state="visible", timeout=timeout)
        logger.info("Support Assistant widget opened")

    def get_message_item_count(self) -> int:
        """Count conversation message items via their testid.

        The widget restores the previous session on open, so this is a
        BASELINE to diff against — never expect an absolute value.

        Returns:
            Number of message items currently rendered
        """
        return self.message_items.count()

    @action("Set Support Assistant input text")
    def set_message_text(self, text: str):
        """Replace the input content with ``text`` using real input events.

        ``fill`` dispatches the events React's controlled ``<textarea>``
        actually listens to; assigning ``value`` directly does not update
        component state (see #1581 — a false defect produced exactly that way).

        Args:
            text: Text to place in the input (``""`` clears it)
        """
        self.message_input_field.fill(text)

    # ------------------------------------------------------------------
    # Copy-to-clipboard helpers (ELITEA-2419) — additive.
    # ------------------------------------------------------------------

    def get_copy_button_count(self) -> int:
        """Count the copy-to-clipboard buttons currently rendered.

        A copy button exists only on a COMPLETED assistant message
        (``MessageItem.tsx``: ``!isStreaming && !isAnimating``), which makes
        this count the most accurate "reply finished" signal on this surface.
        A fresh chat already has one (the greeting), so this is always a
        BASELINE to diff against — never an absolute expectation.

        Returns:
            Number of copy buttons rendered in the conversation
        """
        return self.message_copy_buttons.count()

    def last_assistant_item(self):
        """Locator for the most recent assistant message item.

        Returns:
            Playwright Locator for the last ``data-role="assistant"`` item
        """
        return self.page.locator(self.ASSISTANT_MESSAGE_ITEM).last

    def last_user_item(self):
        """Locator for the most recent user message item.

        Returns:
            Playwright Locator for the last ``data-role="user"`` item
        """
        return self.page.locator(self.USER_MESSAGE_ITEM).last

    def copy_button_in(self, message_item):
        """Locator for the copy button inside a given message item.

        Args:
            message_item: A message-item Locator (see :meth:`last_assistant_item`)

        Returns:
            Playwright Locator scoped to that item's copy button
        """
        return message_item.locator(self.MESSAGE_COPY_BUTTON)

    def bubble_in(self, message_item):
        """Locator for the message bubble inside a given message item.

        Args:
            message_item: A message-item Locator

        Returns:
            Playwright Locator scoped to that item's bubble
        """
        return message_item.locator(self.MESSAGE_BUBBLE)

    @action("Send Support Assistant message")
    def send_message_via_testid(self, text: str, timeout: int = 10000):
        """Type ``text`` and click Send using the testid-based handles.

        Additive counterpart to the legacy :meth:`send_message`, which builds
        raw locators inside its body (pre-policy tech debt #25/#42) and is kept
        byte-identical for its existing callers.

        Args:
            text: Message text to send
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Sending Support Assistant message: %s", text[:50])
        self.set_message_text(text)
        self.send_message_button.click(timeout=timeout)

    # ------------------------------------------------------------------
    # Navigation-persistence helpers (ELITEA-2422) — additive.
    # ------------------------------------------------------------------

    def user_message_item_with_text(self, text: str):
        """Locator for the user message item(s) carrying *text*.

        Composed from the existing :attr:`USER_MESSAGE_ITEM` class constant —
        no new handle. Used as a same-session proof: after an in-app route
        change the message a test sent BEFORE navigating must still be
        rendered, which a reset session would not satisfy.

        The widget restores whatever conversation the test user already has,
        so a prior run's copy of *text* may already be present. Callers take a
        baseline count first and assert a delta, never an absolute.

        Args:
            text: Substring to match against the item's rendered text

        Returns:
            Playwright Locator for the matching user message items
        """
        return self.page.locator(self.USER_MESSAGE_ITEM).filter(has_text=text)

    # ------------------------------------------------------------------
    # Conversation-history helpers (ELITEA-2423) — additive.
    #
    # The legacy :meth:`open_history`, :meth:`get_history_session_count` and
    # :meth:`select_history_session` build ``button.elitea-assistant-history-item``
    # locators inside their bodies (pre-policy tech debt #25/#42); they are left
    # byte-identical for their existing callers.
    # ------------------------------------------------------------------

    @action("Open Support Assistant conversation history")
    def open_history_via_testid(self, timeout: int = 10000):
        """Open the history dropdown using the testid-based handles.

        The caller is expected to have already asserted that
        :attr:`history_toggle_button` is enabled — the button is ``disabled``
        while ``history.length === 0`` (``ChatHeader.tsx``), which makes that
        assertion the honest "the conversation list has loaded" wait on this
        surface rather than a network or timing heuristic.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Opening Support Assistant conversation history")
        self.history_toggle_button.click(timeout=timeout)
        self.history_dropdown.wait_for(state="visible", timeout=timeout)

    def get_history_item_count_via_testid(self) -> int:
        """Count the conversation entries listed in the history dropdown.

        History is shared test-account data that other runs add to, so this is
        a BASELINE to compare against itself across a refresh — never an
        absolute expectation.

        Returns:
            Number of history entries currently rendered
        """
        return self.history_items.count()

    def first_openable_history_item(self):
        """Locator for the first history entry that can actually be opened.

        Entries are ``disabled`` when they are the currently-open conversation,
        so "open a previous session" means the first ``:not([disabled])`` entry
        — clicking index 0 right after a page refresh is a no-op, because the
        widget auto-restores the list's first conversation.

        Returns:
            Playwright Locator for the first enabled history entry
        """
        return self.page.locator(self.HISTORY_ITEM_OPENABLE).first

    # ------------------------------------------------------------------
    # Attachment helpers (ELITEA-2421) — additive. The legacy
    # :meth:`attach_file` drives the pre-policy ``attach_button`` fallback
    # field and waits on the network; it is left byte-identical for its
    # existing callers.
    # ------------------------------------------------------------------

    @action("Attach file to Support Assistant message")
    def attach_file_via_testid(self, file_path: str, timeout: int = 10000):
        """Open the file picker from the testid-based attach button and pick *file_path*.

        No network wait afterwards: the upload fires on **Send**, not on
        attach (``MessageInput.handleSend`` -> ``startUpload``), so attaching
        only stages a PENDING chip in local state. Waiting for the network here
        would either time out or pass vacuously — the caller asserts the chip
        instead.

        Args:
            file_path: Path to the file to attach
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Attaching file to Support Assistant message: %s", file_path)
        with self.page.expect_file_chooser(timeout=timeout) as fc_info:
            self.attach_file_button.click(timeout=timeout)
        fc_info.value.set_files(file_path)

    def user_message_items(self):
        """Locator for every user message item in the conversation.

        Composed from the existing :attr:`USER_MESSAGE_ITEM` class constant —
        no new handle. The plural counterpart to :meth:`last_user_item`, for
        callers that assert a count delta rather than inspect the newest item.

        Returns:
            Playwright Locator for all ``data-role="user"`` message items
        """
        return self.page.locator(self.USER_MESSAGE_ITEM)

    def get_user_message_item_count(self) -> int:
        """Count the user message items currently rendered.

        The widget restores the previous session on open, so this is a
        BASELINE to diff against — never an absolute expectation.

        Returns:
            Number of user message items rendered in the conversation
        """
        return self.user_message_items().count()

    def get_attachment_chip_count(self) -> int:
        """Count the attachment chips currently staged in the composer.

        The composer is cleared on a successful send
        (``chat.hook.ts`` ``clearAttachments()``), so this returning to 0 after
        Send distinguishes "chip cleared by design" from "chip never existed".

        Returns:
            Number of attachment chips rendered in the composer
        """
        return self.attachment_chips.count()

    # ------------------------------------------------------------------
    # Drag-and-drop attachment helpers (ELITEA-2420) — additive.
    #
    # Playwright cannot drive a native OS-level file drag (Finder/Explorer):
    # there is no browser API surface for it. The technique below is the one
    # already merged and reviewed as :meth:`pages.chat_page.ChatPage.
    # drag_and_drop_file` on the main chat composer — build a synthetic
    # ``DataTransfer`` holding a REAL ``File`` reconstructed in-page from the
    # real file's own bytes, and dispatch ``DragEvent``s at the testid'd drop
    # zone.
    #
    # Fidelity: this substitutes only the INPUT GESTURE, which is not the
    # system under test; from ``handleDragEnter``/``handleDrop`` onward the
    # product code path is byte-identical to a human drag, and every asserted
    # value (overlay render, chip, Send state, upload status, predict frame,
    # reply) is product-produced. TRANSIT ONLY — nothing observable is
    # fabricated (.agents/testing.md § Fidelity policy).
    #
    # The gesture is exposed as three composable phases rather than one call
    # because the drag-over affordance must be asserted to REVERT mid-gesture
    # (``handleDragLeave`` decrements ``dragCounterRef``), which a monolithic
    # enter-over-drop helper cannot express.
    # ------------------------------------------------------------------

    # Constructing the DataTransfer is done once and shared by every phase.
    # ``handleDragEnter`` reads only ``dataTransfer.types``, ``handleDragLeave``
    # reads nothing, and ``handleDrop`` reads ``dataTransfer.files`` — so each
    # phase builds its own transfer and none depends on another's state.
    # Events MUST carry ``bubbles``/``cancelable``: React listens at the root
    # container, and the handlers call ``preventDefault()``.
    _DISPATCH_DRAG_EVENTS_JS = """(el, args) => {
        const [b64, name, mime, types] = args;
        const binary = atob(b64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        const file = new File([bytes], name, { type: mime });
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        for (const type of types) {
            el.dispatchEvent(new DragEvent(type, {
                bubbles: true,
                cancelable: true,
                dataTransfer,
            }));
        }
    }"""

    def _dispatch_drag_events(self, file_path: str, event_types: list, timeout: int) -> None:
        """Dispatch *event_types* as ``DragEvent``s carrying *file_path* at the drop zone.

        Args:
            file_path: Absolute or relative path to a real file on disk
            event_types: Ordered DOM event names, e.g. ``["dragenter"]``
            timeout: Maximum wait for the drop zone to be visible (ms)
        """
        path = Path(file_path)
        file_b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        mime_type = mimetypes.guess_type(path.name)[0] or "text/plain"

        self.drop_zone.wait_for(state="visible", timeout=timeout)
        self.drop_zone.evaluate(
            self._DISPATCH_DRAG_EVENTS_JS,
            [file_b64, path.name, mime_type, event_types],
        )

    @action("Drag file over Support Assistant composer")
    def drag_file_over_composer(self, file_path: str, timeout: int = 10000):
        """Begin a file drag over the composer (``dragenter`` + ``dragover``).

        Leaves the drag in progress: the caller asserts the drop overlay is
        visible, then either :meth:`drag_leave_composer` or
        :meth:`drop_file_on_composer`.

        Args:
            file_path: Path to the real file being dragged
            timeout: Maximum wait for the drop zone to be visible (ms)
        """
        logger.info("Dragging file over Support Assistant composer: %s", file_path)
        self._dispatch_drag_events(file_path, ["dragenter", "dragover"], timeout)

    @action("Drag leave Support Assistant composer")
    def drag_leave_composer(self, file_path: str, timeout: int = 10000):
        """End a drag WITHOUT dropping (``dragleave``).

        ``handleDragLeave`` decrements ``dragCounterRef`` and clears
        ``isDragOver`` when it reaches 0, so this must be paired 1:1 with the
        ``dragenter`` deliveries that preceded it.

        Args:
            file_path: Path to the real file being dragged (the handler ignores
                the payload, but the event is built the same way)
            timeout: Maximum wait for the drop zone to be visible (ms)
        """
        logger.info("Dragging file away from Support Assistant composer")
        self._dispatch_drag_events(file_path, ["dragleave"], timeout)

    @action("Drop file on Support Assistant composer")
    def drop_file_on_composer(self, file_path: str, timeout: int = 10000):
        """Complete a drag by dropping the file on the composer.

        Delivers the full ``dragenter`` -> ``dragover`` -> ``drop`` sequence so
        the call is self-contained regardless of whether a drag is already in
        progress: ``handleDrop`` resets ``dragCounterRef`` to 0 unconditionally,
        so the counter cannot leak.

        Args:
            file_path: Path to the real file being dropped
            timeout: Maximum wait for the drop zone to be visible (ms)
        """
        logger.info("Dropping file on Support Assistant composer: %s", file_path)
        self._dispatch_drag_events(file_path, ["dragenter", "dragover", "drop"], timeout)
