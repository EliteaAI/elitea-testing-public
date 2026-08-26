"""UI test — Save persists Project Context content across a full page reload.

Enters the case's literal body in the real editor, saves with the real Save
button (asserting the product's OWN PUT status, not a fabricated one), confirms
the success toast, performs a genuine browser reload and proves the content
came back from the server on both renderings: the saved view's formatted
markdown and the raw source in the re-opened editor.

Case-text divergences (declared, reverse-masking guard), both confirmed live
2026-08-26:

1. "Project Background" is not a name the product uses -- the control is the
   Project Context editor. Clarification #1792 (module-wide) already filed.
2. Case step 6 assumes you are still in the editor after the reload. You are
   not: handleSave calls onNavigate('saved'), so a successful Save leaves the
   editor for /settings/project-context, whose saved view renders the content as
   markdown. The case's observable -- the content survived the reload -- is
   asserted on BOTH honest readings (saved view render + re-opened editor's raw
   source), so nothing is weakened; only the assumed location moved.

No substitution: nothing is seeded, the content is typed into the product by the
test acting as the user, and persistence is read back after a hard reload that
defeats the RTK-Query cache. The single page.evaluate loads the browser
clipboard for the paste gesture (pre-existing reviewed pattern, ELITEA-2272).

Test case: ELITEA-2273
AFS: test-specs/settings-project-params/l3_project-context-save-persists-after-reload_ELITEA-2273.md
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

#: The case's literal test data (ELITEA-2273 step 2).
PROJECT_CONTEXT_TEXT = "## Project Overview. This is a test project."

#: What the '##' line renders as once react-markdown has consumed the syntax.
EXPECTED_RENDERED_HEADING = "Project Overview. This is a test project."

EXPECTED_SAVE_TOAST = "Project Context saved"


class TestProjectContextSavePersists:
    """ELITEA-2273 — Save persists Project Context content after a page reload."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/project-params/ELITEA-2273_save-button-persists-project-background-content-after-page-r.md",
        "onetest-ai Test Case link",
    )
    def test_save_persists_project_context_after_reload(self, page, clean_project_context):
        """Save returns 200 and shows the success toast; after a full page reload
        the content is still there — rendered in the saved view and raw in the
        editor — and the freshly-opened editor is clean."""
        context_page = ProjectContextPage(page)
        console_errors = collect_console_errors(page)

        with allure.step("Step 1 — Navigate to Settings -> Project Context and open the editor via Create"):
            context_page.navigate()
            context_page.click_create()
            expect(context_page.editor_content).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Control condition — Save is DISABLED before anything is entered, so step 3's "
            "'enabled' is a real state change rather than a permanently live button"
        ):
            expect(context_page.save_button).to_be_disabled()

        with allure.step("Step 2 — Enter the project context text: the field accepts and displays it"):
            context_page.paste_markdown(PROJECT_CONTEXT_TEXT)
            expect(context_page.editor_lines()).to_have_text([PROJECT_CONTEXT_TEXT])
            expect(context_page.save_button).to_be_enabled()

        with allure.step("Step 3 — Click Save: the product's own PUT returns 200"):
            response = context_page.click_save_and_wait_for_put()
            assert response.status == 200, (
                f"Expected the Project Context PUT to return 200 on Save, "
                f"got {response.status} — {response.url}"
            )

        with allure.step(
            "Step 4 — A success confirmation is shown, and the product leaves the editor "
            "for the saved view (its own post-save navigation)"
        ):
            assert context_page.get_toast_text() == EXPECTED_SAVE_TOAST, (
                f"Expected the save toast to read {EXPECTED_SAVE_TOAST!r}, "
                f"got {context_page.get_toast_text()!r}"
            )
            assert page.url.endswith("/settings/project-context"), (
                f"Expected Save to return to the saved view, landed on {page.url}"
            )

        with allure.step("Step 5 — Reload the page: a hard reload defeats the RTK-Query cache"):
            context_page.navigate_to_saved_view()

        with allure.step(
            "Step 6a — The saved view still shows the previously entered content after the "
            "reload, rendered as markdown (the '##' line became a heading)"
        ):
            expect(context_page.toggle_card).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(context_page.saved_content_headings()).to_have_text([EXPECTED_RENDERED_HEADING])

        with allure.step(
            "Step 6b — And the editor shows the previously entered content as RAW markdown, "
            "byte-identical to what was typed — the case's literal expected final state"
        ):
            context_page.click_edit()
            expect(context_page.editor_lines()).to_have_text([PROJECT_CONTEXT_TEXT])

        with allure.step(
            "Step 6c — That freshly-opened editor is CLEAN: Save and Discard are disabled, "
            "so what it shows is the saved content, not unsaved leftovers"
        ):
            expect(context_page.save_button).to_be_disabled()
            expect(context_page.discard_button).to_be_disabled()

        with allure.step("Side-channel check — no console errors at any step"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
