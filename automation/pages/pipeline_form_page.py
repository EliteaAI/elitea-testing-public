"""Pipeline form page object for create/edit operations.

Handles pipeline form filling, save/cancel/discard operations.

URL: /pipelines/create, /pipelines/all/{id}
"""

import logging
from playwright.sync_api import Page
from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from components.mui import Dialog

logger = logging.getLogger("elitea.pages.pipeline_form")


class PipelineFormPage(BasePage):
    """Pipeline create/edit form page.

    Handles:
    - Form field operations (name, description)
    - Save/cancel/discard actions
    - Form validation waits
    - MUI form patterns (click + type instead of fill)

    URL: /pipelines/create or /pipelines/all/{id}
    """

    # LocatorDescriptors - testid + fallback pattern
    name_input = LocatorDescriptor(
        testid="agent-name-input",
        fallback=lambda page: page.get_by_role("textbox", name="Name"),
        description="Pipeline name input field"
    )

    description_input = LocatorDescriptor(
        testid="agent-description-input",
        fallback=lambda page: page.get_by_role("textbox", name="Description"),
        description="Pipeline description input field"
    )

    save_button = LocatorDescriptor(
        testid="agent-save-button",
        fallback=lambda page: page.get_by_role("button", name="Save", exact=True),
        description="Save pipeline button"
    )

    cancel_button = LocatorDescriptor(
        fallback=lambda page: page.get_by_role("button", name="Cancel"),
        description="Cancel button"
    )

    discard_button = LocatorDescriptor(
        testid="discard-button",
        fallback=lambda page: page.get_by_role("button", name="Discard"),
        description="Discard changes button"
    )

    # Tags combobox (ELITEA-2021 — testid gap closed via add-data-testid;
    # TagEditor/AutoCompleteDropDown wiring mirrors CreateSkillForm.jsx's
    # skill-tags-input shape one prefix over, per the AFS's declared-
    # improvisation naming: .agents/role-overrides.md § Declared-
    # improvisation protocol).
    tags_input = LocatorDescriptor(
        testid="agent-tags-input",
        description="Tags combobox wrapper (Autocomplete root)"
    )
    tags_input_field = LocatorDescriptor(
        testid="agent-tags-input-field",
        description="Tags combobox's real <input> element"
    )
    tag_chip = LocatorDescriptor(
        testid="agent-tag-chip",
        description="A committed tag chip in the Tags combobox"
    )

    # Dynamic (runtime-parameterized) testid — one per committed tag option
    # in the dropdown. Class-level template constant per .agents/testing.md
    # § Locator policy, formatted with test-generated data only at the call site.
    TAG_OPTION = '[data-testid="agent-tag-option-{}"]'

    # Welcome message / Chat starters / Step limit — same shared components
    # as AgentFormPage/AgentDetailPage (CreateAgentForm.jsx composes them
    # identically for entityType="pipeline"), same testids. Ported here
    # since PipelineFormPage had no locators for them yet (AFS ELITEA-2021
    # Automation Hints).
    welcome_message_input = LocatorDescriptor(
        testid="agent-welcome-message-input",
        description="Welcome message field"
    )
    conversation_starter_add_button = LocatorDescriptor(
        testid="agent-conversation-starter-add",
        description="Add conversation starter button"
    )
    conversation_starter_inputs = LocatorDescriptor(
        testid="agent-conversation-starter-input",
        description="Conversation starter textarea field(s)"
    )
    step_limit_input = LocatorDescriptor(
        testid="agent-step-limit-input",
        description="Step limit input (Advanced accordion section)"
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate_to_create(self):
        """Navigate to create pipeline page and wait for form load."""
        super().navigate("/pipelines/create?viewMode=owner")
        self.wait_for_page_load()
        logger.info("Navigated to create pipeline page")

    def navigate_to_edit(self, pipeline_id: int):
        """Navigate to pipeline edit page and wait for form load.

        Args:
            pipeline_id: The numeric pipeline ID.
        """
        super().navigate(f"/pipelines/all/{pipeline_id}?viewMode=owner")
        self.wait_for_page_load()
        logger.info("Navigated to pipeline %d edit page", pipeline_id)

    # ------------------------------------------------------------------
    # Wait methods
    # ------------------------------------------------------------------

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for the pipeline form to fully load.

        Waits for name field to be visible and network to settle.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.name_input.wait_for(state="visible", timeout=timeout)
        self.wait_for_network(timeout=10000)
        self.page.wait_for_timeout(1000)  # Form initialization
        logger.info("Pipeline form loaded")

    def wait_for_form_validation(self, timeout: int = 1000):
        """Wait for MUI form validation to complete.

        MUI forms have debounce delay for validation (300-500ms).
        Pages with persistent WebSocket connections never reach networkidle,
        so any TimeoutError is silently ignored here.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        try:
            self.wait_for_network(timeout=timeout)
        except Exception:
            pass  # Pages with WebSocket may never reach networkidle
        self.page.wait_for_timeout(500)  # MUI debounce

    # ------------------------------------------------------------------
    # Form operations
    # ------------------------------------------------------------------

    def fill_form(self, name: str, description: str):
        """Fill in the pipeline create/edit form.

        Uses click() + type() instead of fill() because MUI React forms
        do not recognize programmatic fill() value changes.

        Args:
            name: Pipeline name (required).
            description: Pipeline description (required).
        """
        logger.info("Filling pipeline form: name=%s", name)

        # Name field
        self.name_input.click()
        self.name_input.type(name)
        self.page.wait_for_timeout(200)

        # Description field
        self.description_input.click()
        self.description_input.type(description)
        self.page.wait_for_timeout(200)

    def update_text_field(self, field_name: str, value: str, wait_for_validation: bool = True):
        """Update a text field using React onChange pattern.

        Uses click + select all + type to trigger React onChange event.

        Args:
            field_name: Field to update ("name" or "description").
            value: New value for the field.
            wait_for_validation: Whether to wait for form validation after update.
        """
        field_map = {
            "name": self.name_input,
            "description": self.description_input,
        }

        if field_name not in field_map:
            raise ValueError(f"Unknown field: {field_name}. Must be 'name' or 'description'")

        field = field_map[field_name]
        field.click()
        # el.select() is the only reliable way to select all text in a React-controlled
        # MUI input/textarea: Ctrl+A via Playwright press() doesn't always propagate to
        # the native selection (React may consume the event without selecting).
        field.evaluate("el => el.select()")
        self.page.keyboard.type(value)

        if wait_for_validation:
            self.wait_for_form_validation()

    def update_name(self, name: str):
        """Update pipeline name field.

        Args:
            name: New name value.
        """
        self.update_text_field("name", name)

    def update_description(self, description: str):
        """Update pipeline description field.

        Args:
            description: New description value.
        """
        self.update_text_field("description", description)

    # ------------------------------------------------------------------
    # Getters
    # ------------------------------------------------------------------

    def get_name(self) -> str:
        """Read the current value of the Name field.

        Returns:
            Current name input value.
        """
        return self.name_input.input_value()

    def get_description(self) -> str:
        """Read the current value of the Description field.

        Returns:
            Current description input value.
        """
        return self.description_input.input_value()

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def add_tag(self, tag_name: str, timeout: int = 5000):
        """Type a tag into the Tags combobox and commit it with Enter.

        Args:
            tag_name: Tag text to add.
            timeout: Maximum wait time for the chip to appear.
        """
        logger.info("Adding tag '%s'", tag_name)
        self.tags_input_field.click()
        self.tags_input_field.press_sequentially(tag_name, delay=50)
        self.page.keyboard.press("Enter")
        self.tag_chip.filter(has_text=tag_name).first.wait_for(state="visible", timeout=timeout)
        logger.info("Tag '%s' committed", tag_name)

    def has_tag_chip(self, tag_name: str, timeout: int = 5000) -> bool:
        """Check whether a committed tag chip reading *tag_name* is visible.

        Args:
            tag_name: Tag text to look for.
            timeout: Maximum wait time.

        Returns:
            True if a matching chip is visible, False otherwise.
        """
        try:
            self.tag_chip.filter(has_text=tag_name).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Welcome message
    # ------------------------------------------------------------------

    def fill_welcome_message(self, text: str):
        """Fill the Welcome message field.

        Uses click + clear + press_sequentially to trigger React's onChange
        (.claude/rules/mui-patterns.md).

        Args:
            text: Welcome message text.
        """
        self.welcome_message_input.click()
        self.welcome_message_input.clear()
        self.welcome_message_input.press_sequentially(text, delay=30)
        self.page.wait_for_timeout(200)

    def get_welcome_message(self) -> str:
        """Read the current value of the Welcome message field."""
        return self.welcome_message_input.input_value()

    # ------------------------------------------------------------------
    # Conversation starters
    # ------------------------------------------------------------------

    def add_conversation_starter(self, text: str, timeout: int = 5000):
        """Click "+ Starter" and fill the newly-added starter textarea.

        Args:
            text: Starter text to fill.
            timeout: Maximum wait time for the new input to appear.
        """
        logger.info("Adding conversation starter")
        self.conversation_starter_add_button.click()
        self.page.wait_for_timeout(500)
        inputs = self.conversation_starter_inputs
        inputs.last.wait_for(state="visible", timeout=timeout)
        inputs.last.click()
        self.page.wait_for_timeout(200)
        if text:
            inputs.last.fill(text)
            self.page.wait_for_timeout(300)

    def get_conversation_starter_text(self, index: int = 0) -> str:
        """Read the value of a conversation starter textarea.

        Args:
            index: Index of the conversation starter (0-based).
        """
        return self.conversation_starter_inputs.nth(index).input_value()

    # ------------------------------------------------------------------
    # Step limit (Advanced section)
    # ------------------------------------------------------------------

    def set_step_limit(self, value: str):
        """Set the Step limit field (Advanced section) to *value*.

        Uses Playwright's native ``.clear()`` (a real event-triggering
        clear) before typing — a raw select-all+Backspace key-event
        sequence was confirmed live (AFS ELITEA-2021) to NOT reliably clear
        this React-controlled field's stale default value ("25" on a fresh
        create form), producing a corrupted result ("255"/"2550") instead.
        ``press_sequentially()`` after ``clear()`` correctly triggers
        React's onChange per keystroke (.claude/rules/mui-patterns.md).

        Args:
            value: Target step limit value (numeric string).
        """
        self.step_limit_input.click()
        self.step_limit_input.clear()
        self.step_limit_input.press_sequentially(value, delay=50)
        self.page.wait_for_timeout(300)

    def get_step_limit(self) -> str:
        """Read the current value of the Step limit field."""
        return self.step_limit_input.input_value()

    # ------------------------------------------------------------------
    # Save/Cancel/Discard actions
    # ------------------------------------------------------------------

    def click_save(self, timeout: int = 10000):
        """Click the Save button and wait for network.

        Uses JavaScript click to bypass MUI overlay interception.

        Args:
            timeout: Maximum wait time for save to complete.
        """
        logger.info("Clicking Save")
        self.save_button.evaluate("el => el.click()")
        self.wait_for_network(timeout=timeout)

    def save_and_wait_for_navigation(self, timeout: int = 15000):
        """Click Save and wait for navigation to detail page.

        Encapsulates save + navigation + detail page load wait.

        Args:
            timeout: Maximum wait time for save and navigation.
        """
        self.click_save(timeout=timeout)
        # After save on create, URL changes to /pipelines/all/{id}
        # Wait for URL to change
        self.page.wait_for_url("**/pipelines/all/*", timeout=timeout)
        self.wait_for_network(timeout=10000)

    def is_save_enabled(self) -> bool:
        """Check if the Save button is enabled.

        Returns:
            True if save button is enabled, False otherwise.
        """
        return self.save_button.is_enabled()

    def click_cancel(self):
        """Click the Cancel button."""
        logger.info("Clicking Cancel")
        self.cancel_button.click()
        self.page.wait_for_timeout(500)

    def click_discard(self, timeout: int = 5000):
        """Click the Discard button and confirm dialog if present.

        The Discard button reverts unsaved changes. It may show a
        confirmation dialog.

        Args:
            timeout: Maximum wait time for discard action.
        """
        logger.info("Clicking Discard")
        self.dismiss_banner_if_present()
        self.discard_button.wait_for(state="visible", timeout=timeout)
        self.discard_button.evaluate("el => el.click()")
        self.page.wait_for_timeout(500)

        # Handle confirmation dialog if present
        try:
            dialog = Dialog.wait_for(self.page, timeout=3000)
            Dialog.click_first_button(dialog, "Discard", "Confirm")
        except Exception:
            pass  # No confirmation dialog

        self.wait_for_network(timeout=timeout)
        logger.info("Discard clicked")

    def is_discard_enabled(self) -> bool:
        """Check if the Discard button is visible and enabled.

        Returns:
            True if discard button is enabled, False otherwise.
        """
        return (
            self.discard_button.is_visible()
            and self.discard_button.is_enabled()
        )
