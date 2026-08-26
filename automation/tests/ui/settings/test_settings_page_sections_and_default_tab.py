"""UI test -- Settings page loads and displays the correct PROJECT and PERSONAL
drawer sections, with General selected and active by default.

Read-only navigation/inventory check against the logged-in user's `Private`
project (`.agents/testing.md` § Test data strategy). Nothing is created,
modified, or deleted.

Test case: ELITEA-2242
AFS: test-specs/settings-navigation/l2_settings_page_sections_and_default_tab_ELITEA-2242.md

Case-text drift -- this test asserts the LIVE contract
--------------------------------------------------------
The TMS case describes a PROJECT/PERSONAL inventory ("AI Configuration,
Project Params, Secrets, Users, Analytics" / "Personalization, Personal
Tokens, Notifications, Log out") and a default active tab ("AI
Configuration") that do not exist in the live product. Confirmed live this
session: PROJECT = General, AI Providers, Project Context, Secrets, Analytics,
Usage (Users hidden on the `Private` project); PERSONAL = Profile,
Preferences, AI Personality, Memory, Personal Tokens, Notifications (no Log
out item anywhere in the drawer); the default active tab is General
(`project-general`). Per the reverse-masking guard, this spec asserts the live
inventory and default, not the stale case text. Already tracked as
clarification EliteaAI/elitea-testing-public#1772 (rows 1-3); not re-filed.

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p2: priority (per AFS metadata: l2 -- case priority `high`)
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

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000

#: Live PROJECT inventory on the `Private` project, in DOM order (`users` is
#: hidden -- see `test-specs/settings-navigation/_surface.md` § Known traps).
EXPECTED_PROJECT_TAB_IDS = [
    "project-general",
    "ai-providers",
    "project-context",
    "secrets",
    "analytics",
    "usage",
]

#: Live PERSONAL inventory, in DOM order. No `logout` id -- there is no Log
#: out item in the drawer (clarification #1772).
EXPECTED_PERSONAL_TAB_IDS = [
    "profile",
    "preferences",
    "ai-personality",
    "memory",
    "tokens",
    "notifications",
]

DEFAULT_ACTIVE_TAB_ID = "project-general"


class TestSettingsPageSectionsAndDefaultTab:
    """ELITEA-2242 -- Settings page sections and default tab."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2242_settings-page-loads-and-displays-correct-project-and-personal-sections.md",
        "onetest-ai Test Case link",
    )
    def test_settings_page_sections_and_default_tab(self, page):
        """Settings loads at `/settings/project-general` with a non-blank
        content pane; the drawer shows exactly the PROJECT and PERSONAL group
        headers; each lists its live inventory in order; General is the only
        active nav item; the content pane recognizably shows the General
        page; and zero console errors are logged."""
        drawer = SettingsDrawerPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Step 1 — Navigate to Settings via the sidebar; verify the URL, drawer and non-blank content pane"
        ):
            drawer.open_via_sidebar(timeout=UI_ELEMENT_TIMEOUT)
            expect(page).to_have_url(f"{settings.app_base_url}/settings/project-general")
            expect(drawer.settings_drawer).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(drawer.settings_content).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            content_text = drawer.settings_content.text_content() or ""
            assert content_text.strip(), "Expected non-empty Settings content pane on initial load"

        with allure.step("Step 2 — Verify the drawer shows two labelled groups: PROJECT and PERSONAL"):
            expect(drawer.section_header("project")).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(drawer.section_header("project")).to_have_text("PROJECT")
            expect(drawer.section_header("personal")).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(drawer.section_header("personal")).to_have_text("PERSONAL")

        with allure.step("Step 3 — Verify the PROJECT section inventory (live contract, not case text)"):
            for tab_id in EXPECTED_PROJECT_TAB_IDS:
                expect(drawer.nav_item(tab_id), f"PROJECT item {tab_id!r}").to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            # `users` is project-dependent -- explicitly NOT asserted either way
            # (`.agents/testing.md` § Known traps).

        with allure.step(
            "Step 4 — Verify the PERSONAL section inventory (live contract, not case text), "
            "and that no 'Log out' control exists in the drawer"
        ):
            for tab_id in EXPECTED_PERSONAL_TAB_IDS:
                expect(drawer.nav_item(tab_id), f"PERSONAL item {tab_id!r}").to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            # Drift's absence half (clarification #1772) -- test-enforced
            # invariant per .agents/testing.md § Locator policy (#579
            # discipline: absence assertion, no testid exists for a thing
            # that isn't rendered).
            expect(drawer.drawer_logout_controls()).to_have_count(0)

        with allure.step("Step 4b — Verify both groups render in the exact expected order (DOM order)"):
            observed_ids = drawer.nav_item_ids_in_order()
            expected_ids = EXPECTED_PROJECT_TAB_IDS + EXPECTED_PERSONAL_TAB_IDS
            assert observed_ids == expected_ids, (
                f"Expected drawer nav items in order {expected_ids}, got {observed_ids}"
            )

        with allure.step("Step 5 — Verify General is selected and active by default"):
            expect(drawer.nav_item(DEFAULT_ACTIVE_TAB_ID)).to_have_attribute("data-active", "true")
            for tab_id in EXPECTED_PROJECT_TAB_IDS + EXPECTED_PERSONAL_TAB_IDS:
                if tab_id == DEFAULT_ACTIVE_TAB_ID:
                    continue
                expect(drawer.nav_item(tab_id), f"{tab_id!r} should not be active").to_have_attribute(
                    "data-active", "false"
                )

        with allure.step(
            "Step 6 — Verify the main content area loads the General page without "
            "blank or error state (case step 8, corrected target)"
        ):
            expect(drawer.settings_content).to_contain_text("General", timeout=UI_ELEMENT_TIMEOUT)
            expect(drawer.settings_content).to_contain_text("AI Configurations", timeout=UI_ELEMENT_TIMEOUT)
            # This route never visits AI Personality, so #1771 does not fire
            # here -- strict zero, no filter.
            assert not console_errors, f"Unexpected console errors: {console_errors}"
