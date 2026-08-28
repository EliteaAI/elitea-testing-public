"""UI test — hovering the Overview "Daily Activity" chart shows a tooltip with
the hovered day's date and every rendered series' value, updates on a second
data point, and unmounts on mouse-out.

Read-only verification against the currently-selected project's own analytics
data (`.agents/testing.md` § Test data strategy). This case never creates,
modifies, or deletes anything.

Test case: ELITEA-2326
AFS: test-specs/settings-analytics/l2_overview-daily-activity-chart-hover-tooltip_ELITEA-2326.md

Fidelity (`.agents/testing.md` § Fidelity policy) — **no substitutions**. Both
hovers are real `page.mouse.move()` CDP input events (never a `page.evaluate`
dispatched synthetic event, which would make the test the producer of the
observable), and every asserted number is compared against the live
`analytics/prompt_lib/` response body captured off the wire.

Case-text drift (filed elitea-testing-public#1954): the case's step 3 says the
tooltip shows "numeric values for both series (Events and Users)". Live, the
chart renders FOUR series — `LLM Calls`, `Tool Runs`, `Agent & Pipeline Runs`
and (only on a non-personal project, `!isPersonalProject`) `Active Users` — and
none of them is named "Events". This test asserts the live contract, not the
stale case text (reverse-masking guard).
"""

import logging

import allure
import pytest
from pages.analytics_page import AnalyticsPage
from playwright.sync_api import expect
from utils.analytics_format import fmt_num
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

# The Overview "Daily Activity" chart's `<Area>` declarations, in render order
# (`AnalyticsOverview.jsx:184-221`) — series NAME -> the `daily_activity` field
# the value is read from. `Active Users` is CONDITIONAL on `!isPersonalProject`,
# so the expected list is derived from the rendered area-path count at run time
# rather than hardcoded — the same spec is then honest on a personal project
# (3 series) and a non-personal one (4).
SERIES_NAME_TO_RESPONSE_KEY = (
    ("LLM Calls", "llm_calls"),
    ("Tool Runs", "tool_runs"),
    ("Agent & Pipeline Runs", "agent_runs"),
    ("Active Users", "active_users"),
)

# Fractions of the chart container's width to hover. Recharts snaps to the
# nearest category, so no exact datum-pixel maths is needed — the test reads
# whichever date it landed on out of the captured response.
FIRST_HOVER_FRACTION = 0.25
SECOND_HOVER_FRACTION = 0.75


class TestAnalyticsOverviewDailyChartTooltip:
    """ELITEA-2326 — Overview tab's "Daily Activity" area chart: hover raises a
    tooltip carrying the day's date plus one line per rendered series with the
    value the backend reported for that day; moving to another point re-renders
    it against the new day; moving off the chart unmounts it."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/analytics/ELITEA-2326_hovering-over-daily-activity-chart-on-overview-tab-shows-too.md",
        "onetest-ai Test Case link",
    )
    def test_overview_daily_chart_hover_tooltip(self, page):
        """Hovering the Overview Daily Activity chart shows a tooltip whose
        label is the hovered day and whose series lines carry that day's
        values from the captured analytics response; a second hover updates
        it; moving away removes it from the DOM."""
        analytics_page = AnalyticsPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            'Step 1 — Navigate to Settings -> Analytics (Overview is default), click "Last 30d" '
            "and capture the analytics response as the oracle"
        ):
            analytics_page.navigate()
            response = analytics_page.select_date_preset_capturing_analytics(analytics_page.preset_last_30d)
            assert analytics_page.is_tab_selected(analytics_page.tab_overview), (
                "Expected the Overview tab to be aria-selected=true on the default Analytics load"
            )
            expect(analytics_page.overview_daily_chart_container).to_be_visible()

            daily_activity = response.get("daily_activity") or []
            # Precondition, asserted against the captured response so an empty
            # project fails loudly here rather than as a confusing
            # tooltip-never-changes timeout in step 4.
            assert len(daily_activity) >= 2, (
                f"Expected the selected project to have at least 2 daily_activity entries over "
                f"Last 30d so the case's 'move to a different data point' step has a second "
                f"point to move to, got {len(daily_activity)}"
            )
            dates_to_points = {entry["date"]: entry for entry in daily_activity}

        with allure.step("Step 2 — Hover a data point on the Daily Activity area chart"):
            series_count = analytics_page.get_chart_area_series_count(
                analytics_page.overview_daily_chart_container
            )
            assert series_count in (3, 4), (
                f"Expected the Daily Activity chart to render 3 series (personal project) or 4 "
                f"(non-personal, with 'Active Users'), got {series_count}"
            )
            expected_series = SERIES_NAME_TO_RESPONSE_KEY[:series_count]

            analytics_page.hover_chart_at_fraction(
                analytics_page.overview_daily_chart_container, FIRST_HOVER_FRACTION
            )
            expect(analytics_page.overview_daily_chart_tooltip).to_be_visible()

        with allure.step(
            "Step 3 — Verify the tooltip's label is the hovered day and its series lines carry "
            "that day's values from the captured response"
        ):
            first_lines = analytics_page.read_chart_tooltip_lines(
                analytics_page.overview_daily_chart_tooltip
            )
            first_label = _assert_tooltip_matches_a_response_day(
                first_lines, dates_to_points, expected_series
            )
            logger.info("First hover landed on %s: %s", first_label, first_lines[1:])

        with allure.step(
            "Step 4 — Move to a different data point and verify the tooltip re-renders against "
            "the new day"
        ):
            analytics_page.hover_chart_at_fraction(
                analytics_page.overview_daily_chart_container, SECOND_HOVER_FRACTION
            )
            second_lines = analytics_page.wait_for_chart_tooltip_change(
                analytics_page.overview_daily_chart_tooltip, first_lines
            )
            expect(analytics_page.overview_daily_chart_tooltip).to_be_visible()
            second_label = _assert_tooltip_matches_a_response_day(
                second_lines, dates_to_points, expected_series
            )
            assert second_label != first_label, (
                f"Expected the second hover to land on a different day than the first, but both "
                f"tooltips are labelled {first_label!r}"
            )

        with allure.step("Step 5 — Move the cursor away from the chart and verify the tooltip disappears"):
            analytics_page.move_mouse_off_chart(analytics_page.overview_daily_chart_container)
            # The shared `ChartTooltip` returns null when `!active`, so the node
            # UNMOUNTS rather than merely hiding — count 0, not not_to_be_visible.
            expect(analytics_page.overview_daily_chart_tooltip).to_have_count(0)

        assert not console_errors, f"Unexpected console errors: {console_errors}"


def _assert_tooltip_matches_a_response_day(lines, dates_to_points, expected_series) -> str:
    """Assert *lines* (a `ChartTooltip` render: label first, then one
    ``"{series}: {value}"`` line per series) describes one of the days in the
    captured response, and return that day's label.

    Every asserted number comes from the response body the UI itself rendered
    from — the test never authors an expected value.
    """
    assert lines, "Expected the hover tooltip to render at least a label line"
    label = lines[0]
    assert label in dates_to_points, (
        f"Expected the tooltip's label line to be one of the captured response's "
        f"daily_activity dates, got {label!r} (available: {sorted(dates_to_points)!r})"
    )
    point = dates_to_points[label]
    expected_lines = [f"{name}: {fmt_num(point[key])}" for name, key in expected_series]
    assert lines[1:] == expected_lines, (
        f"Expected the tooltip for {label!r} to list exactly {expected_lines!r} "
        f"(series names and values from the captured response), got {lines[1:]!r}"
    )
    return label
