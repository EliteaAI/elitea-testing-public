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

    instructions_edit_mode_button = LocatorDescriptor(
        testid="skill-instructions-edit-mode-button",
        description="Instructions Edit/Preview toggle — Edit mode button (ELITEA-2432)"
    )

    instructions_preview_mode_button = LocatorDescriptor(
        testid="skill-instructions-preview-mode-button",
        description="Instructions Edit/Preview toggle — Preview mode button (ELITEA-2432)"
    )

    instructions_preview_content = LocatorDescriptor(
        testid="skill-instructions-preview-content",
        description="Instructions Preview-mode rendered Markdown container (ELITEA-2432)"
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

    name_input_field = LocatorDescriptor(
        testid="skill-name-input-field",
        description="Skill name — real <input> element (skill-name-input is the wrapper)"
    )

    description_input_field = LocatorDescriptor(
        testid="skill-description-input-field",
        description="Skill description — real <textarea> element (skill-description-input is the wrapper)"
    )

    tags_input_field = LocatorDescriptor(
        testid="skill-tags-input-field",
        description="Tags combobox — real <input> element (skill-tags-input is the wrapper)"
    )

    tag_chip = LocatorDescriptor(
        testid="skill-tag-chip",
        description="Committed tag chip (one per tag; shared testid, collection locator)"
    )

    # Dynamic (runtime-parameterized) testid template — Tags autocomplete
    # option for a previously-created project tag. See
    # ``select_existing_tag()``.
    SKILL_TAG_OPTION = '[data-testid="skill-tag-option-{}"]'

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def wait_for_form_load(self, timeout: int = 15000):
        """Wait for the skill create/edit form to be fully loaded.

        Waits for the Name input to be visible and network to settle.
        """
        self.name_input.wait_for(state="visible", timeout=timeout)
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

    @action("Set name")
    def set_name(self, name: str):
        """Replace the Name field's content (works on pre-filled fields).

        Mirrors :meth:`set_description` exactly — the wrapper-level click +
        Ctrl+A pattern in :meth:`fill_form`/:meth:`_fill_text_input` only
        reliably clears an *empty* field; ``Control+a`` alone does not
        reliably select existing content first (typed text ends up inserted
        rather than replacing it, or an empty ``text`` argument leaves the
        prior value in place since a bare selection with nothing typed over
        it does not clear the field). Uses ``Locator.select_text()`` +
        Backspace to reliably clear the real, editable input (addressed
        directly via its own ``skill-name-input-field`` testid, set on the
        real element via MUI's ``inputProps``/``htmlInput`` slot, not a raw
        CSS chain off the ``skill-name-input`` wrapper testid) before typing
        the replacement — needed for a step that must clear an
        already-populated Name field back to empty.

        Args:
            name: New name text (pass ``""`` to clear the field).
        """
        field = self.name_input_field
        field.click()
        field.select_text()
        self.page.wait_for_timeout(100)
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(100)
        if name:
            self.page.keyboard.type(name)
        self.page.wait_for_timeout(300)
        logger.info("Set name: %r", name[:60])

    @action("Set description")
    def set_description(self, description: str):
        """Replace the Description field's content (works on pre-filled fields).

        The Description field renders as two ``<textarea>`` elements (MUI's
        autosize shadow copy plus the real, editable one) — the wrapper-level
        click + Ctrl+A pattern in :meth:`fill_form` only reliably clears an
        *empty* field; ``Control+a`` alone does not reliably select existing
        content here (typed text ends up inserted rather than replacing it).
        Uses Locator.select_text() + Backspace to clear the real, editable
        textarea (addressed directly via its own
        ``skill-description-input-field`` testid, set on the real element via
        MUI's ``inputProps``/``htmlInput`` slot, not a raw CSS chain off the
        ``skill-description-input`` wrapper testid) before typing the
        replacement.

        Args:
            description: New description text.
        """
        field = self.description_input_field
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
        the root wrapper); the actual text input carries its own
        ``skill-tags-input-field`` testid.

        Args:
            tag: Tag text to type and commit.
        """
        tag_field = self.tags_input_field
        tag_field.click()
        tag_field.type(tag)
        tag_field.press("Enter")
        self.page.wait_for_timeout(200)
        logger.info("Added tag: %r", tag)

    @action("Select existing tag from autocomplete")
    def select_existing_tag(self, tag_name: str, timeout: int = 5000):
        """Select a previously-created tag from the Tags autocomplete dropdown.

        Unlike :meth:`add_tag` (type + Enter, which commits a brand-new tag),
        this selects an existing project-scoped tag suggestion — confirmed
        live (ELITEA-1740 AFS exploration): once a tag exists in the project,
        later skills' Tags combobox surfaces it as a clickable option in the
        MUI Autocomplete listbox. Each option carries its own
        ``skill-tag-option-{tag_name}`` testid (set directly on the
        ``<li role="option">`` node), addressed via the
        :attr:`SKILL_TAG_OPTION` class-level template constant rather than
        an inline per-call testid lookup.

        Args:
            tag_name: Existing tag text to select from the dropdown.
            timeout: Maximum wait time in milliseconds for the option to appear.
        """
        tag_field = self.tags_input_field
        tag_field.click()
        tag_field.type(tag_name)
        option = self.page.locator(self.SKILL_TAG_OPTION.format(tag_name))
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        self.page.wait_for_timeout(200)
        logger.info("Selected existing tag: %r", tag_name)

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

    @action("Fill instructions editor with Markdown source (list-safe)")
    def fill_instructions_markdown(self, text: str):
        """Replace the CodeMirror instructions editor's content with raw
        Markdown source that may contain multi-line lists (ELITEA-2432).

        Same reliable-clear mechanism as :meth:`fill_instructions`
        (``select_text()`` + Backspace, works on both empty and populated
        editors), but inserts via ``Keyboard.insert_text()`` instead of
        ``Keyboard.type()``. Confirmed live: this editor's markdown
        language mode (``@codemirror/lang-markdown``) auto-continues an
        unordered list on Enter — ``keyboard.type()`` dispatches a
        discrete Enter keydown for every ``\\n`` in the typed text, which
        triggers that continuation and inserts an extra ``"- "`` at the
        start of the line right after a list-item line, corrupting any
        typed multi-line list Markdown (e.g. typing
        ``"- Item one\\n- Item two"`` renders as
        ``"- Item one\\n- - Item two"``). ``keyboard.insert_text()`` inserts
        the whole string as one atomic operation with no discrete Enter
        keydown, so the list-continuation keymap never fires, while still
        triggering the editor's real input handling (confirmed live: the
        character counter and React form state update correctly).

        Args:
            text: Markdown instructions text to enter verbatim.
        """
        self.instructions_editor.click()
        self.page.wait_for_timeout(200)
        self.instructions_editor_content.select_text()
        self.page.wait_for_timeout(100)
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(100)
        self.page.keyboard.insert_text(text)
        self.page.wait_for_timeout(300)
        logger.info("Filled instructions editor with Markdown source (list-safe)")

    # ------------------------------------------------------------------
    # Instructions Edit/Preview toggle (ELITEA-2432)
    # ------------------------------------------------------------------

    @action("Switch Instructions to Edit mode")
    def click_edit_mode(self, timeout: int = 5000):
        """Switch the Instructions section to Edit mode (raw Markdown/CodeMirror).

        100% client-side toggle (local ``useState`` in ``CreateSkillForm.jsx``) —
        no network wait needed, only a short settle for the view swap.
        """
        self.instructions_edit_mode_button.click()
        self.page.wait_for_timeout(200)
        logger.info("Switched Instructions to Edit mode")

    @action("Switch Instructions to Preview mode")
    def click_preview_mode(self, timeout: int = 5000):
        """Switch the Instructions section to Preview mode (rendered Markdown).

        100% client-side toggle — no network wait needed, only a short
        settle for the view swap.
        """
        self.instructions_preview_mode_button.click()
        self.page.wait_for_timeout(200)
        logger.info("Switched Instructions to Preview mode")

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
        not the inner ``<input>`` — the real element carries its own
        ``skill-name-input-field`` testid.
        """
        return self.name_input_field.input_value()

    def get_description(self) -> str:
        """Return the current value of the Description field.

        The ``skill-description-input`` testid is on the MUI FormControl
        wrapper; the actual ``<textarea>`` carries its own
        ``skill-description-input-field`` testid.
        """
        return self.description_input_field.input_value()

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

    def get_instructions_multiline(self) -> str:
        """Return the Instructions CodeMirror editor's text content,
        preserving line breaks (ELITEA-2432).

        :meth:`get_instructions` reads ``text_content()``, which
        concatenates CodeMirror's per-line ``<div class="cm-line">``
        elements with NO separator — correct for the single-line
        instructions every other caller of :meth:`get_instructions` uses,
        but confirmed live to silently drop every line break for
        multi-line content (a 3-line Markdown source round-trips as one
        unbroken string via ``text_content()``). ``inner_text()`` is
        layout-aware — Playwright inserts a newline between adjacent
        block-level elements — so it reconstructs the editor's line breaks
        correctly with no new selector needed (each ``cm-line`` div is
        already block-level).
        """
        return (self.instructions_editor_content.inner_text() or "").strip()

    def get_preview_content(self) -> str:
        """Return the rendered Markdown text content of the Instructions
        Preview pane (ELITEA-2432).

        Reads ``text_content()`` of the ``skill-instructions-preview-content``
        container — the app's shared ``Markdown`` component renders bold/list/etc.
        as real HTML nodes with the raw Markdown syntax characters (``**``, ``- ``)
        stripped, so this text can be compared directly against the raw source
        from :meth:`get_instructions` to prove real interpretation happened.
        Only meaningful while the Preview mode is active (see :meth:`click_preview_mode`).
        """
        return (self.instructions_preview_content.text_content() or "").strip()

    def get_tags(self) -> list[str]:
        """Return the currently committed tags as a list of strings.

        Reads each committed-tag chip via the shared ``skill-tag-chip``
        testid (one element per tag; the delete icon is an SVG with no
        text nodes, so each chip's text content is exactly its tag name).

        Returns:
            List of tag name strings, in display order.
        """
        chips = self.tag_chip
        return [chips.nth(i).text_content() or "" for i in range(chips.count())]
