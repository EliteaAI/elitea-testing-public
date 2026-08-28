"""UI test — Clicking a user row in Users tab opens the user detail view.

Read-only verification against the currently-selected project's own analytics
data (`.agents/testing.md` § Test data strategy — prefer read-only assertions
on existing data when the observable doesn't require fresh state). This case
never creates, modifies, or deletes anything.

Test case: ELITEA-2313
AFS: test-specs/settings-analytics/l2_users-tab-row-click-opens-detail-view_ELITEA-2313.md

Extended by ELITEA-2329 (`extend-existing`)
AFS: test-specs/settings-analytics/lextend_user-detail-daily-activity-tooltip_ELITEA-2329.md
Steps 8b/8c/8d are that case's gap assertions — the original Step 8 proves a
tooltip appears with *at least one* series label and a non-empty date line;
ELITEA-2329 additionally pins the EXACT series list (`LLM`, `Tool`, `Chat Msg`,
`Agent`, matched against the rendered `<Area>` count), every value against the
captured `analytics_user_detail/prompt_lib/` response, the re-render on a second
data point, and the tooltip unmounting on mouse-out. No existing assertion was
weakened or removed; the only edit to the pre-existing flow is Step 1 calling
`open_user_detail_by_row_capturing_analytics()` (identical click and waits, plus
a 200 assertion) so the response body is available as the oracle.

Case-text drift (see AFS § Known Defects): the case's step 4 lists 6 KPI
cards (LLM Calls, Tool Calls, Chat Msg, Agent Runs, Active Days, Errors),
omitting Total/Input/Output Tokens and Total Cost; live view has 10 cards.
The case's step 7 says "Agents Used"; live label is "Agents & Pipelines
Used" — same stale-count family as ELITEA-2310/2311/2312. Filed clarification
elitea-testing-public#1191. This test asserts the live contract for both.

Known product defect (NOT worked around here — this test's happy path
deliberately selects a row with a non-null email, so it is unaffected):
`AnalyticsUserDetailed.jsx` renders a blank title for a user with no email
(no `User {id}` fallback, unlike the Users-table row which has one). Filed
elitea-testing-public#1192.

Implementer amendment (Phase 2 exploration — see AFS Concrete Handles table):
the analyst's original plan read the 9 non-Errors cards' default color off
the outer `analytics-user-detail-kpi-card` locator itself. Live-verified this
doesn't work — `KpiCard.jsx`'s card `Box` carries no `color` style at all, so
its computed color is constant (`rgb(169, 183, 193)`) regardless of the
Errors branch; only the inner value `Typography` (the `color` prop's target)
varies. Fixed by wiring a uniform `analytics-user-detail-kpi-value` testid on
every card's value node instead of an Errors-only one.
"""

import logging

import allure
import pytest
from pages.analytics_page import AnalyticsPage
from playwright.sync_api import expect
from utils.analytics_format import fmt_num

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

# Live card set, source-confirmed at `AnalyticsUserDetailed.jsx:73-188` (every
# card is unconditional). The product grew this row from 10 to 16 cards AFTER
# ELITEA-2313 was automated — EliteaAI/EliteaUI@f084ea12 ("Display input/output
# token cost breakdown in analytics UI") and EliteaAI/EliteaUI@ce8115c6
# ("surface prompt-cache tokens/cost across analytics UI"), both EL-6267 — which
# left the merged expectation of 10 stale and this spec red on
# `automation/base` BEFORE this branch existed (verified with a pristine-HEAD
# control run: byte-identical failure). Updated to the live contract rather than
# to the stale hypothesis (`.agents/testing.md` reverse-masking guard); the
# assertion is strengthened, not weakened — it still pins the exact set and order.
EXPECTED_KPI_LABELS_IN_ORDER = (
    "ACTIVE DAYS",
    "LLM CALLS",
    "TOOL CALLS",
    "AGENT & PIPELINE RUNS",
    "CHAT MSG",
    "ERRORS",
    "TOTAL TOKENS",
    "INPUT TOKENS",
    "OUTPUT TOKENS",
    "CACHE READ TOKENS",
    "CACHE WRITE TOKENS",
    "CACHE READ COST",
    "CACHE WRITE COST",
    "TOTAL COST",
    "INPUT TOKEN COST",
    "OUTPUT TOKEN COST",
)

# Same resolved theme colors as ELITEA-2312's Users-table Errors column
# (confirmed live via getComputedStyle — do not assume cross-surface reuse
# without re-checking; re-verified live for this view during implementation).
KPI_VALUE_DEFAULT_COLOR = "rgb(255, 255, 255)"
KPI_VALUE_ERRORS_COLOR = "rgb(215, 22, 22)"

# ELITEA-2329 — the user-detail "Daily Activity" chart's `<Area>` declarations, in
# render order (`AnalyticsUserDetailed.jsx:250/260/270/280`): series NAME -> the
# `daily_activity` field its value is read from. This chart renders NO legend, so
# these names exist in the DOM only inside the hover tooltip.
SERIES_NAME_TO_RESPONSE_KEY = (
    ("LLM", "llm"),
    ("Tool", "tool"),
    ("Chat Msg", "chat"),
    ("Agent", "agent"),
)

# Fractions of the chart container's width to hover for the two ELITEA-2329 data
# points. Recharts snaps to the nearest category, so no exact datum-pixel maths is
# needed — the test reads whichever date it landed on out of the captured response.
CENTRE_HOVER_FRACTION = 0.5
FIRST_HOVER_FRACTION = 0.25
SECOND_HOVER_FRACTION = 0.75

CHART_TITLE_TEXT = "Daily Activity"
CHART_SUBTITLE_TEXT = "Events by type per day"

PANEL_TITLES = ("Models Used", "Tools Used", "Agents & Pipelines Used")

HOVER_TOOLTIP_TIMEOUT = 10_000


class TestAnalyticsUserDetailView:
    """ELITEA-2313 — clicking a Users-tab row opens the user detail view:
    email title + back arrow, 10 KPI cards (Errors red only when > 0), a
    conditional Daily Activity chart with a working hover tooltip, three
    summary panels (Models/Tools/Agents & Pipelines Used), and back
    navigation restoring the Users-tab table with no new network request."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-analytics/ELITEA-2313_clicking-a-user-row-in-users-tab-opens-the-user-detail-view.md",
        "onetest-ai Test Case link",
    )
    def test_users_tab_row_click_opens_detail_view(self, page):
        """Clicking a user row (non-null email, errors > 0) swaps the
        Users-tab table for the detail view; verifies title/back-arrow, the
        10-card KPI set (order + Errors-color contract, both branches), the
        Daily Activity chart + hover tooltip, the three summary panels, and
        back navigation back to the table with no new network request."""
        analytics_page = AnalyticsPage(page)
        console_errors = analytics_page.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Analytics, click the Users tab, and click "
                "a user row with a non-null email and errors > 0"
            ):
                analytics_page.navigate()
                analytics_page.open_users_tab()
                row_count = analytics_page.get_users_row_count()
                assert row_count > 0, (
                    "Expected at least one user row (AFS precondition: project has "
                    "usage-analytics data)"
                )
                target_index = next(
                    (
                        i
                        for i in range(row_count)
                        if "@" in analytics_page.get_user_row_identifier(i)
                        and analytics_page.get_user_row_errors_value(i) > 0
                    ),
                    None,
                )
                assert target_index is not None, (
                    "Expected at least one row with a non-null email and errors > 0 to "
                    "exercise the Errors-red-color branch (AFS precondition)"
                )
                target_email = analytics_page.get_user_row_identifier(target_index)

                # ELITEA-2329 needs the user-detail response body as the oracle for the
                # hover-tooltip values; the capturing sibling performs the identical click
                # and waits, and additionally asserts the query resolved 200.
                user_detail_response = analytics_page.open_user_detail_by_row_capturing_analytics(
                    target_index
                )

                assert analytics_page.users_table_header.count() == 0, (
                    "Expected the Users-tab table panel to be replaced (unmounted) by the "
                    "detail view, not merely hidden"
                )

            with allure.step(
                "Step 2 — Verify the detail view's title is the user's email, with a "
                "back-arrow icon button to its left"
            ):
                assert analytics_page.user_detail_title.text_content() == target_email, (
                    f"Expected detail-view title {target_email!r}, got "
                    f"{analytics_page.user_detail_title.text_content()!r}"
                )
                assert analytics_page.user_detail_back_button.is_visible(), (
                    "Expected the back-arrow button to be visible"
                )
                back_box = analytics_page.user_detail_back_button.bounding_box()
                title_box = analytics_page.user_detail_title.bounding_box()
                assert back_box and title_box, "Expected both the back button and title to have a layout box"
                assert back_box["x"] < title_box["x"], (
                    f"Expected the back-arrow button to sit to the left of the title "
                    f"(back x={back_box['x']}, title x={title_box['x']})"
                )

            with allure.step(
                "Step 3 — Verify the KPI cards are shown, in the product's declaration order: "
                "Active Days, LLM Calls, Tool Calls, Agent & Pipeline Runs, Chat Msg, Errors, "
                "Total/Input/Output Tokens, Cache Read/Write Tokens, Cache Read/Write Cost, "
                "Total Cost, Input/Output Token Cost"
            ):
                assert analytics_page.user_detail_kpi_cards.count() == len(EXPECTED_KPI_LABELS_IN_ORDER), (
                    f"Expected exactly {len(EXPECTED_KPI_LABELS_IN_ORDER)} KPI cards, got "
                    f"{analytics_page.user_detail_kpi_cards.count()}"
                )
                actual_labels = analytics_page.get_user_detail_kpi_labels_in_order()
                assert tuple(actual_labels) == EXPECTED_KPI_LABELS_IN_ORDER, (
                    f"Expected KPI labels {EXPECTED_KPI_LABELS_IN_ORDER}, got {tuple(actual_labels)}"
                )

            with allure.step(
                "Step 4 — Verify the Errors KPI card's value renders in the red/rejected "
                "color (errors > 0), and every other card renders in the default text color"
            ):
                errors_index = EXPECTED_KPI_LABELS_IN_ORDER.index("ERRORS")
                expect(analytics_page.user_detail_kpi_values.nth(errors_index)).to_have_css(
                    "color", KPI_VALUE_ERRORS_COLOR
                )
                for i in range(len(EXPECTED_KPI_LABELS_IN_ORDER)):
                    if i == errors_index:
                        continue
                    expect(analytics_page.user_detail_kpi_values.nth(i)).to_have_css(
                        "color", KPI_VALUE_DEFAULT_COLOR
                    )

            with allure.step(
                'Step 5 — Verify a "Daily Activity" multi-series area chart is shown with '
                'subtitle "Events by type per day"'
            ):
                assert analytics_page.user_detail_chart_title.text_content() == CHART_TITLE_TEXT, (
                    f"Expected chart title {CHART_TITLE_TEXT!r}, got "
                    f"{analytics_page.user_detail_chart_title.text_content()!r}"
                )
                assert analytics_page.user_detail_chart_subtitle.text_content() == CHART_SUBTITLE_TEXT, (
                    f"Expected chart subtitle {CHART_SUBTITLE_TEXT!r}, got "
                    f"{analytics_page.user_detail_chart_subtitle.text_content()!r}"
                )
                assert analytics_page.user_detail_chart_container.is_visible(), (
                    "Expected the Daily Activity chart container to be visible "
                    "(AFS precondition: user has daily_activity data)"
                )

            with allure.step(
                "Step 6 — Verify three summary panels are shown below the chart: Models "
                "Used, Tools Used, Agents & Pipelines Used"
            ):
                assert analytics_page.user_detail_models_panel.is_visible(), (
                    "Expected the Models Used panel to be visible"
                )
                assert analytics_page.user_detail_tools_panel.is_visible(), (
                    "Expected the Tools Used panel to be visible"
                )
                assert analytics_page.user_detail_agents_panel.is_visible(), (
                    "Expected the Agents & Pipelines Used panel to be visible"
                )

            with allure.step(
                "Step 7 — Verify each panel shows a count label and, when N > 0, a list of "
                "items with a name and a call/run count; when N = 0, an empty-state string"
            ):
                panel_locators = (
                    analytics_page.user_detail_models_panel,
                    analytics_page.user_detail_tools_panel,
                    analytics_page.user_detail_agents_panel,
                )
                for expected_title, panel_locator in zip(PANEL_TITLES, panel_locators):
                    lines = analytics_page.get_panel_summary(panel_locator)
                    assert lines, f"Expected {expected_title!r} panel to render non-empty content"
                    assert lines[0] == expected_title, (
                        f"Expected panel title {expected_title!r}, got {lines[0]!r}"
                    )
                    assert len(lines) >= 2, (
                        f"Expected {expected_title!r} panel to show a count label line, got {lines!r}"
                    )
                    count_line = lines[1]
                    if count_line.startswith("0 "):
                        assert len(lines) == 3, (
                            f"Expected a single empty-state line for a zero-count "
                            f"{expected_title!r} panel, got {lines[2:]!r}"
                        )
                    else:
                        assert len(lines) > 2, (
                            f"Expected {expected_title!r} panel with count {count_line!r} to "
                            f"list at least one item"
                        )

            with allure.step(
                "Step 8 — Verify hovering over the Daily Activity chart shows a tooltip "
                "with the date and per-series values for that point in time"
            ):
                # Same gesture as before (a real mouse move to the chart's horizontal
                # centre), now routed through the page object so it SCROLLS the chart
                # into view first. EL-6267 added six KPI cards above this chart
                # (EliteaAI/EliteaUI@f084ea12 + @ce8115c6), pushing its vertical centre
                # below the viewport, so the raw move this block used to do silently
                # stopped landing on the plot and the tooltip never appeared —
                # reproduced on a pristine-HEAD control run, i.e. pre-existing on
                # `automation/base`, not introduced by this branch.
                analytics_page.hover_chart_at_fraction(
                    analytics_page.user_detail_chart_container, CENTRE_HOVER_FRACTION
                )
                expect(analytics_page.user_detail_chart_tooltip).to_be_visible(timeout=HOVER_TOOLTIP_TIMEOUT)
                tooltip_text = analytics_page.user_detail_chart_tooltip.inner_text()
                assert any(
                    series in tooltip_text for series in ("LLM", "Tool", "Chat Msg", "Agent")
                ), f"Expected the hover tooltip to contain at least one series label, got {tooltip_text!r}"
                assert tooltip_text.split("\n")[0], (
                    f"Expected the hover tooltip's first line to be a non-empty date label, "
                    f"got {tooltip_text!r}"
                )

            with allure.step(
                "Step 8b — [ELITEA-2329] Verify the tooltip lists EVERY event-type series, in "
                "declaration order, each carrying the captured response's value for the hovered day"
            ):
                daily_activity = user_detail_response.get("daily_activity") or []
                # Precondition for step 8c, asserted against the captured response so a user with
                # a single active day fails loudly here rather than as a tooltip-never-changes
                # timeout.
                assert len(daily_activity) >= 2, (
                    f"Expected the selected user to have at least 2 daily_activity entries so the "
                    f"case's 'move to a different data point' step has a second point to move to, "
                    f"got {len(daily_activity)}"
                )
                dates_to_points = {entry["date"]: entry for entry in daily_activity}

                series_count = analytics_page.get_chart_area_series_count(
                    analytics_page.user_detail_chart_container
                )
                assert series_count == len(SERIES_NAME_TO_RESPONSE_KEY), (
                    f"Expected the tooltip's series lines to match the "
                    f"{len(SERIES_NAME_TO_RESPONSE_KEY)} rendered area series, but the chart drew "
                    f"{series_count}"
                )

                analytics_page.hover_chart_at_fraction(
                    analytics_page.user_detail_chart_container, FIRST_HOVER_FRACTION
                )
                expect(analytics_page.user_detail_chart_tooltip).to_be_visible(
                    timeout=HOVER_TOOLTIP_TIMEOUT
                )
                first_lines = analytics_page.read_chart_tooltip_lines(
                    analytics_page.user_detail_chart_tooltip
                )
                first_label = _assert_tooltip_matches_a_response_day(first_lines, dates_to_points)
                logger.info("First hover landed on %s: %s", first_label, first_lines[1:])

            with allure.step(
                "Step 8c — [ELITEA-2329] Move to a different data point and verify the tooltip "
                "re-renders against that day"
            ):
                analytics_page.hover_chart_at_fraction(
                    analytics_page.user_detail_chart_container, SECOND_HOVER_FRACTION
                )
                second_lines = analytics_page.wait_for_chart_tooltip_change(
                    analytics_page.user_detail_chart_tooltip, first_lines
                )
                expect(analytics_page.user_detail_chart_tooltip).to_be_visible()
                second_label = _assert_tooltip_matches_a_response_day(second_lines, dates_to_points)
                assert second_label != first_label, (
                    f"Expected the second hover to land on a different day than the first, but "
                    f"both tooltips are labelled {first_label!r}"
                )

            with allure.step(
                "Step 8d — [ELITEA-2329, beyond the case text] Move the cursor off the chart and "
                "verify the tooltip is removed from the DOM"
            ):
                analytics_page.move_mouse_off_chart(analytics_page.user_detail_chart_container)
                # The shared `ChartTooltip` returns null when `!active`, so the node UNMOUNTS
                # rather than merely hiding — count 0, not not_to_be_visible.
                expect(analytics_page.user_detail_chart_tooltip).to_have_count(0)

            with allure.step(
                "Step 9 — Click the back arrow and verify the view returns to the Users-tab "
                "User Activity table, with no new network request"
            ):
                analytics_page.back_to_users_table()
                assert analytics_page.users_table_header.is_visible(), (
                    "Expected the Users-tab table header to be visible again after back navigation"
                )
                assert analytics_page.users_activity_title.is_visible(), (
                    "Expected the 'User Activity' title to be visible again after back navigation"
                )
                assert analytics_page.users_count.is_visible(), (
                    "Expected the users-count subtitle to be visible again after back navigation"
                )

            assert not console_errors, f"Unexpected console errors: {[m.text for m in console_errors]}"
        finally:
            console_errors.stop()


def _assert_tooltip_matches_a_response_day(lines, dates_to_points) -> str:
    """ELITEA-2329 — assert *lines* (a `ChartTooltip` render: label first, then one
    ``"{series}: {value}"`` line per series) describes one of the days in the captured
    user-detail response, and return that day's label.

    Every asserted number comes from the response body the UI itself rendered from —
    the test never authors an expected value. Zero-valued days still render their
    series lines, so the expected list is unconditional.
    """
    assert lines, "Expected the hover tooltip to render at least a label line"
    label = lines[0]
    assert label in dates_to_points, (
        f"Expected the tooltip's label line to be one of the captured response's "
        f"daily_activity dates, got {label!r} (available: {sorted(dates_to_points)!r})"
    )
    point = dates_to_points[label]
    expected_lines = [f"{name}: {fmt_num(point[key])}" for name, key in SERIES_NAME_TO_RESPONSE_KEY]
    assert lines[1:] == expected_lines, (
        f"Expected the tooltip for {label!r} to list exactly {expected_lines!r} (every event-type "
        f"series, in declaration order, with values from the captured response), got {lines[1:]!r}"
    )
    return label
