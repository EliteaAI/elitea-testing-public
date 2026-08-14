"""UI test — Agents & Pipelines tab loads Most Active chart, Chat Messages
chart, and Activity table.

Read-only verification against the currently-selected project's own
analytics data (`.agents/testing.md` § Test data strategy — prefer
read-only assertions on existing data when the observable doesn't require
fresh state). This case never creates, modifies, or deletes anything — it
only checks the Agents & Pipelines-tab panel's structure (charts, header,
search input, table columns, row-click navigation) against whatever
agent/pipeline usage the selected project already has analytics rows for,
plus one project switch to exercise the personal-vs-non-personal column-set
branch (`isPersonalProject`).

Test case: ELITEA-2320
AFS: test-specs/settings-analytics/l2_agents-pipelines-tab-charts-and-activity-table_ELITEA-2320.md

Case-text drift (see AFS § Known Defects, filed elitea-testing-public#1195,
same stale-case-text family as #1185/#1188/#1191/#1192): the case calls the
tab "Agents" (live: "Agents & Pipelines"), the bar chart "Most Active
Agents" with subtitle "Top N by events" (live: "Most Active Agents &
Pipelines" / "Top N by runs"), the table "Agent Activity" with example
subtitle "2 agents" (live: "Agent & Pipeline Activity" / "{N} agents &
pipelines"), and lists 5 columns AGENT/EVENTS/USERS/AVG LATENCY/ERRORS
(live: 8 columns for a personal project — no "Events" column exists, the
equivalent is "Runs" — or 9 for a non-personal project, which conditionally
adds "Users" right after "Runs"). The search placeholder is "Search by
agent name" in the case vs live "Search by agent or pipeline name". This
test asserts the live contract throughout.

Errors-column positive branch (AFS § Blocked Steps): all agent/pipeline
rows in the "Private" fixture project have `errors: 0` at analysis/
implementation time (unlike the Users tab's rows in the same project,
which DO have `errors > 0` rows) — only the negative (default-color)
branch is live-exercisable here; the positive/red branch is source-
confirmed only (`AnalyticsAgents.jsx:317`, identical rule shape to the
Users tab's).
"""

import logging
import re

import allure
import pytest
from config import settings
from pages.analytics_page import AnalyticsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

# The header cells' JSX text is title-case, but `tableCell`'s sx applies
# `text-transform: uppercase` (same shared style-object pattern as the Users
# tab) — confirmed live 2026-08-05 via getComputedStyle-backed DOM read, so
# the expected tuples match what actually renders, not the JSX source string.
EXPECTED_COLUMN_LABELS_PERSONAL = (
    "AGENT / PIPELINE",
    "RUNS",
    "COST",
    "TOTAL TOKENS",
    "INPUT TOKENS",
    "OUTPUT TOKENS",
    "AVG LATENCY",
    "ERRORS",
)
EXPECTED_COLUMN_LABELS_NON_PERSONAL = (
    "AGENT / PIPELINE",
    "RUNS",
    "USERS",
    "COST",
    "TOTAL TOKENS",
    "INPUT TOKENS",
    "OUTPUT TOKENS",
    "AVG LATENCY",
    "ERRORS",
)

CHART_SUBTITLE_PATTERN = re.compile(r"^Top (\d+) by runs$")
COUNT_PATTERN = re.compile(r"^(\d+) agents & pipelines$")
PAGE_RANGE_PATTERN = re.compile(r"^(\d+)–\d+ of (\d+)$")

# Errors-cell text colors (rgb), confirmed live via getComputedStyle against
# the currently-active theme (same values as the Users tab's Errors column —
# both consume `palette.status.rejected` / the default text color).
ERRORS_DEFAULT_COLOR = "rgb(255, 255, 255)"  # errors === 0
ERRORS_REJECTED_COLOR = "rgb(215, 22, 22)"  # errors > 0 (palette.status.rejected)

# "UI Testing" — the non-personal project fixture used to exercise the
# 9-column (Users-inserted) header shape (AFS § Automation Hints).
NON_PERSONAL_PROJECT_ID = settings.users_team_project_id


class TestAnalyticsAgentsPipelinesTab:
    """ELITEA-2320 — Agents & Pipelines tab: Most Active bar chart, Chat
    Messages area chart, Agent & Pipeline Activity table (header/count,
    search input, column-set branch, pagination, Errors color), and
    row-click navigation to the agent/pipeline detail sub-view."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-analytics/ELITEA-2320_agents-tab-displays-chat-messages-chart-most-active-agents-bar-chart"
        "-and-agent-activity-table.md",
        "onetest-ai Test Case link",
    )
    def test_agents_pipelines_tab_charts_and_activity_table(self, page):
        """Agents & Pipelines tab renders its bar chart, area chart, and
        Activity table (header + rows + pagination + row-click navigation)
        against the "Private" fixture project, plus the 9-column
        non-personal-project header branch via a project switch."""
        analytics_page = AnalyticsPage(page)
        console_errors = analytics_page.capture_console_errors()
        personal_project_id = str(settings.elitea_project_id)

        try:
            with allure.step("Step 1 — Navigate to Settings -> Analytics, click the Agents & Pipelines tab"):
                analytics_page.navigate()
                analytics_page.open_agents_pipelines_tab()
                assert analytics_page.is_tab_selected(analytics_page.tab_agents_pipelines), (
                    "Expected the 'Agents & Pipelines' tab to be aria-selected=true after clicking it"
                )
                assert analytics_page.agents_table_header.is_visible(), (
                    "Expected the Agents-tab table header to render without error"
                )

            with allure.step(
                'Step 2 — Verify the "Most Active Agents & Pipelines" bar chart is shown with '
                'subtitle "Top {N} by runs" and N matching the visible row total'
            ):
                assert analytics_page.agents_chart_title.text_content() == "Most Active Agents & Pipelines", (
                    f"Expected bar-chart title 'Most Active Agents & Pipelines', got "
                    f"{analytics_page.agents_chart_title.text_content()!r}"
                )
                subtitle_text = analytics_page.agents_chart_subtitle.text_content()
                match = CHART_SUBTITLE_PATTERN.match(subtitle_text or "")
                assert match, f"Expected bar-chart subtitle matching 'Top {{N}} by runs', got {subtitle_text!r}"
                row_count = analytics_page.get_agents_row_count()
                assert int(match.group(1)) == row_count, (
                    f"Expected bar-chart subtitle count {match.group(1)!r} to match the actual "
                    f"rendered row total {row_count}"
                )
                assert analytics_page.agents_chart_container.is_visible(), (
                    "Expected the bar-chart container to be visible"
                )

            with allure.step(
                'Step 3 — Verify the "Chat Messages" area chart is shown with subtitle '
                '"User messages per day"'
            ):
                assert analytics_page.agents_chat_chart_title.text_content() == "Chat Messages", (
                    f"Expected chat-chart title 'Chat Messages', got "
                    f"{analytics_page.agents_chat_chart_title.text_content()!r}"
                )
                assert analytics_page.agents_chat_chart_subtitle.text_content() == "User messages per day", (
                    f"Expected chat-chart subtitle 'User messages per day', got "
                    f"{analytics_page.agents_chat_chart_subtitle.text_content()!r}"
                )
                assert analytics_page.agents_chat_chart_container.is_visible(), (
                    "Expected the Chat Messages chart container to be visible"
                )

            with allure.step(
                'Step 4 — Verify the "Agent & Pipeline Activity" table header shows "{N} agents & '
                'pipelines" matching the pagination total, and pagination controls (rows-per-page '
                "20, range label, prev disabled / next enabled for a > 1 page total)"
            ):
                assert analytics_page.agents_activity_title.text_content() == "Agent & Pipeline Activity", (
                    f"Expected table title 'Agent & Pipeline Activity', got "
                    f"{analytics_page.agents_activity_title.text_content()!r}"
                )
                count_text = analytics_page.agents_count.text_content()
                count_match = COUNT_PATTERN.match(count_text or "")
                assert count_match, f"Expected count text matching '{{N}} agents & pipelines', got {count_text!r}"

                assert analytics_page.agents_pagination_rows_select.text_content() == "20", (
                    f"Expected default rows-per-page value '20', got "
                    f"{analytics_page.agents_pagination_rows_select.text_content()!r}"
                )
                range_text = analytics_page.agents_pagination_range.text_content()
                range_match = PAGE_RANGE_PATTERN.match(range_text or "")
                assert range_match, (
                    f"Expected page-range label matching '{{from}}–{{to}} of {{count}}', got {range_text!r}"
                )
                assert int(range_match.group(2)) == int(count_match.group(1)), (
                    f"Expected the pagination range's total {range_match.group(2)!r} to match the "
                    f"count subtitle's total {count_match.group(1)!r}"
                )
                assert analytics_page.agents_pagination_prev.is_disabled(), (
                    "Expected the previous-page button to be disabled on the first page"
                )
                # The "Private" fixture has more agents/pipelines than one page (rowsPerPage=20),
                # so — unlike the Users tab's single-page fixture — next must be enabled here.
                assert not analytics_page.agents_pagination_next.is_disabled(), (
                    "Expected the next-page button to be enabled (total exceeds one page)"
                )

            with allure.step(
                'Step 7 — Verify a "Search by agent or pipeline name" input is present, positioned '
                "top-right of the Agent & Pipeline Activity card"
            ):
                # Asserted here (ahead of the case's own step 6/row-click) — still on the
                # personal "Private" project's list view, before step 5's project switching or
                # step 6's row click leave it (row click swaps the table for the detail sub-view,
                # out of this case's scope per AFS § Coverage Map row 6).
                assert analytics_page.agents_search_input.is_visible(), (
                    "Expected the 'Search by agent or pipeline name' input to be visible"
                )
                assert (
                    analytics_page.agents_search_input.get_attribute("placeholder")
                    == "Search by agent or pipeline name"
                ), "Expected placeholder text 'Search by agent or pipeline name'"
                title_box = analytics_page.agents_activity_title.bounding_box()
                search_box = analytics_page.agents_search_input.bounding_box()
                assert title_box and search_box, "Expected both title and search input to have a layout box"
                assert search_box["x"] > title_box["x"] + title_box["width"], (
                    f"Expected the search input to sit to the right of the title "
                    f"(title x={title_box['x']}, w={title_box['width']}; search x={search_box['x']})"
                )

            with allure.step(
                "Step 5 — Verify the table header column SET/order: 8 columns for the current "
                "personal project ('Private'), 9 (Users inserted after Runs) after switching to "
                "a non-personal project ('UI Testing')"
            ):
                personal_labels = analytics_page.get_agents_table_column_labels()
                assert tuple(personal_labels) == EXPECTED_COLUMN_LABELS_PERSONAL, (
                    f"Expected personal-project column labels {EXPECTED_COLUMN_LABELS_PERSONAL}, "
                    f"got {tuple(personal_labels)}"
                )

                analytics_page.switch_project(NON_PERSONAL_PROJECT_ID)
                non_personal_labels = analytics_page.get_agents_table_column_labels()
                assert tuple(non_personal_labels) == EXPECTED_COLUMN_LABELS_NON_PERSONAL, (
                    f"Expected non-personal-project column labels "
                    f"{EXPECTED_COLUMN_LABELS_NON_PERSONAL}, got {tuple(non_personal_labels)}"
                )

                analytics_page.switch_project(personal_project_id)
                assert analytics_page.agents_table_header.is_visible(), (
                    "Expected the table header to still render after switching back to the "
                    "personal project"
                )

            with allure.step(
                "Step 5b — Verify the Errors column's negative branch: errors === 0 renders in "
                "the table's default text color (positive branch not live-exercisable, see AFS "
                "§ Blocked Steps)"
            ):
                row_count = analytics_page.get_agents_row_count()
                assert row_count > 0, (
                    "Expected at least one agent/pipeline row to exercise the Errors-color "
                    "assertion against (AFS precondition: project has usage-analytics data)"
                )
                zero_error_rows_checked = 0
                positive_error_rows_checked = 0
                for i in range(row_count):
                    errors_value = analytics_page.get_agent_row_errors_value(i)
                    cell = analytics_page.agents_row_errors.nth(i)
                    if errors_value == 0:
                        expect(cell).to_have_css("color", ERRORS_DEFAULT_COLOR)
                        zero_error_rows_checked += 1
                    else:
                        expect(cell).to_have_css("color", ERRORS_REJECTED_COLOR)
                        positive_error_rows_checked += 1
                assert zero_error_rows_checked > 0, (
                    "Expected at least one errors===0 row to assert the default-color branch against"
                )
                logger.info(
                    "Errors-color check: %d default-color row(s), %d rejected-color row(s)",
                    zero_error_rows_checked,
                    positive_error_rows_checked,
                )

            with allure.step(
                "Step 6 — Verify a table row is clickable: clicking navigates (same-page state "
                "swap, no URL change) to the agent/pipeline detail sub-view; the "
                "analytics_agent_detail query fires once and resolves 200"
            ):
                pre_click_url = page.url
                response = analytics_page.open_agent_detail_by_row(0)
                assert response.status == 200, (
                    f"Expected the analytics_agent_detail query to resolve 200, got {response.status}"
                )
                assert page.url == pre_click_url, (
                    "Expected no URL change on row click (same-page state swap), but the URL changed "
                    f"from {pre_click_url!r} to {page.url!r}"
                )
                expect(analytics_page.agents_table_header).to_have_count(0)

            assert not console_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}"
            )
        finally:
            console_errors.stop()
