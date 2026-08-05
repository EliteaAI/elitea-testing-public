"""Project Context page object (Settings → Project Context).

URL: /settings/project-context (empty-state / saved view) or
     /settings/project-context?view=create (editor)

Covers the empty-state "Create" flow and the editor (CodeMirror content,
character counter, Save) for ``EliteaUI/src/[fsd]/features/settings/ui/project-context/``.

Locator provenance (ELITEA-2272 — all four testids new, none pre-existing):
``project-context-create-button`` is a plain ``data-testid`` on the empty
state's "Create" ``Button.BaseBtn`` (``ProjectContextEmptyState.jsx``, same
call-site pattern as ``skill-save-button`` in ``SaveSkillButton.jsx``).
``project-context-save-button`` is the same pattern on the editor's Save
``Button.BaseBtn`` (``ProjectContextEditor.jsx``). ``project-context-editor-content``
wires the shared ``Field.CodeMirrorEditor``'s pre-existing ``contentTestId``
prop (the SAME mechanism ``skill-instructions-editor-content`` and
``toolkit-raw-json-editor-content`` already use — ``CodeMirrorEditor.jsx``
applies it to the internal ``.cm-content`` node via
``EditorView.contentAttributes``, since CodeMirror renders its own DOM).
``project-context-char-counter`` is a plain ``data-testid`` on the character-
counter ``Typography``.

The Discard/Cancel button carries no testid — out of scope for this case
(never clicked; see the AFS's Concrete Handles "not touched" list and the
Phase-2 amendment on AFS step 3).
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.project_context")

PROJECT_CONTEXT_PATH = "/settings/project-context"


class ProjectContextPage(BasePage):
    """Settings → Project Context page (empty state + create/edit editor)."""

    create_button = LocatorDescriptor(
        testid="project-context-create-button",
        description="Empty-state 'Create' button — navigates to ?view=create",
    )
    editor_content = LocatorDescriptor(
        testid="project-context-editor-content",
        description="CodeMirror editor content node (.cm-content) — the "
        "editable Project Context markdown body",
    )
    save_button = LocatorDescriptor(
        testid="project-context-save-button",
        description="Editor header's Save button — enabled once isDirty is true",
    )
    char_counter = LocatorDescriptor(
        testid="project-context-char-counter",
        description="'<N> characters left...' counter Typography, editor header",
    )
    toast_message = LocatorDescriptor(
        testid="toast-message",
        description="Generic app-wide success toast (reused — see "
        "NotificationCenterPage.success_toast_message / ArtifactsPage.success_toast_message).",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate(self) -> None:
        """Navigate to /settings/project-context and wait for it to be ready."""
        super().navigate(PROJECT_CONTEXT_PATH)
        self.wait_for_page_load()

    def wait_for_page_load(self, timeout: int = 15000) -> None:
        """Wait for either the empty-state Create button or the editor content
        to become visible — whichever the current server state renders."""
        try:
            self.create_button.wait_for(state="visible", timeout=timeout)
        except Exception:
            self.editor_content.wait_for(state="visible", timeout=timeout)
        logger.info("Project Context page loaded")

    def click_create(self) -> None:
        """Click the empty-state 'Create' button and wait for the editor to open."""
        self.create_button.click()
        self.page.wait_for_url(f"**{PROJECT_CONTEXT_PATH}?view=create", timeout=10000)
        self.editor_content.wait_for(state="visible", timeout=10000)
        logger.info("Clicked Create — editor opened")

    def set_editor_content_via_paste(self, text: str) -> None:
        """Replace the editor's content by clearing it, then clipboard-pasting *text*.

        CodeMirror does not respond to ``fill()``. Clears any existing content
        with ``select_text()`` + Backspace (mirrors
        :meth:`SkillFormPage.fill_instructions`), then writes *text* to the
        system clipboard and pastes it via ``Control+V``/``Meta+V`` — confirmed
        live to pass through CodeMirror's ``EditorState.transactionFilter``
        identically to native typing, and is dramatically faster than
        per-keystroke ``type()`` for a 2500-character fill.

        Args:
            text: Replacement content.
        """
        self.editor_content.click()
        self.editor_content.select_text()
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(100)

        self.page.evaluate(
            "(text) => navigator.clipboard.writeText(text)", text
        )
        paste_shortcut = "Meta+V" if self.page.evaluate("() => navigator.platform.includes('Mac')") else "Control+V"
        self.page.keyboard.press(paste_shortcut)
        self.page.wait_for_timeout(300)
        logger.info("Pasted %d characters into Project Context editor", len(text))

    def type_additional_character(self, char: str = "B") -> None:
        """Press one additional character key with focus still in the editor.

        Used to verify content beyond the character limit is silently
        rejected by CodeMirror's ``maxLength`` transaction filter.
        """
        self.editor_content.click()
        self.page.keyboard.press(char)
        self.page.wait_for_timeout(200)
        logger.info("Pressed additional character %r in editor", char)

    def get_editor_content_length(self) -> int:
        """Return the current character count of the editor's rendered content."""
        return len(self.editor_content.text_content() or "")

    def get_char_counter_text(self) -> str:
        """Return the character counter's rendered text, whitespace-normalized."""
        return " ".join((self.char_counter.text_content() or "").split())

    def is_save_enabled(self) -> bool:
        """Return True if the Save button is currently enabled."""
        return self.save_button.is_enabled()

    def click_save(self) -> None:
        """Click Save and wait for the success toast, then for the URL to
        revert to the saved (non-create) view."""
        self.save_button.click()
        self.toast_message.wait_for(state="visible", timeout=10000)
        self.page.wait_for_url(
            lambda url: url.endswith(PROJECT_CONTEXT_PATH), timeout=10000
        )
        logger.info("Saved Project Context")

    def get_toast_text(self) -> str:
        """Return the currently-visible toast message text."""
        return (self.toast_message.text_content() or "").strip()
