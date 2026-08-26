"""UI test — Analytics page loads with default date range and all tabs visible.

Read-only verification against the currently-selected project's own analytics
data (`.agents/testing.md` § Test data strategy — prefer read-only assertions
on existing data when the observable doesn't require fresh state). This case
never creates, modifies, or deletes anything — it only checks page structure
and default-loading state, not specific KPI values (which may legitimately be
0/$0.00 for a project with no usage yet).

Test case: ELITEA-2310
AFS: test-specs/settings-analytics/l2_analytics-page-default-load_ELITEA-2310.md

Case-text drift (see AFS § Known Defects): the case text claims six tabs, a
"Last 24d" default label, and a "Last 7d" default range — all three are stale
against the live product (seven tabs including "Costs" and
"Agents & Pipelines"; default preset is "Last 24h" with a 1-day range,
matching the case's own step-3 preset list). Filed as clarification
elitea-testing-public#1185. This test asserts the live contract.
"""

import logging
from datetime import datetime, timedelta

import allure
import pytest
from pages.analytics_page import AnalyticsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p1, pytest.mark.regression, pytest.mark.new_verified]

EXPECTED_PRESET_LABELS = ("Last 24h", "Last 7d", "Last 30d", "Last 90d")
EXPECTED_TAB_LABELS = (
    "Overview",
    "Costs",
    "Agents & Pipelines",
    "Tools",
    "Users",
    "Health",
    "Guide",
)
# Default range is "Last 24h" (1 day) — allow a small tolerance for
# render-time drift between the From/To Date objects being constructed
# (per AFS § Automation Hints).
DEFAULT_RANGE_TOLERANCE = timedelta(minutes=2)


def _parse_picker_datetime(value: str) -> datetime:
    """Parse a DateTimePicker input's displayed value: 'dd/MM/yyyy HH:mm'."""
    return datetime.strptime(value, "%d/%m/%Y %H:%M")


class TestAnalyticsDefaultLoad:
    """ELITEA-2310 — Analytics page loads with default date range and all
    seven tabs visible."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-analytics/ELITEA-2310_analytics-page-default-load.md",
        "onetest-ai Test Case link",
    )
    def test_analytics_page_default_load(self, page):
        """Header, date filter bar (4 presets, "Last 24h" active by default,
        From/To 1 day apart), 7-tab bar with Overview selected, and the page
        settling out of its loading state all render as specified."""
        analytics_page = AnalyticsPage(page)
        console_errors = analytics_page.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Analytics: page loads at "
                "/settings/analytics without error"
            ):
                analytics_page.navigate()
                assert "/settings/analytics" in page.url, (
                    f"Expected URL to contain '/settings/analytics', got {page.url!r}"
                )

            with allure.step(
                'Step 2 — Verify the page header shows "Analytics" and, since a '
                "project is selected, the project-name badge"
            ):
                assert analytics_page.page_title.text_content() == "Analytics", (
                    f"Expected page header text 'Analytics', got "
                    f"{analytics_page.page_title.text_content()!r}"
                )
                assert analytics_page.project_badge.is_visible(), (
                    "Expected the 'Project: {name}' badge to be visible when a "
                    "project is selected"
                )
                badge_text = analytics_page.project_badge.text_content()
                assert badge_text and badge_text.startswith("Project:"), (
                    f"Expected project badge text to start with 'Project:', got {badge_text!r}"
                )

            with allure.step(
                "Step 3 — Verify the date filter bar shows exactly four preset "
                "toggle buttons, in order: Last 24h, Last 7d, Last 30d, Last 90d"
            ):
                presets = analytics_page.get_preset_buttons_in_order()
                assert len(presets) == len(EXPECTED_PRESET_LABELS), (
                    f"Expected {len(EXPECTED_PRESET_LABELS)} preset buttons, got {len(presets)}"
                )
                for preset_locator, expected_label in zip(presets, EXPECTED_PRESET_LABELS):
                    assert preset_locator.is_visible(), (
                        f"Expected preset button {expected_label!r} to be visible"
                    )
                    actual_label = preset_locator.text_content()
                    assert actual_label == expected_label, (
                        f"Expected preset label {expected_label!r}, got {actual_label!r}"
                    )

            with allure.step(
                'Step 4 — Verify "Last 24h" is the preset shown pressed/active '
                "by default; the other three are not"
            ):
                assert analytics_page.is_preset_active(analytics_page.preset_last_24h), (
                    "Expected 'Last 24h' preset to be aria-pressed=true by default"
                )
                for other_preset in (
                    analytics_page.preset_last_7d,
                    analytics_page.preset_last_30d,
                    analytics_page.preset_last_90d,
                ):
                    assert not analytics_page.is_preset_active(other_preset), (
                        "Expected only 'Last 24h' preset to be active by default"
                    )

            with allure.step(
                "Step 5 — Verify the From and To date/time inputs are present "
                "and, with the default 'Last 24h' preset selected, are exactly "
                "24 hours apart (From = now - 1 day, To = now)"
            ):
                assert analytics_page.date_from_input.is_visible(), (
                    "Expected the From date/time input to be visible"
                )
                assert analytics_page.date_to_input.is_visible(), (
                    "Expected the To date/time input to be visible"
                )
                from_value = analytics_page.date_from_input.input_value()
                to_value = analytics_page.date_to_input.input_value()
                from_dt = _parse_picker_datetime(from_value)
                to_dt = _parse_picker_datetime(to_value)
                actual_span = to_dt - from_dt
                expected_span = timedelta(hours=24)
                assert abs(actual_span - expected_span) <= DEFAULT_RANGE_TOLERANCE, (
                    f"Expected From/To span ~24h (±{DEFAULT_RANGE_TOLERANCE}), got "
                    f"{actual_span} (From={from_value!r}, To={to_value!r})"
                )

            with allure.step(
                "Step 6 — Verify all seven Analytics tabs are visible, in "
                "order: Overview, Costs, Agents & Pipelines, Tools, Users, "
                "Health, Guide"
            ):
                tabs = analytics_page.get_tabs_in_order()
                assert len(tabs) == len(EXPECTED_TAB_LABELS), (
                    f"Expected {len(EXPECTED_TAB_LABELS)} tabs, got {len(tabs)}"
                )
                for tab_locator, expected_label in zip(tabs, EXPECTED_TAB_LABELS):
                    assert tab_locator.is_visible(), (
                        f"Expected tab {expected_label!r} to be visible"
                    )
                    actual_label = tab_locator.text_content()
                    assert actual_label == expected_label, (
                        f"Expected tab label {expected_label!r}, got {actual_label!r}"
                    )

            with allure.step(
                'Step 7 — Verify the "Overview" tab is selected by default'
            ):
                assert analytics_page.is_tab_selected(analytics_page.tab_overview), (
                    "Expected the 'Overview' tab to be aria-selected=true by default"
                )
                for other_tab in (
                    analytics_page.tab_costs,
                    analytics_page.tab_agents_pipelines,
                    analytics_page.tab_tools,
                    analytics_page.tab_users,
                    analytics_page.tab_health,
                    analytics_page.tab_guide,
                ):
                    assert not analytics_page.is_tab_selected(other_tab), (
                        "Expected only the 'Overview' tab to be selected by default"
                    )

            with allure.step(
                "Step 8 — Verify the page does not remain in a permanent "
                "loading state: the loading spinner is gone and the Overview "
                "tab's KPI content is rendered; no console errors"
            ):
                assert analytics_page.loading_indicator.count() == 0, (
                    "Expected the analytics loading spinner to be gone once the "
                    "page has settled"
                )
                assert analytics_page.overview_kpi_row.is_visible(), (
                    "Expected the Overview tab's KPI card row to be visible once "
                    "the analytics fetch has settled"
                )
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
