"""Agent Form Page - Create and edit agent forms.

Handles: /app/agents/create and /app/agents/all/{id} (edit mode)
- Fill in agent details (name, description, instructions)
- Save/cancel operations
- Form validation
"""

import logging
import re
from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action


logger = logging.getLogger("elitea.pages.agent_form")


class AgentFormPage(BasePage):
    """Page object for agent create/edit form."""

    # Form field locators
    name_input = LocatorDescriptor(
        testid="agent-name-input",
        fallback=lambda page: page.get_by_role("textbox", name="Name"),
        description="Agent name input field"
    )

    description_input = LocatorDescriptor(
        testid="agent-description-input",
        fallback=lambda page: page.get_by_role("textbox", name="Description"),
        description="Agent description input field"
    )

    instructions_input = LocatorDescriptor(
        testid="agent-instructions-input",
        fallback=lambda page: page.get_by_role("textbox", name="Guidelines for the AI agent"),
        description="Agent instructions/guidelines field"
    )

    welcome_message_input = LocatorDescriptor(
        testid="agent-welcome-message-input",
        fallback=lambda page: page.get_by_role("textbox", name="Input your welcome message"),
        description="Welcome message field"
    )

    welcome_message_expand_button = LocatorDescriptor(
        testid="agent-welcome-message-expand",
        fallback=lambda page: page.locator('button[aria-label="Full screen view"]'),
        description="Welcome message expand/fullscreen button"
    )

    welcome_message_counter = LocatorDescriptor(
        testid="agent-welcome-message-counter",
        fallback=lambda page: page.get_by_text(re.compile(r'\d+\s*characters?\s*left', re.IGNORECASE)),
        description="Welcome message character counter in collapsed mode"
    )

    welcome_message_fullscreen = LocatorDescriptor(
        testid="agent-welcome-message-dialog",
        fallback=lambda page: page.locator('[role="dialog"]:has-text("Welcome message")'),
        description="Welcome message fullscreen dialog"
    )

    welcome_message_fullscreen_textarea = LocatorDescriptor(
        testid="agent-welcome-message-dialog-textarea",
        fallback=lambda page: page.locator('[role="dialog"]:has-text("Welcome message") textarea, '
                                           '[role="dialog"]:has-text("Welcome message") [contenteditable="true"]'),
        description="Welcome message textarea in fullscreen dialog"
    )

    welcome_message_fullscreen_counter = LocatorDescriptor(
        testid="agent-welcome-message-dialog-counter",
        fallback=lambda page: page.locator('[role="dialog"]').get_by_text(
            re.compile(r'\d+\s*characters?\s*left', re.IGNORECASE)
        ),
        description="Character counter in welcome message fullscreen dialog"
    )

    welcome_message_fullscreen_close = LocatorDescriptor(
        testid="agent-welcome-message-dialog-close",
        fallback=lambda page: page.locator('.MuiDialogTitle-root .MuiBox-root div button').nth(1),
        description="Close button for welcome message fullscreen dialog"
    )

    conversation_starters_section = LocatorDescriptor(
        testid="agent-conversation-starters-section",
        fallback=lambda page: page.get_by_text("Conversation starters"),
        description="Conversation Starters accordion section header"
    )

    conversation_starter_add_button = LocatorDescriptor(
        testid="agent-conversation-starter-add",
        fallback=lambda page: page.locator('div[data-tour="agent-conversation-starters"] button.MuiButton-iconLabel'),
        description="Add conversation starter button"
    )

    conversation_starter_inputs = LocatorDescriptor(
        testid="agent-conversation-starter-input",
        fallback=lambda page: page.locator('textarea[placeholder="Conversation message"]'),
        description="Conversation starter textarea field(s)"
    )

    conversation_starter_counter = LocatorDescriptor(
        testid="agent-conversation-starter-counter",
        fallback=lambda page: page.locator('text=/\\d+\\s*characters?\\s*left/i'),
        description="Conversation starter character counter"
    )

    conversation_starter_expand_button = LocatorDescriptor(
        testid="agent-conversation-starter-expand",
        fallback=lambda page: page.locator('button[aria-label="Full screen view"]'),
        description="Conversation starter expand/fullscreen button"
    )

    conversation_starter_fullscreen = LocatorDescriptor(
        testid="agent-conversation-starter-dialog",
        fallback=lambda page: page.locator('[role="dialog"]:has-text("Conversation starter")'),
        description="Conversation starter fullscreen dialog"
    )

    conversation_starter_fullscreen_textarea = LocatorDescriptor(
        testid="agent-conversation-starter-dialog-textarea",
        fallback=lambda page: page.locator('[role="dialog"] [contenteditable="true"], [role="dialog"] textarea'),
        description="Conversation starter textarea in fullscreen dialog"
    )

    conversation_starter_fullscreen_counter = LocatorDescriptor(
        testid="agent-conversation-starter-dialog-counter",
        fallback=lambda page: page.locator('[role="dialog"]').get_by_text(
            re.compile(r'\d+\s*characters?\s*left', re.IGNORECASE)
        ),
        description="Character counter in conversation starter fullscreen dialog"
    )

    conversation_starter_fullscreen_close = LocatorDescriptor(
        testid="agent-conversation-starter-dialog-close",
        fallback=lambda page: page.locator('.MuiDialogTitle-root .MuiBox-root div button').nth(1),
        description="Close button for conversation starter fullscreen dialog"
    )

    # Button locators
    save_button = LocatorDescriptor(
        testid="agent-save-button",
        fallback=lambda page: page.get_by_role("button", name="Save", exact=True),
        description="Save button"
    )

    cancel_button = LocatorDescriptor(
        testid="agent-cancel-button",
        fallback=lambda page: page.get_by_role("button", name="Cancel"),
        description="Cancel button"
    )

    discard_button = LocatorDescriptor(
        testid="agent-discard-button",
        fallback=lambda page: page.get_by_role("button", name="Discard"),
        description="Discard changes button"
    )

    save_as_version_button = LocatorDescriptor(
        testid="agent-save-as-version-button",
        fallback=lambda page: page.get_by_role("button", name="Save As Version"),
        description="Save as new version button"
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _is_element_red(self, locator) -> bool:
        """Check if element has red/error color styling.

        Detects warning state by checking computed CSS color for red-ish values.

        Args:
            locator: Playwright locator for the element to check.

        Returns:
            True if element has red color (r > 150, r > g*1.5, r > b*1.5).
        """
        try:
            color = locator.evaluate("el => window.getComputedStyle(el).color")
            if color:
                match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
                if match:
                    r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    return r > 150 and r > g * 1.5 and r > b * 1.5
        except Exception:
            pass
        return False

    def _is_counter_warning(self, locator) -> bool:
        """Check if a character counter shows warning state.

        Checks for:
        - CSS classes containing 'error' or 'warning'
        - Red color in computed style
        - Text content containing 'MAXIMUM' and 'limit'

        Args:
            locator: Playwright locator for the counter element.

        Returns:
            True if counter has error/warning styling.
        """
        try:
            if not locator.is_visible(timeout=2000):
                return False

            # Check CSS classes
            classes = locator.get_attribute("class") or ""
            if any(c in classes.lower() for c in ["error", "muiformhelpertext-error", "warning", "Mui-error"]):
                return True

            # Check computed color style (red color detection)
            if self._is_element_red(locator):
                return True

            # Check text content for warning keywords
            text = locator.text_content() or ""
            if "maximum" in text.lower() and "limit" in text.lower():
                return True

            return False
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def wait_for_form_load(self, timeout: int = 15000):
        """Wait for the agent create/edit form to load.

        Waits for the Name field to be visible and for network to settle,
        then adds a brief delay for React to finish rendering.
        """
        self.name_input.wait_for(state="visible", timeout=timeout)
        self.wait_for_network(timeout=10000)
        self.page.wait_for_timeout(1000)
        logger.info("Agent form loaded")

    def wait_for_form_validation(self, timeout: int = 1000):
        """Wait for MUI form validation to complete.

        Handles MUI debounce timing (typically 300-500ms) to ensure
        form validation state is updated before checking Save button.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.wait_for_network(timeout=1000)
        self.page.wait_for_timeout(500)  # MUI debounce
        logger.debug("Form validation wait completed")

    # ------------------------------------------------------------------
    # Form filling
    # ------------------------------------------------------------------

    @action("Fill agent form")
    def fill_form(
        self,
        name: str,
        description: str,
        instructions: str = "",
        welcome_message: str = "",
    ):
        """Fill in the agent create/edit form.

        Uses click() + clear() + press_sequentially() to properly trigger
        React's onChange handlers. The press_sequentially() method types one
        character at a time with delays, ensuring React state updates correctly.

        Args:
            name: Agent name (required).
            description: Agent description (required).
            instructions: System prompt / guidelines.
            welcome_message: Welcome message shown to users.
        """
        logger.info("Filling agent form: name=%s", name)

        # Fill name - use slower delay to ensure all characters are captured
        self.name_input.click()
        self.page.wait_for_timeout(100)  # Wait for focus
        self.name_input.clear()
        self.page.wait_for_timeout(100)  # Wait for clear to complete
        self.name_input.press_sequentially(name, delay=80)
        self.page.wait_for_timeout(300)

        # Fill description
        self.description_input.click()
        self.page.wait_for_timeout(100)
        self.description_input.clear()
        self.page.wait_for_timeout(100)
        self.description_input.press_sequentially(description, delay=80)
        self.page.wait_for_timeout(300)

        # Fill instructions if provided
        if instructions:
            self.instructions_input.click()
            self.page.wait_for_timeout(100)
            self.instructions_input.clear()
            self.page.wait_for_timeout(100)
            self.instructions_input.press_sequentially(instructions, delay=80)
            self.page.wait_for_timeout(300)

        # Fill welcome message if provided
        if welcome_message:
            self.welcome_message_input.click()
            self.page.wait_for_timeout(100)
            self.welcome_message_input.clear()
            self.page.wait_for_timeout(100)
            self.welcome_message_input.press_sequentially(welcome_message, delay=80)
            self.page.wait_for_timeout(300)

        logger.info("Agent form filled successfully")

    # ------------------------------------------------------------------
    # Form field getters
    # ------------------------------------------------------------------

    def get_name(self) -> str:
        """Read the current value of the Name field."""
        return self.name_input.input_value()

    def get_description(self) -> str:
        """Read the current value of the Description field."""
        return self.description_input.input_value()

    def get_instructions(self) -> str:
        """Read the current value of the Instructions field."""
        return self.instructions_input.input_value()

    def get_welcome_message(self) -> str:
        """Read the current value of the Welcome Message field."""
        return self.welcome_message_input.input_value()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    @action("Click save")
    def click_save(self, timeout: int = 10000):
        """Click the Save button and wait for network.

        Uses JavaScript click to bypass MUI overlay interception.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking Save")
        self.save_button.evaluate("el => el.click()")
        self.wait_for_network(timeout=timeout)

    def is_save_enabled(self) -> bool:
        """Check if the Save button is enabled.

        Returns:
            True if Save button is enabled, False otherwise.
        """
        return self.save_button.is_enabled()

    @action("Click cancel")
    def click_cancel(self, timeout: int = 5000):
        """Click the Cancel button.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking Cancel")
        self.cancel_button.click()
        self.wait_for_network(timeout=timeout)

    @action("Save agent")
    def save_and_wait(self, timeout: int = 15000):
        """Click Save and wait for the save to complete.

        Uses JavaScript click to bypass MUI overlay, then waits for
        network to settle and adds a brief delay.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Saving agent and waiting for completion")
        self.save_button.evaluate("el => el.click()")
        self.wait_for_network(timeout=timeout)
        self.page.wait_for_timeout(1000)
        logger.info("Agent saved")

    @action("Save agent and navigate")
    def save_and_wait_for_navigation(self, timeout: int = 15000):
        """Click Save and wait for navigation to complete.

        Handles network settling and page transition after save.
        Returns when the detail page is ready for interaction.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Saving and waiting for navigation")
        self.save_button.evaluate("el => el.click()")
        self.wait_for_network(timeout=timeout)

        # Wait for navigation to detail page
        self.page.wait_for_load_state("networkidle", timeout=timeout)
        self.page.wait_for_timeout(1000)

        logger.info("Saved and navigation completed")

    # ------------------------------------------------------------------
    # Field update helpers
    # ------------------------------------------------------------------

    def update_text_field(self, field_name: str, value: str, wait_for_validation: bool = True):
        """Update text field with React-compatible pattern.

        Uses click + select all + type to trigger React onChange.
        Waits for validation if requested.

        Args:
            field_name: Field to update ("name", "description", "instructions")
            value: New value to set
            wait_for_validation: Whether to wait for form validation after update
        """
        field_map = {
            "name": self.name_input,
            "description": self.description_input,
            "instructions": self.instructions_input
        }

        if field_name not in field_map:
            raise ValueError(f"Unknown field: {field_name}. Must be one of {list(field_map.keys())}")

        field = field_map[field_name]
        field.click()
        field.press("ControlOrMeta+a")  # Works on both macOS (Cmd+A) and Windows/Linux (Ctrl+A)
        field.type(value)

        if wait_for_validation:
            self.wait_for_form_validation()

        logger.debug(f"Updated {field_name} field to: {value}")

    @action("Update agent name")
    def update_name(self, new_name: str):
        """Update agent name field.

        Args:
            new_name: New agent name
        """
        self.update_text_field("name", new_name)
        logger.info(f"Updated agent name to: {new_name}")

    @action("Update agent description")
    def update_description(self, new_description: str):
        """Update agent description field.

        Args:
            new_description: New agent description
        """
        self.update_text_field("description", new_description)
        logger.info(f"Updated agent description to: {new_description}")

    # ------------------------------------------------------------------
    # Welcome Message methods
    # ------------------------------------------------------------------

    def get_welcome_message_counter_text(self) -> str | None:
        """Get the character counter text for welcome message in collapsed mode."""
        try:
            if self.welcome_message_counter.is_visible(timeout=2000):
                return self.welcome_message_counter.text_content()
        except Exception:
            pass
        return None

    def get_welcome_message_remaining_chars(self) -> int | None:
        """Parse remaining characters from welcome message counter.

        Welcome message has a 768 character limit.
        Format: "741 characters left"

        Returns:
            Number of remaining characters, or None if counter not found/parseable.
        """
        import re
        counter_text = self.get_welcome_message_counter_text()
        if counter_text:
            match = re.search(r'(\d+)\s*characters?\s*left', counter_text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def is_welcome_message_counter_warning(self) -> bool:
        """Check if welcome message counter shows warning state (red/error).

        Returns:
            True if counter has error/warning styling (typically red when at limit).
        """
        return self._is_counter_warning(self.welcome_message_counter)

    def is_welcome_message_at_limit(self) -> bool:
        """Check if welcome message has reached character limit.

        Returns:
            True if remaining characters is 0 or counter shows error state.
        """
        remaining = self.get_welcome_message_remaining_chars()
        if remaining is not None and remaining <= 0:
            return True
        return self.is_welcome_message_counter_warning()

    @action("Open welcome message fullscreen")
    def open_welcome_message_fullscreen(self, timeout: int = 5000):
        """Open the welcome message fullscreen dialog.

        Args:
            timeout: Maximum wait time for dialog to appear.
        """
        logger.info("Opening welcome message fullscreen dialog")
        self.welcome_message_expand_button.click()
        self.welcome_message_fullscreen.wait_for(state="visible", timeout=timeout)
        self.page.wait_for_timeout(300)  # Dialog animation
        logger.info("Welcome message fullscreen dialog opened")

    @action("Close welcome message fullscreen")
    def close_welcome_message_fullscreen(self, timeout: int = 5000):
        """Close the welcome message fullscreen dialog.

        Args:
            timeout: Maximum wait time for dialog to close.
        """
        logger.info("Closing welcome message fullscreen dialog")
        self.welcome_message_fullscreen_close.click()
        self.welcome_message_fullscreen.wait_for(state="hidden", timeout=timeout)
        self.page.wait_for_timeout(300)  # Dialog animation
        logger.info("Welcome message fullscreen dialog closed")

    def is_welcome_message_fullscreen_open(self) -> bool:
        """Check if welcome message fullscreen dialog is open.

        Returns:
            True if dialog is visible.
        """
        try:
            return self.welcome_message_fullscreen.is_visible(timeout=1000)
        except Exception:
            return False

    def get_welcome_message_fullscreen_counter_text(self) -> str | None:
        """Get character counter text from fullscreen dialog."""
        try:
            if self.welcome_message_fullscreen_counter.is_visible(timeout=2000):
                return self.welcome_message_fullscreen_counter.text_content()
        except Exception:
            pass
        return None

    def is_welcome_message_fullscreen_counter_warning(self) -> bool:
        """Check if dialog counter shows warning state (red/error).

        Returns:
            True if counter has error/warning styling.
        """
        return self._is_counter_warning(self.welcome_message_fullscreen_counter)

    def fill_welcome_message_in_fullscreen(self, text: str):
        """Fill welcome message in fullscreen mode.

        Args:
            text: Text to enter in the fullscreen textarea.
        """
        logger.info(f"Filling welcome message in fullscreen: {len(text)} characters")
        self.welcome_message_fullscreen_textarea.click()
        self.welcome_message_fullscreen_textarea.fill(text)
        self.page.wait_for_timeout(500)

    # ------------------------------------------------------------------
    # Conversation Starter methods
    # ------------------------------------------------------------------

    def get_conversation_starter_count(self) -> int:
        """Get the number of conversation starter inputs visible.

        Returns:
            Number of conversation starter input fields.
        """
        try:
            return self.conversation_starter_inputs.count()
        except Exception:
            return 0

    @action("Add conversation starter")
    def add_conversation_starter(self, text: str = ""):
        """Add a new conversation starter.

        Args:
            text: Optional text to fill in the new starter field.
        """
        logger.info("Adding conversation starter")
        self.conversation_starter_add_button.click()
        self.page.wait_for_timeout(500)

        # Wait for input field to appear
        inputs = self.conversation_starter_inputs
        inputs.last.wait_for(state="visible", timeout=5000)

        # Always click the input to focus it
        last_input = inputs.last
        last_input.click()
        self.page.wait_for_timeout(200)

        if text:
            last_input.fill(text)
            self.page.wait_for_timeout(300)

        logger.info(f"Added conversation starter: {text[:30] if text else 'empty'}...")

    def get_conversation_starter_counter_text(self, index: int = 0) -> str | None:
        """Get character counter text for a specific conversation starter.

        Args:
            index: Index of the conversation starter (0-based).
        """
        try:
            counters = self.conversation_starter_counter
            if counters.count() > index:
                return counters.nth(index).text_content()
        except Exception:
            pass
        return None

    def is_conversation_starter_counter_warning(self, index: int = 0) -> bool:
        """Check if conversation starter counter shows warning state (red/error).

        Args:
            index: Index of the conversation starter (0-based).

        Returns:
            True if counter has error/warning styling.
        """
        try:
            counters = self.conversation_starter_counter
            if counters.count() <= index:
                return False
            return self._is_counter_warning(counters.nth(index))
        except Exception:
            return False

    def fill_conversation_starter(self, index: int, text: str):
        """Fill a specific conversation starter field.

        Args:
            index: Index of the conversation starter (0-based).
            text: Text to enter.
        """
        inputs = self.conversation_starter_inputs
        if inputs.count() > index:
            input_field = inputs.nth(index)
            input_field.click()
            input_field.fill(text)
            self.page.wait_for_timeout(300)
            logger.info(f"Filled conversation starter {index}: {len(text)} characters")

    # ------------------------------------------------------------------
    # Conversation Starter Fullscreen methods
    # ------------------------------------------------------------------

    @action("Open conversation starter fullscreen")
    def open_conversation_starter_fullscreen(self, index: int = 0, timeout: int = 5000):
        """Open the conversation starter fullscreen dialog.
        Args:
            index: Index of the conversation starter (0-based).
            timeout: Maximum wait time for dialog to appear.
        """
        logger.info(f"Opening conversation starter {index} fullscreen dialog")
        inputs = self.conversation_starter_inputs
        if inputs.count() > index:
            inputs.nth(index).hover()
            self.page.wait_for_timeout(500)

        self.conversation_starter_expand_button.click()
        self.conversation_starter_fullscreen.wait_for(state="visible", timeout=timeout)
        self.page.wait_for_timeout(300)
        logger.info("Conversation starter fullscreen dialog opened")

    @action("Close conversation starter fullscreen")
    def close_conversation_starter_fullscreen(self, timeout: int = 5000):
        """Close the conversation starter fullscreen dialog.

        Args:
            timeout: Maximum wait time for dialog to close.
        """
        logger.info("Closing conversation starter fullscreen dialog")
        self.conversation_starter_fullscreen_close.click()
        self.conversation_starter_fullscreen.wait_for(state="hidden", timeout=timeout)
        self.page.wait_for_timeout(300)
        logger.info("Conversation starter fullscreen dialog closed")

    def is_conversation_starter_fullscreen_open(self) -> bool:
        """Check if conversation starter fullscreen dialog is open."""
        try:
            return self.conversation_starter_fullscreen.is_visible(timeout=1000)
        except Exception:
            return False

    def get_conversation_starter_fullscreen_counter_text(self) -> str | None:
        """Get character counter text from conversation starter fullscreen dialog."""
        try:
            if self.conversation_starter_fullscreen_counter.is_visible(timeout=2000):
                return self.conversation_starter_fullscreen_counter.text_content()
        except Exception:
            pass
        return None

    def is_conversation_starter_fullscreen_counter_warning(self) -> bool:
        """Check if dialog counter shows warning state (red/error)."""
        return self._is_counter_warning(self.conversation_starter_fullscreen_counter)

    def fill_conversation_starter_in_fullscreen(self, text: str):
        """Fill conversation starter in fullscreen mode.

        Args:
            text: Text to enter in the fullscreen textarea.
        """
        logger.info(f"Filling conversation starter in fullscreen: {len(text)} characters")
        self.conversation_starter_fullscreen_textarea.click()
        self.conversation_starter_fullscreen_textarea.fill(text)
        self.page.wait_for_timeout(500)
