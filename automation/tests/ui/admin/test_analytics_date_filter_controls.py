"""UI tests — Analytics date-filter controls: presets, custom From/To range,
and the From-cannot-exceed-To constraint.

Read-only verification against the currently-selected project's own analytics
data (`.agents/testing.md` § Test data strategy). Nothing is created, mutated
or deleted — the tests only drive the date-filter controls and read what the
product renders.

Test cases:
- ELITEA-2314 — AFS: test-specs/settings-analytics/l2_date-presets-update-pickers-and-content_ELITEA-2314.md
- ELITEA-2315 — AFS: test-specs/settings-analytics/l2_custom-date-range-filters-data_ELITEA-2315.md
- ELITEA-2316 — AFS: test-specs/settings-analytics/l2_from-date-cannot-exceed-to-date_ELITEA-2316.md

Fidelity: every asserted value is produced by the system — the picker inputs
the product renders and the query parameters of the product's OWN request,
captured live via `expect_response`. No response is fabricated, no state is
injected (`.agents/testing.md` § Fidelity policy).

Case-text drift asserted against the LIVE contract (reverse-masking guard):
- ELITEA-2314 step 2 claims "Last 7d" is the default preset with a 7-day
  range; the live default is **Last 24h / 1 day** (`AnalyticsContainer.jsx`,
  `useState(1)`). The 7-day range is still covered — by clicking `Last 7d`
  explicitly. Same stale-case-text family as elitea-testing-public#1185.
- ELITEA-2315/2316 say the picker is confirmed with "Ok"; the live button
  reads **"Apply"** (`localeText.okButtonLabel`).
"""

import logging
from datetime import datetime, timedelta

import allure
import pytest
from pages.analytics_page import AnalyticsPage
from utils.analytics_oracles import (
    assert_date_chart_matches,
    assert_overview_content_matches,
    response_dates,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression]

# From/To are built from two separate `new Date()` calls and the picker shows
# whole minutes only, so a preset's span is compared with a small tolerance.
SPAN_TOLERANCE = timedelta(minutes=2)

# `date_from`/`date_to` are ISO-8601 UTC in the request; the picker displays
# local time. Comparing the two therefore allows one minute of rounding on top
# of the timezone conversion the helper performs.
REQUEST_MATCH_TOLERANCE = timedelta(minutes=2)


def _request_range(response) -> tuple[datetime, datetime]:
    """`date_from`/`date_to` of an analytics request, as naive LOCAL datetimes."""
    from urllib.parse import parse_qs, unquote, urlparse

    params = parse_qs(urlparse(response.url).query)
    parsed = []
    for key in ("date_from", "date_to"):
        raw = unquote(params[key][0]).replace("Z", "+00:00")
        parsed.append(datetime.fromisoformat(raw).astimezone().replace(tzinfo=None))
    return parsed[0], parsed[1]


def _assert_span(analytics_page: AnalyticsPage, days: int, label: str) -> None:
    """The two picker inputs are exactly *days* apart (± render tolerance)."""
    date_from, date_to = analytics_page.get_date_range()
    span = date_to - date_from
    assert abs(span - timedelta(days=days)) <= SPAN_TOLERANCE, (
        f"{label}: expected the From/To pickers to be {days} day(s) apart, got {span} "
        f"(From={analytics_page.get_date_from_text()!r}, To={analytics_page.get_date_to_text()!r})"
    )


def _assert_request_matches_pickers(analytics_page: AnalyticsPage, response, label: str) -> None:
    """The refetch asked for exactly the range the pickers now display."""
    req_from, req_to = _request_range(response)
    ui_from, ui_to = analytics_page.get_date_range()
    assert abs(req_from - ui_from) <= REQUEST_MATCH_TOLERANCE, (
        f"{label}: request date_from {req_from} does not match the displayed From {ui_from}"
    )
    assert abs(req_to - ui_to) <= REQUEST_MATCH_TOLERANCE, (
        f"{label}: request date_to {req_to} does not match the displayed To {ui_to}"
    )
    assert response.status == 200, f"{label}: analytics request returned {response.status}"


def _assert_only_preset_pressed(analytics_page: AnalyticsPage, expected: str) -> None:
    pressed = analytics_page.get_pressed_preset_labels()
    assert pressed == [expected], (
        f"Expected exactly one highlighted preset ({expected!r}), got {pressed!r}"
    )


class TestAnalyticsDatePresets:
    """ELITEA-2314 — predefined presets update the From/To pickers and refresh content."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-analytics/ELITEA-2314_predefined-date-presets.md",
        "onetest-ai Test Case link",
    )
    def test_presets_update_pickers_and_refresh_content(self, page):
        """Each preset sets its own From/To span, re-queries with exactly that
        range, re-renders the Overview content, and stays mutually exclusive."""
        analytics_page = AnalyticsPage(page)
        console_errors = analytics_page.capture_console_errors()

        try:
            with allure.step("Step 1 — Navigate to Settings -> Analytics"):
                analytics_page.navigate()
                assert "/settings/analytics" in page.url, (
                    f"Expected URL to contain '/settings/analytics', got {page.url!r}"
                )

            with allure.step(
                'Step 2 — Default preset is "Last 24h" with a 1-day From/To range '
                "(case text says Last 7d / 7 days — stale, see module docstring)"
            ):
                _assert_only_preset_pressed(analytics_page, "Last 24h")
                _assert_span(analytics_page, 1, "default state")

            for step_no, (label, locator, days) in enumerate(
                (
                    ("Last 7d", analytics_page.preset_last_7d, 7),
                    ("Last 24h", analytics_page.preset_last_24h, 1),
                    ("Last 30d", analytics_page.preset_last_30d, 30),
                    ("Last 90d", analytics_page.preset_last_90d, 90),
                ),
                start=3,
            ):
                with allure.step(
                    f'Step {step_no} — Click "{label}": pickers show a {days}-day range, the '
                    "analytics query re-fires for exactly that range, content re-renders, and "
                    "only this preset is highlighted"
                ):
                    response = analytics_page.click_preset(locator)
                    analytics_page.wait_for_overview_settled()

                    _assert_only_preset_pressed(analytics_page, label)
                    _assert_span(analytics_page, days, label)
                    _assert_request_matches_pickers(analytics_page, response, label)

                    # "Content re-renders" was claimed by this test's docstring
                    # and every step title, but only the REQUEST was asserted —
                    # a refetch whose result never reached the DOM passed. The
                    # Overview surfaces are now matched against this preset's
                    # own captured response, so each of the four ranges is
                    # evidence rather than narration.
                    body = response.json()
                    assert_overview_content_matches(analytics_page, body, label)
                    dates = response_dates(body, "daily_activity")
                    if dates:
                        assert_date_chart_matches(
                            analytics_page.get_daily_chart_tick_labels(),
                            dates,
                            f"{label} Daily Activity chart",
                        )

            with allure.step("Step 7 — No unexpected console errors during the preset sequence"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()


class TestAnalyticsCustomDateRange:
    """ELITEA-2315 — a custom From/To range, chosen through the calendars, filters the data."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-analytics/ELITEA-2315_custom-date-range.md",
        "onetest-ai Test Case link",
    )
    def test_custom_from_to_range_filters_data(self, page):
        """From = day 15 of the month the From picker opens on after `Last 90d`,
        To = day 10 of the current month; both fields display the selections and
        the Overview content matches the response for that custom range."""
        analytics_page = AnalyticsPage(page)
        console_errors = analytics_page.capture_console_errors()

        try:
            with allure.step("Step 1 — Navigate to Settings -> Analytics"):
                analytics_page.navigate()

            with allure.step(
                'Setup — Click "Last 90d" so the From picker opens on a month roughly three '
                "months back, where every day is inside the picker's maxDateTime bound"
            ):
                analytics_page.click_preset(analytics_page.preset_last_90d)
                analytics_page.wait_for_overview_settled()

            with allure.step(
                "Step 2 — Open the From calendar and select a past day (day 15 of the "
                "displayed month)"
            ):
                analytics_page.open_date_picker("from")
                from_month = analytics_page.get_picker_month_label("from")
                analytics_page.select_picker_day("from", 15)
                expected_from = analytics_page.get_date_from_text()
                assert expected_from.startswith("15/"), (
                    f"Expected the From input to show day 15 of {from_month!r}, got {expected_from!r}"
                )

            with allure.step('Step 3 — Confirm with "Apply" (case text says "Ok"): the popper closes'):
                analytics_page.apply_picker("from")

            with allure.step(
                "Step 4 — Open the To calendar and select a day after From (day 10 of the "
                "current month)"
            ):
                analytics_page.open_date_picker("to")
                to_month = analytics_page.get_picker_month_label("to")
                response = analytics_page.select_picker_day("to", 10)
                expected_to = analytics_page.get_date_to_text()
                assert expected_to.startswith("10/"), (
                    f"Expected the To input to show day 10 of {to_month!r}, got {expected_to!r}"
                )

            with allure.step('Step 5 — Confirm with "Apply": the popper closes'):
                analytics_page.apply_picker("to")
                analytics_page.wait_for_overview_settled()

            with allure.step("Step 6 — Both fields display the selected values and From < To"):
                assert analytics_page.get_date_from_text() == expected_from
                assert analytics_page.get_date_to_text() == expected_to
                date_from, date_to = analytics_page.get_date_range()
                assert date_from < date_to, f"Expected From < To, got {date_from} / {date_to}"

            with allure.step(
                "Step 7 — The custom range drove the query and the Overview content matches "
                "the response returned for it; the control switched to the Custom preset"
            ):
                _assert_request_matches_pickers(analytics_page, response, "custom range")
                _assert_only_preset_pressed(analytics_page, "Custom")

                body = response.json()
                # All 8 KPI cards (COST included), the leaderboard's count,
                # conditional container and top-row content, and the Model Usage
                # table — the same oracle the sibling spec uses, so no range is
                # checked more weakly than another.
                assert_overview_content_matches(analytics_page, body, "custom range")

                # The chart, on data. An earlier round asserted a bare SUBSET of
                # the response's dates, which a chart still drawing a narrower
                # older range can satisfy; the shared oracle also pins the last
                # tick and the rendered span.
                dates = response_dates(body, "daily_activity")
                if dates:
                    assert_date_chart_matches(
                        analytics_page.get_daily_chart_tick_labels(),
                        dates,
                        "custom range Daily Activity chart",
                    )

            with allure.step("Step 8 — No unexpected console errors"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()


class TestAnalyticsFromDateConstraint:
    """ELITEA-2316 — the From picker cannot be set later than the To value."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-analytics/ELITEA-2316_from-date-cannot-exceed-to.md",
        "onetest-ai Test Case link",
    )
    def test_from_date_cannot_be_later_than_to_date(self, page):
        """With To moved into the past, every later day in the From calendar is
        disabled, a forced click changes nothing, and no request is made for the
        invalid timespan."""
        analytics_page = AnalyticsPage(page)
        console_errors = analytics_page.capture_console_errors()

        try:
            with allure.step("Step 1 — Navigate to Settings -> Analytics"):
                analytics_page.navigate()

            with allure.step(
                'Setup — Click "Last 90d" and set From to day 10 of the month the picker opens '
                "on (a month ~3 months back, entirely selectable)"
            ):
                analytics_page.click_preset(analytics_page.preset_last_90d)
                analytics_page.wait_for_overview_settled()
                analytics_page.open_date_picker("from")
                target_month = analytics_page.get_picker_month_label("from")
                analytics_page.select_picker_day("from", 10)
                analytics_page.apply_picker("from")

            with allure.step(
                "Step 2 — Set To into the past: day 20 of that same month (the case's "
                '"5 days ago" with a calendar-boundary-free date, see AFS Automation Hints)'
            ):
                analytics_page.open_date_picker("to")
                analytics_page.go_to_picker_month("to", target_month)
                response = analytics_page.select_picker_day("to", 20)
                analytics_page.apply_picker("to")
                analytics_page.wait_for_overview_settled()

                assert analytics_page.get_date_to_text().startswith("20/"), (
                    f"Expected To to show day 20 of {target_month!r}, got "
                    f"{analytics_page.get_date_to_text()!r}"
                )
                _assert_request_matches_pickers(analytics_page, response, "To set into the past")

            with allure.step(
                "Step 3 — Attempt to set From later than To: day 21 of the same month is "
                "rendered disabled, as is every later day and the next-month control; the "
                "click is dispatched anyway (force)"
            ):
                from_before = analytics_page.get_date_from_text()
                analytics_page.open_date_picker("from")
                assert analytics_page.get_picker_month_label("from") == target_month, (
                    "From picker should re-open on the month of its current value"
                )

                invalid_day = analytics_page.get_picker_day_cell("from", 21)
                assert invalid_day.is_disabled(), (
                    "Day 21 (later than the To value) should be disabled in the From calendar"
                )
                for later_day in (22, 28):
                    assert analytics_page.get_picker_day_cell("from", later_day).is_disabled(), (
                        f"Day {later_day} (later than the To value) should be disabled too"
                    )
                assert analytics_page.picker_month_nav("from", "next").is_disabled(), (
                    "The From picker's 'Next month' control should be disabled — the whole "
                    "range beyond To is out of bounds, not just single cells"
                )

                invalid_day.click(force=True)

            with allure.step(
                "Step 4 — The selection was prevented: From is unchanged, From < To still "
                "holds, no request was made for the invalid timespan, and the content is intact"
            ):
                analytics_page.assert_no_analytics_request(window_ms=1_500)
                assert analytics_page.get_date_from_text() == from_before, (
                    f"From changed after the forced click on a disabled day: "
                    f"{from_before!r} -> {analytics_page.get_date_from_text()!r}"
                )
                date_from, date_to = analytics_page.get_date_range()
                assert date_from < date_to, (
                    f"From must still be earlier than To, got {date_from} / {date_to}"
                )
                analytics_page.apply_picker("from")
                assert analytics_page.overview_kpi_row.is_visible(), (
                    "Overview content should still be rendered from the last valid response"
                )

            with allure.step("Step 5 — No unexpected console errors"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
