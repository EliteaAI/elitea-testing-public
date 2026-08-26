"""UI test — cancelling the Project Context AI dialog leaves the editor content
untouched.

Two phases, because the product swaps the toolbar's AI control on content:

  Phase A -- untouched editor: the toolbar shows "Build with AI"; open it,
             Cancel, and the editor is still empty with Save/Discard still
             disabled (not even the dirty flag moved).
  Phase B -- the case's manual-content path: type manual content, observe the
             toolbar control is now "Edit with AI", open it, Cancel, and the
             editor content is byte-identical to what was typed.

Case-text divergence (declared, reverse-masking guard) -- filed as
clarification #1797. The case says "enter manual content" (step 2) and then
"click Build with AI" (step 3), but ProjectContextEditor.jsx renders
`content.trim() ? <AIEditProjectContextButton/> : <GenerateProjectContextButton/>`,
so once step 2 is done the Build-with-AI button is gone from the DOM entirely
(confirmed live 2026-08-26). They are two different dialogs: Build with AI
generates a draft from a project description, Edit with AI refines what is
already in the editor. Nothing is weakened to accommodate this -- the case's
observable ("cancel the dialog, the editor content is unchanged") is asserted
against BOTH controls, and the swap itself is asserted rather than assumed, so
a future revert fails loudly instead of silently re-enabling a stale case.

The case also calls the editor the "Project Background editor"; no section of
that name exists (module-wide clarification #1792, already filed, not re-filed).

Fidelity (no substitution): the content is typed into the real editor by the
test acting as the user, and "unchanged" is read back off the product's own
CodeMirror lines. Cancelling from either dialog's prompt step issues no network
request at all. This spec fabricates no response, injects no state, replaces no
client and patches nothing -- it only clicks, types and reads.

Test case: ELITEA-2270
AFS: test-specs/settings-project-params/l3_project-context-build-with-ai-cancel-leaves-content_ELITEA-2270.md
"""

import logging

import allure
import pytest
from pages.generate_project_context_modal_page import GenerateProjectContextModalPage
from pages.project_context_page import ProjectContextPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

#: Manual editor content (case step 2), typed rather than pasted: the case's
#: gesture IS typing, and a single line keeps CodeMirror's markdown
#: auto-continuation (which rewrites multi-line typed input) out of play.
MANUAL_CONTENT = "Manual project background entered by hand."


class TestProjectContextBuildWithAICancel:
    """ELITEA-2270 — the AI dialog can be cancelled without modifying the editor."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/project-params/ELITEA-2270_build-with-ai-can-be-cancelled-without-modifying-the-edito.md",
        "onetest-ai Test Case link",
    )
    def test_ai_dialog_cancel_leaves_editor_content_unchanged(self, page, clean_project_context):
        """Cancelling the AI dialog changes neither the editor's text nor its
        dirty state — on an untouched editor and on one holding manual content."""
        context_page = ProjectContextPage(page)
        modal = GenerateProjectContextModalPage(page)
        console_errors = collect_console_errors(page)

        with allure.step("Step 1 — Navigate to Settings -> Project Context and open the editor"):
            context_page.navigate()
            context_page.click_create()
            assert page.url.endswith("/settings/project-context/edit"), (
                f"Create should open the editor route, got {page.url}"
            )
            expect(context_page.editor_lines()).to_have_text([""], timeout=UI_ELEMENT_TIMEOUT)
            expect(modal.open_button).to_be_visible()
            expect(modal.open_button).to_have_text("Build with AI")
            expect(context_page.save_button).to_be_disabled()
            expect(context_page.discard_button).to_be_disabled()

        with allure.step("Phase A / Steps 3-4 — Open 'Build with AI' and cancel it without submitting"):
            modal.open_modal(timeout=UI_ELEMENT_TIMEOUT)
            expect(modal.title).to_have_text("Build with AI")
            modal.click_cancel()
            expect(modal.modal).to_have_count(0)

        with allure.step("Phase A / Step 5 — Verify the editor content is unchanged"):
            expect(context_page.editor_lines()).to_have_text([""])
            expect(context_page.save_button).to_be_disabled()
            expect(context_page.discard_button).to_be_disabled()

        with allure.step("Step 2 — Enter manual content in the editor"):
            context_page.type_at_end_of_content(MANUAL_CONTENT)
            expect(context_page.editor_lines()).to_have_text([MANUAL_CONTENT])
            expect(context_page.save_button).to_be_enabled()

        with allure.step(
            "Step 3 (declared divergence #1797) — with content present the toolbar "
            "control is 'Edit with AI', not 'Build with AI'"
        ):
            expect(modal.open_button).to_have_count(0)
            expect(context_page.ai_edit_button).to_be_visible()
            expect(context_page.ai_edit_button).to_have_text("Edit with AI")

        with allure.step("Phase B / Steps 3-4 — Open the AI dialog and cancel it without submitting"):
            context_page.open_ai_edit_modal()
            expect(context_page.ai_edit_title).to_have_text("Edit with AI")
            context_page.cancel_ai_edit_modal()
            expect(context_page.ai_edit_modal).to_have_count(0)

        with allure.step("Phase B / Step 5 — Verify the Project Background editor content is unchanged"):
            expect(context_page.editor_lines()).to_have_text([MANUAL_CONTENT])
            expect(context_page.save_button).to_be_enabled()

        with allure.step("Axis 2 — No console errors during the cancel flows"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
