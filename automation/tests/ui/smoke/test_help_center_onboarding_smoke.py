"""Foundation smoke tests — Help Center + Onboarding (cov60 campaign).

Standing smoke coverage for the two page objects built in the cov60
campaign's foundation pass:

- ``pages.help_center_page.HelpCenterPage`` — test-specs/help-center/
  l3_page-loads-via-sidebar-icon_ELITEA-2219.md
- ``pages.onboarding_page.OnboardingPage`` — test-specs/onboarding/
  l2_sure-lets-go-triggers-provisioning-and-onboarding-tips_ELITEA-2232.md

Per the foundation-pass mini-gate (test-automation-workflow skill,
references/campaign-planning.md § The stages), this file is the ONE smoke
spec exercising both new page objects end-to-end. It stays as a permanent
asset — later wave specs re-prove per-case coverage against the same page
objects; this smoke spec proves the foundation itself works.

Markers:
    - smoke: quick sanity checks
    - ui: requires a browser
    - help_center / onboarding: per-surface feature markers

Usage::

    cd automation
    pytest tests/ui/smoke/test_help_center_onboarding_smoke.py -v
    HEADLESS=false pytest tests/ui/smoke/test_help_center_onboarding_smoke.py -v
"""

import allure
import pytest
from pages.chat_page import ChatPage
from pages.help_center_page import VERSION_PATTERN, HelpCenterPage
from pages.onboarding_page import OnboardingPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.smoke, pytest.mark.ui]

# Timeout constants
PAGE_LOAD_TIMEOUT = 15_000
PROVISIONING_POLL_TIMEOUT = 10_000  # covers Onboarding.jsx's 5s poll interval with margin

EXPECTED_CARD_TITLES = [
    "Documentation",
    "Release Notes",
    "Video Library",
    "Tutorials",
    "Interactive Tours",
]


class TestHelpCenterSmoke:
    """Foundation smoke for HelpCenterPage — the Help Center surface end-to-end.

    Covers the ELITEA-2219 happy path: sidebar entry, header content, all
    five resource cards (title/subtitle/icon), and the version-info block.
    """

    pytestmark = pytest.mark.help_center

    def test_help_center_page_loads_with_cards(self, page):
        """Sidebar "?" icon opens Help Center; header + all 5 cards render."""
        console_errors = None
        with allure.step("Step 1 — Navigate to an authenticated page (chat)"):
            chat_page = ChatPage(page)
            chat_page.navigate_to_chat()
            console_errors = chat_page.capture_console_errors()

        with allure.step("Step 2 — Open Help Center via the sidebar icon"):
            help_center = HelpCenterPage(page)
            help_center.open_via_sidebar(timeout=PAGE_LOAD_TIMEOUT)

        with allure.step("Step 3 — Verify header title, subtitle, and description"):
            expect(help_center.help_center_page_title).to_have_text("Help Center")
            expect(help_center.help_center_subtitle).to_have_text("Explore Help Center")
            expect(help_center.help_center_description).to_have_text(
                "Guides, documentation, and release notes to support your work."
            )

        with allure.step("Step 4 — Verify all five resource cards render title/subtitle/icon"):
            actual_titles = []
            for card_testid in HelpCenterPage.CARD_TESTIDS:
                title_locator = help_center.card_title_locator(card_testid)
                expect(title_locator).to_be_visible(timeout=PAGE_LOAD_TIMEOUT)
                actual_titles.append(title_locator.text_content() or "")

                subtitle_locator = help_center.card_subtitle_locator(card_testid)
                assert (subtitle_locator.text_content() or "").strip(), (
                    f"Card {card_testid} should have a non-empty subtitle"
                )

                assert help_center.card_icon_locator(card_testid).is_visible(), (
                    f"Card {card_testid} should show its icon"
                )

            assert actual_titles == EXPECTED_CARD_TITLES, (
                f"Expected card titles {EXPECTED_CARD_TITLES}, got {actual_titles}"
            )

        with allure.step("Step 5 — Verify the Interactive Tours card's links (title + href)"):
            tours_links = help_center.card_link_locators(
                HelpCenterPage.CARD_TESTIDS[-1]  # resources-interactive-tours-card
            )
            expect(tours_links).to_have_count(2)
            expect(tours_links.nth(0)).to_have_text("Sidebar Interactive Tour")
            expect(tours_links.nth(0)).to_have_attribute("href", "/app/chat?tour=sidebar")
            expect(tours_links.nth(1)).to_have_text("Chat Interactive Tour")
            expect(tours_links.nth(1)).to_have_attribute("href", "/app/chat?tour=chat")

        with allure.step("Step 6 — Verify version info matches the expected pattern"):
            version_text = help_center.get_version_info_text()
            assert VERSION_PATTERN.match(version_text), (
                f"Version info {version_text!r} should match 'Version: X.X.X (DD-Mon-YYYY)'"
            )
            assert help_center.help_center_version_info_icon.is_visible(), (
                "Version info icon should be visible"
            )

        with allure.step("Step 7 — Verify no console errors occurred"):
            assert not console_errors, f"Unexpected console errors: {list(console_errors)}"
            console_errors.stop()


class TestOnboardingSmoke:
    """Foundation smoke for OnboardingPage — Welcome screen through to "ready".

    Covers the ELITEA-2232 happy path: a simulated never-onboarded user
    (via the ``fresh_user_route`` fixture) sees the Welcome screen, clicking
    "Sure, let's go!" shows tour slide 1/48 with its provisioning progress
    footer, and once provisioning is simulated complete the real sidebar +
    project selector appear.
    """

    pytestmark = pytest.mark.onboarding

    def test_welcome_to_tour_to_ready_flow(self, page, fresh_user_route):
        """Welcome screen -> tour slide 1/48 -> post-provisioning sidebar."""
        with allure.step("Step 1 — Navigate to entry point as a simulated never-onboarded user"):
            onboarding = OnboardingPage(page)
            console_errors = onboarding.capture_console_errors()
            onboarding.navigate_to_entry()
            onboarding.wait_for_welcome_screen(timeout=PAGE_LOAD_TIMEOUT)

        with allure.step("Step 2 — Click 'Sure, let's go!'"):
            onboarding.click_get_started()

        with allure.step("Step 3 — Verify tour slide 1/48 renders with logo and progress footer"):
            onboarding.wait_for_tour_view(timeout=PAGE_LOAD_TIMEOUT)
            expect(onboarding.onboarding_tour_logo).to_be_visible()
            expect(onboarding.onboarding_tour_slide_counter).to_have_text("1 / 48")
            assert "Tip 1: Welcome to ELITEA" in onboarding.get_tour_content_text(), (
                "Tour content should show slide 1's title"
            )
            assert onboarding.is_progress_footer_visible(), (
                "Provisioning progress footer should be visible during the tour"
            )
            expect(onboarding.onboarding_tour_progress_bar).to_be_visible()

        with allure.step("Step 4 — Simulate provisioning completion and verify the ready state"):
            fresh_user_route.mark_provisioning_complete()
            chat_page = ChatPage(page)
            expect(chat_page.sidebar_toggle).to_be_visible(timeout=PROVISIONING_POLL_TIMEOUT)
            expect(chat_page.project_selector_trigger).to_contain_text("Private")

        with allure.step("Step 5 — Verify no console errors occurred"):
            assert not console_errors, f"Unexpected console errors: {list(console_errors)}"
            console_errors.stop()
