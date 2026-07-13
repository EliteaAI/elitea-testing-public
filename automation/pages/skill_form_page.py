"""Skill Form Page - Create and edit skill forms.

Handles: /skills/create and /skills/all/{id} (edit mode)
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

    URL: /skills/create (create) or /skills/all/{id} (edit)
    """

    # Form field locators
    name_input = LocatorDescriptor(
        testid="skill-name-input",
        description="Skill name input field"
    )

    description_input = LocatorDescriptor(
        testid="skill-description-input",
        description="Skill description input field"
    )

    instructions_editor = LocatorDescriptor(
        testid="skill-instructions-editor",
        description="Skill instructions CodeMirror editor wrapper"
    )

    instructions_editor_content = LocatorDescriptor(
        testid="skill-instructions-editor-content",
        description="Skill instructions CodeMirror content element (.cm-content)"
    )

    save_button = LocatorDescriptor(
        testid="skill-save-button",
        description="Save skill button"
    )

    cancel_button = LocatorDescriptor(
        testid="skill-cancel-button",
        description="Cancel button"
    )

    tags_input = LocatorDescriptor(
        testid="skill-tags-input",
        description="Tags combobox wrapper (MUI Autocomplete root)"
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
        self.page.get_by_test_id("skill-name-input").wait_for(
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

    @action("Set description")
    def set_description(self, description: str):
        """Replace the Description field's content (works on pre-filled fields).

        The Description field renders as two ``<textarea>`` elements (MUI's
        autosize shadow copy plus the real, editable one) — the wrapper-level
        click + Ctrl+A pattern in :meth:`fill_form` only reliably clears an
        *empty* field; ``Control+a`` alone does not reliably select existing
        content here (typed text ends up inserted rather than replacing it).
        Uses Locator.select_text() + Backspace to clear the real (first,
        non-``aria-hidden``) textarea before typing the replacement.

        Args:
            description: New description text.
        """
        field = self.description_input.locator("textarea").first
        field.click()
        field.select_text()
        self.page.wait_for_timeout(100)
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(100)
        self.page.keyboard.type(description)
        self.page.wait_for_timeout(300)
        logger.info("Set description: %r", description[:60])

    @action("Add tag")
    def add_tag(self, tag: str):
        """Type a tag into the Tags combobox and commit it with Enter.

        The Tags field is a MUI Autocomplete (``skill-tags-input`` testid on
        the root wrapper); the actual text input is the wrapper's single
        ``input`` element.

        Args:
            tag: Tag text to type and commit.
        """
        tag_field = self.tags_input.locator("input")
        tag_field.click()
        tag_field.type(tag)
        tag_field.press("Enter")
        self.page.wait_for_timeout(200)
        logger.info("Added tag: %r", tag)

    def _fill_text_input(self, locator, text: str):
        """Fill a standard MUI text input with React-safe keyboard events.

        Clicks the wrapper to transfer focus to the inner input, then uses
        page.keyboard so events go to the focused element (not the wrapper div).

        Args:
            locator: LocatorDescriptor or Playwright locator for the input.
            text: Text to type.
        """
        locator.click()
        self.page.wait_for_timeout(200)
        self.page.keyboard.press("Control+a")
        self.page.keyboard.type(text)
        self.page.wait_for_timeout(300)

    @action("Fill instructions editor")
    def fill_instructions(self, text: str):
        """Replace the CodeMirror instructions editor's content.

        CodeMirror does not respond to fill(). On an *empty* editor,
        click + Ctrl+A + keyboard.type() works. On an *already-populated*
        editor (editing an existing skill's instructions), Ctrl+A does not
        reliably select the existing content first — typed text ends up
        inserted rather than replacing it, producing a doubled value
        (``"new text" + "old text"``). Mirrors the same finding documented
        for the Description textarea (:meth:`set_description`) — use
        ``Locator.select_text()`` + Backspace to reliably clear first,
        which works for both empty and populated editors alike.

        Args:
            text: Instructions text to enter.
        """
        self.instructions_editor.click()
        self.page.wait_for_timeout(200)
        self.instructions_editor_content.select_text()
        self.page.wait_for_timeout(100)
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(100)
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

        # Poll for either the nav-blocker confirm button or the detail page URL.
        # The nav-blocker dialog appears ~0-3s after save; dismiss it if it shows.
        import time as _time
        deadline = _time.time() + timeout / 1000
        while _time.time() < deadline:
            # Check if navigation already happened
            if "/skills/all/" in self.page.url and "/create" not in self.page.url:
                logger.info("Navigated to detail page directly (no dialog)")
                break
            # Check if the nav-blocker dialog is visible
            confirm_btn = self.page.get_by_test_id("alert-dialog-confirm-button")
            if confirm_btn.count() > 0 and confirm_btn.is_visible():
                confirm_btn.click()
                logger.info("Dismissed nav-blocker dialog after save")
                break
            self.page.wait_for_timeout(300)

        # Wait for the detail page URL to settle, then for the page to render.
        self.page.wait_for_url("**/skills/all/**", timeout=timeout)
        self.page.get_by_test_id("skill-information-section").wait_for(
            state="visible", timeout=timeout
        )
        self.wait_for_network(timeout=5000)
        logger.info("Saved skill — URL: %s", self.page.url)

    # ------------------------------------------------------------------
    # Read field values
    # ------------------------------------------------------------------

    def get_name(self) -> str:
        """Return the current value of the Name input field.

        The ``skill-name-input`` testid is on the MUI FormControl wrapper,
        not the inner ``<input>``, so the value is read from the descendant
        input element.
        """
        return self.name_input.locator("input").input_value()

    def get_description(self) -> str:
        """Return the current value of the Description field.

        The ``skill-description-input`` testid is on the MUI FormControl
        wrapper; the actual field renders as a ``<textarea>`` (multiline).
        """
        return self.description_input.locator("textarea").first.input_value()

    def get_instructions(self) -> str:
        """Return the current text content of the Instructions CodeMirror editor.

        CodeMirror has no ``input_value()`` — read the rendered text content
        of the ``.cm-content`` element instead, addressed via its own
        ``skill-instructions-editor-content`` testid (set directly on the
        CodeMirror content node via EditorView.contentAttributes in
        EliteaUI, ELITEA-1737) rather than a raw CSS selector chained off
        the wrapper testid.
        """
        return (self.instructions_editor_content.text_content() or "").strip()

    def get_tags(self) -> list[str]:
        """Return the currently committed tags as a list of strings.

        Reads the MUI Chip labels rendered inside the Tags combobox
        (each committed tag renders as a removable chip).

        Returns:
            List of tag name strings, in display order.
        """
        chips = self.tags_input.locator(".MuiChip-label")
        return [chips.nth(i).text_content() or "" for i in range(chips.count())]
