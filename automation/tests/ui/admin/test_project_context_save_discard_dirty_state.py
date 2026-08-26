"""UI test — Save and Discard are active only while the Project Context editor
has unsaved changes.

Opens the editor on existing saved content, asserts both buttons start disabled,
types one character and asserts both become enabled, then clicks Discard and
asserts they are inactive again — and that the typed character is gone, which is
WHY they are inactive.

Case-text divergence (declared, reverse-masking guard): case step 5 cannot be
observed in place. handleDiscard calls onNavigate('saved'), so a moment after
the click there are no Save/Discard buttons left to read (confirmed live
2026-08-26). Both halves of that are asserted instead: the buttons are gone from
the DOM immediately after the click (count 0 — this IS how the product
deactivates them), and they are back and DISABLED on the editor the user next
opens. Module-wide case-text drift already filed as clarification #1792; not
re-filed.

Precondition substitution (declared, TRANSIT ONLY): saved content is seeded via
the API by project_context_seed, satisfying the case's own step-1 precondition
("with existing saved content") — which is also what makes the sibling button
Discard rather than Cancel (create mode's Cancel calls a different handler). The
seed writes CONTENT only and never authors the enabled flag. The seeded TEXT is
never asserted; every observable here — each button's disabled state at each
phase, the label, the post-Discard navigation, the absence of the typed
character — is produced by the product.

Test case: ELITEA-2275
AFS: test-specs/settings-project-params/l3_project-context-save-discard-enabled-only-when-dirty_ELITEA-2275.md
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

SEED_CONTENT = "## ELITEA-2275 saved content"

#: The minimum change that makes the editor dirty (case step 3).
DIRTY_CHAR = "X"


class TestProjectContextSaveDiscardDirtyState:
    """ELITEA-2275 — Save and Discard are only active when there are unsaved changes."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/project-params/ELITEA-2275_save-and-discard-buttons-are-only-active-when-there-are-unsa.md",
        "onetest-ai Test Case link",
    )
    def test_save_and_discard_active_only_with_unsaved_changes(self, page, project_context_seed):
        """Both buttons are disabled on a clean editor, enabled after a single
        character, and inactive again once Discard has cleared the change."""
        context_page = ProjectContextPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Setup — seed CONTENT only (transit only: the case's own precondition is "
            "'with existing saved content'). No 'enabled' is authored"
        ):
            project_context_seed(SEED_CONTENT)

        with allure.step(
            "Step 1 — Navigate to Settings -> Project Context with existing saved content and "
            "open the editor: it really is EDIT mode (non-empty content, sibling button 'Discard')"
        ):
            context_page.navigate_to_saved_view()
            context_page.click_edit()
            expect(context_page.editor_content).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(context_page.editor_content).not_to_be_empty()
            expect(context_page.discard_button).to_have_text("Discard")

        with allure.step("Step 2 — Save and Discard are inactive when no changes have been made"):
            expect(context_page.save_button).to_be_disabled()
            expect(context_page.discard_button).to_be_disabled()

        with allure.step("Step 3 — Make a change in the editor (one character)"):
            context_page.type_at_end_of_content(DIRTY_CHAR)
            expect(context_page.editor_lines().last).to_contain_text(DIRTY_CHAR)

        with allure.step("Step 4 — Save and Discard become active"):
            expect(context_page.save_button).to_be_enabled()
            expect(context_page.discard_button).to_be_enabled()

        with allure.step(
            "Step 5a — Click Discard: the product leaves the editor for the saved view, so "
            "both buttons are gone from the DOM entirely — this is HOW it deactivates them"
        ):
            context_page.click_discard()
            expect(context_page.save_button).to_have_count(0)
            expect(context_page.discard_button).to_have_count(0)

        with allure.step(
            "Step 5b — And on the editor the user next opens they are inactive again: both "
            "disabled, and the typed character is gone — which is WHY there is nothing to save"
        ):
            context_page.click_edit()
            expect(context_page.save_button).to_be_disabled()
            expect(context_page.discard_button).to_be_disabled()
            expect(context_page.editor_lines()).to_have_text([SEED_CONTENT])

        with allure.step("Side-channel check — no console errors at any step"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
