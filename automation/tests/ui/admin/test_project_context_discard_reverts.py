"""UI test — Discard reverts unsaved Project Context changes.

Opens the editor on saved content, reads the current content off the product as
the comparison baseline, appends an unsaved edit, clicks Discard, and proves the
edit is gone on three independent readings: the saved view's render, the
re-opened editor, and a hard reload that can only show what the server has.

Case-text divergence (declared, reverse-masking guard): Discard LEAVES the
editor. ProjectContextEditor.handleDiscard calls setIsDirty(false) then
onNavigate('saved'), so the click returns to /settings/project-context rather
than staying put with reverted text (confirmed live 2026-08-26). Case steps 5-6
are therefore asserted on the editor the user next opens plus the server-truth
reload; the observable -- the edit did not survive Discard -- is unchanged and
asserted more strictly than the case asks. Module-wide case-text drift is
already filed as clarification #1792; not re-filed.

Precondition substitution (declared, TRANSIT ONLY): saved content is seeded via
the API by project_context_seed, because the case's step 2 ("note the CURRENT
content") requires the editor to open in EDIT mode -- the same button reads
Cancel in create mode and calls a different handler (handleCancel -> empty
state). The seed writes CONTENT only and never authors the enabled flag (it
defaults to None = echo the product's own value). Crucially, the baseline every
assertion compares against is READ OFF THE PRODUCT in step 2, not taken from the
seed string, so the case's observable is never read off a value the test wrote.

Test case: ELITEA-2274
AFS: test-specs/settings-project-params/l3_project-context-discard-reverts-unsaved-changes_ELITEA-2274.md
"""

import logging

import allure
import pytest
from pages.project_context_page import ProjectContextPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

SEED_CONTENT = "## ELITEA-2274 baseline\n\nSaved content that Discard must restore."

#: The unsaved change of case step 3.
UNSAVED_MARKER = "UNSAVED EDIT"


class TestProjectContextDiscardReverts:
    """ELITEA-2274 — Discard reverts unsaved changes."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/project-params/ELITEA-2274_discard-button-reverts-unsaved-changes.md",
        "onetest-ai Test Case link",
    )
    def test_discard_reverts_unsaved_changes(self, page, project_context_seed):
        """An edit made in the editor and then discarded is absent from the saved
        view, from the re-opened editor, and from the server after a reload."""
        context_page = ProjectContextPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Setup — seed CONTENT only (transit only: the case needs existing saved content "
            "so the editor opens in EDIT mode). No 'enabled' is authored"
        ):
            project_context_seed(SEED_CONTENT)

        with allure.step("Step 1 — Navigate to Settings -> Project Context and open the editor via Edit"):
            context_page.navigate_to_saved_view()
            context_page.click_edit()
            expect(context_page.editor_content).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 2 — Note the current content: the baseline every later assertion compares "
            "against is READ OFF THE PRODUCT here, never taken from the seed string"
        ):
            baseline_lines = context_page.get_editor_lines()
            assert baseline_lines and any(line.strip() for line in baseline_lines), (
                f"Baseline read from the editor is empty ({baseline_lines!r}) — every later "
                "comparison would be vacuous"
            )
            expect(context_page.discard_button).to_have_text("Discard")
            expect(context_page.save_button).to_be_disabled()
            expect(context_page.discard_button).to_be_disabled()

        with allure.step("Step 3 — Make a change to the content (append an unsaved line)"):
            context_page.type_at_end_of_content(f"\n{UNSAVED_MARKER}")
            changed_lines = context_page.get_editor_lines()
            assert changed_lines != baseline_lines, (
                "The editor content did not change after typing — the rest of the case would "
                "verify nothing"
            )
            assert changed_lines[-1] == UNSAVED_MARKER, (
                f"Expected the appended line to be {UNSAVED_MARKER!r}, got {changed_lines[-1]!r}"
            )
            expect(context_page.save_button).to_be_enabled()
            expect(context_page.discard_button).to_be_enabled()

        with allure.step(
            "Step 4 — Click Discard: the product returns to the saved view, whose render "
            "does NOT contain the discarded edit"
        ):
            context_page.click_discard()
            expect(context_page.saved_content).not_to_contain_text(UNSAVED_MARKER)

        with allure.step(
            "Step 5 — The editor reverts to the previously saved content: re-opened, it "
            "matches the step-2 baseline exactly and is clean again"
        ):
            context_page.click_edit()
            expect(context_page.editor_lines()).to_have_text(baseline_lines)
            expect(context_page.editor_content).not_to_contain_text(UNSAVED_MARKER)
            expect(context_page.save_button).to_be_disabled()
            expect(context_page.discard_button).to_be_disabled()

        with allure.step(
            "Step 6 — No changes are persisted: after a FULL page reload (which defeats the "
            "RTK-Query cache) the server's own content is still the baseline"
        ):
            context_page.navigate_to_editor()
            expect(context_page.editor_lines()).to_have_text(baseline_lines)
            expect(context_page.editor_content).not_to_contain_text(UNSAVED_MARKER)

        with allure.step("Side-channel check — no console errors at any step"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
