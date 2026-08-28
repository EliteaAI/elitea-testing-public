"""UI test — Health tab displays Requests vs Errors chart and Health by Event Type table.

Read-only verification against the currently-selected project's own analytics
data (`.agents/testing.md` § Test data strategy). Nothing is created, modified
or deleted.

Test case: ELITEA-2324
AFS: test-specs/settings-analytics/l2_health-tab-chart-and-event-type-table_ELITEA-2324.md

Fidelity (`.agents/testing.md` § Fidelity policy): NO substitution. The Health
tab shares the Overview endpoint, so the live `analytics/prompt_lib/` response
body is captured around the preset click and used as the ORACLE for the event
type rows. The chart's series names are read by really hovering the chart with
`Locator.hover()` — never a synthetic event dispatched by the test.

Case-text drift (see AFS § Metadata, filed elitea-testing-public#1949): the case
lists six fixed event-type rows (api, socketio, llm, tool, agent, rpc). The rows
are DATA-DRIVEN — one per entry of the response's `health` array — so a range
with no agent runs legitimately renders five rows and no `agent` row. This test
asserts the rendered rows equal the response's rows exactly, and that every
rendered event type is a member of the case's known set (so an unexpected or
garbage event type still fails).
"""

import logging

import allure
import pytest
from pages.analytics_page import AnalyticsPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

#: The header cells' DOM TEXT, in rendered order. Title case is what the DOM
#: actually holds — the capitalisation the case text shows is CSS
#: (`styles.tableCell.textTransform`), asserted separately below.
EXPECTED_COLUMN_LABELS = ("Event Type", "Total", "Errors", "Error Rate", "Avg Latency")

#: The computed `text-transform` that renders those DOM labels uppercase.
EXPECTED_COLUMN_TEXT_TRANSFORM = "uppercase"

# The event types the case enumerates and the Guide tab documents — the row set
# is data-driven, but any rendered type outside this set is a failure.
KNOWN_EVENT_TYPES = {"api", "socketio", "llm", "tool", "agent", "rpc"}

EXPECTED_CHART_TITLE = "Requests vs Errors"
EXPECTED_CHART_SUBTITLE = "Total requests trend with error overlay"
EXPECTED_SERIES_NAMES = ("Total Requests", "Errors")
EXPECTED_AREA_SERIES_COUNT = 2


class TestAnalyticsHealthTab:
    """ELITEA-2324 — Health tab: the dual-series "Requests vs Errors" area chart
    and the "Health by Event Type" table (rows + 5-column header)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/analytics/ELITEA-2324_health-tab-displays-requests-vs-errors-chart-and-health-by-e.md",
        "onetest-ai Test Case link",
    )
    def test_health_tab_chart_and_event_type_table(self, page):
        """Health tab renders a two-series area chart whose series are named
        Total Requests and Errors, plus a Health by Event Type table whose rows
        and columns match the live analytics response."""
        analytics_page = AnalyticsPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Step 1 — Navigate to Settings -> Analytics, select 'Last 30d' capturing the "
            "analytics response body as the oracle, then open the Health tab"
        ):
            analytics_page.navigate_capturing_analytics()
            body = analytics_page.select_date_preset_capturing_analytics(
                analytics_page.preset_last_30d
            )
            health = body.get("health", [])
            assert health, (
                "Expected the selected project to have analytics activity in the last 30 "
                "days — with an empty `health` array the whole tab renders "
                "'No health data available.' instead of the chart and table. "
                "AFS § Preconditions."
            )
            assert body.get("daily_activity"), (
                "Expected non-empty `daily_activity` — the Requests vs Errors chart is not "
                "rendered at all otherwise (errorTrend.length > 0 guard). AFS § Preconditions."
            )
            analytics_page.open_health_tab()
            assert analytics_page.is_tab_selected(analytics_page.tab_health), (
                "Expected the 'Health' tab to be aria-selected=true after clicking it"
            )
            expect(analytics_page.loading_indicator).to_have_count(0)

        with allure.step(
            "Step 2 — Verify the dual-series area chart: title, subtitle, exactly two "
            "rendered series, and both series named in the hover tooltip"
        ):
            assert analytics_page.health_chart_title.text_content() == EXPECTED_CHART_TITLE, (
                f"Expected chart title {EXPECTED_CHART_TITLE!r}, got "
                f"{analytics_page.health_chart_title.text_content()!r}"
            )
            assert (
                analytics_page.health_chart_subtitle.text_content() == EXPECTED_CHART_SUBTITLE
            ), (
                f"Expected chart subtitle {EXPECTED_CHART_SUBTITLE!r}, got "
                f"{analytics_page.health_chart_subtitle.text_content()!r}"
            )
            assert analytics_page.health_chart_container.is_visible(), (
                "Expected the Requests vs Errors chart container to be visible"
            )
            series_count = analytics_page.get_health_chart_area_series_count()
            assert series_count == EXPECTED_AREA_SERIES_COUNT, (
                f"Expected exactly {EXPECTED_AREA_SERIES_COUNT} rendered area series "
                f"(Total Requests + Errors), got {series_count}"
            )
            # The chart renders NO legend, so the series names live only in
            # the hover tooltip — hovering is the only honest way to assert
            # the case's "Total Requests and Errors series".
            tooltip_text = analytics_page.hover_health_chart_and_read_tooltip()
            for series_name in EXPECTED_SERIES_NAMES:
                assert series_name in tooltip_text, (
                    f"Expected the chart tooltip to name the {series_name!r} series, got "
                    f"{tooltip_text!r}"
                )

        with allure.step("Step 3 — Verify the Health by Event Type table is shown"):
            assert (
                analytics_page.health_table_title.text_content() == "Health by Event Type"
            ), (
                f"Expected table title 'Health by Event Type', got "
                f"{analytics_page.health_table_title.text_content()!r}"
            )
            assert analytics_page.health_table_header.is_visible(), (
                "Expected the Health by Event Type table header to render"
            )

        with allure.step(
            "Step 4 — Verify the rendered event-type rows are exactly the response's "
            "`health` rows, and every one is a known event type"
        ):
            expected_event_types = [entry["event_type"] for entry in health]
            actual_event_types = analytics_page.get_health_event_types()
            assert actual_event_types == expected_event_types, (
                f"Expected the rendered event types to match the response's health array "
                f"{expected_event_types}, got {actual_event_types}"
            )
            assert actual_event_types, "Expected at least one event-type row to render"
            unknown = set(actual_event_types) - KNOWN_EVENT_TYPES
            assert not unknown, (
                f"Expected every rendered event type to be one of {sorted(KNOWN_EVENT_TYPES)}, "
                f"found {sorted(unknown)}"
            )
            assert analytics_page.health_rows.count() == len(expected_event_types), (
                f"Expected {len(expected_event_types)} rendered rows, got "
                f"{analytics_page.health_rows.count()}"
            )
            logger.info("Health rows rendered: %s", actual_event_types)

        with allure.step(
            "Step 5 — Verify the table columns: Event Type, Total, Errors, Error Rate, "
            "Avg Latency"
        ):
            actual_labels = tuple(analytics_page.get_health_table_column_labels())
            assert actual_labels == EXPECTED_COLUMN_LABELS, (
                f"Expected the header cells' DOM text to be {EXPECTED_COLUMN_LABELS}, "
                f"got {actual_labels}"
            )
            transforms = analytics_page.get_health_table_column_text_transforms()
            assert transforms == [EXPECTED_COLUMN_TEXT_TRANSFORM] * len(EXPECTED_COLUMN_LABELS), (
                f"Expected every column header to render uppercase via "
                f"`text-transform: {EXPECTED_COLUMN_TEXT_TRANSFORM}` (this is why the case "
                f"writes the columns capitalised while the DOM text is title case), got "
                f"{transforms}"
            )

        with allure.step("Step 6 — Verify no console errors were logged throughout"):
            assert not console_errors, (
                f"Unexpected console errors: {console_errors}"
            )
