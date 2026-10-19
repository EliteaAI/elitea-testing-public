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

from playwright.sync_api import Page, expect

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

    # ------------------------------------------------------------------
    # Saved (read-only) view — added ELITEA-3315. Confirmed live 2026-10-17:
    # when content already exists, navigating/reloading this page renders a
    # THIRD state neither `create_button` nor `editor_content` covers — a
    # read-only saved view ("Edit with AI" / "Edit" buttons + the content as
    # plain text), distinct from the ?view=create editor CodeMirror state
    # (`editor_content`) that only renders after clicking "Edit" or "Create".
    # Neither prior case (ELITEA-3368/3369) ever called `navigate()` on a
    # project that already had content — both reach the editor only via the
    # in-chat chip/Canvas — so this state had no test exercising it before.
    # ------------------------------------------------------------------
    edit_button = LocatorDescriptor(
        role="button",
        name="Edit",
        exact=True,
        suggested_testid="project-context-edit-button",
        description="Saved-view 'Edit' button — opens the CodeMirror editor "
        "on existing content (confirmed live unique via exact match; "
        "'Edit with AI' is a separate button with a different accessible "
        "name). No data-testid on DEV as of 2026-10-17.",
    )
    saved_content_text = LocatorDescriptor(
        xpath='//button[normalize-space(.)="Edit"]/ancestor::main//p/parent::div',
        suggested_testid="project-context-saved-content-text",
        description="Saved-view read-only content container. Multi-paragraph "
        "content renders as multiple sibling <p> tags (confirmed live with "
        "2 paragraphs), so this targets their shared parent <div> rather than "
        "a bare '//p' (which strict-mode-violates on >1 paragraph) — "
        "non-positional: no numeric predicate, just a relative ancestor/"
        "parent axis search, confirmed live unique (exactly one such parent "
        "under the <main> reached via the saved-view's own 'Edit' button "
        "text match). Rungs 1-4 don't apply: no data-testid on DEV as of "
        "2026-10-17, and label/css have no stable handle for arbitrary "
        "AI-generated prose.",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate(self) -> None:
        """Navigate to /settings/project-context and wait for it to be ready."""
        super().navigate(PROJECT_CONTEXT_PATH)
        self.wait_for_page_load()

    def wait_for_page_load(self, timeout: int = 15000) -> None:
        """Wait for whichever of the three states the server currently
        renders: the empty-state Create button, the CodeMirror editor, or
        the read-only saved view (content exists, not currently editing)."""
        try:
            self.create_button.wait_for(state="visible", timeout=timeout)
            logger.info("Project Context page loaded (empty state)")
            return
        except Exception:
            pass
        try:
            self.editor_content.wait_for(state="visible", timeout=timeout)
            logger.info("Project Context page loaded (editor state)")
            return
        except Exception:
            pass
        self.edit_button.wait_for(state="visible", timeout=timeout)
        logger.info("Project Context page loaded (saved/read-only state)")

    def is_saved_view_showing(self) -> bool:
        """Return True if the read-only saved view (content exists, not
        currently editing) is the state currently rendered."""
        return self.edit_button.count() > 0

    def get_saved_content_text(self) -> str:
        """Return the saved-view's read-only content text."""
        return self.saved_content_text.text_content() or ""

    def click_edit(self) -> None:
        """Click the saved-view 'Edit' button and wait for the CodeMirror
        editor to open with the existing content loaded."""
        self.edit_button.click()
        self.editor_content.wait_for(state="visible", timeout=10000)
        logger.info("Clicked Edit — editor opened on existing content")

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

        Uses condition-based waits throughout (no ``wait_for_timeout``): a
        web-first assertion confirms the clear landed before pasting, another
        confirms the paste landed in the editor, and a third confirms the
        character counter (a separate element, driven by its own slightly
        lagged state update off the same CodeMirror transaction) has caught
        up too — before this method returns, so a caller reading
        :meth:`get_char_counter_text` immediately after never observes a
        stale pre-paste value.

        Args:
            text: Replacement content.
        """
        self.editor_content.click()
        self.editor_content.select_text()
        self.page.keyboard.press("Backspace")
        expect(self.editor_content).to_have_text("", timeout=5000)

        counter_before_paste = self.get_char_counter_text()

        self.page.evaluate(
            "(text) => navigator.clipboard.writeText(text)", text
        )
        paste_shortcut = "Meta+V" if self.page.evaluate("() => navigator.platform.includes('Mac')") else "Control+V"
        self.page.keyboard.press(paste_shortcut)
        expect(self.editor_content).to_have_text(text, timeout=10000)
        expect(self.char_counter).not_to_have_text(counter_before_paste, timeout=5000)
        logger.info("Pasted %d characters into Project Context editor", len(text))

    def type_additional_character(self, char: str = "B") -> None:
        """Press one additional character key with focus still in the editor.

        Used to verify content beyond the character limit is silently
        rejected by CodeMirror's ``maxLength`` transaction filter.

        Waits (condition-based, no ``wait_for_timeout``) for the keystroke to
        be fully processed — i.e. for the rendered content length to settle
        at one of its two possible terminal values: unchanged (rejected) or
        +1 (accepted). This method does not itself assert which outcome
        occurred — that accept/reject verdict is the caller's assertion
        (AFS Step 7); it only waits for CodeMirror's transaction filter to
        finish so the caller reads a settled DOM, not a mid-keystroke one.
        """
        length_before = self.get_editor_content_length()
        self.editor_content.click()
        self.page.keyboard.press(char)
        self.page.wait_for_function(
            """([expectedBefore, expectedAfter]) => {
                const el = document.querySelector('[data-testid="project-context-editor-content"]');
                if (!el) return false;
                const len = el.textContent.length;
                return len === expectedBefore || len === expectedAfter;
            }""",
            arg=[length_before, length_before + len(char)],
            timeout=5000,
        )
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
