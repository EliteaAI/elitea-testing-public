"""UI test — Tools tab displays Most Popular Tools bar chart and Tool Details table.

Read-only verification against the currently-selected project's own analytics
data (`.agents/testing.md` § Test data strategy). Nothing is created, modified
or deleted.

Test case: ELITEA-2322
AFS: test-specs/settings-analytics/l2_tools-tab-chart-and-details-table_ELITEA-2322.md

Fidelity (`.agents/testing.md` § Fidelity policy): NO substitution. The Tools
tab's own live `analytics_tools/prompt_lib/` response body is captured
(`expect_response`) and used as the ORACLE for the chart's series, the tool
count and every row's errors value — the product produces every number, the
test only checks the UI carried it through faithfully.

Case-text drift, bar colours (case step 3, filed elitea-testing-public#1952):
"each bar has a distinct color" holds only while the tool count is within the
10-entry `CHART_COLORS` palette — the fill is `CHART_COLORS[i % 10]`, so bar 11
legitimately repeats bar 1. The fixture project has 34 tools (20 plotted), so
this test asserts the live contract: distinct within the first 10, then the
palette cycling exactly.

Errors-colour rule (case step 6): asserted as a TWO-DIRECTIONAL invariant — the
cell is red iff its value is > 0 — rather than a one-way "is red", because the
fixture project has no `errors > 0` tool row (AFS § Blocked Steps). The
invariant is satisfiable today (proving the negative branch against real data)
and automatically covers the positive branch the day such data exists. A row is
never fabricated to exercise it (that would be a terminal substitution).

Case-text drift note: the case writes the column labels upper-cased. The JSX
text is title-case and the uppercase look comes from `tableCell`'s
`text-transform: uppercase`; Playwright's `inner_text()` returns the
CSS-rendered text, so the uppercase tuple below IS the assertion of the case's
visual contract (same shape as the merged Users/Agents tab specs).
"""

import logging
import re

import allure
import pytest
from pages.analytics_page import AnalyticsPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

EXPECTED_COLUMN_LABELS = ("TOOL", "CALLS", "USERS", "AVG LATENCY", "ERRORS")

CHART_SUBTITLE_PATTERN = re.compile(r"^Top (\d+) by usage$")
# Not pluralised by the product (a single tool reads "1 tools") — known defect
# elitea-testing-public#1951; the pattern deliberately encodes the live format.
TOOL_COUNT_PATTERN = re.compile(r"^(\d+) tools$")
PAGE_RANGE_PATTERN = re.compile(r"^\d+–\d+ of (\d+)$")

# The chart series is `rows.slice(0, 20)` (AnalyticsTools.jsx).
CHART_MAX_BARS = 20
# `AnalyticsCommonConstants.CHART_COLORS` has 10 entries and the bar fill is
# `CHART_COLORS[i % length]`, so colours are distinct only while N <= 10 and
# repeat by design beyond that. The case's "each bar has a distinct color" is
# stale for a project with more than 10 tools — filed as case-text drift
# elitea-testing-public#1952; this test asserts the live contract instead
# (`.agents/testing.md` reverse-masking guard).
CHART_PALETTE_SIZE = 10
DEFAULT_ROWS_PER_PAGE = 20
EXPECTED_ROWS_PER_PAGE_OPTIONS = ["10", "20", "50"]

# Errors-cell text colours (rgb), the same theme values the merged Users- and
# Agents-tab specs confirmed live via getComputedStyle.
ERRORS_DEFAULT_COLOR = "rgb(255, 255, 255)"  # errors === 0
ERRORS_REJECTED_COLOR = "rgb(215, 22, 22)"  # errors > 0 (palette.status.rejected)


class TestAnalyticsToolsTab:
    """ELITEA-2322 — Tools tab: "Most Popular Tools" bar chart (subtitle, X-axis
    labels, distinct bar colours) and "Tool Details" table (count, search input,
    5-column header, Errors colour invariant, pagination)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/analytics/ELITEA-2322_tools-tab-displays-most-popular-tools-bar-chart-and-tool-det.md",
        "onetest-ai Test Case link",
    )
    def test_tools_tab_chart_and_details_table(self, page):
        """Tools tab renders the Most Popular Tools bar chart and the Tool
        Details table, both matching the live analytics_tools response."""
        analytics_page = AnalyticsPage(page)
        console_errors = collect_console_errors(page)

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Analytics, select 'Last 30d', open the Tools "
                "tab, capturing its response body as the oracle"
            ):
                analytics_page.navigate_capturing_analytics()
                analytics_page.select_date_preset_capturing_analytics(analytics_page.preset_last_30d)
                body = analytics_page.open_tools_tab()
                assert analytics_page.is_tab_selected(analytics_page.tab_tools), (
                    "Expected the 'Tools' tab to be aria-selected=true after clicking it"
                )
                expect(analytics_page.tools_loading_indicator).to_have_count(0)
                rows = body.get("rows", [])
                total = body.get("total", 0)
                assert rows, (
                    "Expected the selected project to have at least one tool call in the last 30 "
                    "days — the Most Popular Tools chart is not rendered at all otherwise "
                    "(toolChartData.length > 0 guard). AFS § Preconditions."
                )

            with allure.step(
                'Step 2 — Verify the "Most Popular Tools" bar chart: title, "Top N by usage" '
                "subtitle matching the response, and the tool names on the X axis"
            ):
                assert analytics_page.tools_chart_title.text_content() == "Most Popular Tools", (
                    f"Expected bar-chart title 'Most Popular Tools', got "
                    f"{analytics_page.tools_chart_title.text_content()!r}"
                )
                subtitle_text = analytics_page.tools_chart_subtitle.text_content()
                match = CHART_SUBTITLE_PATTERN.match(subtitle_text or "")
                assert match, f"Expected chart subtitle matching 'Top {{N}} by usage', got {subtitle_text!r}"
                expected_series_length = min(len(rows), CHART_MAX_BARS)
                assert int(match.group(1)) == expected_series_length, (
                    f"Expected the chart subtitle to report {expected_series_length} series "
                    f"(min(len(rows)={len(rows)}, {CHART_MAX_BARS})), got {match.group(1)!r}"
                )
                assert analytics_page.tools_chart_container.is_visible(), (
                    "Expected the bar-chart container to be visible"
                )
                expected_tool_names = [row["tool_name"] for row in rows[:expected_series_length]]
                actual_tick_labels = analytics_page.get_tools_chart_x_axis_labels()
                assert actual_tick_labels == expected_tool_names, (
                    f"Expected the X-axis tick labels to be the response's tool names "
                    f"{expected_tool_names}, got {actual_tick_labels}"
                )

            with allure.step(
                "Step 3 — Verify the bars are distinctly coloured from the chart palette "
                "(distinct within the first 10; the 10-colour palette cycles beyond that)"
            ):
                bar_fills = analytics_page.get_tools_chart_bar_fills()
                assert len(bar_fills) == expected_series_length, (
                    f"Expected {expected_series_length} rendered bars, got {len(bar_fills)}"
                )
                palette = bar_fills[:CHART_PALETTE_SIZE]
                assert len(set(palette)) == len(palette), (
                    f"Expected the first {len(palette)} bars to each have a distinct colour, "
                    f"got {palette}"
                )
                assert all(
                    fill == palette[i % CHART_PALETTE_SIZE] for i, fill in enumerate(bar_fills)
                ), (
                    f"Expected every bar's fill to be CHART_COLORS[i % {CHART_PALETTE_SIZE}], "
                    f"got {bar_fills}"
                )

            with allure.step(
                'Step 4 — Verify the "Tool Details" header block: title, "{N} tools" count '
                'matching the response total, and the "Search by tool name" input'
            ):
                assert analytics_page.tools_details_title.text_content() == "Tool Details", (
                    f"Expected table title 'Tool Details', got "
                    f"{analytics_page.tools_details_title.text_content()!r}"
                )
                count_text = analytics_page.tools_count.text_content()
                count_match = TOOL_COUNT_PATTERN.match(count_text or "")
                assert count_match, f"Expected count text matching '{{N}} tools', got {count_text!r}"
                assert int(count_match.group(1)) == total, (
                    f"Expected the count label to report the response total {total}, got "
                    f"{count_match.group(1)!r}"
                )
                assert analytics_page.tools_search_input.is_visible(), (
                    "Expected the 'Search by tool name' input to be visible"
                )
                assert (
                    analytics_page.tools_search_input.get_attribute("placeholder")
                    == "Search by tool name"
                ), "Expected placeholder text 'Search by tool name'"

            with allure.step(
                "Step 5 — Verify the table header row: TOOL, CALLS, USERS, AVG LATENCY, ERRORS"
            ):
                actual_labels = tuple(analytics_page.get_tools_table_column_labels())
                assert actual_labels == EXPECTED_COLUMN_LABELS, (
                    f"Expected column labels {EXPECTED_COLUMN_LABELS}, got {actual_labels}"
                )

            with allure.step(
                "Step 6 — Verify the Errors column's colour is red IFF the value is > 0, with "
                "every rendered value cross-checked against the response row"
            ):
                row_count = analytics_page.get_tools_row_count()
                assert row_count > 0, "Expected at least one rendered tool row"
                zero_error_rows = 0
                positive_error_rows = 0
                for i in range(row_count):
                    rendered_name = analytics_page.get_tool_row_name(i)
                    assert rendered_name == rows[i]["tool_name"], (
                        f"Expected row {i} to render the response's tool name "
                        f"{rows[i]['tool_name']!r}, got {rendered_name!r}"
                    )
                    errors_value = analytics_page.get_tool_row_errors_value(i)
                    assert errors_value == rows[i]["errors"], (
                        f"Expected row {i}'s Errors cell to render the response's value "
                        f"{rows[i]['errors']!r}, got {errors_value!r}"
                    )
                    cell = analytics_page.tools_row_errors.nth(i)
                    if errors_value == 0:
                        expect(cell).to_have_css("color", ERRORS_DEFAULT_COLOR)
                        zero_error_rows += 1
                    else:
                        expect(cell).to_have_css("color", ERRORS_REJECTED_COLOR)
                        positive_error_rows += 1
                logger.info(
                    "Errors-colour invariant: %d default-colour row(s), %d red row(s)",
                    zero_error_rows,
                    positive_error_rows,
                )

            with allure.step(
                "Step 7 — Verify pagination: rows-per-page selector (default 20, options "
                "10/20/50) and a page-range label whose total matches the response"
            ):
                assert (
                    analytics_page.tools_pagination_rows_select.text_content()
                    == str(DEFAULT_ROWS_PER_PAGE)
                ), (
                    f"Expected default rows-per-page value {DEFAULT_ROWS_PER_PAGE!r}, got "
                    f"{analytics_page.tools_pagination_rows_select.text_content()!r}"
                )
                assert (
                    analytics_page.open_tools_rows_per_page_options()
                    == EXPECTED_ROWS_PER_PAGE_OPTIONS
                ), (
                    f"Expected rows-per-page options {EXPECTED_ROWS_PER_PAGE_OPTIONS}, got "
                    f"{analytics_page.open_tools_rows_per_page_options()}"
                )
                range_text = analytics_page.tools_pagination_range.text_content()
                range_match = PAGE_RANGE_PATTERN.match(range_text or "")
                assert range_match, (
                    f"Expected page-range label matching '{{from}}–{{to}} of {{count}}', got "
                    f"{range_text!r}"
                )
                assert int(range_match.group(1)) == total, (
                    f"Expected the page-range total to match the response total {total}, got "
                    f"{range_match.group(1)!r}"
                )
                assert row_count == min(total, DEFAULT_ROWS_PER_PAGE), (
                    f"Expected {min(total, DEFAULT_ROWS_PER_PAGE)} rendered rows on the first "
                    f"page (total {total}, rows per page {DEFAULT_ROWS_PER_PAGE}), got {row_count}"
                )

            with allure.step("Step 8 — Verify no console errors were logged throughout"):
                assert not console_errors, (
                    f"Unexpected console errors: {console_errors}"
                )
        finally:
            analytics_page.clear_tools_search()
