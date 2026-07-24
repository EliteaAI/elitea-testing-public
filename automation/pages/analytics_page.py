"""Analytics page object for Elitea platform.

Handles ``/settings/analytics`` — the Overview tab's KPI row + "Top 5 AI
Adopters" leaderboard, the cross-tab drill-down into a single user's detail
view (Users tab, pre-seeded via the leaderboard-row click), and the Users
tab's own list header (used only for GAP-073's absence checks proving the
drill-down bypasses the list).

Scope is exactly what GAP-073 (Overview leaderboard -> user detail -> Back)
touches: the TEAM KPI card, the leaderboard row, the six user-detail KPI
cards, the detail Back button/title, and the Users-list title/search input
(referenced only via absence assertions — canon ruling #511 extension,
``.agents/testing.md`` § Locator policy).

URL: /settings/analytics
"""

import logging

from playwright.sync_api import Page
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.analytics")


class AnalyticsPage(BasePage):
    """Page object for ``/settings/analytics``.

    URL: /settings/analytics
    """

    # ------------------------------------------------------------------
    # Overview tab
    # ------------------------------------------------------------------

    overview_kpi_team = LocatorDescriptor(
        testid="analytics-overview-kpi-team",
        description="'TEAM' KPI card on the Overview tab",
    )

    # Every leaderboard row shares one testid (repeated-list-item pattern,
    # not a state-switched identity) — index/first() to address a specific row.
    overview_leaderboard_row = LocatorDescriptor(
        testid="analytics-overview-leaderboard-row",
        description="A 'Top 5 AI Adopters' leaderboard row on the Overview tab",
    )

    # Date preset toggle used only to reach a non-empty leaderboard —
    # declared improvisation: not requested by GAP-073's own Concrete
    # Handles table, but the project's locator policy has no non-testid
    # rung, so a scoped testid was added to the existing TabGroupButton
    # buttonProps extension point (same mechanism as ThemeModeToggle).
    date_preset_30d_button = LocatorDescriptor(
        testid="analytics-date-preset-30d-button",
        description="'Last 30d' date-range preset button",
    )

    # ------------------------------------------------------------------
    # Users tab — cross-tab user detail (drill-down target)
    # ------------------------------------------------------------------

    user_detail_back_button = LocatorDescriptor(
        testid="analytics-user-detail-back-button",
        description="Back arrow on the user-detail view",
    )
    user_detail_title = LocatorDescriptor(
        testid="analytics-user-detail-title",
        description="User-detail view title (the user's email)",
    )
    user_detail_kpi_llm_calls = LocatorDescriptor(testid="analytics-user-detail-kpi-llm-calls")
    user_detail_kpi_tool_calls = LocatorDescriptor(testid="analytics-user-detail-kpi-tool-calls")
    user_detail_kpi_chat_msg = LocatorDescriptor(testid="analytics-user-detail-kpi-chat-msg")
    user_detail_kpi_agent_runs = LocatorDescriptor(testid="analytics-user-detail-kpi-agent-runs")
    user_detail_kpi_active_days = LocatorDescriptor(testid="analytics-user-detail-kpi-active-days")
    user_detail_kpi_errors = LocatorDescriptor(testid="analytics-user-detail-kpi-errors")

    # ------------------------------------------------------------------
    # Users tab — native list (referenced only via absence checks, per
    # canon ruling #511 extension: an absent-testid check IS a reference)
    # ------------------------------------------------------------------

    users_list_title = LocatorDescriptor(
        testid="analytics-users-list-title",
        description="'User Activity' heading — absent while the cross-tab detail view is showing",
    )
    users_list_search_input = LocatorDescriptor(
        testid="analytics-users-list-search-input",
        description="Users-list search box — absent while the cross-tab detail view is showing",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate_to_analytics(self) -> None:
        """Navigate to /settings/analytics and wait for the Overview KPI row."""
        self.navigate("/settings/analytics")
        self.date_preset_30d_button.wait_for(state="visible", timeout=15000)
        logger.info("Navigated to Analytics page")

    @action("Select Last 30d date preset")
    def select_last_30d(self) -> None:
        """Click the 'Last 30d' date-range preset (widens the leaderboard window)."""
        self.date_preset_30d_button.click()
        self.overview_kpi_team.wait_for(state="visible", timeout=15000)

    def get_leaderboard_row_count(self) -> int:
        """Return how many leaderboard rows are currently rendered."""
        return self.overview_leaderboard_row.count()

    def first_leaderboard_email(self) -> str:
        """Return the first leaderboard row's raw text (contains the user's email)."""
        return (self.overview_leaderboard_row.first.text_content() or "").strip()

    @action("Click first leaderboard row")
    def click_first_leaderboard_row(self) -> None:
        """Click the first 'Top 5 AI Adopters' row — drills into that user's detail."""
        self.overview_leaderboard_row.first.click()
        self.user_detail_title.wait_for(state="visible", timeout=15000)

    def user_detail_title_text(self) -> str:
        """Return the user-detail view's title text (the user's email)."""
        return (self.user_detail_title.text_content() or "").strip()

    def is_user_detail_kpi_visible(self, kpi: str) -> bool:
        """Return True if the named user-detail KPI card is visible.

        Args:
            kpi: one of 'llm_calls', 'tool_calls', 'chat_msg', 'agent_runs',
                'active_days', 'errors'.
        """
        field = getattr(self, f"user_detail_kpi_{kpi}", None)
        if field is None:
            raise ValueError(f"Unknown KPI card: {kpi!r}")
        return field.count() > 0 and field.first.is_visible()

    @action("Click user-detail Back button")
    def click_user_detail_back(self) -> None:
        """Click the user-detail view's Back arrow — returns to the Overview tab."""
        self.user_detail_back_button.click()
        self.overview_kpi_team.wait_for(state="visible", timeout=15000)

    def is_users_list_showing(self) -> bool:
        """Return True if the native Users-list (title + search) is present.

        Used as the absence check proving the cross-tab drill-down bypassed
        the list entirely (GAP-073 step 5) — both testids are referenced
        via this absence assertion (canon ruling #511 extension).
        """
        return self.users_list_title.count() > 0 or self.users_list_search_input.count() > 0
