"""Chat page object for Elitea chat interface.

Provides locators and methods for interacting with chat conversations,
message input, participants, and chat settings.
"""

import logging
import re
import time
from playwright.sync_api import Page
from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor, OptionalLocatorDescriptor
from components.mui import Dialog, Popper
from utils.actions import action
from config import settings

logger = logging.getLogger("elitea.pages.chat")


class FeatureNotAvailableError(Exception):
    """Raised when a UI feature is not available in the current UI version."""
    pass


class ChatPage(BasePage):
    """Page object for Elitea chat interface (/app/chat).

    Handles:
    - Message sending and history
    - Model selection
    - Chat settings and context
    - Sidebar navigation
    - File attachments
    - Message actions (copy, delete, regenerate)

    URL: /app/chat, /app/chat/{conversation_id}
    """

    # ------------------------------------------------------------------
    # Message input area
    # ------------------------------------------------------------------

    message_input = LocatorDescriptor(
        testid="chat-message-input",
        description="Main message input textarea"
    )

    send_button = LocatorDescriptor(
        testid="chat-send-button",
        description="Send message button"
    )

    attach_files_button = LocatorDescriptor(
        testid="chat-attach-button",
        description="Attach files button"
    )

    # ------------------------------------------------------------------
    # Sidebar / drawer
    # ------------------------------------------------------------------

    sidebar_toggle = LocatorDescriptor(
        testid="sidebar-toggle",
        description="Sidebar toggle button"
    )

    search_conversations_input = LocatorDescriptor(
        testid="search-conversations-input",
        description="Search conversations input field in sidebar"
    )

    # ------------------------------------------------------------------
    # Model selector
    # ------------------------------------------------------------------

    model_selector = LocatorDescriptor(
        testid="model-selector-button",
        description="Model selector dropdown button"
    )

    # ------------------------------------------------------------------
    # Chat actions
    # ------------------------------------------------------------------

    context_budget_panel = LocatorDescriptor(
        testid="context-budget-panel",
        description=(
            "Context Budget panel in the right sidebar. "
            "Appears only after at least one message has been sent."
        ),
    )

    context_budget_tokens_display = LocatorDescriptor(
        testid="context-budget-tokens",
        description="Token usage display inside Context Budget panel.",
    )

    edit_context_button = LocatorDescriptor(
        testid="context-settings-button",
        description="Edit context settings button in the right panel Context Budget section"
    )

    plus_menu_button = LocatorDescriptor(
        testid="plus-menu-button",
        description="Plus menu button - entry point for adding participants, internal tools, and attachments"
    )

    internal_tools_menuitem = LocatorDescriptor(
        testid="internal-tools-menuitem",
        description="Internal Tools menuitem inside plus menu dropdown"
    )

    # Legacy locator - kept for backward compatibility
    internal_tools_toggle = LocatorDescriptor(
        testid="internal-tools-toggle",
        description="DEPRECATED: Internal tools toggle button (moved to plus menu in v2.0.3)"
    )

    # ------------------------------------------------------------------
    # Message actions
    # ------------------------------------------------------------------

    copy_message_button = LocatorDescriptor(
        testid="chat-message-copy",
        description="Copy message to clipboard button"
    )

    regenerate_button = LocatorDescriptor(
        testid="message-regenerate-button",
        description="Regenerate AI response button"
    )

    # ------------------------------------------------------------------
    # Voice / TTS Controls
    # ------------------------------------------------------------------
    # VoiceMiniPlayer appears in chat only when Read-out and Voice mode
    # features are activated. By default it should NOT be visible.

    voice_mini_player = OptionalLocatorDescriptor(
        testid="chat-voice-mini-player",
        description="Voice mini player container. Only visible when voice features activated."
    )

    voice_play_stop_button = LocatorDescriptor(
        testid="chat-voice-play-stop-button",
        description="Play/Stop button in voice mini player"
    )

    voice_settings_button = LocatorDescriptor(
        testid="chat-voice-settings-button",
        description="Voice settings button in voice mini player"
    )

    read_out_button = LocatorDescriptor(
        testid="chat-read-out-button",
        description="Read out (speaker) button on AI messages to start TTS"
    )

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    messages_list = LocatorDescriptor(
        testid="chat-messages-list",
        description="Main messages list container"
    )

    messages_container = LocatorDescriptor(
        testid="chat-message-block",
        description="Individual message blocks (user + AI)"
    )

    def __init__(self, page: Page):
        super().__init__(page)
        
    @action("Navigate to chat")
    def navigate_to_chat(self, conversation_id: str = None):
        """Navigate to chat page and wait until ready.

        When navigating to a specific conversation the SPA may redirect to
        the last-viewed conversation stored in the browser session.  If that
        happens we retry once with a hard reload.

        For localhost (no /app prefix), clicks Chat in sidebar instead of direct navigation.

        Automatically waits for the page to load (spinner disappears, input
        visible). For explicit waiting (e.g., after sending a message), use
        wait_for_page_load().

        Args:
            conversation_id: Optional conversation ID to navigate to specific chat
        """
        # Check if running on localhost (from settings, not current page URL)
        base_url = settings.elitea_url or ""
        is_localhost = "localhost" in base_url or "127.0.0.1" in base_url

        # Wait a moment for page URL to settle (may be in navigation)
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass  # Page might not be loaded yet

        # Check if already on chat page (skip navigation if so)
        current_url = self.page.url
        already_on_chat = "/chat" in current_url and "about:blank" not in current_url

        if already_on_chat:
            logger.info("Already on chat page (%s), skipping navigation", current_url)
        elif is_localhost:
            # On localhost, just go to base URL - EliteaUI auto-redirects to /chat
            logger.info("Localhost detected, navigating to %s", base_url)
            self.page.goto(base_url, wait_until="domcontentloaded")
            self.page.wait_for_load_state("networkidle", timeout=15000)
        else:
            # On dev/stage, use direct navigation
            path = f"/app/chat/{conversation_id}" if conversation_id else "/app/chat"
            self.navigate(path)

            # If we targeted a specific conversation, verify the SPA didn't redirect
            if conversation_id and f"/app/chat/{conversation_id}" not in self.page.url:
                logger.warning(
                    "SPA redirected to %s instead of /app/chat/%s — retrying",
                    self.page.url, conversation_id,
                )
                self.page.goto(
                    f"{self.page.url.split('/app/')[0]}/app/chat/{conversation_id}",
                    wait_until="domcontentloaded",
                )
                self.page.wait_for_load_state("networkidle", timeout=30000)

        self.wait_for_page_load()
        logger.info(f"Navigated to chat, page loaded (actual URL: {self.page.url})")
        
    def wait_for_page_load(self, timeout: int = 30000):
        """Wait for chat page to fully load.

        Args:
            timeout: Maximum wait time in ms (default 30s)
        """
        # Wait for network idle first
        self.wait_for_network(timeout=timeout)

        # Primary check: message input is ready (page is usable)
        # This is more reliable than waiting for spinners to disappear,
        # as some spinners (AI processing indicators) may persist.
        try:
            self.message_input.wait_for(state="visible", timeout=timeout)
            logger.info("Chat page loaded - message input visible")
        except Exception:
            # Fallback: check for full-page loading spinner and wait for it
            spinner = self.page.get_by_test_id("loading-spinner")
            if spinner.count() > 0:
                spinner.first.wait_for(state="hidden", timeout=timeout)
                logger.info("Loading spinner disappeared")
            # Try message input again
            self.message_input.wait_for(state="visible", timeout=15000)
            logger.info("Chat page loaded after spinner wait")
        
    @action("Send message")
    def send_message(self, text: str, use_enter: bool = False):
        """Send a message in the chat.

        Args:
            text: Message text to send
            use_enter: If True, use Enter key instead of clicking send button
        """
        logger.info(f"Sending message: {text[:50]}...")
        self.message_input.fill(text)

        if use_enter:
            self.message_input.press("Enter")
        else:
            # Wait for send button to be visible and enabled, then click.
            # force=True is needed because MUI overlay elements can
            # intercept pointer events on the send button.
            self.send_button.wait_for(state="visible", timeout=5000)
            self.send_button.click(force=True, timeout=5000)
            
    @action("Send multi-line message")
    def send_message_with_shift_enter(self, lines: list):
        """Send a multi-line message using Shift+Enter for line breaks.

        Args:
            lines: List of text lines to send
        """
        logger.info(f"Sending multi-line message with {len(lines)} lines")
        for i, line in enumerate(lines):
            self.message_input.type(line)
            if i < len(lines) - 1:
                self.message_input.press("Shift+Enter")
        self.send_button.click(force=True)
        
    def get_message_count(self) -> int:
        """Get the count of messages in the chat history.
        
        Returns:
            Number of messages displayed
        """
        count = self.messages_container.count()
        logger.info(f"Message count: {count}")
        return count
        
    @staticmethod
    def _extract_message_body(message_locator) -> str:
        """Extract the body text from a message ``<li>``, excluding headers.

        Each message ``<li>`` contains a header row (sender name,
        timestamp, etc.) and a body area.  For AI messages the body
        is an ``<Answer>`` div rendered via ``<Markdown>`` which
        produces ``<p>`` tags for paragraphs and ``<ul><li>`` for
        bullet/numbered lists.  For user messages the body is a
        ``<Typography variant="bodyMedium">`` span.

        The extractor collects text from all ``<p>`` and ``<li>``
        elements so that list responses (e.g. branch listings) are
        captured in full rather than only the introductory sentence.

        Returns an empty string when no body content is found (e.g.
        the AI is still streaming or the response is empty).  This
        is intentional — callers like ``wait_for_message_content_stable``
        treat empty text as "not ready yet" and keep polling.
        """
        # AI messages: content is rendered via Markdown which produces <p> for
        # paragraphs and <ul><li> for bullet lists.  Collect all block-level
        # text nodes so that list items are not silently dropped.
        # Strategy: grab the inner text of all <p> and <li> elements in
        # document order, then join them.  Using `inner_text()` on the
        # container would include header metadata (sender name, timestamp),
        # so we enumerate block elements explicitly.
        block_elements = message_locator.locator('p, li')
        if block_elements.count() > 0:
            parts = []
            for i in range(block_elements.count()):
                parts.append(block_elements.nth(i).text_content() or "")
            text = "\n".join(p for p in parts if p.strip()).strip()
            if text:
                return text

        # User messages: content is in bodyMedium Typography spans
        body_spans = message_locator.locator('.MuiTypography-bodyMedium')
        if body_spans.count() > 0:
            parts = []
            for i in range(body_spans.count()):
                parts.append(body_spans.nth(i).text_content() or "")
            text = "\n".join(parts).strip()
            if text:
                return text

        return ""

    def get_last_message_text(self) -> str:
        """Get the text content of the last message body.

        Extracts the body content (excluding header/metadata) from
        the last message ``<li>`` element.

        Returns:
            Text of the last message body
        """
        last_msg = self.messages_container.last
        text = self._extract_message_body(last_msg)
        logger.info(f"Last message: {text[:50]}...")
        return text
        
    def wait_for_ai_response(self, initial_count: int = 0, timeout: int = 10000):
        """Wait for the AI to respond after sending a message.

        After the user sends a message, the conversation grows by at least 2:
        the user's own message at index ``initial_count``, and the AI's response
        at index ``initial_count + 1``. This method waits for that AI response
        element to appear in the DOM before returning.

        Args:
            initial_count: Number of messages present *before* the user sent
                           the message (captured via ``get_message_count()``).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info(
            "Waiting for AI response (initial_count=%d, timeout=%dms)...",
            initial_count,
            timeout,
        )
        # User's message lands at nth(initial_count).
        # AI's response lands at nth(initial_count + 1).
        ai_response_index = initial_count + 1
        self.messages_container.nth(ai_response_index).wait_for(
            state="visible", timeout=timeout,
        )
        self.wait_for_network(timeout=5000)
        logger.info("AI response element appeared at index %d", ai_response_index)

    # Transient messages that indicate generation is still in progress
    TRANSIENT_MESSAGES = frozenset([
        "waking the agent",
        "waking the agent…",
        "waking the agent...",
        "thinking",
        "thinking…",
        "thinking...",
    ])

    def _is_transient_message(self, text: str) -> bool:
        """Check if the message is a transient state that should be ignored."""
        return text.lower().strip().rstrip(".…") in self.TRANSIENT_MESSAGES or \
               text.lower().strip() in self.TRANSIENT_MESSAGES

    def wait_for_message_content_stable(
        self, stable_duration_ms: int = 2000, timeout: int = 30000
    ):
        """Wait until the last message content stops changing.

        Polls the last message text at short intervals and considers it
        stable once the text hasn't changed for *stable_duration_ms*.
        Ignores transient states like "Waking the agent…" or "Thinking…".

        Args:
            stable_duration_ms: Duration in ms the content must remain
                unchanged before it's considered stable.
            timeout: Maximum total wait time in milliseconds.
        """
        logger.info(
            "Waiting for message content to stabilise "
            "(stable=%dms, timeout=%dms)...",
            stable_duration_ms,
            timeout,
        )
        poll_interval = 0.5  # seconds
        stable_duration = stable_duration_ms / 1000.0
        deadline = time.monotonic() + timeout / 1000.0

        last_text = ""
        stable_since = time.monotonic()

        while time.monotonic() < deadline:
            try:
                current_text = self._extract_message_body(
                    self.messages_container.last
                )
            except Exception:
                current_text = ""

            # Skip transient messages - they don't count as stable content
            if self._is_transient_message(current_text):
                logger.debug("Skipping transient message: %s", current_text[:50])
                time.sleep(poll_interval)
                continue

            if current_text != last_text:
                last_text = current_text
                stable_since = time.monotonic()

            if (
                last_text
                and time.monotonic() - stable_since >= stable_duration
            ):
                logger.info("Message content stable after %.1fs", time.monotonic() - (stable_since - stable_duration))
                return

            time.sleep(poll_interval)

        # If we only saw transient messages, raise an error
        if self._is_transient_message(last_text) or not last_text:
            raise TimeoutError(
                f"Timed out waiting for non-transient message content. "
                f"Last message: '{last_text}'"
            )
        logger.warning("Timed out waiting for stable message content (last: %s)", last_text[:100])

    def wait_for_generation_complete(self, timeout: int = 60000):
        """Wait until the AI finishes generating the full response.

        Call this after ``wait_for_ai_response`` to guarantee you read the
        complete response rather than a mid-generation snapshot.

        Args:
            timeout: Maximum wait in milliseconds (default 60 s — long enough
                     for toolkit execution which involves an external API call).
        """
        logger.info("Waiting for generation to complete (Speaking mode button)...")
        # The Speaking mode button appears when generation is complete
        # During generation, a stop button is shown instead
        speaking_mode_btn = self.page.get_by_test_id("chat-speaking-mode-button")
        deadline = time.monotonic() + timeout / 1000.0
        while time.monotonic() < deadline:
            try:
                if speaking_mode_btn.count() > 0 and speaking_mode_btn.first.is_visible():
                    logger.info("Generation complete — Speaking mode button visible")
                    return
            except Exception:
                pass  # element temporarily detached during re-render
            time.sleep(0.5)
        raise TimeoutError(
            f"Generation did not complete within {timeout} ms — "
            "Speaking mode button never appeared"
        )

    def wait_for_input_ready(self, timeout: int = 10000):
        """Wait until the message input is visible and interactable.

        Useful after sending a message when the SPA may navigate to a new
        URL (``/app/chat/{id}?name=...``) and re-render the page.
        """
        self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
        self.message_input.wait_for(state="visible", timeout=timeout)

    def wait_for_message_count(self, expected_count: int, timeout: int = 10000):
        """Wait until the displayed message count reaches *expected_count*.

        Args:
            expected_count: Minimum number of messages expected.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Waiting for message count >= %d", expected_count)
        self.messages_container.nth(expected_count - 1).wait_for(
            state="visible", timeout=timeout,
        )

    def wait_for_navigation(self, url_pattern: str, timeout: int = 10000):
        """Wait for the page URL to match *url_pattern*.

        Args:
            url_pattern: Substring that the URL must contain.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Waiting for URL to contain '%s'", url_pattern)
        self.page.wait_for_url(lambda url: url_pattern in url, timeout=timeout)

    def is_input_empty(self) -> bool:
        """Check if message input is empty.
        
        Returns:
            True if input is empty
        """
        value = self.message_input.input_value()
        return len(value.strip()) == 0
        
    def is_send_button_enabled(self) -> bool:
        """Check if send button is enabled.
        
        Returns:
            True if send button is enabled
        """
        return self.send_button.is_enabled()
        
    @action("Clear chat history")
    def clear_chat_history(self):
        """Click the Clear chat history button."""
        logger.info("Clearing chat history")
        self.clear_history_button.click()
        
    def click_model_selector(self):
        """Click the model selector to open model menu."""
        logger.info("Opening model selector")
        self.model_selector.first.click()
        
    def get_selected_model(self) -> str:
        """Get the currently selected model name.
        
        Returns:
            Model name (e.g., 'GPT-5 mini', 'Claude 4.6')
        """
        model_text = self.model_selector.first.text_content()
        logger.info(f"Selected model: {model_text}")
        return model_text
        
    def open_sidebar(self):
        """Open the sidebar drawer to show full text labels.

        The sidebar has two states:
        - Collapsed: shows only icons (mini-sidebar)
        - Expanded: shows icons + text labels

        The "open drawer" button toggles between these states.
        """
        logger.info("Opening sidebar")
        # Check if already expanded (Agents sidebar item visible with text)
        agents_item = self.page.get_by_test_id("sidebar-item-agents")
        if agents_item.count() > 0 and agents_item.is_visible():
            logger.info("Sidebar already expanded")
            return

        # Click the toggle to expand
        if self.sidebar_toggle.is_visible():
            self.sidebar_toggle.click()
            self.page.wait_for_timeout(300)  # Allow animation

    def close_sidebar(self):
        """Close the sidebar drawer to show only icons (mini-sidebar).

        Clicks the drawer toggle to collapse to icon-only mode.
        """
        logger.info("Closing sidebar")
        # Check if already collapsed
        agents_item = self.page.get_by_test_id("sidebar-item-agents")
        if agents_item.count() == 0 or not agents_item.is_visible():
            logger.info("Sidebar already collapsed")
            return

        # Click the toggle to collapse
        if self.sidebar_toggle.is_visible():
            self.sidebar_toggle.click()
            self.page.wait_for_timeout(300)  # Allow animation
        
    def open_file_chooser(self, timeout: int = 10000):
        """Click the attach button and return the FileChooser dialog.

        Use this when the test needs to inspect chooser properties (e.g.
        ``is_multiple()``) before selecting files.  For the common case of
        just attaching a file, call ``attach_file()`` instead.

        Args:
            timeout: Maximum wait for the file chooser to appear (ms).

        Returns:
            playwright.sync_api.FileChooser
        """
        with self.page.expect_file_chooser(timeout=timeout) as fc_info:
            self.attach_files_button.click()
        return fc_info.value

    @action("Attach file")
    def attach_file(self, file_path: str, timeout: int = 10000):
        """Attach a file to the message.

        Clicks the attach button, waits for the OS file chooser, selects
        the file, then waits for the upload network activity to settle.

        Args:
            file_path: Absolute or relative path to the file to attach.
            timeout: Maximum wait for the file chooser to appear (ms).
        """
        logger.info("Attaching file: %s", file_path)
        file_chooser = self.open_file_chooser(timeout=timeout)
        file_chooser.set_files(file_path)
        self.wait_for_network(timeout=timeout)
        
    @action("Copy message")
    def copy_message(self, message_index: int = -1):
        """Copy a message to clipboard.

        Hovers over the target message to reveal action buttons, then clicks
        the copy button within that message. Waits for the clipboard operation
        to complete.

        Args:
            message_index: Index of message to copy (-1 for last)
        """
        logger.info(f"Copying message at index {message_index}")

        # Get the target message block
        message_block = self.messages_container.nth(message_index)
        message_block.scroll_into_view_if_needed()

        # Hover over the message to reveal action buttons
        message_block.hover()
        self.page.wait_for_timeout(500)  # Wait for hover effect

        # Find and click the copy button within this message
        copy_button = message_block.get_by_test_id("chat-message-copy")
        if copy_button.count() == 0:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            raise PlaywrightTimeoutError(
                f"No copy button found on message at index {message_index}"
            )
        copy_button.first.click()

        # Wait for clipboard API to complete (async operation)
        self.page.wait_for_timeout(500)
        logger.info("Copy to clipboard completed")

    @action("Delete message")
    def delete_message(self, message_index: int = -1):
        """Delete a message by hovering over it and clicking the delete button.

        The delete button has NO aria-label. It's a button inside a generic
        container with text "Delete". The button only becomes visible on hover
        over the message. After clicking, a confirmation dialog appears.

        Args:
            message_index: Index of message to delete (-1 for last)
        """
        logger.info(f"Deleting message at index {message_index}")

        # Get the target message block
        message_block = self.messages_container.nth(message_index)
        message_block.scroll_into_view_if_needed()

        # Hover over the message to reveal action buttons
        message_block.hover()
        self.page.wait_for_timeout(500)  # Wait for hover effect

        # Find the delete button within this message
        # The delete button structure:
        # - It's the 3rd button after Copy and Regenerate buttons
        # - Inside a generic with accessible name "Delete"
        # - Has NO aria-label attribute

        # Find the delete button using its testid within this message block
        delete_button = message_block.get_by_test_id("chat-message-delete")
        if delete_button.count() == 0:
            # Relative scoping: last button in the message (Delete is always last)
            delete_button = message_block.locator('button').last

        # Click the delete button
        delete_button.click(force=True)
        logger.info("Clicked delete button")

        # Handle the confirmation dialog
        dialog = Dialog.wait_for(self.page, timeout=5000)
        Dialog.click_button(dialog, "Confirm")
        logger.info("Confirmed message deletion")

        # Wait for deletion to complete
        self.page.wait_for_timeout(1000)
        
    @action("Regenerate response")
    def regenerate_response(self):
        """Click regenerate button on last AI message."""
        logger.info("Regenerating AI response")
        self.regenerate_button.click()
        
    @action("Search participants")
    def search_participants_with_hash(self, query: str):
        """Use # to search for participants to add.

        Types ``#query`` into the message input and waits for a dropdown.

        Args:
            query: Search query after #

        Raises:
            TimeoutError: If no dropdown appears within 5 seconds.
        """
        logger.info(f"Searching participants with #{query}")
        self.message_input.fill(f"#{query}")
        # Wait for search results panel
        self.page.get_by_test_id("chat-participant-search-panel").wait_for(
            state="visible", timeout=5000
        )
        
    @action("Select participant")
    def select_participant_from_search(self, participant_name: str):
        """Select a participant from # search results.

        Args:
            participant_name: Name of participant to select
        """
        logger.info(f"Selecting participant: {participant_name}")
        option = self.page.get_by_test_id("chat-participant-search-panel").get_by_test_id(
            "chat-participant-option"
        ).filter(has_text=participant_name).first
        option.click()
        
    def edit_context_settings(self):
        """Open context settings dialog."""
        logger.info("Opening context settings")
        self.edit_context_button.click()
        
    def toggle_internal_tools(self):
        """Toggle internal tools checkbox."""
        logger.info("Toggling internal tools")
        self.internal_tools_toggle.click()

    def close_open_dialogs(self):
        """Close any open dialogs or modals by pressing Escape."""
        dialog = self.page.get_by_test_id("dialog-container")
        if dialog.count() > 0:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)

    def wait_for_model_menu(self, timeout: int = 5000):
        """Wait for model selector menu to appear after clicking.

        Returns the menu locator.
        """
        menu = self.page.get_by_test_id("model-selector-menu")
        menu.wait_for(state="visible", timeout=timeout)
        return menu

    def wait_for_hash_search_dropdown(self, timeout: int = 5000):
        """Wait for # mention search results panel to appear.

        Returns the search results panel locator or raises TimeoutError.
        """
        search_results = self.page.get_by_test_id("chat-participant-search-panel")
        search_results.wait_for(state="visible", timeout=timeout)
        return search_results

    def get_hash_search_first_option(self):
        """Get the first clickable option from hash search results.

        Returns the first clickable participant option locator or None if no options.
        """
        panel = self.page.get_by_test_id("chat-participant-search-panel")
        if panel.count() == 0:
            return None
        options = panel.get_by_test_id("chat-participant-option")
        if options.count() > 0:
            return options.first
        return None

    def is_hash_search_dropdown_visible(self) -> bool:
        """Check if the # mention search results panel is currently visible.

        Returns:
            True if the search results panel is visible, False if it has closed.
        """
        panel = self.page.get_by_test_id("chat-participant-search-panel")
        return panel.count() > 0 and panel.first.is_visible()

    def wait_for_search_dialog(self, timeout: int = 5000):
        """Wait for search conversations input to appear.

        Returns the search input locator.
        """
        search_input = self.page.get_by_test_id("search-conversations-input")
        search_input.wait_for(state="visible", timeout=timeout)
        return search_input

    def wait_for_sidebar_expanded(self, timeout: int = 5000):
        """Wait for sidebar to expand and show full labels."""
        self.page.get_by_test_id("sidebar-item-agents").wait_for(state="visible", timeout=timeout)

    def has_error_notification(self) -> bool:
        """Check if an error notification is present on the page.

        Returns:
            True if error notification visible, False otherwise.
        """
        error = self.page.get_by_test_id("error-notification")
        return error.count() > 0 and error.first.is_visible()

    def open_search_conversations(self):
        """Open search conversations via the Search conversations button."""
        logger.info("Opening search conversations via button")
        search_btn = self.page.get_by_test_id("conversation-search-button")
        search_btn.wait_for(state="visible", timeout=5000)
        search_btn.click()

    def navigate_to_agents(self):
        """Navigate to Agents page via the sidebar drawer."""
        logger.info("Navigating to Agents")
        self.open_sidebar()
        agents_btn = self.page.get_by_test_id("sidebar-item-agents")
        agents_btn.wait_for(state="visible", timeout=5000)
        agents_btn.click()

    # ------------------------------------------------------------------
    # Conversation management helpers
    # ------------------------------------------------------------------

    @action("Create new conversation")
    def click_create_conversation(self, timeout: int = 10000):
        """Click the "+ Conversation" button in the sidebar.

        Uses data-tour attribute locator for reliability across UI versions.
        The button shows "+ Conversation" with a dropdown chevron.

        LOCATOR: [data-tour="sidebar-create-button"] button:has-text("Conversation")

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking +Conversation button")
        btn = self.page.get_by_test_id("create-conversation-button")
        btn.wait_for(state="visible", timeout=timeout)
        btn.click(force=True)
        # Wait for the "Creating conversation..." state to finish
        self.page.wait_for_timeout(1000)
        self.wait_for_network(timeout=timeout)
        # The message input should become available in the new conversation
        self.message_input.wait_for(state="visible", timeout=timeout)
        logger.info("New conversation created, URL: %s", self.page.url)

    @action("Create new conversation")
    def click_create_new_conversation(self, timeout: int = 10000):
        """Click the "+Conversation" button in the sidebar.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking +Conversation button")
        btn = self.page.get_by_test_id("create-conversation-button")
        btn.wait_for(state="visible", timeout=timeout)
        btn.click(force=True)
        self.page.wait_for_timeout(1000)
        self.wait_for_network(timeout=timeout)
        self.message_input.wait_for(state="visible", timeout=timeout)
        logger.info("New conversation created, URL: %s", self.page.url)

    def get_conversation_list_items(self):
        """Return a Playwright locator for conversation items in the sidebar list.

        Each conversation is rendered as a <button> element that is a direct
        child of the conversation list container.  That container also holds
        date-group headers (h6 elements like "Today", "Yesterday") as siblings.

        The selector ``:has(h6) > button`` exploits this structural relationship:
        - ``:has(h6)`` — the list container that holds at least one date-group heading
        - ``> button`` — direct-child conversation item buttons only

        This avoids brittle CSS class names (which are MUI-generated and change
        between builds) and correctly excludes toolbar buttons (which are nested
        deeper or have aria-label attributes).
        """
        return self.page.get_by_test_id("conversation-item")

    def get_conversation_names(self, timeout: int = 5000) -> list[str]:
        """Return the names of all conversations visible in the sidebar list.

        Uses the same locator as get_conversation_list_items() to ensure consistency.

        Args:
            timeout: Time to wait for at least one item to appear.

        Returns:
            List of conversation name strings (may be empty).
        """
        items = self.get_conversation_list_items()
        try:
            items.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            logger.info("No conversation items visible in list")
            return []
        
        names = []
        for i in range(items.count()):
            try:
                text = items.nth(i).text_content().strip()
                if text:
                    names.append(text)
            except Exception as e:
                logger.debug(f"Failed to extract text from item {i}: {e}")
                continue
        
        logger.info(f"Found {len(names)} conversation(s): {names}")
        return names

    @action("Select conversation")
    def select_conversation_from_list(self, name: str, timeout: int = 5000):
        """Click a conversation in the sidebar list by its name.

        Uses ``force=True`` because MUI overlay divs (``css-1pybsfx``)
        can intercept pointer events in the conversations panel.

        Args:
            name: The conversation name to click.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Selecting conversation: %s", name)
        item = self.page.get_by_test_id("conversation-item").filter(has_text=name).first
        item.wait_for(state="visible", timeout=timeout)
        item.click(force=True)
        self.wait_for_network(timeout=timeout)

    @action("Select conversation by ID")
    def select_conversation_by_id(self, conversation_id: str | int, timeout: int = 5000):
        """Click a conversation in the sidebar list by its numeric ID.
        
        This is more reliable than name-based selection because conversation names
        can be auto-renamed after the first message is sent.
        
        Attempts multiple strategies:
        1. Look for data-conversation-id or similar attributes
        2. Look for href containing /app/chat/{id}
        3. Fallback: extract ID from all visible conversations and match
        
        Args:
            conversation_id: Numeric conversation ID (can be string or int).
            timeout: Maximum wait time in milliseconds.
            
        Raises:
            AssertionError: If conversation with given ID is not found.
        """
        conv_id = str(conversation_id)
        logger.info("Selecting conversation by ID: %s", conv_id)
        
        # Strategy 1: Look for conversation-item with data-conversation-id
        item = self.page.get_by_test_id("conversation-item").filter(
            has=self.page.locator(f'[data-conversation-id="{conv_id}"]')
        ).first

        if item.count() > 0:
            logger.info("Found conversation via data-conversation-id attribute")
            item.wait_for(state="visible", timeout=timeout)
            item.click(force=True)
            self.wait_for_network(timeout=timeout)
            return

        # Strategy 2: Find conversation item by href containing the id
        item = self.page.get_by_test_id("conversation-item").filter(
            has=self.page.locator(f'[href*="/app/chat/{conv_id}"]')
        ).first
        if item.count() == 0:
            # Direct anchor element with href
            item = self.page.get_by_test_id("conversation-item").filter(
                has=self.page.locator(f'[href*="{conv_id}"]')
            ).first
        if item.count() > 0:
            logger.info("Found conversation via href attribute")
            item.wait_for(state="visible", timeout=timeout)
            item.click(force=True)
            self.wait_for_network(timeout=timeout)
            return
        
        raise AssertionError(
            f"Could not find conversation with ID {conv_id} in the sidebar. "
            "The conversation list may not have loaded, or the ID doesn't match any visible conversation."
        )

    def conversation_exists_in_list(self, name: str, timeout: int = 3000) -> bool:
        """Check whether a conversation with *name* is visible in the sidebar.

        Uses ``:has-text()`` for partial matching because conversation
        names may be truncated with "..." in the sidebar.

        Args:
            name: Conversation name (or prefix) to look for.
            timeout: How long to wait for it to appear.

        Returns:
            True if the conversation is visible, False otherwise.
        """
        try:
            self.page.get_by_test_id("conversation-item").filter(has_text=name).first.wait_for(
                state="visible", timeout=timeout,
            )
            return True
        except Exception:
            return False

    def open_search_conversations_button(self, timeout: int = 5000):
        """Click the search conversations icon/button in the conversations sidebar.

        The search button appears as an icon in the conversations panel header.
        Uses data-testid="conversation-search-button" (ConversationSearchButton component).

        A banner overlay (z-index 1200) may cover the button on first load,
        so we dismiss it before clicking.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Opening search conversations via button")
        self.dismiss_banner_if_present()
        search_btn = self.page.get_by_test_id("conversation-search-button")
        search_btn.wait_for(state="visible", timeout=timeout)
        search_btn.click()

    def search_conversations_via_button(self, query: str, timeout: int = 5000):
        """Open the search dialog and type a query.

        Args:
            query: Text to type into the search input.
            timeout: Maximum wait time in milliseconds.
        """
        self.open_search_conversations_button(timeout=timeout)
        search_input = self.page.get_by_test_id("search-conversations-input")
        search_input.wait_for(state="visible", timeout=timeout)
        search_input.fill(query)
        logger.info("Searched conversations for: %s", query)

    def delete_conversation_ui(self, timeout: int = 5000):
        """Delete the current conversation via the UI three-dot / delete button.

        Looks for a delete button inside the conversations panel context
        menu or action buttons, then confirms the deletion dialog.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Deleting conversation via UI")
        delete_btn = self.page.get_by_test_id("conversation-delete-button")
        delete_btn.first.wait_for(state="visible", timeout=timeout)
        delete_btn.first.click()

        # Handle confirmation dialog
        dialog = Dialog.wait_for(self.page, timeout=timeout)
        Dialog.click_first_button(dialog, "Confirm", "Delete")
        self.wait_for_network(timeout=timeout)
        logger.info("Conversation deleted via UI")

    def open_conversation_menu(self, conv_name: str = None, timeout: int = 5000):
        """Open the three-dot context menu on a conversation list item.

        Hovers the conversation item to reveal the hidden menu button,
        then clicks it via JS (to bypass MUI overlay).  If *conv_name*
        is ``None``, operates on the first conversation in the list.

        Args:
            conv_name: Name of the conversation to target.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Opening conversation menu for: %s", conv_name or "(first)")
        if conv_name:
            item = self.page.get_by_test_id("conversation-item").filter(has_text=conv_name).first
        else:
            item = self.page.get_by_test_id("conversation-item").first
        item.wait_for(state="visible", timeout=timeout)
        item.hover()
        self.page.wait_for_timeout(500)

        # Click the three-dot button — scoped to the conversation item
        menu_btn = item.get_by_test_id("conversation-menu-button")
        menu_btn.wait_for(state="attached", timeout=timeout)
        menu_btn.evaluate("el => el.click()")
        self.page.wait_for_timeout(300)
        logger.info("Conversation context menu opened")

    @action("Rename conversation")
    def rename_conversation_via_menu(
        self, new_name: str, conv_name: str = None, timeout: int = 5000,
    ):
        """Rename a conversation using the three-dot → Edit flow.

        Opens the context menu, clicks *Edit*, clears the inline input,
        types *new_name*, and presses Enter to confirm.

        Args:
            new_name: The new conversation name.
            conv_name: Current name of the conversation (``None`` = first).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Renaming conversation to '%s'", new_name)
        self.open_conversation_menu(conv_name, timeout=timeout)

        # Click "Edit" menu item
        self.page.get_by_test_id("conversation-menu-edit-item").click()
        self.page.wait_for_timeout(500)

        # Find the inline rename input
        rename_input = self.page.get_by_test_id("conversation-rename-input")
        rename_input.wait_for(state="visible", timeout=timeout)
        rename_input.clear()
        rename_input.fill(new_name)
        rename_input.press("Enter")
        self.page.wait_for_timeout(500)
        self.wait_for_network(timeout=timeout)
        logger.info("Conversation renamed to '%s'", new_name)

    @action("Delete conversation")
    def delete_conversation_via_menu(
        self, conv_name: str = None, timeout: int = 5000,
    ):
        """Delete a conversation via three-dot → Delete → confirm dialog.

        Args:
            conv_name: Name of the conversation to delete (``None`` = first).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Deleting conversation via three-dot menu: %s", conv_name or "(first)")
        self.open_conversation_menu(conv_name, timeout=timeout)

        # Click "Delete" menu item
        self.page.get_by_test_id("conversation-menu-delete-item").click()

        # Handle confirmation dialog
        dialog = Dialog.wait_for(self.page, timeout=timeout)
        Dialog.click_button(dialog, "Delete")
        self.wait_for_network(timeout=timeout)
        logger.info("Conversation deleted via menu")

    def click_create_folder(self, timeout: int = 5000):
        """Click the "Create folder" button in the Conversations panel.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking Create folder")
        btn = self.page.get_by_test_id("create-folder-button")
        btn.wait_for(state="visible", timeout=timeout)
        btn.click()

    def get_delete_button_count(self) -> int:
        """Get count of delete message buttons visible on the page.

        Returns:
            Number of delete buttons found
        """
        delete_btns = self.page.get_by_test_id("chat-message-delete")
        count = delete_btns.count()
        logger.info(f"Delete button count: {count}")
        return count

    def wait_for_conversation_url(self, conv_id: str, timeout: int = 10000):
        """Wait for URL to reflect the conversation ID.

        Args:
            conv_id: Conversation ID to wait for in URL
            timeout: Maximum wait time in milliseconds
        """
        logger.info(f"Waiting for URL to contain /app/chat/{conv_id}")
        self.page.wait_for_url(
            lambda url: f"/app/chat/{conv_id}" in url,
            timeout=timeout
        )

    def wait_for_naming_label_to_resolve(self, timeout: int = 10000):
        """Wait for 'Naming' placeholder to be replaced with actual title.

        After creating a conversation, the backend asynchronously generates
        a title based on the first message. The UI shows "Naming" as a
        placeholder until this completes.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Waiting for 'Naming' label to resolve to actual title")
        naming_label = self.page.get_by_test_id("conversation-naming-placeholder")
        if naming_label.count() > 0:
            try:
                naming_label.first.wait_for(state="hidden", timeout=timeout)
                logger.info("Naming label resolved")
            except Exception as e:
                logger.info(f"Naming label did not resolve within timeout: {e}")

    def get_conversation_link_count(self) -> int:
        """Get count of conversation items in the sidebar list.

        Delegates to get_conversation_list_items() which locates role="button"
        elements inside the conversationList panel.

        Returns:
            Number of conversation items found
        """
        items = self.get_conversation_list_items()
        count = items.count()
        logger.info(f"Conversation link count: {count}")
        return count

    def get_conversation_link_titles(self, limit: int = 5) -> list[str]:
        """Get titles of conversations in sidebar (first N items).

        Returns text content of conversation list items, useful for verifying
        titles are not stuck on placeholder values like "Naming".

        Args:
            limit: Maximum number of titles to return

        Returns:
            List of conversation title strings
        """
        items = self.get_conversation_list_items()
        count = min(items.count(), limit)
        titles = [items.nth(i).text_content() or "" for i in range(count)]
        logger.info(f"Conversation link titles (first {limit}): {titles}")
        return titles

    def wait_for_conversations_to_load(self, timeout: int = 5000) -> bool:
        """Wait for at least one conversation to appear in sidebar.

        Returns True if conversations loaded, False if not available.
        Used to verify the conversation list populates after actions.

        Args:
            timeout: Maximum wait time in milliseconds

        Returns:
            True if conversations loaded, False otherwise
        """
        logger.info("Waiting for conversations to load in sidebar")
        items = self.get_conversation_list_items()
        try:
            items.first.wait_for(state="attached", timeout=timeout)
            logger.info("Conversations loaded")
            return True
        except Exception:
            logger.info("No conversations loaded within timeout")
            return False

    def click_delete_menu_item(self):
        """Click Delete menu item in conversation context menu.

        Must be called after open_conversation_menu() has been used
        to reveal the context menu.
        """
        logger.info("Clicking Delete menu item")
        self.page.get_by_test_id("conversation-menu-delete-item").click()

    # ------------------------------------------------------------------
    # Internal Tools / Image Creation
    # ------------------------------------------------------------------

    def open_internal_tools_menu(self, timeout: int = 5000):
        """Open the internal tools panel via plus menu → Internal Tools.

        In v2.0.3+, internal tools are accessed through the plus menu dropdown.
        Clicks plus menu, then "Internal Tools" menuitem to reveal the tools
        panel with toggles for Image creation, Data Analysis, Planner, etc.

        Args:
            timeout: Maximum wait time in milliseconds

        Raises:
            FeatureNotAvailableError: If the plus menu or Internal Tools menuitem
                is not visible
        """
        logger.info("Opening internal tools menu via plus menu")

        # Step 1: Open plus menu
        if not self.plus_menu_button.is_visible():
            raise FeatureNotAvailableError(
                "Plus menu button not visible — feature may not be available "
                "in current UI version"
            )
        self.plus_menu_button.wait_for(state="visible", timeout=timeout)
        self.plus_menu_button.click()
        self.page.wait_for_timeout(300)  # Menu animation

        # Step 2: Click "Internal Tools" menuitem
        self.internal_tools_menuitem.wait_for(state="visible", timeout=timeout)
        self.internal_tools_menuitem.click()

        # Wait for the tools panel with switches to appear
        self.page.get_by_test_id("internal-tools-panel").wait_for(
            state="visible", timeout=timeout
        )
        logger.info("Internal tools menu opened")

    def get_visible_switch_count(self) -> int:
        """Count visible toggle switches in internal tools panel.

        Use after open_internal_tools_menu() to verify expected tool count.

        Returns:
            Number of visible switch elements
        """
        return self.page.get_by_test_id("internal-tools-panel").locator('[role="switch"]').count()

    @action("Enable image creation")
    def enable_image_creation(self, timeout: int = 5000):
        """Enable the Image creation toggle in internal tools menu.

        Opens the internal tools menu if not already open, then enables
        the Image creation switch.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Enabling Image creation")

        # Check if menu is already open by looking for the panel
        image_switch = self.page.get_by_test_id("internal-tool-image-creation-switch")
        if image_switch.count() == 0:
            self.open_internal_tools_menu(timeout=timeout)
            image_switch = self.page.get_by_test_id("internal-tool-image-creation-switch")

        image_switch.wait_for(state="visible", timeout=timeout)

        # Check if already enabled (checked attribute)
        is_checked = image_switch.is_checked()
        if not is_checked:
            image_switch.click()
            logger.info("Image creation enabled")
        else:
            logger.info("Image creation was already enabled")

        # Close the menu by clicking elsewhere
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

    @action("Disable image creation")
    def disable_image_creation(self, timeout: int = 5000):
        """Disable the Image creation toggle in internal tools menu.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Disabling Image creation")

        image_switch = self.page.get_by_test_id("internal-tool-image-creation-switch")
        if image_switch.count() == 0:
            self.open_internal_tools_menu(timeout=timeout)
            image_switch = self.page.get_by_test_id("internal-tool-image-creation-switch")

        image_switch.wait_for(state="visible", timeout=timeout)

        is_checked = image_switch.is_checked()
        if is_checked:
            image_switch.click()
            logger.info("Image creation disabled")
        else:
            logger.info("Image creation was already disabled")

        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

    def is_image_creation_enabled(self, timeout: int = 5000) -> bool:
        """Check if Image creation toggle is enabled.

        Args:
            timeout: Maximum wait time in milliseconds

        Returns:
            True if Image creation is enabled, False otherwise
        """
        image_switch = self.page.get_by_test_id("internal-tool-image-creation-switch")
        if image_switch.count() == 0:
            self.open_internal_tools_menu(timeout=timeout)
            image_switch = self.page.get_by_test_id("internal-tool-image-creation-switch")

        image_switch.wait_for(state="visible", timeout=timeout)
        is_checked = image_switch.is_checked()

        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

        return is_checked

    @action("Select model")
    def select_model(self, model_name: str, timeout: int = 5000):
        """Select a specific LLM model from the model selector.

        Args:
            model_name: Name of the model to select (e.g., "GPT-5.2", "Claude 4.6 Sonnet")
            timeout: Maximum wait time in milliseconds
        """
        logger.info(f"Selecting model: {model_name}")

        # Click the model selector to open the dropdown
        self.model_selector.first.click()

        # Wait for menu to appear
        menu = self.page.get_by_test_id("model-selector-menu")
        menu.wait_for(state="visible", timeout=timeout)

        # Find and click the model option
        model_option = menu.get_by_test_id(f"model-option-{model_name.lower().replace(' ', '-').replace('.', '-')}")
        if model_option.count() == 0:
            model_option = menu.locator(f'[role="menuitem"]:has-text("{model_name}")')
        model_option.wait_for(state="visible", timeout=timeout)
        model_option.click()

        # Wait for menu to close and selection to apply
        self.page.wait_for_timeout(500)
        logger.info(f"Model '{model_name}' selected")

    def get_images_in_last_message(self) -> int:
        """Get count of generated images in the last message.

        Returns:
            Number of meaningful images (> 50px) in the last message,
            excluding small UI elements like the sender avatar.
        """
        last_msg = self.messages_container.last
        images = last_msg.locator('img:not([alt="EliteaStage"]):not([class*="avatar"])')
        count = sum(
            1 for i in range(images.count())
            if (box := images.nth(i).bounding_box()) and box["width"] > 50 and box["height"] > 50
        )
        logger.info(f"Found {count} images in last message")
        return count

    def wait_for_image_in_response(self, timeout: int = 60000):
        """Wait for a generated image in the last AI message, failing fast if generation ends without one.

        Uses native browser-side polling (wait_for_function, 100ms interval). Returns as soon
        as an image is found. If the send button re-enables with no image, raises AssertionError
        immediately rather than waiting out the full timeout.

        Avatar images (alt='Elitea' / alt='EliteaStage') are excluded.

        Args:
            timeout: Maximum wait time in milliseconds

        Raises:
            AssertionError: If AI finished responding with no image in last message
            TimeoutError: If timeout is reached before either condition
        """
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        logger.info("Waiting for image in last AI message (timeout=%dms)...", timeout)
        try:
            handle = self.page.wait_for_function(
                """() => {
                    const msgs = document.querySelectorAll(
                        'main ul.MuiList-root > li.MuiListItem-root'
                    );
                    if (!msgs.length) return null;
                    const lastMsg = msgs[msgs.length - 1];

                    // Non-avatar image present — success
                    for (const img of lastMsg.querySelectorAll('img')) {
                        const alt = img.alt || '';
                        if (alt !== 'Elitea' && alt !== 'EliteaStage' && img.src?.length > 0) {
                            return 'image';
                        }
                    }

                    // Fail fast: send button enabled means generation is complete
                    // Use multiple selectors with case-insensitive aria-label match
                    const btn = document.querySelector(
                        '[data-testid="chat-send-button"], button[aria-label*="send" i], button[type="submit"]'
                    );
                    if (btn && !btn.disabled && btn.getAttribute('aria-disabled') !== 'true') {
                        return 'done';
                    }

                    return null;
                }""",
                timeout=timeout,
            )
        except PlaywrightTimeoutError:
            raise TimeoutError(f"No image appeared in response within {timeout}ms")

        result = handle.json_value()
        if result == "image":
            logger.info("Image found in last AI message")
        elif result == "done":
            raise AssertionError("AI finished responding but no image found in last message")

    def get_generated_image_src(self) -> str | None:
        """Get the source URL of the generated image in the last message.

        Skips small UI elements (like the sender avatar, which is < 50px) and
        returns the src of the first large image (width > 50px AND height > 50px).

        Returns:
            Image source URL or None if no generated image found
        """
        last_msg = self.messages_container.last
        images = last_msg.locator('img:not([alt="EliteaStage"]):not([class*="avatar"])')
        for i in range(images.count()):
            img = images.nth(i)
            box = img.bounding_box()
            if box and box["width"] > 50 and box["height"] > 50:
                src = img.get_attribute("src")
                logger.info(f"Generated image src: {src[:50] if src else 'None'}...")
                return src
        return None

    # ------------------------------------------------------------------
    # Participants Panel helpers
    # ------------------------------------------------------------------

    def is_participants_panel_expanded(self) -> bool:
        """Return True if the Participants panel is expanded (showing full content).

        In v2.0.3+, the Participants panel is collapsed by default. When collapsed,
        only a narrow strip with icons is visible. When expanded, the full
        "Participants" title and "Context Budget" section are visible.

        Returns:
            True if the panel is expanded (Participants title is visible).
        """
        participants_title = self.page.get_by_test_id("participants-panel-title")
        return participants_title.count() > 0 and participants_title.first.is_visible()

    def expand_participants_panel(self, timeout: int = 5000) -> bool:
        """Expand the Participants panel if it's currently collapsed.

        In v2.0.3+, the Participants panel is collapsed by default per AC2.
        This method finds and clicks the expand button (DoubleLeftIcon) to
        show the full panel with Context Budget.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if panel is now expanded, False if expand button not found.
        """
        if self.is_participants_panel_expanded():
            logger.info("Participants panel already expanded")
            return True

        logger.info("Attempting to expand Participants panel...")

        # The expand button is in the collapsed panel area on the right side.
        expand_btn = self.page.get_by_test_id("participants-panel-expand-button")
        try:
            expand_btn.first.wait_for(state="visible", timeout=timeout)
            expand_btn.first.click()
            self.page.wait_for_timeout(500)  # Wait for animation
            if self.is_participants_panel_expanded():
                logger.info("Successfully expanded Participants panel")
                return True
        except Exception:
            pass

        logger.warning("Could not find Participants panel expand button")
        return False

    def collapse_participants_panel(self, timeout: int = 5000) -> bool:
        """Collapse the Participants panel if it's currently expanded.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if panel is now collapsed, False if collapse button not found.
        """
        if not self.is_participants_panel_expanded():
            logger.info("Participants panel already collapsed")
            return True

        logger.info("Attempting to collapse Participants panel...")

        # The collapse button is next to the "Participants" title
        collapse_btn = self.page.get_by_test_id("participants-panel-collapse-button")
        if collapse_btn.count() > 0:
            collapse_btn.first.click()
            self.page.wait_for_timeout(500)  # Wait for animation
            if not self.is_participants_panel_expanded():
                logger.info("Successfully collapsed Participants panel")
                return True

        logger.warning("Could not find Participants panel collapse button")
        return False

    # ------------------------------------------------------------------
    # Context Budget helpers
    # ------------------------------------------------------------------

    def is_context_budget_panel_visible(self) -> bool:
        """Return True if the Context Budget panel is visible in the sidebar.

        The panel only appears after at least one message has been sent in
        the conversation.

        Returns:
            True if the Context Budget heading is visible.
        """
        budget_panel = self.page.get_by_test_id("context-budget-panel")
        visible = budget_panel.count() > 0 and budget_panel.first.is_visible()
        logger.info("Context Budget panel visible: %s", visible)
        return visible

    def wait_for_context_budget_panel(self, timeout: int = 10000) -> None:
        """Wait until the Context Budget panel becomes visible.

        In v2.0.3+, the Participants panel (containing Context Budget) is
        collapsed by default. This method will automatically expand the panel
        if needed before waiting for the Context Budget heading.

        Should be called after sending the first message in a conversation.

        Args:
            timeout: Maximum wait time in milliseconds.

        Raises:
            TimeoutError: If the panel does not appear within *timeout*.
        """
        logger.info("Waiting for Context Budget panel to appear...")

        # First, expand the Participants panel if it's collapsed (v2.0.3+ behavior)
        if not self.is_participants_panel_expanded():
            logger.info("Participants panel is collapsed, expanding it first...")
            self.expand_participants_panel(timeout=timeout // 2)

        budget_panel = self.page.get_by_test_id("context-budget-panel")
        budget_panel.wait_for(state="visible", timeout=timeout)
        logger.info("Context Budget panel is visible")

    def get_context_budget_tokens_text(self) -> str:
        """Return the raw tokens display string from the Context Budget panel.

        The text has the format ``"22 / 64 000 tokens"`` (may include spaces
        in the number for locale formatting).

        Returns:
            Raw text of the token usage line (e.g. ``"22 / 64 000 tokens"``).

        Raises:
            TimeoutError: If the panel is not visible.
        """
        # Find the token display inside the Context Budget panel
        token_locator = self.page.get_by_test_id("context-budget-tokens")
        text = token_locator.first.text_content() or ""
        logger.info("Context Budget tokens display: %r", text)
        return text.strip()

    def get_context_budget_max_tokens(self) -> int:
        """Parse and return the max-tokens value from the Context Budget panel.

        Extracts the second number from ``"22 / 64 000 tokens"``-style text,
        stripping spaces used as thousands separators.

        Returns:
            Max token limit as integer (e.g. 64000 from ``"22 / 64 000 tokens"``).

        Raises:
            ValueError: If the text cannot be parsed.
        """
        text = self.get_context_budget_tokens_text()
        # Format: "N / M tokens" where M may contain spaces (locale thousands sep)
        # e.g. "22 / 64 000 tokens" → max=64000
        # Note: May contain narrow no-break space (\u202f) or regular space
        try:
            after_slash = text.split("/")[1]  # " 64 000 tokens"
            numeric_part = after_slash.replace("tokens", "").strip()  # "64 000"
            # Remove all whitespace characters including Unicode spaces
            cleaned = re.sub(r"[\s\u00a0\u202f,]+", "", numeric_part)
            max_tokens = int(cleaned)
            logger.info("Parsed max tokens from Context Budget: %d", max_tokens)
            return max_tokens
        except (IndexError, ValueError) as exc:
            raise ValueError(
                f"Cannot parse max tokens from Context Budget text: {text!r}"
            ) from exc

    def open_add_teammate_dialog(self, timeout: int = 5000) -> tuple[bool, str]:
        """Open the 'Invite Users' dialog via the plus menu.

        In v2.0.3+, adding teammates/users is done via the plus menu → "Invite Users"
        option. This option is ONLY available in Team Projects (not Private Projects).

        Per story #5188 AC3: "Adding Participants is Only Allowed via the `+` Icon"
        The "Invite Users" menuitem only appears when:
        - The project is a Team Project (not Private)
        - The user has permission to invite others

        Args:
            timeout: Maximum wait time in milliseconds

        Returns:
            Tuple of (success: bool, reason: str)
            - (True, "") if dialog opened successfully
            - (False, reason) if feature not available with explanation
        """
        logger.info("Attempting to open Invite Users dialog via plus menu")

        # Open the plus menu
        plus_menu = self.page.get_by_test_id("plus-menu-button")
        if not plus_menu.is_visible():
            return (False, "Plus menu button not visible")

        plus_menu.click()
        self.page.wait_for_timeout(500)

        # Look for "Invite Users" menuitem in the plus menu
        invite_users = self.page.get_by_test_id("invite-users-menuitem")

        if invite_users.count() == 0:
            # Close the menu
            self.page.keyboard.press("Escape")
            logger.info("'Invite Users' not found in plus menu — likely a Private Project")
            return (False, "Invite Users option not available — this feature is only available in Team Projects, not Private Projects (per story #5188)")

        if not invite_users.is_enabled():
            self.page.keyboard.press("Escape")
            logger.info("'Invite Users' is disabled — user may not have permission")
            return (False, "Invite Users option is disabled — user may not have invite permissions")

        invite_users.click()
        self.page.wait_for_timeout(500)

        # Wait for the invite users dialog
        picker = self.page.get_by_test_id("invite-users-dialog")
        try:
            picker.first.wait_for(state="visible", timeout=timeout)
            logger.info("Invite Users dialog opened")
            return (True, "")
        except Exception as e:
            logger.warning(f"Invite Users dialog did not appear: {e}")
            return (False, f"Dialog did not appear after clicking Invite Users: {e}")

    # ------------------------------------------------------------------
    # Participant management helpers
    # ------------------------------------------------------------------

    def wait_for_add_agent_button(self, timeout: int = 15000) -> None:
        """Wait for the 'plus menu' button to be visible (entry point for adding agents)."""
        self.page.get_by_test_id("plus-menu-button").wait_for(state="visible", timeout=timeout)

    @action("Add agent participant")
    def add_agent_participant(self, agent_name_prefix: str, timeout: int = 10000):
        """Add an agent as a chat participant via the plus menu → Agents flow.

        Opens the plus menu, clicks 'Agents', searches for agents whose name starts with
        *agent_name_prefix*, selects the first result, and waits for the agent to be added.

        Args:
            agent_name_prefix: Search prefix (e.g. "autotest_")
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Adding agent participant with prefix '%s'", agent_name_prefix)

        # Step 1: Open plus menu
        plus_btn = self.page.get_by_test_id("plus-menu-button")
        plus_btn.wait_for(state="visible", timeout=timeout)
        plus_btn.click(force=True)
        self.page.wait_for_timeout(300)  # Menu animation

        # Step 2: Click "Agents" menuitem
        agents_menu = self.page.get_by_test_id("plus-menu-agents-menuitem")
        agents_menu.wait_for(state="visible", timeout=timeout)
        agents_menu.click()
        self.page.wait_for_timeout(300)  # Submenu animation

        # Step 3: Search for agent in the search input
        search_input = self.page.get_by_test_id("agent-search-input")
        search_input.wait_for(state="visible", timeout=timeout)
        search_input.click()
        search_input.press_sequentially(agent_name_prefix, delay=50)
        self.page.wait_for_timeout(500)  # Search debounce

        # Step 4: Select the agent from results
        agent_item = self.page.get_by_test_id("agent-search-result-item").filter(has_text=agent_name_prefix).first
        agent_item.wait_for(state="visible", timeout=timeout)
        agent_item.click()

        # Wait for the API write to complete
        self.wait_for_network(timeout=timeout)

        logger.info("Agent added as chat participant")

    @action("Add toolkit participant")
    def add_toolkit_participant(self, toolkit_name: str, timeout: int = 10000):
        """Add a toolkit as a chat participant via the 'Add toolkit' button and popper search.

        Clicks the 'Add toolkit' button, searches using the first 20 characters of
        *toolkit_name*, selects the first result, and waits for the placeholder
        "Still no toolkits added" to disappear.

        Args:
            toolkit_name: Full toolkit name (first 20 chars used for search)
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Adding toolkit participant '%s'", toolkit_name)
        add_btn = self.page.get_by_test_id("add-toolkit-button")
        add_btn.wait_for(state="visible", timeout=timeout)
        add_btn.click(force=True)

        search_input = Popper.find_visible_search_input(self.page, timeout=timeout)
        # Same fix as add_agent_participant — press_sequentially triggers
        # React onChange; fill() does not.
        search_input.click()
        search_input.press_sequentially(toolkit_name[:20], delay=50)

        toolkit_option = self.page.get_by_test_id("toolkit-search-result-item").filter(has_text=toolkit_name[:15]).first
        toolkit_option.wait_for(state="visible", timeout=timeout)
        toolkit_option.click()

        self.page.get_by_test_id("no-toolkits-placeholder").wait_for(
            state="hidden", timeout=timeout,
        )

        # Same optimistic-UI race as add_agent_participant — wait for the
        # toolkit registration write to land on the server before returning.
        self.wait_for_network(timeout=timeout)

        logger.info("Toolkit '%s' added as chat participant", toolkit_name)

    # ------------------------------------------------------------------
    # UI state wait helpers
    # ------------------------------------------------------------------

    def wait_for_input_empty(self, timeout: int = 5000):
        """Wait until the message input textarea becomes empty.

        Encapsulates the raw page.wait_for_function pattern.
        Use after send_message_with_shift_enter() to confirm the message was submitted.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        self.page.wait_for_function(
            """() => {
                const ta = document.querySelector('[data-testid="chat-message-input"]');
                return ta && ta.value.trim() === '';
            }""",
            timeout=timeout,
        )
        logger.info("Message input is empty")

    def wait_for_sidebar_collapsed(self, timeout: int = 5000):
        """Wait for the sidebar to collapse — expanded text labels become hidden.

        The sidebar is considered collapsed when the 'Agents' button's text
        is no longer visible (only icon remains in mini-sidebar mode).

        Args:
            timeout: Maximum wait time in milliseconds
        """
        # When collapsed, the sidebar item for Agents should not be visible
        agents_item = self.page.get_by_test_id("sidebar-item-agents")
        try:
            agents_item.wait_for(state="hidden", timeout=timeout)
        except Exception:
            # Some deployments keep mini-sidebar visible; fall back to network settle
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        logger.info("Sidebar collapsed")

    def get_internal_tool_switch(self, tool_name: str):
        """Get the toggle switch locator for a named internal tool.

        Must be called while the internal tools menu is open
        (after open_internal_tools_menu()).

        Args:
            tool_name: Accessible name of the tool
                (e.g. "Image creation", "Data Analysis", "Planner")

        Returns:
            Playwright Locator for the switch element
        """
        testid = f"internal-tool-{tool_name.lower().replace(' ', '-')}-switch"
        return self.page.get_by_test_id(testid)

    # ------------------------------------------------------------------
    # TTS (Text-to-Speech) Controls
    # ------------------------------------------------------------------

    def is_voice_mini_player_visible(self) -> bool:
        """Check if Voice Mini Player is visible in chat.

        The Voice Mini Player should NOT be visible by default.
        It only appears when Read-out and Voice mode features are activated.

        Returns:
            True if Voice Mini Player is visible, False otherwise.
        """
        return self.voice_mini_player is not None and self.voice_mini_player.count() > 0 and self.voice_mini_player.first.is_visible()

    @action("Click read out button")
    def click_read_out(self, message_index: int = -1, timeout: int = 10000):
        """Click the 'Read out' (speaker) button on a message to start TTS.

        The read out button appears on AI messages and triggers text-to-speech
        playback. When clicked, a playback control bar appears with play/stop
        and settings controls.

        Args:
            message_index: Index of message (-1 for last AI message).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking Read out button on message %d", message_index)
        message = self.messages_container.nth(message_index)
        message.scroll_into_view_if_needed()
        message.hover()
        self.page.wait_for_timeout(500)

        # Find read out button by testid
        read_out_btn = message.get_by_test_id("chat-read-out-button")

        # Wait for button to be visible and ENABLED (disabled while AI is generating)
        read_out_btn.first.wait_for(state="visible", timeout=timeout)
        # Wait until not disabled
        self.page.wait_for_function(
            """(selector) => {
                const btn = document.querySelector(selector);
                return btn && !btn.disabled;
            }""",
            arg='[data-testid="chat-read-out-button"]',
            timeout=timeout
        )
        read_out_btn.first.click()
        self.page.wait_for_timeout(500)
        logger.info("Read out button clicked, TTS playback started")

    def is_tts_playing(self) -> bool:
        """Check if TTS playback is currently active.

        Looks for the TTS control bar that appears during playback.

        Returns:
            True if TTS control bar is visible, False otherwise.
        """
        # Check for play/stop button in voice mini player
        try:
            locator = self.page.get_by_test_id("chat-voice-play-stop-button")
            return locator.count() > 0 and locator.first.is_visible()
        except Exception:
            return False

    def wait_for_tts_controls(self, timeout: int = 5000):
        """Wait for TTS playback controls to become visible.

        The control bar appears after clicking Read out and contains
        play/stop button, settings gear, and volume controls.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Waiting for TTS playback controls...")
        # Wait for voice mini player to appear
        self.voice_mini_player.first.wait_for(state="visible", timeout=timeout)
        logger.info("TTS playback controls visible")

    @action("Open voice settings from TTS")
    def open_voice_settings_from_tts(self, timeout: int = 5000):
        """Open the Voice Settings dialog from the TTS playback control bar.

        Must be called while TTS playback is active (after click_read_out).
        Clicks the gear/settings icon in the TTS control bar.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator to the Voice Settings dialog.
        """
        from components.voice_settings import VoiceSettingsDialog

        logger.info("Opening Voice Settings from TTS control bar")
        self.voice_settings_button.first.wait_for(state="visible", timeout=timeout)
        self.voice_settings_button.first.click()

        dialog = VoiceSettingsDialog.wait_for(self.page, timeout=timeout)
        return dialog

    def trigger_tts_and_open_settings(self, message_index: int = -1, timeout: int = 10000):
        """Convenience method: trigger TTS on a message and open Voice Settings.

        Combines click_read_out and open_voice_settings_from_tts into a single
        action for tests that need to access voice settings from chat.

        Idempotent: if TTS is already playing (mini player visible), skips
        click_read_out and goes directly to opening settings. This allows
        tests to call this method multiple times without worrying about state.

        Args:
            message_index: Index of message (-1 for last).
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator to the Voice Settings dialog.
        """
        if not self.is_tts_playing():
            self.click_read_out(message_index=message_index, timeout=timeout)
            self.wait_for_tts_controls(timeout=timeout)
        return self.open_voice_settings_from_tts(timeout=timeout)
