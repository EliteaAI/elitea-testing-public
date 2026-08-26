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
    build_with_ai_button = LocatorDescriptor(
        testid="project-context-build-with-ai-button",
        description="Empty-state 'Build with AI' button — navigates to "
        "/settings/project-context/edit AND auto-opens the generate-draft dialog "
        "(onNavigate('create', { openAi: true }))",
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

    saved_content = LocatorDescriptor(
        testid="project-context-saved-content",
        description="Saved view's content area — the Box rendering the stored "
        "Project Context as formatted markdown",
    )
    preview_pane = LocatorDescriptor(
        testid="project-context-preview",
        description="Markdown preview pane — replaces the CodeMirror editor entirely "
        "while preview (eye) mode is selected",
    )

    #: The "Edit with AI" dialog opened from THIS page's editor toolbar
    #: (``AIEditProjectContextModal.jsx``). Its open button is
    #: :attr:`ai_edit_button` above; these two complete the open→cancel pair
    #: ELITEA-2270 exercises. Both testids pre-exist in EliteaUI — nothing was
    #: added for them. A full page object for the dialog's refine/apply wizard is
    #: deliberately not built here: no case has needed it yet.
    ai_edit_modal = LocatorDescriptor(
        testid="ai-edit-project-context-modal",
        description="'Edit with AI' modal container (MUI Dialog root; no keepMounted, "
        "so its count is 0 while closed)",
    )
    ai_edit_cancel_button = LocatorDescriptor(
        testid="ai-edit-project-context-cancel-button",
        description="'Edit with AI' dialog's Cancel button (prompt step) — closes it "
        "without refining anything",
    )

    #: CodeMirror's line-number gutter. **#579 exception 2** (third-party editor
    #: library internal render node): CodeMirror owns this DOM entirely — it is
    #: not app JSX, so no ``data-testid`` can be placed on it. Always scoped to
    #: the app-owned ``project-context-editor-wrapper`` testid parent via
    #: :meth:`line_number_gutter`. Do NOT extend this handle to any node that
    #: COULD carry a testid.
    EDITOR_GUTTERS = ".cm-gutters"

    #: CodeMirror's per-line render nodes and its line-number gutter elements.
    #: **#579 exception 2** (third-party editor library internal render nodes),
    #: same node family and same discipline as :attr:`EDITOR_GUTTERS`: CodeMirror
    #: renders this DOM itself, so no ``data-testid`` can be placed on it. Always
    #: scoped to the app-owned ``project-context-editor-wrapper`` testid parent.
    #: Needed because ``.cm-content``'s ``textContent`` concatenates the document
    #: with NO newlines ("## H- a- b"), so a multi-line body can only be asserted
    #: line by line.
    EDITOR_LINES = ".cm-line"
    #: ``:visible`` excludes CodeMirror's hidden width-measuring element (renders
    #: the text "9" with ``visibility: hidden``), leaving exactly the real numbers.
    EDITOR_LINE_NUMBERS = ".cm-lineNumbers .cm-gutterElement:visible"

    #: react-markdown's rendered output inside the preview pane. **#579**
    #: (third-party library internal render nodes — named explicitly in
    #: ``.agents/testing.md`` § Locator policy). Always scoped to the app-owned
    #: ``project-context-preview`` testid parent: the app sidebar renders its own
    #: ``<li>`` elements, so an unscoped handle cannot disambiguate.
    PREVIEW_HEADING_2 = "h2"
    PREVIEW_LIST_ITEM = "li"

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

    def click_build_with_ai(self) -> None:
        """Click the EMPTY STATE's 'Build with AI' button and wait for the editor route.

        Additive sibling of :meth:`click_create` (left byte-identical for its
        merged callers): this button navigates to the same
        ``/settings/project-context/edit`` route but with router state
        ``{ openAi: true }``, which ``ProjectContextEditor``'s first-render
        effect turns into an auto-opened generate-draft dialog. The dialog
        itself is driven by
        :class:`~pages.generate_project_context_modal_page.GenerateProjectContextModalPage`,
        so this method deliberately waits only on the route — the caller asserts
        the dialog.

        Note the editor's CodeMirror pane is NOT waited on here: the auto-opened
        dialog sits over it, and waiting for a covered element is a needless
        race.
        """
        self.build_with_ai_button.click()
        self.page.wait_for_url(f"**{PROJECT_CONTEXT_EDIT_PATH}", timeout=10000)
        logger.info("Clicked empty-state 'Build with AI' — editor route opened")

    def open_ai_edit_modal(self) -> None:
        """Open the editor toolbar's 'Edit with AI' dialog and wait for it.

        Only reachable while the editor content is NON-empty:
        ``ProjectContextEditor.jsx`` renders ``content.trim() ?
        <AIEditProjectContextButton/> : <GenerateProjectContextButton/>``, so on
        an untouched editor this button does not exist at all (clarification
        #1797).
        """
        self.ai_edit_button.click()
        self.ai_edit_modal.wait_for(state="visible", timeout=10000)
        logger.info("Opened the 'Edit with AI' dialog")

    def cancel_ai_edit_modal(self) -> None:
        """Cancel the 'Edit with AI' dialog and wait for it to close.

        Cancelling from the prompt step issues no network request, so the
        dialog's removal from the DOM is the only readiness condition.
        """
        self.ai_edit_cancel_button.click()
        self.ai_edit_modal.wait_for(state="detached", timeout=10000)
        logger.info("Cancelled the 'Edit with AI' dialog")

    def import_markdown_file(self, file_path: str, expected_lines: list[str]) -> bool:
        """Import *file_path* through the toolbar's 'Import from markdown file' control.

        The product clicks a hidden ``<input type="file" accept=".md,text/markdown">``
        programmatically (``handleImportClick`` → ``fileInputRef.current.click()``),
        which raises the browser's native OS file picker. Playwright's
        ``expect_file_chooser`` intercepts that picker — the gesture a user's OS
        dialog performs — leaving the application's own ``handleFileUpload`` /
        ``FileReader`` path completely intact. This is **not** a substitution of
        the system under test: the product still reads and parses the file.

        The hidden ``<input>`` carries no ``data-testid`` and should not get one —
        it is never referenced by a locator on any test's executed path (#511);
        the chooser is a browser event, not a DOM handle.

        Args:
            file_path: Absolute path to the ``.md`` file to import.
            expected_lines: The file's own lines, used as the web-first wait
                condition so the caller never reads a half-applied editor.

        Returns:
            ``True`` when the chooser accepted a single file only (the product
            handles ``files?.[0]``), so the caller can assert that contract.
        """
        with self.page.expect_file_chooser(timeout=10000) as chooser_info:
            self.import_button.click()
        chooser = chooser_info.value
        is_single_file = not chooser.is_multiple()
        chooser.set_files(file_path)
        expect(self.editor_lines()).to_have_text(expected_lines, timeout=10000)
        logger.info("Imported %s (%d lines) into the Project Context editor", file_path, len(expected_lines))
        return is_single_file

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

    def editor_lines(self) -> Locator:
        """Return CodeMirror's per-line nodes, scoped to the editor wrapper.

        **Sanctioned raw-handle exception #579 (case 2 — third-party editor
        library internal render node)**, identical in kind to
        :meth:`line_number_gutter`: CodeMirror owns this DOM, so no
        ``data-testid`` can be placed on a line. Scoped to the app-owned
        ``project-context-editor-wrapper`` testid parent via the class constant
        :attr:`EDITOR_LINES`.

        Why it is needed rather than a plain text assertion on
        ``project-context-editor-content``: CodeMirror renders every line as its
        own ``div``, so the content node's ``textContent`` runs the document
        together with **no newlines** — ``"## Project Overview- First bullet"``.
        A multi-line body is therefore only assertable line by line.

        Boundary: do NOT extend this exception to any node that COULD carry a
        testid — every app-owned element on this page has one.
        """
        return self.editor_wrapper.locator(self.EDITOR_LINES)

    def get_editor_lines(self) -> list[str]:
        """Return the editor's rendered lines, in document order.

        Blank lines come back as ``""`` (confirmed live 2026-08-26).
        """
        return self.editor_lines().all_text_contents()

    def line_numbers(self) -> Locator:
        """Return the editor's visible line-number elements (see :attr:`EDITOR_LINE_NUMBERS`).

        Same #579 exception-2 scope as :meth:`line_number_gutter`, one level
        finer so the *numbers themselves* can be asserted rather than merely the
        gutter's presence.
        """
        return self.editor_wrapper.locator(self.EDITOR_LINE_NUMBERS)

    def preview_headings(self) -> Locator:
        """Return the level-2 headings react-markdown rendered in the preview pane.

        **Sanctioned raw-handle exception #579** (third-party library internal
        render nodes — ``.agents/testing.md`` § Locator policy names
        react-markdown output explicitly). react-markdown generates this DOM from
        the markdown source, so the heading is not app JSX and cannot carry a
        testid. Scoped to the app-owned ``project-context-preview`` testid parent
        via :attr:`PREVIEW_HEADING_2`.

        Boundary: the pane container itself DOES carry a testid
        (``project-context-preview``, added for exactly this reason) — do not use
        a page-level handle for anything here.
        """
        return self.preview_pane.locator(self.PREVIEW_HEADING_2)

    def preview_list_items(self) -> Locator:
        """Return the list items react-markdown rendered in the preview pane.

        Same #579 exception and same scoping as :meth:`preview_headings`. The
        scoping is load-bearing rather than stylistic: the application sidebar
        renders its own ``<li>`` elements, so an unscoped handle would match nine
        navigation entries alongside the two bullets under test.
        """
        return self.preview_pane.locator(self.PREVIEW_LIST_ITEM)

    def paste_markdown(self, text: str) -> None:
        """Replace the editor's content with multi-line *text* via a real paste.

        Additive sibling of :meth:`set_editor_content_via_paste` (left
        byte-identical for its merged ELITEA-2272 caller), which waits on
        ``expect(editor_content).to_have_text(text)`` — an assertion a multi-line
        body can never satisfy, because ``.cm-content``'s ``textContent`` carries
        no newlines. This variant waits per line instead.

        **Paste, not keystrokes, is required for markdown.** CodeMirror's
        ``markdown()`` extension auto-continues list items on Enter: typing
        ``"## H\\n- a\\n- b\\nplain"`` character by character produced
        ``"- - b"`` and ``"  - plain"`` live (2026-08-26). A paste is a single
        transaction with no Enter keypresses and lands the text verbatim, while
        still passing through CodeMirror's own ``EditorState.transactionFilter``
        exactly like typed input.

        The clipboard write is the only ``page.evaluate`` here and is not a
        substitution of the system under test: it loads the *browser's*
        clipboard so the paste gesture has something to paste; the product still
        processes the paste itself. Same pattern as
        :meth:`set_editor_content_via_paste`.

        Args:
            text: Replacement content; ``\\n``-separated lines.
        """
        self.editor_content.click()
        self.page.keyboard.press("ControlOrMeta+a")
        self.page.keyboard.press("Backspace")
        expect(self.editor_content).to_have_text("", timeout=5000)

        self.page.evaluate("(text) => navigator.clipboard.writeText(text)", text)
        self.page.keyboard.press("ControlOrMeta+v")
        expect(self.editor_lines()).to_have_text(text.split("\n"), timeout=10000)
        logger.info("Pasted %d markdown lines into Project Context editor", len(text.split("\n")))

    def type_at_end_of_content(self, text: str) -> None:
        """Move the caret to the end of the document and type *text* for real.

        ``ControlOrMeta+End`` is CodeMirror's own document-end binding, so this
        is the gesture a user performs — no ``evaluate``, no injected state.
        A web-first assertion confirms the keystrokes landed before returning.
        """
        self.editor_content.click()
        self.page.keyboard.press("ControlOrMeta+End")
        self.page.keyboard.type(text)
        expect(self.editor_lines().last).to_contain_text(text.split("\n")[-1], timeout=5000)
        logger.info("Typed %r at the end of the Project Context editor", text)

    def click_preview_mode(self) -> None:
        """Switch the editor to preview (eye) mode and wait for the swap.

        The two panes are mutually exclusive (``mode === 'edit' ? <CodeMirror> :
        <Markdown>``), so the readiness condition is the CodeMirror pane being
        GONE plus the preview pane being visible — not a timeout.
        """
        self.mode_preview_button.click()
        expect(self.mode_preview_button).to_have_attribute("aria-pressed", "true")
        expect(self.preview_pane).to_be_visible(timeout=10000)
        expect(self.editor_content).to_have_count(0)
        logger.info("Switched Project Context editor to preview mode")

    def click_code_view_mode(self) -> None:
        """Switch the editor back to code view (``</>``) mode and wait for the swap."""
        self.mode_edit_button.click()
        expect(self.mode_edit_button).to_have_attribute("aria-pressed", "true")
        expect(self.editor_content).to_be_visible(timeout=10000)
        expect(self.preview_pane).to_have_count(0)
        logger.info("Switched Project Context editor to code-view mode")

    def click_discard(self) -> None:
        """Click Discard and wait for the product's own reaction.

        ``ProjectContextEditor.handleDiscard`` clears ``isDirty`` and calls
        ``onNavigate('saved')`` — Discard **leaves the editor** rather than
        staying put with reverted text (confirmed live 2026-08-26). The wait
        therefore pins the saved route and the saved view, which is what the
        product actually does.

        Note the sibling label: this same button reads ``Cancel`` in create mode
        and calls ``handleCancel`` (→ empty state), a different flow. Callers
        that depend on edit-mode semantics should assert the label first.
        """
        self.discard_button.click()
        self.page.wait_for_url(lambda url: url.endswith(PROJECT_CONTEXT_PATH), timeout=10000)
        self.wait_for_saved_view()
        logger.info("Discarded Project Context edits — returned to the saved view")

    def is_discard_enabled(self) -> bool:
        """Return True if the Discard/Cancel button is currently enabled."""
        return self.discard_button.is_enabled()

    def saved_content_headings(self) -> Locator:
        """Return the level-2 headings react-markdown rendered in the SAVED view.

        Same **#579** exception and same discipline as :meth:`preview_headings`
        (react-markdown owns this DOM, so the heading itself cannot carry a
        testid), scoped here to the saved view's own app-owned container
        ``project-context-saved-content``. Scoping matters: the settings page
        renders other headings outside this container.
        """
        return self.saved_content.locator(self.PREVIEW_HEADING_2)
