"""UI test — the Project Context toggle enables and disables context injection.

Flips the saved view's enable toggle OFF, proves the state survives both an
in-app navigation round-trip and a full page reload, flips it back ON and
proves that persists too — asserting on each flip the product's own PUT
response, the "turned off" banner, and the Edit / Edit-with-AI affordances that
the flag gates.

Case-text divergence (declared, reverse-masking guard): the case says "Click
Save" after each flip. The saved view has NO Save button —
``ProjectContextSavedView.handleToggle`` fires the PUT immediately on change
(auto-save, confirmed live). The case's observable — the toggle's state
persists across a reload — is unchanged and fully asserted; only its assumed
mechanism does not exist. Routed as clarification #1792.

Precondition substitution (declared, TRANSIT ONLY): a non-empty Project Context
is seeded via the API by the ``project_context_seed`` fixture, because the
toggle only renders in the saved view (an empty project shows the empty state,
which has no toggle at all — #1793). **The seed writes CONTENT only** — it
deliberately passes no ``enabled`` argument, so the fixture carries the
product's own current flag forward (``serverData?.enabled ?? true``, and the
fixture seeds onto a freshly-deleted resource, so that is the server's own
default). That matters because case step 2's observable IS the flag ("Verify
the toggle is ON by default"): had the seed written ``enabled=True``, step 2
would have asserted a value the test itself authored. Every asserted value
here — the PUT status, the default-ON state, the toggle state after a hard
reload, the banner text, the button states — is produced by the product.

Test case: ELITEA-2267
AFS: test-specs/settings-project-params/l2_project-context-toggle-enable-disable_ELITEA-2267.md
"""

import logging

import allure
import pytest
from pages.project_context_page import ProjectContextPage
from pages.settings_drawer_page import SettingsDrawerPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

SEED_CONTENT = "ELITEA-2267 toggle seed."

EXPECTED_DISABLED_BANNER = (
    "Project Context is turned off. The project background is not applied to "
    "AI responses or workflows."
)

GENERAL_TAB_ID = "project-general"
PROJECT_CONTEXT_TAB_ID = "project-context"


class TestProjectContextToggleEnableDisable:
    """ELITEA-2267 — Project Context toggle enables and disables context injection."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/project-params/ELITEA-2267_project-context-toggle-enables-and-disables-context-injectio.md",
        "onetest-ai Test Case link",
    )
    def test_project_context_toggle_enable_disable(self, page, project_context_seed):
        """The toggle is ON by default; turning it OFF auto-saves (PUT 200),
        shows the 'turned off' banner and disables Edit / Edit with AI; the OFF
        state survives an in-app navigation round-trip AND a full page reload;
        turning it back ON auto-saves and that ON state survives a reload too."""
        context_page = ProjectContextPage(page)
        drawer = SettingsDrawerPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Setup — seed CONTENT only (transit only; the toggle needs a non-empty context). "
            "No 'enabled' is authored: the default-ON state is case step 2's own observable, "
            "so it is left to the product"
        ):
            project_context_seed(SEED_CONTENT)

        with allure.step("Step 1 — Navigate to Settings -> Project Context: the saved view's toggle card renders"):
            context_page.navigate_to_saved_view()
            expect(context_page.toggle_card).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 2 — The toggle is ON by default: checked, no banner, Edit enabled (case step 2)"):
            expect(context_page.enable_toggle).to_be_checked()
            expect(context_page.disabled_banner).to_have_count(0)
            expect(context_page.edit_button).to_be_enabled()

        with allure.step(
            "Step 3-4 — Click the toggle to turn it OFF: the product's own PUT returns 200 "
            "(this IS the save — there is no Save button), the switch is unchecked, the "
            "'turned off' banner appears and Edit / Edit with AI become disabled (case steps 3-4)"
        ):
            response = context_page.click_enable_toggle_and_wait_for_put()
            assert response.status == 200, (
                f"Expected the Project Context PUT to return 200 when turning the toggle OFF, "
                f"got {response.status} — {response.url}"
            )
            expect(context_page.enable_toggle).not_to_be_checked()
            expect(context_page.disabled_banner).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(context_page.disabled_banner).to_have_text(EXPECTED_DISABLED_BANNER)
            expect(context_page.edit_button).to_be_disabled()
            expect(context_page.ai_edit_button).to_be_disabled()

        with allure.step("Step 5 — Navigate away (General) and back to Project Context (case step 5)"):
            drawer.click_nav_item(GENERAL_TAB_ID, timeout=UI_ELEMENT_TIMEOUT)
            drawer.click_nav_item(PROJECT_CONTEXT_TAB_ID, timeout=UI_ELEMENT_TIMEOUT)
            expect(context_page.toggle_card).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 6a — The toggle is still OFF after the in-app round-trip (case step 6)"):
            expect(context_page.enable_toggle).not_to_be_checked()
            expect(context_page.disabled_banner).to_be_visible()

        with allure.step(
            "Step 6b — And still OFF after a FULL page reload: a hard reload defeats the "
            "RTK-Query cache, so this is what proves the server persisted it"
        ):
            context_page.navigate_to_saved_view()
            expect(context_page.enable_toggle).not_to_be_checked()
            expect(context_page.disabled_banner).to_be_visible()

        with allure.step("Step 7 — Toggle back ON: the product's own PUT returns 200 (case step 7)"):
            response = context_page.click_enable_toggle_and_wait_for_put()
            assert response.status == 200, (
                f"Expected the Project Context PUT to return 200 when turning the toggle back ON, "
                f"got {response.status} — {response.url}"
            )

        with allure.step(
            "Step 8 — After a full page reload the toggle is saved as ON: checked, no "
            "banner, Edit enabled again (case step 8)"
        ):
            context_page.navigate_to_saved_view()
            expect(context_page.enable_toggle).to_be_checked()
            expect(context_page.disabled_banner).to_have_count(0)
            expect(context_page.edit_button).to_be_enabled()

        with allure.step("Side-channel check — no console errors at any step"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
