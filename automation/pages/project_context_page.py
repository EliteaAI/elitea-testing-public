"""Project Context page object (Settings → Project Context).

Routes (``EliteaUI/src/routes.js``) — the ``?view=`` query param was RETIRED;
there are two real routes:

- ``/settings/project-context``      — empty state (no content) or saved view (content)
- ``/settings/project-context/edit`` — the CodeMirror editor (create AND edit)

Covers the empty-state "Create" flow, the saved view (page title, enable-toggle
card, disabled banner, Edit) and the editor (toolbar, CodeMirror content,
character counter, Save/Discard) for
``EliteaUI/src/[fsd]/features/settings/ui/project-context/``.

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

Locator provenance (ELITEA-2266/2267/2276 — thirteen further testids added
to ``EliteaAI/EliteaUI`` ``automation/testids``): ``project-context-page-title``
rides ``DrawerPageHeader``'s pre-existing ``titleTestId`` prop;
``project-context-toggle-card`` / ``-title`` / ``-description`` /
``project-context-enable-toggle`` are caller-supplied ``testId``-style props on
``EnableToggleCard`` (the switch testid reaches the real ``<input
type="checkbox">`` through MUI's ``slotProps.input``, so ``checked`` state is
assertable); ``project-context-disabled-banner`` is a caller-supplied ``testId``
prop on the SHARED ``BannerMessage`` (defaulting to the pre-existing
``credential-warning-banner``, so every merged caller is untouched);
``project-context-mode-edit-button`` / ``-mode-preview-button`` ride
``TabGroupButton``'s pre-existing ``item.buttonProps`` spread;
``project-context-edit-button``, ``-discard-button``, ``-import-button``,
``-editor-wrapper`` and ``-loader`` are plain ``data-testid`` attributes at
their feature call sites.
"""

import logging

from playwright.sync_api import Locator, Page, expect

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.project_context")

PROJECT_CONTEXT_PATH = "/settings/project-context"
PROJECT_CONTEXT_EDIT_PATH = "/settings/project-context/edit"

#: The single Project Context REST resource. Used ONLY to wait on the product's
#: own request/response (``page.expect_response``) — never to fabricate one.
PROJECT_CONTEXT_API_FRAGMENT = "/elitea_core/project_context/prompt_lib/"
PROJECT_CONTEXT_API_SUFFIX = "/project-context"


class ProjectContextPage(BasePage):
    """Settings → Project Context page (empty state + create/edit editor)."""

    create_button = LocatorDescriptor(
        testid="project-context-create-button",
        description="Empty-state 'Create' button — navigates to /settings/project-context/edit",
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
    page_title = LocatorDescriptor(
        testid="project-context-page-title",
        description="Saved/empty view page header title ('Project Context')",
    )
    toggle_card = LocatorDescriptor(
        testid="project-context-toggle-card",
        description="Saved view's enable-toggle card container (EnableToggleCard root)",
    )
    toggle_card_title = LocatorDescriptor(
        testid="project-context-toggle-card-title",
        description="Enable-toggle card title Typography ('Project Context')",
    )
    toggle_card_description = LocatorDescriptor(
        testid="project-context-toggle-card-description",
        description="Enable-toggle card description Typography (feature explainer)",
    )
    enable_toggle = LocatorDescriptor(
        testid="project-context-enable-toggle",
        description="Enable-toggle switch — the real <input type='checkbox'>, so "
        "checked/unchecked state is directly assertable",
    )
    disabled_banner = LocatorDescriptor(
        testid="project-context-disabled-banner",
        description="'Project Context is turned off…' banner — present only while "
        "the enable toggle is OFF",
    )
    edit_button = LocatorDescriptor(
        testid="project-context-edit-button",
        description="Saved view's 'Edit' button — disabled while the toggle is OFF",
    )
    ai_edit_button = LocatorDescriptor(
        testid="ai-edit-project-context-open-button",
        description="'Edit with AI' button (rendered instead of 'Build with AI' "
        "once content is non-empty) — disabled while the toggle is OFF",
    )
    discard_button = LocatorDescriptor(
        testid="project-context-discard-button",
        description="Editor header's Discard (edit mode) / Cancel (create mode) "
        "button — enabled once isDirty is true",
    )
    import_button = LocatorDescriptor(
        testid="project-context-import-button",
        description="Editor toolbar's 'Import from markdown file' icon button",
    )
    mode_edit_button = LocatorDescriptor(
        testid="project-context-mode-edit-button",
        description="Editor toolbar's code-view ('</>') mode button; selected state "
        "is exposed as aria-pressed",
    )
    mode_preview_button = LocatorDescriptor(
        testid="project-context-mode-preview-button",
        description="Editor toolbar's preview (eye) mode button; selected state is "
        "exposed as aria-pressed",
    )
    editor_wrapper = LocatorDescriptor(
        testid="project-context-editor-wrapper",
        description="Box wrapping the CodeMirror editor — the app-owned scope for "
        "the library-internal gutter handle (see line_number_gutter())",
    )
    loader = LocatorDescriptor(
        testid="project-context-loader",
        description="Full-pane CircularProgress shown while the Project Context "
        "query is in flight",
    )

    #: CodeMirror's line-number gutter. **#579 exception 2** (third-party editor
    #: library internal render node): CodeMirror owns this DOM entirely — it is
    #: not app JSX, so no ``data-testid`` can be placed on it. Always scoped to
    #: the app-owned ``project-context-editor-wrapper`` testid parent via
    #: :meth:`line_number_gutter`. Do NOT extend this handle to any node that
    #: COULD carry a testid.
    EDITOR_GUTTERS = ".cm-gutters"

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
        """Click the empty-state 'Create' button and wait for the editor to open.

        Waits for ``/settings/project-context/edit``. The former
        ``?view=create`` query param was retired in the product (``routes.js``
        now declares two real routes) — this method waited for the dead URL and
        timed out on every run (issue #1794, reproduced 2026-08-26). Repaired
        here rather than weakened: the assertion still pins the exact route the
        product navigates to, so a future rename fails loudly.
        """
        self.create_button.click()
        self.page.wait_for_url(f"**{PROJECT_CONTEXT_EDIT_PATH}", timeout=10000)
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

    def navigate_to_saved_view(self) -> None:
        """Navigate to ``/settings/project-context`` and wait for the SAVED view.

        Additive sibling of :meth:`navigate` (which waits for the empty state's
        Create button or the editor, and is kept byte-identical for its merged
        caller): the saved view renders neither of those, only the enable-toggle
        card, so it needs its own readiness condition.
        """
        super().navigate(PROJECT_CONTEXT_PATH)
        self.wait_for_saved_view()

    def navigate_to_editor(self) -> None:
        """Navigate straight to ``/settings/project-context/edit``.

        Bare-path navigation is this project's own established convention
        (page objects call ``navigate("/…")`` and ``settings.app_base_url``
        supplies ``APP_PREFIX``). The route is unguarded by the enable toggle,
        so this is the only way to reach the editor while the toggle is OFF —
        the saved view's Edit affordance is ``disabled={!enabled}``
        (see ELITEA-2276's AFS § Classification note, clarification #1793).
        """
        super().navigate(PROJECT_CONTEXT_EDIT_PATH)
        self.editor_content.wait_for(state="visible", timeout=15000)
        logger.info("Opened Project Context editor by direct URL")

    def wait_for_saved_view(self, timeout: int = 15000) -> None:
        """Wait for the saved view (content non-empty) — i.e. the toggle card."""
        self.toggle_card.wait_for(state="visible", timeout=timeout)
        logger.info("Project Context saved view loaded")

    def click_edit(self) -> None:
        """Click the saved view's 'Edit' button and wait for the editor route."""
        self.edit_button.click()
        self.page.wait_for_url(f"**{PROJECT_CONTEXT_EDIT_PATH}", timeout=10000)
        self.editor_content.wait_for(state="visible", timeout=10000)
        logger.info("Clicked Edit — editor opened")

    def line_number_gutter(self) -> Locator:
        """Return CodeMirror's line-number gutter, scoped to the editor wrapper.

        **Sanctioned raw-handle exception #579 (case 2 — third-party editor
        library internal render node).** The gutter is rendered by CodeMirror
        itself, not by EliteaUI JSX, so no ``data-testid`` can be placed on it.
        The handle is therefore scoped to a real app testid parent
        (``project-context-editor-wrapper``, a ``LocatorDescriptor`` class
        field) via the class constant :attr:`EDITOR_GUTTERS`.

        Boundary: do NOT extend this exception to any node that COULD carry a
        testid — every app-owned element on this page has one.
        """
        return self.editor_wrapper.locator(self.EDITOR_GUTTERS)

    def _is_project_context_put(self, response) -> bool:
        """True for the product's own PUT on the Project Context resource."""
        return (
            PROJECT_CONTEXT_API_FRAGMENT in response.url
            and response.url.endswith(PROJECT_CONTEXT_API_SUFFIX)
            and response.request.method == "PUT"
        )

    def click_enable_toggle_and_wait_for_put(self, timeout: int = 15000):
        """Flip the enable toggle and return the product's own PUT response.

        The saved view has NO Save button for the toggle —
        ``ProjectContextSavedView.handleToggle`` fires the ``PUT`` immediately
        on change (auto-save, confirmed live). Waiting on the real response is
        both the honest success signal and a condition wait (never a sleep).

        Returns:
            The ``Response`` for the ``PUT`` the product itself issued.
        """
        with self.page.expect_response(self._is_project_context_put, timeout=timeout) as response_info:
            self.enable_toggle.click()
        response = response_info.value
        logger.info("Enable toggle flipped — PUT %s => %s", response.url, response.status)
        return response

    def clear_editor_content(self) -> None:
        """Clear the editor with a real select-all + Backspace keystroke pair.

        Uses ``ControlOrMeta+a`` so the gesture is the one a user performs and
        it passes through CodeMirror's own transaction filter, exactly like
        typed input. A web-first assertion confirms the clear landed before
        returning, so a caller reading the char counter never sees a stale
        pre-clear value.
        """
        self.editor_content.click()
        self.page.keyboard.press("ControlOrMeta+a")
        self.page.keyboard.press("Backspace")
        expect(self.editor_content).to_have_text("", timeout=5000)
        logger.info("Cleared Project Context editor content")

    def click_save_and_wait_for_put(self, timeout: int = 15000):
        """Click Save and return the product's own PUT response.

        Additive sibling of :meth:`click_save` (left byte-identical for its
        merged caller): this variant hands the real response back so a spec can
        assert the case's "saves without error" on the product's own status
        code rather than on the toast alone.
        """
        with self.page.expect_response(self._is_project_context_put, timeout=timeout) as response_info:
            self.save_button.click()
        response = response_info.value
        self.toast_message.wait_for(state="visible", timeout=10000)
        self.page.wait_for_url(lambda url: url.endswith(PROJECT_CONTEXT_PATH), timeout=10000)
        logger.info("Saved Project Context — PUT => %s", response.status)
        return response
