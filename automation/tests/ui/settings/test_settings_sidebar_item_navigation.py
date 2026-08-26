"""UI test -- clicking each Settings sidebar item navigates to its own
dedicated page, updating the URL, the drawer's selection state and the
content pane every time.

Read-only click-through against the logged-in user's `Private` project
(`.agents/testing.md` § Test data strategy). Nothing is created, modified, or
deleted.

Test case: ELITEA-2243
AFS: test-specs/settings-navigation/l3_settings_sidebar_item_navigation_ELITEA-2243.md

Case-text drift on step 6 -- this test asserts the LIVE contract
------------------------------------------------------------------
The case's step 6 ("Log out is visible as the last PERSONAL item and does NOT
navigate to a settings sub-page") assumes a Log out drawer item that does not
exist. This test asserts the absence instead, and that Notifications is
genuinely the last PERSONAL entry (clarification
EliteaAI/elitea-testing-public#1772, not re-filed here). Steps 1-5 execute
exactly as written and pass live.

Known defect -- expected, not chased
-------------------------------------
Clicking `settings-nav-item-ai-personality` deterministically fires one React
console warning (a `disableUnderline` prop leaking onto a DOM node). Filed as
EliteaAI/elitea-testing-public#1771 (MINOR, OPEN), confirmed live,
deterministic, single-cause. Per `.agents/testing.md` § Merge gate
sanctioned-RED / known-defect pattern, this click's console-error assertion
is a soft failure (aggregated via `soft_failures` + a final `pytest.fail()`,
same pattern as `test_agent_hub_like_agent_from_modal.py`); every OTHER
click's console-error assertion is a hard, strict-zero assert.

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

#: PROJECT items to click (General is already active from the initial load --
#: it is verified in step 1, not re-clicked).
PROJECT_CLICK_TAB_IDS = ["ai-providers", "project-context", "secrets", "analytics", "usage"]

#: PERSONAL items to click, in drawer order.
PERSONAL_CLICK_TAB_IDS = ["profile", "preferences", "ai-personality", "memory", "tokens", "notifications"]

#: The one tab id known to fire the #1771 console warning.
KNOWN_DEFECT_1771_TAB_ID = "ai-personality"
KNOWN_DEFECT_1771_TEXT_FRAGMENT = "disableUnderline"
KNOWN_DEFECT_1771_URL = "https://github.com/EliteaAI/elitea-testing-public/issues/1771"

LAST_PERSONAL_TAB_ID = "notifications"


class TestSettingsSidebarItemNavigation:
    """ELITEA-2243 -- clicking each Settings sidebar item navigates to its own page."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2243_clicking-each-settings-sidebar-item-navigates-to-its-dedicated-page.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(KNOWN_DEFECT_1771_URL, "Known defect — disableUnderline console warning on AI Personality click")
    def test_settings_sidebar_item_navigation(self, page):
        """Every PROJECT and PERSONAL drawer item, when clicked, updates the
        URL to its own route, marks itself (and only itself) active, and
        changes the content pane's text from the prior tab's — with a strict
        zero-console-error bar except the known #1771 warning on AI
        Personality, which is soft-asserted and does not fail the test on its
        own. Log out is confirmed absent from the drawer, and Notifications
        is confirmed the genuine last PERSONAL item."""
        drawer = SettingsDrawerPage(page)
        console_errors = collect_console_errors(page)
        soft_failures: list[str] = []

        with allure.step("Step 1 — Navigate to Settings; verify General is active (starting state)"):
            drawer.open_via_sidebar(timeout=UI_ELEMENT_TIMEOUT)
            expect(drawer.settings_drawer).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(drawer.nav_item(DEFAULT_ACTIVE_TAB_ID)).to_have_attribute("data-active", "true")

        active_tab_id = DEFAULT_ACTIVE_TAB_ID
        previous_content_text = drawer.settings_content.text_content() or ""

        with allure.step(
            "Step 2 — Click each PROJECT item one by one; verify the content area updates each time (case steps 2-3)"
        ):
            for tab_id in PROJECT_CLICK_TAB_IDS:
                errors_before = len(console_errors)

                drawer.click_nav_item(tab_id, timeout=UI_ELEMENT_TIMEOUT)

                expect(page).to_have_url(f"{settings.app_base_url}/settings/{tab_id}")
                expect(drawer.nav_item(tab_id), f"{tab_id!r} should be active").to_have_attribute("data-active", "true")
                expect(
                    drawer.nav_item(active_tab_id), f"{active_tab_id!r} should no longer be active"
                ).to_have_attribute("data-active", "false")
                new_content_text = drawer.settings_content.text_content() or ""
                assert new_content_text != previous_content_text, (
                    f"Expected content to change from the {active_tab_id!r} tab after clicking {tab_id!r}"
                )

                new_errors = console_errors[errors_before:]
                assert not new_errors, f"Unexpected console errors on {tab_id!r} click: {new_errors}"

                active_tab_id = tab_id
                previous_content_text = new_content_text

        with allure.step(
            "Step 3 — Click each PERSONAL item one by one; verify the content area updates each time (case steps 4-5)"
        ):
            for tab_id in PERSONAL_CLICK_TAB_IDS:
                errors_before = len(console_errors)

                drawer.click_nav_item(tab_id, timeout=UI_ELEMENT_TIMEOUT)

                expect(page).to_have_url(f"{settings.app_base_url}/settings/{tab_id}")
                expect(drawer.nav_item(tab_id), f"{tab_id!r} should be active").to_have_attribute("data-active", "true")
                expect(
                    drawer.nav_item(active_tab_id), f"{active_tab_id!r} should no longer be active"
                ).to_have_attribute("data-active", "false")
                new_content_text = drawer.settings_content.text_content() or ""
                assert new_content_text != previous_content_text, (
                    f"Expected content to change from the {active_tab_id!r} tab after clicking {tab_id!r}"
                )

                new_errors = console_errors[errors_before:]
                if tab_id == KNOWN_DEFECT_1771_TAB_ID:
                    unexpected_errors = [e for e in new_errors if KNOWN_DEFECT_1771_TEXT_FRAGMENT not in e]
                    assert not unexpected_errors, f"Unexpected console errors on {tab_id!r} click: {unexpected_errors}"
                    known_defect_errors = [e for e in new_errors if KNOWN_DEFECT_1771_TEXT_FRAGMENT in e]
                    if known_defect_errors:
                        # Known defect: #1771 — recorded in soft_failures so
                        # this stays RED until the product fix ships.
                        soft_failures.append(
                            f"Known defect {KNOWN_DEFECT_1771_URL}: disableUnderline console "
                            f"warning(s) on {tab_id!r} click: {len(known_defect_errors)} occurrence(s)"
                        )
                else:
                    assert not new_errors, f"Unexpected console errors on {tab_id!r} click: {new_errors}"

                active_tab_id = tab_id
                previous_content_text = new_content_text

        with allure.step(
            "Step 4 — Verify Log out is NOT a drawer item, and Notifications is "
            "genuinely the last PERSONAL entry (case step 6, corrected)"
        ):
            expect(drawer.drawer_logout_controls()).to_have_count(0)
            expect(drawer.last_personal_nav_item()).to_have_attribute(
                "data-testid", f"settings-nav-item-{LAST_PERSONAL_TAB_ID}"
            )

        if soft_failures:
            pytest.fail(
                "Test flow completed and all functional assertions passed, but "
                "known-defect soft failures were recorded:\n" + "\n".join(soft_failures)
            )
