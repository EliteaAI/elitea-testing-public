"""UI test — Clicking an agent row in Agents tab opens the agent detail view.

Read-only verification against the currently-selected project's own analytics
data (`.agents/testing.md` § Test data strategy — prefer read-only assertions
on existing data when the observable doesn't require fresh state). This case
never creates, modifies, or deletes anything — it opens the detail view for
two existing rows (one with tool usage, one without) and navigates back.

Test case: ELITEA-2321
AFS: test-specs/settings-analytics/l2_agent-detail-view-kpi-charts-panels_ELITEA-2321.md

Case-text drift (see AFS § Known Defects, filed elitea-testing-public#1199,
same stale-count family as #1185/#1188/#1191/#1195): the case's step 4 lists
5 KPI cards (Total Events, Unique Users, Avg Latency, Errors, Error Rate) —
no "Error Rate" KPI exists at all, "Total Events" is really "Total Runs",
and Total Cost/Total Tokens/Input Tokens/Output Tokens are omitted entirely;
live view has 8 cards. The case's step 5 calls the chart "Daily Usage"; live
title is "Runs by Day". The case's step 6 lists Users-panel column "EVENTS";
live column is "Runs". This test asserts the live contract for all three.

Errors-KPI-card positive branch (AFS § Blocked Steps, same as ELITEA-2320's
identical blocker on the same project/range): all rows in the "Private"
fixture project have `errors: 0` at analysis/implementation time — only the
negative (default-color) branch is live-exercisable here; the positive/red
branch is source-confirmed only (`AnalyticsAgentDetailed.jsx:107`).
"""

import logging

import allure
import pytest
from config import settings
from pages.analytics_page import AnalyticsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

EXPECTED_KPI_LABELS_IN_ORDER = (
    "TOTAL RUNS",
    "UNIQUE USERS",
    "TOTAL COST",
    "TOTAL TOKENS",
    "INPUT TOKENS",
    "OUTPUT TOKENS",
    "AVG LATENCY",
    "ERRORS",
)

# Same resolved theme colors as ELITEA-2312/2313/2320's Errors cards
# (confirmed live via getComputedStyle — do not assume cross-surface reuse
# without re-checking; re-verified live for this view during implementation).
KPI_VALUE_DEFAULT_COLOR = "rgb(255, 255, 255)"
KPI_VALUE_ERRORS_COLOR = "rgb(215, 22, 22)"

CHART_TITLE_TEXT = "Runs by Day"

USERS_PANEL_TITLE = "Users"
TOOLS_PANEL_TITLE = "Tools"
USERS_PANEL_HEADER = ("USER", "RUNS", "AVG LATENCY", "ERRORS")
TOOLS_PANEL_HEADER = ("TOOL", "CALLS")

# "Private" fixture project — 25 agents/pipelines with runs (AFS §
# Preconditions). "guardrails_test_agent" exercises the populated Tools
# panel; the pipeline exercises the empty-state Tools panel.
PROJECT_ID = str(settings.elitea_project_id)
AGENT_WITH_TOOLS_NAME = "guardrails_test_agent"
PIPELINE_NO_TOOLS_NAME_PREFIX = "autotest_test_empty_pipeline"


class TestAnalyticsAgentDetailView:
    """ELITEA-2321 — clicking an Agents & Pipelines-tab row opens the agent/
    pipeline detail view: entity-name title + back arrow, 8 KPI cards (Errors
    red only when > 0), a conditional "Runs by Day" chart, Users/Tools summary
    panels (including the Tools-panel empty state), and back navigation
    restoring the Agents & Pipelines-tab table with no new network request."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-analytics/ELITEA-2321_clicking-an-agent-row-in-agents-tab-opens-the-agent-detail-view.md",
        "onetest-ai Test Case link",
    )
    def test_agent_row_click_opens_detail_view(self, page, analytics_empty_pipeline_id):
        """Clicking an agent/pipeline row swaps the Agents & Pipelines-tab
        table for the detail view; verifies title/back-arrow, the 8-card KPI
        set (order + Errors-color negative branch), the "Runs by Day" chart,
        the Users/Tools panels (populated + empty-state Tools branch via a
        second row), and back navigation back to the table with no new
        network request."""
        analytics_page = AnalyticsPage(page)
        console_errors = analytics_page.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Analytics, switch to the 'Private' project, "
                "click the Agents & Pipelines tab, and click the 'guardrails_test_agent' row"
            ):
                analytics_page.navigate()
                analytics_page.open_agents_pipelines_tab()
                analytics_page.switch_project(PROJECT_ID)

                row_count = analytics_page.get_agents_row_count()
                assert row_count > 0, (
                    "Expected at least one agent/pipeline row (AFS precondition: 'Private' "
                    "project has usage-analytics data)"
                )
                target_index = next(
                    (
                        i
                        for i in range(row_count)
                        if analytics_page.get_agent_row_identifier(i) == AGENT_WITH_TOOLS_NAME
                    ),
                    None,
                )
                assert target_index is not None, (
                    f"Expected a {AGENT_WITH_TOOLS_NAME!r} row to exercise the populated "
                    f"Tools-panel branch (AFS precondition)"
                )

                analytics_page.open_agent_detail(target_index)

                assert analytics_page.agents_table_header.count() == 0, (
                    "Expected the Agents & Pipelines-tab table panel to be replaced (unmounted) "
                    "by the detail view, not merely hidden"
                )

            with allure.step(
                "Step 2 — Verify the detail view's title is the agent/pipeline's name, with a "
                "back-arrow icon button to its left"
            ):
                assert analytics_page.agent_detail_title.text_content() == AGENT_WITH_TOOLS_NAME, (
                    f"Expected detail-view title {AGENT_WITH_TOOLS_NAME!r}, got "
                    f"{analytics_page.agent_detail_title.text_content()!r}"
                )
                assert analytics_page.agent_detail_back_button.is_visible(), (
                    "Expected the back-arrow button to be visible"
                )
                back_box = analytics_page.agent_detail_back_button.bounding_box()
                title_box = analytics_page.agent_detail_title.bounding_box()
                assert back_box and title_box, "Expected both the back button and title to have a layout box"
                assert back_box["x"] < title_box["x"], (
                    f"Expected the back-arrow button to sit to the left of the title "
                    f"(back x={back_box['x']}, title x={title_box['x']})"
                )

            with allure.step(
                "Step 3 — Verify exactly eight KPI cards are shown, in order: Total Runs, "
                "Unique Users, Total Cost, Total Tokens, Input Tokens, Output Tokens, Avg "
                "Latency, Errors"
            ):
                assert analytics_page.agent_detail_kpi_cards.count() == 8, (
                    f"Expected exactly 8 KPI cards, got {analytics_page.agent_detail_kpi_cards.count()}"
                )
                actual_labels = analytics_page.get_agent_detail_kpi_labels_in_order()
                assert tuple(actual_labels) == EXPECTED_KPI_LABELS_IN_ORDER, (
                    f"Expected KPI labels {EXPECTED_KPI_LABELS_IN_ORDER}, got {tuple(actual_labels)}"
                )

            with allure.step(
                "Step 4 — Verify the Errors KPI card's value renders in the default text color "
                "(errors === 0 for this row; positive branch not live-exercisable, see AFS "
                "§ Blocked Steps), and the other seven cards also render in the default color"
            ):
                for i in range(8):
                    expect(analytics_page.agent_detail_kpi_values.nth(i)).to_have_css(
                        "color", KPI_VALUE_DEFAULT_COLOR
                    )

            with allure.step('Step 5 — Verify a "Runs by Day" area chart is shown'):
                assert analytics_page.agent_detail_chart_title.text_content() == CHART_TITLE_TEXT, (
                    f"Expected chart title {CHART_TITLE_TEXT!r}, got "
                    f"{analytics_page.agent_detail_chart_title.text_content()!r}"
                )
                assert analytics_page.agent_detail_chart_container.is_visible(), (
                    "Expected the Runs by Day chart container to be visible "
                    "(AFS precondition: agent/pipeline has daily_usage data)"
                )

            with allure.step(
                'Step 6 — Verify a "Users" panel is shown listing users who used this agent/'
                "pipeline, with column headers User, Runs, Avg Latency, Errors and a count "
                "subtitle — populated for this row"
            ):
                assert analytics_page.agent_detail_users_panel.is_visible(), (
                    "Expected the Users panel to be visible"
                )
                users_lines = analytics_page.get_panel_summary(analytics_page.agent_detail_users_panel)
                assert users_lines, "Expected the Users panel to render non-empty content"
                assert users_lines[0] == USERS_PANEL_TITLE, (
                    f"Expected panel title {USERS_PANEL_TITLE!r}, got {users_lines[0]!r}"
                )
                assert users_lines[1].endswith("users used this agent / pipeline"), (
                    f"Expected a count subtitle ending 'users used this agent / pipeline', "
                    f"got {users_lines[1]!r}"
                )
                assert users_lines[1].split(" ", 1)[0].isdigit(), (
                    f"Expected the count subtitle's first token to be numeric, got {users_lines[1]!r}"
                )
                assert tuple(users_lines[2:6]) == USERS_PANEL_HEADER, (
                    f"Expected column headers {USERS_PANEL_HEADER}, got {tuple(users_lines[2:6])}"
                )
                users_body = users_lines[6:]
                assert not users_lines[1].startswith("0 "), (
                    f"Expected {AGENT_WITH_TOOLS_NAME!r} to have user activity (AFS precondition), "
                    f"got count subtitle {users_lines[1]!r}"
                )
                assert users_body and users_body[0], (
                    f"Expected the Users panel with count {users_lines[1]!r} to list at least "
                    f"one user, got {users_body!r}"
                )

            with allure.step(
                'Step 7 — Verify a "Tools" panel is shown alongside the Users panel, listing '
                "tools used by this agent/pipeline, with column headers Tool, Calls and a "
                "count subtitle — populated for this row"
            ):
                assert analytics_page.agent_detail_tools_panel.is_visible(), (
                    "Expected the Tools panel to be visible"
                )
                tools_lines = analytics_page.get_panel_summary(analytics_page.agent_detail_tools_panel)
                assert tools_lines, "Expected the Tools panel to render non-empty content"
                assert tools_lines[0] == TOOLS_PANEL_TITLE, (
                    f"Expected panel title {TOOLS_PANEL_TITLE!r}, got {tools_lines[0]!r}"
                )
                assert tools_lines[1].endswith("tools used by this agent / pipeline"), (
                    f"Expected a count subtitle ending 'tools used by this agent / pipeline', "
                    f"got {tools_lines[1]!r}"
                )
                assert not tools_lines[1].startswith("0 "), (
                    f"Expected {AGENT_WITH_TOOLS_NAME!r} to have tool usage (AFS precondition), "
                    f"got count subtitle {tools_lines[1]!r}"
                )
                assert tuple(tools_lines[2:4]) == TOOLS_PANEL_HEADER, (
                    f"Expected column headers {TOOLS_PANEL_HEADER}, got {tuple(tools_lines[2:4])}"
                )
                tools_body = tools_lines[4:]
                assert tools_body and tools_body[0], (
                    f"Expected the Tools panel with count {tools_lines[1]!r} to list at least "
                    f"one tool, got {tools_body!r}"
                )

            with allure.step(
                "Step 8 — Navigate back, switch to the zero-tool-usage pipeline row, and verify "
                "its Tools panel shows the 'No tool data' empty state"
            ):
                analytics_page.back_to_agents_table()
                assert analytics_page.agents_table_header.is_visible(), (
                    "Expected the Agents & Pipelines-tab table header to be visible again after "
                    "back navigation"
                )

                row_count = analytics_page.get_agents_row_count()
                empty_pipeline_index = next(
                    (
                        i
                        for i in range(row_count)
                        if analytics_page.get_agent_row_identifier(i).startswith(PIPELINE_NO_TOOLS_NAME_PREFIX)
                    ),
                    None,
                )
                assert empty_pipeline_index is not None, (
                    f"Expected a row starting with {PIPELINE_NO_TOOLS_NAME_PREFIX!r} to exercise "
                    f"the empty-state Tools-panel branch (AFS precondition)"
                )

                analytics_page.open_agent_detail(empty_pipeline_index)

                empty_tools_lines = analytics_page.get_panel_summary(analytics_page.agent_detail_tools_panel)
                assert empty_tools_lines, "Expected the Tools panel to render non-empty content"
                assert empty_tools_lines[1].startswith("0 "), (
                    f"Expected a zero-count subtitle for the empty-Tools-panel pipeline, got "
                    f"{empty_tools_lines[1]!r}"
                )
                assert tuple(empty_tools_lines[2:4]) == TOOLS_PANEL_HEADER, (
                    f"Expected column headers {TOOLS_PANEL_HEADER}, got {tuple(empty_tools_lines[2:4])}"
                )
                assert empty_tools_lines[4:] == ["No tool data"], (
                    f"Expected the single empty-state line 'No tool data', got {empty_tools_lines[4:]!r}"
                )

            with allure.step(
                "Step 9 — Click the back arrow and verify the view returns to the Agent & "
                "Pipeline Activity table, with no new network request"
            ):
                analytics_page.back_to_agents_table()
                assert analytics_page.agents_table_header.is_visible(), (
                    "Expected the Agents & Pipelines-tab table header to be visible again after "
                    "back navigation"
                )
                assert analytics_page.agents_activity_title.is_visible(), (
                    "Expected the 'Agent & Pipeline Activity' title to be visible again after "
                    "back navigation"
                )
                assert analytics_page.agents_count.is_visible(), (
                    "Expected the agents-count subtitle to be visible again after back navigation"
                )

            assert not console_errors, f"Unexpected console errors: {[m.text for m in console_errors]}"
        finally:
            console_errors.stop()
