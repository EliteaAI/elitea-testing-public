"""UI test — Project Context page loads with the correct layout and components.

Walks the saved view (page header, enable-toggle card with its title,
description and default-ON switch) into the editor (AI button, import button,
edit/preview mode buttons, line-numbered CodeMirror, Save + Discard), asserting
each component the case lists where the product actually renders it, with no
console errors and no residual loading spinner.

Two case elements are deliberately NOT asserted — a "Project Background"
section title and its goals/terminology/workflows/constraints subtitle exist
nowhere in the product (``grep -rn "Project Background" src/`` finds only a
modal label and a placeholder). Asserting them would fail on a stale case
hypothesis rather than on a product defect, so they are routed as clarification
#1792 instead of silently dropped. Likewise Save/Discard are asserted by
presence and label, never by position: they sit in the page header, not "at the
bottom" as the case says (same clarification).

Precondition substitution (declared, TRANSIT ONLY): a non-empty Project Context
is seeded via the API by the ``project_context_seed`` fixture, because the
toggle card only renders in the saved view. Every value this test asserts is
produced by the product and read off the live UI.

Test case: ELITEA-2266
AFS: test-specs/settings-project-params/l3_project-context-page-layout_ELITEA-2266.md
"""

import logging

import allure
import pytest
from config import settings
from pages.project_context_page import (
    PROJECT_CONTEXT_EDIT_PATH,
    ProjectContextPage,
)
from pages.settings_drawer_page import SettingsDrawerPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

SEED_CONTENT = "ELITEA-2266 layout seed."

EXPECTED_PAGE_TITLE = "Project Context"
EXPECTED_CARD_TITLE = "Project Context"
EXPECTED_CARD_DESCRIPTION = (
    "Project-specific background information that the AI uses to generate more "
    "accurate and relevant responses, tailored to your workflows, data, and goals."
)
EXPECTED_DISCARD_LABEL = "Discard"
EXPECTED_IMPORT_TOOLTIP = "Import from markdown file"


class TestProjectContextPageLayout:
    """ELITEA-2266 — Project Context page loads with correct layout and components."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/project-params/ELITEA-2266_project-context-page-loads-with-correct-layout-and-component.md",
        "onetest-ai Test Case link",
    )
    def test_project_context_page_layout(self, page, project_context_seed):
        """Every component the case enumerates is present where the product
        renders it — the toggle card (title, description, default-ON switch, no
        turned-off banner) on the saved view; the AI, import and mode buttons,
        the line-numbered editor and the disabled Save/Discard pair in the
        editor — with no console errors and no permanent loading spinner."""
        context_page = ProjectContextPage(page)
        drawer = SettingsDrawerPage(page)
        console_errors = collect_console_errors(page)

        with allure.step("Setup — seed a non-empty, enabled Project Context (transit only; the toggle card needs it)"):
            project_context_seed(SEED_CONTENT, enabled=True)

        with allure.step(
            "Step 1-2 — Navigate to Settings -> Project Context: page loads, "
            "header reads 'Project Context' (case steps 1-2)"
        ):
            context_page.navigate_to_saved_view()
            expect(drawer.settings_content).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(context_page.page_title).to_have_text(EXPECTED_PAGE_TITLE, timeout=UI_ELEMENT_TIMEOUT)
            # Case step 16, first half: no PERMANENT loading state — the query has
            # resolved, so the CircularProgress pane is gone, not merely hidden.
            expect(context_page.loader).to_have_count(0)

        with allure.step(
            "Step 3 — Toggle card at the top: visible, exact title, exact description, "
            "switch ON by default, no 'turned off' banner (case steps 3-6)"
        ):
            expect(context_page.toggle_card).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(context_page.toggle_card_title).to_have_text(EXPECTED_CARD_TITLE)
            expect(context_page.toggle_card_description).to_have_text(EXPECTED_CARD_DESCRIPTION)
            expect(context_page.enable_toggle).to_be_checked()
            # Axis 2: the banner is the visible consequence of the OFF state, so its
            # absence turns "enabled by default" into a test-enforced invariant.
            expect(context_page.disabled_banner).to_have_count(0)

        with allure.step("Step 4 — Click 'Edit': the editor route opens"):
            context_page.click_edit()
            expect(page).to_have_url(f"{settings.app_base_url}{PROJECT_CONTEXT_EDIT_PATH}")

        with allure.step(
            "Step 5 — Editor toolbar: AI button, import icon button, code-view ('</>') "
            "button selected on load, preview (eye) button unselected (case steps 10-13)"
        ):
            # Case step 10 says "Build with AI"; with non-empty content the product
            # renders "Edit with AI" instead (ProjectContextEditor swaps the component
            # on content.trim()). The AI affordance the case asks for IS present —
            # only its label differs. Clarification #1792.
            expect(context_page.ai_edit_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(context_page.import_button).to_be_visible()
            expect(context_page.import_button).to_have_attribute("aria-label", EXPECTED_IMPORT_TOOLTIP)
            expect(context_page.mode_edit_button).to_be_visible()
            expect(context_page.mode_edit_button).to_have_attribute("aria-pressed", "true")
            expect(context_page.mode_preview_button).to_be_visible()
            expect(context_page.mode_preview_button).to_have_attribute("aria-pressed", "false")

        with allure.step(
            "Step 6 — Markdown editor carries the seeded content and renders a "
            "line-number gutter (case step 14)"
        ):
            expect(context_page.editor_content).to_be_visible()
            expect(context_page.editor_content).to_have_text(SEED_CONTENT)
            expect(context_page.line_number_gutter()).to_be_visible()

        with allure.step(
            "Step 7 — Save and Discard are both present and, with no edit made yet, "
            "both disabled; Discard is labelled 'Discard' in edit mode (case step 15)"
        ):
            expect(context_page.save_button).to_be_visible()
            expect(context_page.save_button).to_be_disabled()
            expect(context_page.discard_button).to_be_visible()
            expect(context_page.discard_button).to_have_text(EXPECTED_DISCARD_LABEL)
            expect(context_page.discard_button).to_be_disabled()

        with allure.step("Step 8 — No errors and no permanent loading state anywhere in the run (case step 16)"):
            expect(context_page.loader).to_have_count(0)
            assert not console_errors, f"Unexpected console errors: {console_errors}"
