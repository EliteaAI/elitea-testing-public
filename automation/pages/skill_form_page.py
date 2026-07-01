"""Skill Form Page - Create and edit skill forms.

Handles: /app/skills/create and /app/skills/all/{id} (edit mode)
- Fill in skill details (name, description, instructions)
- Save/cancel operations
- Form validation
"""

import logging
from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action


logger = logging.getLogger("elitea.pages.skill_form")


class SkillFormPage(BasePage):
    """Page object for skill create/edit form.

    URL: /app/skills/create (create) or /app/skills/all/{id} (edit)
    """

    # Form field locators
    name_input = LocatorDescriptor(
        testid="skill-name-input",
        fallback=lambda page: page.locator('[data-testid="skill-name-input"]'),
        description="Skill name input field"
    )

    description_input = LocatorDescriptor(
        testid="skill-description-input",
        fallback=lambda page: page.locator('[data-testid="skill-description-input"]'),
        description="Skill description input field"
    )

    instructions_editor = LocatorDescriptor(
        testid="skill-instructions-editor",
        fallback=lambda page: page.locator('.cm-content[contenteditable]').first,
        description="Skill instructions CodeMirror editor"
    )

    save_button = LocatorDescriptor(
        testid="skill-save-button",
        fallback=lambda page: page.get_by_role("button", name="Save", exact=True),
        description="Save skill button"
    )

    cancel_button = LocatorDescriptor(
        testid=None,
        fallback=lambda page: page.get_by_role("button", name="Cancel"),
        description="Cancel button"
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def wait_for_form_load(self, timeout: int = 15000):
        """Wait for the skill create/edit form to be fully loaded.

        Waits for the Name input to be visible and network to settle.
        """
        # Try testid first, fall back to input#name
        try:
            self.page.get_by_test_id("skill-name-input").wait_for(
                state="visible", timeout=timeout
            )
        except Exception:
            self.page.locator('input#name').wait_for(
                state="visible", timeout=timeout
            )
        self.wait_for_network(timeout=10000)
        self.page.wait_for_timeout(1000)
        logger.info("Skill form loaded")

    # ------------------------------------------------------------------
    # Form operations
    # ------------------------------------------------------------------

    @action("Fill skill form")
    def fill_form(
        self,
        name: str,
        instructions: str,
        description: str = "Automation test skill",
    ):
        """Fill all required fields in the skill form.

        Name and description use click + clear + press_sequentially (React
        onChange pattern). Instructions use the CodeMirror pattern:
        click + Ctrl+A + keyboard.type().

        Args:
            name: Skill name (required).
            instructions: Skill instructions text (required, CodeMirror).
            description: Skill description (required, defaults to generic value).
        """
        self._fill_text_input(self.name_input, name)
        self._fill_text_input(self.description_input, description)
        self.fill_instructions(instructions)
        logger.info("Filled skill form: name=%r", name)

    def _fill_text_input(self, locator, text: str):
        """Fill a standard MUI text input with React-safe keyboard events.

        Args:
            locator: LocatorDescriptor or Playwright locator for the input.
            text: Text to type.
        """
        locator.click()
        self.page.wait_for_timeout(200)
        # Select all existing content and replace
        locator.press("Control+a")
        locator.press_sequentially(text, delay=80)
        self.page.wait_for_timeout(300)

    @action("Fill instructions editor")
    def fill_instructions(self, text: str):
        """Fill the CodeMirror instructions editor.

        CodeMirror does not respond to fill() — it requires a click to focus,
        then Ctrl+A to select existing content, then keyboard.type() to insert.

        Args:
            text: Instructions text to enter.
        """
        # The editor wrapper (data-testid="skill-instructions-editor") contains
        # the .cm-content[contenteditable] element.
        editor_wrapper = self.instructions_editor
        # Click on the cm-content within the wrapper
        cm_content = editor_wrapper.locator('.cm-content[contenteditable]').first
        if cm_content.count() == 0:
            # Fallback: instructions_editor IS the cm-content
            cm_content = editor_wrapper

        cm_content.click()
        self.page.wait_for_timeout(200)
        self.page.keyboard.press("Control+a")
        self.page.keyboard.type(text)
        self.page.wait_for_timeout(300)
        logger.info("Filled instructions editor")

    # ------------------------------------------------------------------
    # Save state
    # ------------------------------------------------------------------

    def is_save_enabled(self) -> bool:
        """Return True if the Save button is currently enabled.

        Returns:
            True if Save is enabled, False if disabled.
        """
        return self.save_button.is_enabled()

    def wait_for_form_validation(self, timeout: int = 1000):
        """Wait for React form debounce and validation to complete.

        After filling form fields, React's onChange + validation pipeline
        takes ~500ms to update the Save button's disabled state.
        """
        self.wait_for_network(timeout=timeout)
        self.page.wait_for_timeout(500)

    @action("Save skill and wait for navigation")
    def save_and_wait_for_navigation(self, timeout: int = 15000):
        """Click Save and wait for navigation to the skill detail page.

        The create form's useBlocker (nav guard) intercepts the programmatic
        navigate() call that fires after a successful save because the form is
        still marked dirty at that moment.  The blocker shows a "There are
        unsaved changes. Are you sure you want to leave?" dialog.  We wait up
        to 3 s for that dialog to appear, click Confirm if it does, then wait
        for the URL to settle on /skills/all/{id}.

        Args:
            timeout: Maximum wait time in milliseconds for the final URL change.
        """
        logger.info("Clicking Save and waiting for navigation")
        self.save_button.evaluate("el => el.click()")

        # Wait for the nav-blocker dialog and dismiss it.
        # It reliably appears ~0–2 s after the save mutation completes.
        try:
            confirm_btn = self.page.get_by_role("button", name="Confirm")
            confirm_btn.wait_for(state="visible", timeout=5000)
            confirm_btn.click()
            logger.info("Dismissed nav-blocker dialog after save")
        except Exception:
            logger.debug("Nav-blocker dialog did not appear — direct navigation")

        # Wait for URL to include /skills/all/ (glob pattern, no lambda)
        self.page.wait_for_url("**/skills/all/**", timeout=timeout)
        self.wait_for_network(timeout=5000)
        self.page.wait_for_timeout(500)
        logger.info("Saved skill — URL: %s", self.page.url)

    # ------------------------------------------------------------------
    # Read field values
    # ------------------------------------------------------------------

    def get_name(self) -> str:
        """Return the current value of the Name input field."""
        try:
            return self.name_input.input_value()
        except Exception:
            return self.page.locator('input#name').input_value()
