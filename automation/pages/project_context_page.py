"""Project Context page object (Settings → Project Context).

URL: /settings/project-context (empty-state / saved view) or
     /settings/project-context/edit (editor — confirmed live 2026-10-16; see
     the ELITEA-3252/3253/3254/3255 family AFS, which supersedes this
     module's older ``?view=create`` provenance note below)

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

**Extended for ELITEA-3252/3253/3254/3255** (Build-with-AI create flow,
Edit-with-AI edit flow, Activation description field). Locator provenance for
the new fields:

- ``project-context-activation-description`` — NEW plain ``<input>`` testid,
  confirmed live on DEV 2026-10-16 (not present at ELITEA-2272's 2026-08-05
  analysis). Required (non-empty) for Save to enable on the create/edit flow
  — ``isDirty`` on the editor content alone is NO LONGER sufficient (a
  shared-component regression risk flagged in the family AFS's Axis 2 notes;
  ELITEA-2272's own test file was removed from the suite independently by
  commit 3fcc1478 — "unstable UI tests" cleanup — so there is no live
  regression to re-verify here, confirmed via ``git log --diff-filter=D``).
- ``ai-edit-project-context-*`` — NEW testids on the Edit-with-AI modal
  (open button, modal container, close, prompt input, cancel, generate,
  error alert), all confirmed live on DEV.
- The empty-state "Build with AI" button and everything inside its dialog
  (textarea, "Generate Draft", review-step "Apply") carry NO testid yet
  (confirmed via live ``[data-testid]`` enumeration) — declared on the
  `role`+`name` / `css` ladder rungs below, each with a `suggested_testid=`.
"""

import logging

from playwright.sync_api import Page, expect

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor, ScopedLocator

logger = logging.getLogger("elitea.pages.project_context")

PROJECT_CONTEXT_PATH = "/settings/project-context"
PROJECT_CONTEXT_EDIT_PATH = "/settings/project-context/edit"


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

    # ------------------------------------------------------------------
    # ELITEA-3252/3255 — Activation description (NEW field, required for Save)
    # ------------------------------------------------------------------
    activation_description = LocatorDescriptor(
        testid="project-context-activation-description",
        description="'When should this context be used?' input, max 300 chars. "
        "NEW since ELITEA-2272 — required non-empty for Save to enable.",
    )

    # ------------------------------------------------------------------
    # ELITEA-3252/3253 — empty-state "Build with AI" dialog (no testids yet
    # on DEV — confirmed via live [data-testid] enumeration; ladder rungs
    # below with suggested_testid= hints)
    # ------------------------------------------------------------------
    build_with_ai_button = LocatorDescriptor(
        role="button",
        name="Build with AI",
        exact=True,
        suggested_testid="project-context-build-with-ai-button",
        description="Empty-state 'Build with AI' button — opens the AI-generation dialog.",
    )
    build_with_ai_dialog = LocatorDescriptor(
        role="dialog",
        suggested_testid="project-context-build-with-ai-dialog",
        description="The 'Build with AI' modal (prompt step + review step share one dialog).",
    )
    BUILD_WITH_AI_PROMPT_INPUT = ScopedLocator(
        css='textarea[placeholder^="Describe your project"]',
        suggested_testid="project-context-build-with-ai-prompt-input",
        description="Dialog's prompt textarea — stable css on the placeholder prefix "
        "(the field has no label/aria-label; the placeholder text itself is the only "
        "unique, stable handle).",
    )
    BUILD_WITH_AI_GENERATE_BUTTON = ScopedLocator(
        role="button",
        name="Generate Draft",
        suggested_testid="project-context-build-with-ai-generate-button",
        description="Dialog's 'Generate Draft' button — disabled until the prompt is non-empty.",
    )
    BUILD_WITH_AI_APPLY_BUTTON = ScopedLocator(
        role="button",
        name="Apply",
        exact=True,
        suggested_testid="project-context-build-with-ai-apply-button",
        description="Review step's 'Apply' button — applies the generated draft to the main editor.",
    )
    BUILD_WITH_AI_ERROR_ALERT = ScopedLocator(
        role="alert",
        suggested_testid="project-context-build-with-ai-error-alert",
        description="Inline MUI Alert shown on a 422 (generated draft would exceed 2500 chars).",
    )
    BUILD_WITH_AI_REVIEW_DRAFT = ScopedLocator(
        css="textarea:not([aria-hidden='true'])",
        suggested_testid="project-context-build-with-ai-review-draft",
        description="Review step's editable 'Project Background' textarea — the dialog's "
        "only non-aria-hidden textarea once generation succeeds (MUI's multiline "
        "TextField renders a second, aria-hidden sizing-mirror textarea alongside "
        "the real one; this excludes it, confirmed live).",
    )

    # ------------------------------------------------------------------
    # ELITEA-3255 — saved-view "Edit with AI" modal (all NEW testids,
    # confirmed live on DEV)
    # ------------------------------------------------------------------
    ai_edit_open_button = LocatorDescriptor(
        testid="ai-edit-project-context-open-button",
        description="Saved-view 'Edit with AI' button — visible directly, no separate "
        "'Edit' click needed first (case-text drift — see the family AFS's Known Defects).",
    )
    ai_edit_modal = LocatorDescriptor(
        testid="ai-edit-project-context-modal",
        description="'Edit with AI' modal container.",
    )
    ai_edit_prompt_input = LocatorDescriptor(
        testid="ai-edit-project-context-prompt-input",
        description="'Edit with AI' modal's edit-instruction prompt input.",
    )
    ai_edit_generate_button = LocatorDescriptor(
        testid="ai-edit-project-context-generate-button",
        description="'Edit with AI' modal's 'Generate Draft' button.",
    )
    ai_edit_error_alert = LocatorDescriptor(
        testid="ai-edit-project-context-error-alert",
        description="'Edit with AI' modal's inline error Alert on a 422 overflow.",
    )
    AI_EDIT_APPLY_SAVE_BUTTON = ScopedLocator(
        role="button",
        name="Apply & Save",
        suggested_testid="ai-edit-project-context-apply-save-button",
        description="'Edit with AI' modal's combined Apply+Save button (unlike the create "
        "flow's separate Apply-then-Save, this surface applies and saves in one action).",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate(self) -> None:
        """Navigate to /settings/project-context and wait for it to be ready."""
        super().navigate(PROJECT_CONTEXT_PATH)
        self.wait_for_page_load()

    def wait_for_page_load(self, timeout: int = 15000) -> None:
        """Wait for whichever of the THREE states the server renders to
        become visible: the empty-state 'Create' button, the create/edit
        editor's content, or the populated saved view's 'Edit with AI'
        button (confirmed live, ELITEA-3254 family AFS — a populated saved
        view renders neither of the other two testids, so a caller
        navigating straight to a project that already has content needs
        this third branch; this method previously only distinguished
        empty-vs-editor and hung for 15s on a populated saved view)."""
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
        try:
            self.ai_edit_open_button.wait_for(state="visible", timeout=timeout)
            logger.info("Project Context page loaded (saved view, Edit with AI)")
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
        """Click the empty-state 'Create' button and wait for the editor to open.

        URL target confirmed live 2026-10-16: ``/settings/project-context/edit``
        (PROJECT_CONTEXT_EDIT_PATH) — NOT ``?view=create`` as this method's
        original ELITEA-2272 assertion read; the route shape changed since
        that 2026-08-05 analysis (family AFS ELITEA-3252/3253/3254/3255,
        Phase 2 amendment).
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

    # ------------------------------------------------------------------
    # ELITEA-3252/3255 — Activation description (NEW field, required for Save)
    # ------------------------------------------------------------------
    def fill_activation_description(self, text: str) -> None:
        """Fill the 'Activation description' input (click + type, MUI/React
        onChange needs keyboard events — ``fill()`` would not trigger it,
        per ``.claude/rules/mui-patterns.md``)."""
        self.activation_description.click()
        self.activation_description.press_sequentially(text, delay=20)
        logger.info("Filled activation description (%d chars)", len(text))

    # ------------------------------------------------------------------
    # ELITEA-3252/3253 — "Build with AI" (empty-state create flow)
    # ------------------------------------------------------------------
    def click_build_with_ai(self) -> None:
        """Click the empty-state 'Build with AI' button and wait for its dialog."""
        self.build_with_ai_button.click()
        self.build_with_ai_dialog.wait_for(state="visible", timeout=10000)
        logger.info("Opened 'Build with AI' dialog")

    def generate_draft_from_prompt(self, prompt: str, timeout: int = 30000):
        """Fill the Build-with-AI prompt and click 'Generate Draft'.

        Waits for the ``generate_project_context_draft`` response and returns
        it (status 200 on success with a review step; 422 when the generated
        draft would exceed 2500 chars — caller asserts on ``.status``).

        Args:
            prompt: Project description to generate a draft from.
            timeout: Maximum wait time in milliseconds for the response.

        Returns:
            The Playwright ``Response`` for the generate-draft call.
        """
        dialog = self.build_with_ai_dialog
        prompt_input = self.BUILD_WITH_AI_PROMPT_INPUT.within(dialog)
        prompt_input.fill(prompt)
        generate_button = self.BUILD_WITH_AI_GENERATE_BUTTON.within(dialog)
        expect(generate_button).to_be_enabled(timeout=5000)
        with self.page.expect_response(
            lambda r: "generate_project_context_draft" in r.url, timeout=timeout
        ) as resp_info:
            generate_button.click()
        response = resp_info.value
        logger.info("generate_project_context_draft -> %d", response.status)
        return response

    def get_build_with_ai_prompt_value(self) -> str:
        """Return the current value of the Build-with-AI prompt textarea."""
        return self.BUILD_WITH_AI_PROMPT_INPUT.within(self.build_with_ai_dialog).input_value()

    def get_build_with_ai_review_draft(self) -> str:
        """Return the generated draft's text from the review step's textarea
        (the dialog's only visible, non-``aria-hidden`` ``<textarea>`` once a
        successful 200 generation has transitioned past the prompt step)."""
        return self.BUILD_WITH_AI_REVIEW_DRAFT.within(self.build_with_ai_dialog).input_value()

    def click_build_with_ai_apply(self) -> None:
        """Click the review step's 'Apply' button and wait for the dialog to
        close and the draft to populate the main editor."""
        self.BUILD_WITH_AI_APPLY_BUTTON.within(self.build_with_ai_dialog).click()
        expect(self.build_with_ai_dialog).to_have_count(0, timeout=10000)
        self.editor_content.wait_for(state="visible", timeout=10000)
        logger.info("Applied Build-with-AI draft to editor")

    def get_build_with_ai_error_text(self) -> str:
        """Return the Build-with-AI dialog's inline 422 error Alert text."""
        return (
            self.BUILD_WITH_AI_ERROR_ALERT.within(self.build_with_ai_dialog).text_content() or ""
        ).strip()

    # ------------------------------------------------------------------
    # ELITEA-3255 — "Edit with AI" (saved-view edit flow)
    # ------------------------------------------------------------------
    def click_edit_with_ai(self) -> None:
        """Click the saved-view 'Edit with AI' button and wait for its modal.

        No separate 'Edit' click needed first — confirmed live, "Edit" and
        "Edit with AI" are two independent, adjacent buttons on this build
        (family AFS Known Defects — case-text drift against an older design)."""
        self.ai_edit_open_button.click()
        self.ai_edit_modal.wait_for(state="visible", timeout=10000)
        logger.info("Opened 'Edit with AI' modal")

    def generate_edit_draft(self, instruction: str, timeout: int = 30000):
        """Fill the Edit-with-AI prompt and click 'Generate Draft'.

        Same response-wait contract as :meth:`generate_draft_from_prompt`.

        Args:
            instruction: Edit instruction (e.g. "Add one short sentence about security.").
            timeout: Maximum wait time in milliseconds for the response.

        Returns:
            The Playwright ``Response`` for the generate-draft call.
        """
        self.ai_edit_prompt_input.click()
        self.ai_edit_prompt_input.press_sequentially(instruction, delay=20)
        expect(self.ai_edit_generate_button).to_be_enabled(timeout=5000)
        with self.page.expect_response(
            lambda r: "generate_project_context_draft" in r.url, timeout=timeout
        ) as resp_info:
            self.ai_edit_generate_button.click()
        response = resp_info.value
        logger.info("Edit-with-AI generate_project_context_draft -> %d", response.status)
        return response

    def click_edit_with_ai_apply_and_save(self, timeout: int = 15000) -> None:
        """Click the Edit-with-AI modal's 'Apply & Save' button and wait for
        the PUT to persist, the success toast, and the modal to close.

        Unlike the create flow (separate Apply-then-Save clicks), this
        surface applies the edited draft and saves it in one action
        (confirmed live — family AFS case ELITEA-3255)."""
        with self.page.expect_response(
            lambda r: "/project-context" in r.url and r.request.method == "PUT", timeout=timeout
        ):
            self.AI_EDIT_APPLY_SAVE_BUTTON.within(self.ai_edit_modal).click()
        self.toast_message.wait_for(state="visible", timeout=timeout)
        expect(self.ai_edit_modal).to_have_count(0, timeout=timeout)
        logger.info("Edit-with-AI: applied and saved")

    def get_edit_with_ai_error_text(self) -> str:
        """Return the Edit-with-AI modal's inline 422 error Alert text."""
        return (self.ai_edit_error_alert.text_content() or "").strip()
