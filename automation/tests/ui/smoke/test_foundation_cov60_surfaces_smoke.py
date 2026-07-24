"""Foundation smoke tests for the cov60 gap-cluster surfaces.

Standing smoke coverage for the shared grounding (page objects, API client,
fixtures) built for four surfaces that had zero prior automation:
Analytics, Notifications, Hubs (Catalog), and Settings (Preferences).

This file is NOT a substitute for the individual GAP-020/054/073/077 cases
that motivated the foundation build — it is the surface's standing smoke
check and stays even once those cases land as their own dedicated specs.
Each test below exercises the corresponding new page object end-to-end
against a real, meaningful interaction (not just "the page loads").

Markers:
    - smoke: fast critical-path validation
    - ui: requires a browser
    - regression: counted in full regression runs
    - analytics / notifications / hubs / settings: per-surface feature markers
"""

import allure
import pytest
from pages.analytics_page import AnalyticsPage
from pages.catalog_page import CatalogPage
from pages.notification_quick_panel_page import NotificationQuickPanelPage
from pages.user_profile_settings_page import UserProfileSettingsPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.smoke, pytest.mark.ui, pytest.mark.regression]


def _restore_theme(settings_page: UserProfileSettingsPage, original_mode: str | None) -> None:
    """Restore ``localStorage['mode']`` to *original_mode* (or remove the key).

    Mirrors GAP-020's own cleanup guidance: clicking the toggle when the
    original mode differs from the current one, or removing the key
    directly (never writing back the literal string 'dark') when the key
    started absent.
    """
    if original_mode is None:
        settings_page.set_theme_mode_in_storage(None)
        return
    if settings_page.get_theme_mode_from_storage() != original_mode:
        settings_page.click_theme_toggle(original_mode)


@pytest.mark.settings
@pytest.mark.p2
def test_preferences_theme_toggle_switches_and_persists(page):
    """Settings/Preferences: Theme toggle switches Dark<->Light and persists (GAP-020 smoke)."""
    settings_page = UserProfileSettingsPage(page)

    with allure.step("Step 1 — Navigate to Preferences and capture the starting theme"):
        settings_page.navigate_to_preferences()
        original_mode = settings_page.get_theme_mode_from_storage()

    try:
        with allure.step("Step 2 — Switch to Light; storage, selected state, and palette update"):
            if settings_page.is_theme_selected("light"):
                settings_page.click_theme_toggle("dark")
            settings_page.click_theme_toggle("light")
            assert settings_page.get_theme_mode_from_storage() == "light"
            assert settings_page.is_theme_selected("light")
            assert not settings_page.is_theme_selected("dark")
            assert settings_page.get_body_background_color() == "rgba(0, 0, 0, 0)"

        with allure.step("Step 3 — Switch to Dark; value survives a full-navigation reload"):
            settings_page.click_theme_toggle("dark")
            assert settings_page.get_theme_mode_from_storage() == "dark"
            assert settings_page.get_body_background_color() == "rgb(14, 19, 29)"

            page.reload(wait_until="domcontentloaded")
            settings_page.preferences_theme_dark_toggle.wait_for(state="visible", timeout=15000)

            assert settings_page.get_theme_mode_from_storage() == "dark"
            assert settings_page.is_theme_selected("dark")
    finally:
        with allure.step("Cleanup — restore the original theme"):
            _restore_theme(settings_page, original_mode)


@pytest.mark.hubs
@pytest.mark.p2
def test_catalog_category_show_more_show_less(page):
    """Hubs/Catalog: 'Other' category Show more/Show less pagination (GAP-054 smoke)."""
    catalog_page = CatalogPage(page)
    category = "Other"

    with allure.step("Step 1 — Navigate to the Agents tab; category renders with the initial card count"):
        catalog_page.navigate_to_tab("agents")
        catalog_page.category_section(category).wait_for(state="visible", timeout=15000)
        initial_count = catalog_page.get_category_card_count(category)
        assert initial_count > 0, "'Other' category should render at least one card"

    with allure.step("Step 2 — Toggle reads 'Show more'"):
        assert catalog_page.get_show_more_button_text(category) == "Show more"

    with allure.step("Step 3 — Click Show more; card count increases and label flips to 'Show less'"):
        catalog_page.toggle_show_more(category)
        expect(catalog_page.category_cards(category)).not_to_have_count(initial_count, timeout=10000)
        expanded_count = catalog_page.get_category_card_count(category)
        assert expanded_count > initial_count
        assert catalog_page.get_show_more_button_text(category) == "Show less"

    with allure.step("Step 4 — Click Show less; card count collapses back to the initial count"):
        catalog_page.toggle_show_more(category)
        expect(catalog_page.category_cards(category)).to_have_count(initial_count, timeout=10000)
        assert catalog_page.get_show_more_button_text(category) == "Show more"


@pytest.mark.analytics
@pytest.mark.p2
def test_analytics_overview_leaderboard_drill_to_user_detail_and_back(page):
    """Analytics: Overview leaderboard row drills into user detail; Back returns to Overview (GAP-073 smoke)."""
    analytics_page = AnalyticsPage(page)

    with allure.step("Step 1 — Navigate to Analytics, select Last 30d, wait for the leaderboard"):
        analytics_page.navigate_to_analytics()
        analytics_page.select_last_30d()
        expect(analytics_page.overview_leaderboard_row.first).to_be_visible(timeout=15000)

    with allure.step("Step 2 — Capture the first leaderboard row's email"):
        first_row_text = analytics_page.first_leaderboard_email()
        assert first_row_text

    with allure.step("Step 3 — Click the first leaderboard row; user detail renders directly"):
        analytics_page.click_first_leaderboard_row()
        assert analytics_page.user_detail_title_text() in first_row_text
        for kpi in ("llm_calls", "tool_calls", "chat_msg", "agent_runs", "active_days", "errors"):
            assert analytics_page.is_user_detail_kpi_visible(kpi), f"KPI card '{kpi}' should be visible"

    with allure.step("Step 4 — The native Users list is bypassed (mutual exclusion by control flow)"):
        assert not analytics_page.is_users_list_showing()

    with allure.step("Step 5 — Click Back; Overview KPI row + leaderboard render again"):
        analytics_page.click_user_detail_back()
        expect(analytics_page.overview_kpi_team).to_be_visible(timeout=15000)
        expect(analytics_page.overview_leaderboard_row.first).to_be_visible(timeout=15000)


@pytest.mark.notifications
@pytest.mark.p2
def test_notifications_quick_panel_hover_mark_toggle(page, notification_unread_id):
    """Notifications: quick-panel hover reveals the mark-toggle; hover-out removes it (GAP-077 smoke)."""
    panel = NotificationQuickPanelPage(page)

    # Setup (not a case step): land on a page where the sidebar — and its bell
    # button — actually renders. The bell is sidebar-gated on the EXPANDED
    # state (GAP-077 precondition: collapsed sidebar removes it from the DOM
    # entirely, not merely hides it), so wait for it rather than clicking blind.
    panel.navigate("/")
    panel.bell_button.wait_for(state="visible", timeout=15000)

    with allure.step("Step 1 — Open the quick panel; no mark-toggle renders before any hover"):
        panel.open_quick_panel()
        assert not panel.is_mark_toggle_visible()
        assert panel.get_unread_row_count() >= 1, "Seeded unread row should be present in the quick panel"

    with allure.step("Step 2 — Hover the seeded unread row; toggle shows 'Mark as read'"):
        panel.hover_first_unread_row()
        expect(panel.mark_toggle_button).to_be_visible(timeout=5000)
        assert panel.get_mark_toggle_label() == "Mark as read"

    with allure.step("Step 3 — Move the pointer off the row; the toggle unmounts"):
        panel.move_pointer_away()
        expect(panel.mark_toggle_button).to_have_count(0, timeout=5000)
