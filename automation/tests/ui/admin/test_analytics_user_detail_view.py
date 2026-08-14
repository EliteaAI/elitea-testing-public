"""UI test — Clicking a user row in Users tab opens the user detail view.

Read-only verification against the currently-selected project's own analytics
data (`.agents/testing.md` § Test data strategy — prefer read-only assertions
on existing data when the observable doesn't require fresh state). This case
never creates, modifies, or deletes anything.

Test case: ELITEA-2313
AFS: test-specs/settings-analytics/l2_users-tab-row-click-opens-detail-view_ELITEA-2313.md

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

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

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
    "TOTAL COST",
)

# Same resolved theme colors as ELITEA-2312's Users-table Errors column
# (confirmed live via getComputedStyle — do not assume cross-surface reuse
# without re-checking; re-verified live for this view during implementation).
KPI_VALUE_DEFAULT_COLOR = "rgb(255, 255, 255)"
KPI_VALUE_ERRORS_COLOR = "rgb(215, 22, 22)"

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

                analytics_page.open_user_detail_by_row(target_index)

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
                "Step 3 — Verify exactly ten KPI cards are shown, in order: Active Days, "
                "LLM Calls, Tool Calls, Agent & Pipeline Runs, Chat Msg, Errors, Total "
                "Tokens, Input Tokens, Output Tokens, Total Cost"
            ):
                assert analytics_page.user_detail_kpi_cards.count() == 10, (
                    f"Expected exactly 10 KPI cards, got "
                    f"{analytics_page.user_detail_kpi_cards.count()}"
                )
                actual_labels = analytics_page.get_user_detail_kpi_labels_in_order()
                assert tuple(actual_labels) == EXPECTED_KPI_LABELS_IN_ORDER, (
                    f"Expected KPI labels {EXPECTED_KPI_LABELS_IN_ORDER}, got {tuple(actual_labels)}"
                )

            with allure.step(
                "Step 4 — Verify the Errors KPI card's value renders in the red/rejected "
                "color (errors > 0), and the other nine cards render in the default text color"
            ):
                errors_index = EXPECTED_KPI_LABELS_IN_ORDER.index("ERRORS")
                expect(analytics_page.user_detail_kpi_values.nth(errors_index)).to_have_css(
                    "color", KPI_VALUE_ERRORS_COLOR
                )
                for i in range(10):
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
                chart_box = analytics_page.user_detail_chart_container.bounding_box()
                assert chart_box, "Expected the chart container to have a layout box to hover into"
                page.mouse.move(
                    chart_box["x"] + chart_box["width"] / 2,
                    chart_box["y"] + chart_box["height"] / 2,
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
