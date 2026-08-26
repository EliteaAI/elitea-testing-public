"""UI test -- navigating away from Settings and back restores the default
landing tab, not the last-viewed sub-tab.

Read-only navigation check against the logged-in user's `Private` project
(`.agents/testing.md` § Test data strategy). Nothing is created, modified, or
deleted.

Test case: ELITEA-2244
AFS: test-specs/settings-navigation/l3_settings_default_landing_tab_restored_ELITEA-2244.md

Case-text note -- mechanism confirmed correct, only the label needed pinning
-------------------------------------------------------------------------------
The case's title says "restores the default landing tab" and does not name
"AI Configuration" in its own steps. Confirmed live: clicking "Settings" in
the sidebar always hardcodes the destination to `project-general` ("General"),
regardless of which Settings sub-tab was last viewed -- the mechanism the case
describes is exactly what the product does. Only the case-text's likely
assumed label ("AI Configuration", not present in this case's own text but
part of the same root-cause drift as ELITEA-2242/2243) is corrected to the
live "General" (clarification EliteaAI/elitea-testing-public#1772, row 3; not
re-filed here).

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p3: priority (per AFS metadata: l3 -- case priority `medium`)
    - regression
"""

import logging

import allure
import pytest
from config import settings
from pages.settings_drawer_page import SettingsDrawerPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p3, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000

DEFAULT_ACTIVE_TAB_ID = "project-general"
SECRETS_TAB_ID = "secrets"


class TestSettingsDefaultLandingTabRestored:
    """ELITEA-2244 -- navigating away from Settings and back restores the default tab."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2244_navigating-away-from-settings-and-back-restores-the-default-landing-tab.md",
        "onetest-ai Test Case link",
    )
    def test_settings_default_landing_tab_restored(self, page):
        """Settings -> Secrets loads normally; navigating to Agents genuinely
        leaves the Settings routes; re-entering Settings via the sidebar
        button lands back on `/settings/project-general` (General) -- the
        hardcoded default -- regardless of Secrets having been the last tab
        viewed; the re-entered page is non-blank, error-free, with General
        correctly marked active."""
        drawer = SettingsDrawerPage(page)
        console_errors = collect_console_errors(page)

        with allure.step("Step 1 — Navigate to Settings -> Secrets (case step 1)"):
            drawer.open_via_sidebar(timeout=UI_ELEMENT_TIMEOUT)
            drawer.click_nav_item(SECRETS_TAB_ID, timeout=UI_ELEMENT_TIMEOUT)
            expect(page).to_have_url(f"{settings.app_base_url}/settings/{SECRETS_TAB_ID}")
            expect(drawer.nav_item(SECRETS_TAB_ID)).to_have_attribute("data-active", "true")
            content_text = drawer.settings_content.text_content() or ""
            assert content_text.strip(), "Expected non-empty Settings content pane on Secrets"

        with allure.step('Step 2 — Click "Agents" in the left sidebar to navigate away (case step 2)'):
            drawer.sidebar_menu_item("agents").click()
            expect(page).to_have_url(f"{settings.app_base_url}/agents/all", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step('Step 3 — Click "Settings" again (case step 3)'):
            drawer.sidebar_settings_button.click()
            drawer.settings_drawer.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            # Core assertion: re-entering Settings lands on the default tab,
            # NOT the last-viewed sub-tab (Secrets).
            expect(page).to_have_url(f"{settings.app_base_url}/settings/{DEFAULT_ACTIVE_TAB_ID}")

        with allure.step(
            "Step 4 — Verify the Settings page loads without error and content area is "
            "not blank (case step 4 / Expected Final State)"
        ):
            expect(drawer.settings_drawer).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(drawer.nav_item(DEFAULT_ACTIVE_TAB_ID)).to_have_attribute("data-active", "true")
            expect(drawer.settings_content).to_contain_text("General", timeout=UI_ELEMENT_TIMEOUT)
            expect(drawer.settings_content).to_contain_text("AI Configurations", timeout=UI_ELEMENT_TIMEOUT)
            # This path visits Secrets then General -- neither is AI
            # Personality, so #1771 does not apply here; strict zero.
            assert not console_errors, f"Unexpected console errors: {console_errors}"
