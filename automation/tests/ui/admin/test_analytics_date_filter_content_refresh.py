"""UI tests — switching the Analytics date filter refreshes tab content, and the
filter itself survives tab switches.

Read-only verification against the currently-selected project's own analytics
data (`.agents/testing.md` § Test data strategy). Nothing is created, mutated
or deleted.

Test cases:
- ELITEA-2317 — AFS: test-specs/settings-analytics/l2_preset-switch-updates-overview-content_ELITEA-2317.md
- ELITEA-2318 — AFS: test-specs/settings-analytics/l2_preset-switch-updates-tab-content_ELITEA-2318.md
- ELITEA-2319 — AFS: test-specs/settings-analytics/l1_date-filter-retained-across-tabs_ELITEA-2319.md

Fidelity (`.agents/testing.md` § Fidelity policy → "How to test a
NONDETERMINISTIC producer without substituting it"): the content assertions use
the product's OWN response, captured live via `expect_response`, as the oracle —
rendered KPI values, row counts and chart ticks are compared against the body
the backend returned for the range under test. Nothing is mocked, stubbed or
injected. A naive "the numbers must differ between 7d and 30d" assertion was
deliberately NOT written: it is data-dependent (live-observed 2026-08-28,
project 471: `Last 7d` returns all zeros and no Model Usage table at all, while
`Last 30d` returns populated content) and would fail honestly-correct product
behaviour on a quiet project.

Case-text drift asserted against the LIVE contract (reverse-masking guard):
ELITEA-2317 says "all 6 KPI cards" (live: EIGHT), ELITEA-2318 says the "Agents"
tab under "Last 24d" (live: "Agents & Pipelines" tab, and the preset is
"Last 24h"), and ELITEA-2319's tab list omits the Costs and Tokens tabs the live
tab bar also carries. Same stale-case-text family as
elitea-testing-public#1185/#1195.
"""

import logging
import re
from datetime import timedelta

import allure
import pytest
from pages.analytics_page import AnalyticsPage
from utils.analytics_oracles import (
    CHART_MAX_SERIES,
    assert_category_chart_matches,
    assert_date_chart_matches,
    assert_overview_content_matches,
    response_dates,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression]

SPAN_TOLERANCE = timedelta(minutes=2)



class TestAnalyticsOverviewContentRefresh:
    """ELITEA-2317 — switching presets updates KPI cards, chart, and tables on Overview."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-analytics/ELITEA-2317_preset-updates-overview.md",
        "onetest-ai Test Case link",
    )
    def test_preset_switch_updates_overview_content(self, page):
        """Under Last 7d and then Last 30d, every Overview surface renders what
        the response for that range carried, and the chart axis widens."""
        analytics_page = AnalyticsPage(page)
        console_errors = analytics_page.capture_console_errors()

        try:
            with allure.step(
                'Step 1 — Navigate to Settings -> Analytics -> Overview tab under "Last 7d"'
            ):
                analytics_page.navigate()
                assert analytics_page.is_tab_selected(analytics_page.tab_overview), (
                    "Overview should be the default selected tab"
                )
                response_7d = analytics_page.click_preset(analytics_page.preset_last_7d)
                analytics_page.wait_for_overview_settled()

            with allure.step(
                "Step 2 — Note the KPI card values and the Daily Activity chart shape: all 8 "
                "cards, the leaderboard and the Model Usage table match the 7-day response"
            ):
                assert_overview_content_matches(
                    analytics_page, response_7d.json(), "Last 7d"
                )
                dates_7d = response_dates(response_7d.json(), "daily_activity")
                ticks_7d = analytics_page.get_daily_chart_tick_labels()
                # Same DATA check the 30-day branch makes in step 5. An earlier
                # round computed this span and never asserted anything about it,
                # so the 7d chart was covered by presence alone while the 30d one
                # was covered on data — the asymmetry this oracle removes.
                span_7d = assert_date_chart_matches(
                    ticks_7d, dates_7d, "Last 7d Daily Activity chart"
                )
                kpis_7d = analytics_page.get_overview_kpi_values()
                logger.info("Last 7d — KPI values %s, chart ticks %s", kpis_7d, ticks_7d)

            with allure.step('Step 3 — Click "Last 30d": the analytics query re-fires'):
                response_30d = analytics_page.click_preset(analytics_page.preset_last_30d)
                analytics_page.wait_for_overview_settled()
                assert response_30d.status == 200, (
                    f"30-day analytics request returned {response_30d.status}"
                )
                date_from, date_to = analytics_page.get_date_range()
                assert abs((date_to - date_from) - timedelta(days=30)) <= SPAN_TOLERANCE, (
                    f"Expected a 30-day range after clicking Last 30d, got {date_to - date_from}"
                )

            with allure.step("Step 4 — KPI card values update: all 8 match the 30-day response"):
                assert_overview_content_matches(
                    analytics_page, response_30d.json(), "Last 30d"
                )

            with allure.step(
                "Step 5 — The Daily Activity chart's time axis extends to cover 30 days"
            ):
                body_30d = response_30d.json()
                dates_30d = response_dates(body_30d, "daily_activity")
                ticks_30d = analytics_page.get_daily_chart_tick_labels()
                span_30d = assert_date_chart_matches(
                    ticks_30d, dates_30d, "Last 30d Daily Activity chart"
                )
                assert span_30d >= 20, (
                    f"Expected the 30-day chart axis to span at least 20 days, got {span_30d} "
                    f"(ticks {ticks_30d}) — recharts thins labels, hence the span check"
                )
                assert span_30d > span_7d, (
                    f"Expected the axis to widen when switching 7d -> 30d, got {span_7d} -> "
                    f"{span_30d} days"
                )

            with allure.step(
                "Step 6 — Top 5 AI Adopters and Model Usage Breakdown reflect the 30-day "
                "response (asserted inside step 4's shared check, restated here explicitly)"
            ):
                assert_overview_content_matches(
                    analytics_page, response_30d.json(), "Last 30d (restated)"
                )

            with allure.step("Step 7 — No unexpected console errors"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()


class TestAnalyticsTabContentRefresh:
    """ELITEA-2318 — preset switches update the Agents, Tools, and Users tab content."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-analytics/ELITEA-2318_preset-updates-tabs.md",
        "onetest-ai Test Case link",
    )
    def test_preset_switch_updates_agents_tools_and_users_tabs(self, page):
        """Each data tab re-queries its own endpoint for the new range and
        re-renders its table (and, on Agents, its two conditional charts)."""
        analytics_page = AnalyticsPage(page)
        console_errors = analytics_page.capture_console_errors()

        def assert_table_matches(response, rows_locator, count_locator, unit, label):
            body = response.json()
            expected_rows = len(body.get("rows") or [])
            assert rows_locator.count() == expected_rows, (
                f"{label}: {rows_locator.count()} rows rendered, the response carried "
                f"{expected_rows}"
            )
            count_text = count_locator.inner_text().strip()
            match = re.match(r"^(\d+)\s", count_text)
            assert match, f"{label}: count label {count_text!r} does not start with a number"
            assert int(match.group(1)) == body.get("total"), (
                f"{label}: count label {count_text!r} disagrees with the response's total "
                f"{body.get('total')!r}"
            )
            assert unit in count_text, f"{label}: expected {unit!r} in the count label {count_text!r}"

        def assert_agents_charts_match(response, label):
            body = response.json()
            has_rows = bool(body.get("rows"))
            has_chat = bool(body.get("chat_daily"))
            assert analytics_page.agents_chart_container.count() == (1 if has_rows else 0), (
                f"{label}: the Most Active Agents & Pipelines chart must render iff the "
                f"response has rows (rows={len(body.get('rows') or [])})"
            )
            assert analytics_page.agents_chat_chart_container.count() == (1 if has_chat else 0), (
                f"{label}: the Chat Messages chart must render iff the response has chat_daily "
                f"data (chat_daily={len(body.get('chat_daily') or [])})"
            )
            if has_chat:
                # Presence alone is not "the chart updated its data" (case
                # steps 2 and 4): a chart frozen on the PREVIOUS range's series
                # is still exactly one container. So the rendered axis is
                # compared against this response's own `chat_daily` — the
                # AreaChart's XAxis renders `date.slice(5)` of that very array
                # (`AnalyticsAgents.jsx`), which makes tick labels and response
                # dates directly comparable.
                chat_dates = response_dates(body, "chat_daily")
                chat_ticks = analytics_page.get_agents_chat_chart_tick_labels()
                what = f"{label}: Chat Messages chart"
                rendered_span = assert_date_chart_matches(chat_ticks, chat_dates, what)
                logger.info(
                    "%s — chat_daily=%d entries, rendered ticks %s spanning %d days",
                    what, len(chat_dates), chat_ticks, rendered_span,
                )
            if has_rows:
                # The "Most Active Agents & Pipelines" BAR chart, on DATA.
                #
                # An earlier round asserted this chart on presence + the
                # `Top {N} by runs` subtitle only — and neither can detect a
                # stale chart: the container count is invariant under a frozen
                # render, and two different ranges very often chart the same
                # NUMBER of agents while charting different ones. Case steps 2
                # and 4 name this chart's data, so its axis is compared to the
                # response's own charted names, exactly as the Tools chart's is.
                charted = body["rows"][:CHART_MAX_SERIES]
                subtitle = analytics_page.agents_chart_subtitle.inner_text().strip()
                assert subtitle == f"Top {len(charted)} by runs", (
                    f"{label}: bar-chart subtitle {subtitle!r} disagrees with the response's "
                    f"{len(charted)} charted series"
                )
                # `AnalyticsAgents.jsx` charts `name: a.entity_name || \`Agent #${a.entity_id}\``
                # with `dataKey="name"` and `interval={0}` — no thinning, so the
                # rendered tick list EQUALS the charted names, in order.
                expected_names = [
                    str(row.get("entity_name") or f"Agent #{row.get('entity_id')}")
                    for row in charted
                ]
                agent_ticks = analytics_page.get_agents_chart_x_axis_labels()
                logger.info(
                    "%s — Most Active Agents & Pipelines: %d charted rows, rendered ticks %s",
                    label, len(charted), agent_ticks,
                )
                assert_category_chart_matches(
                    agent_ticks, expected_names,
                    f"{label}: Most Active Agents & Pipelines chart",
                )

        def assert_tools_chart_matches(response, label):
            """The Tools tab's "Most Popular Tools" bar chart, on DATA.

            Same shape as `assert_agents_charts_match`: the chart is
            conditionally rendered (`toolChartData.length > 0`), so presence is
            asserted iff the response carried rows — and when it renders, its
            axis is compared to THIS response's own `rows`. `AnalyticsTools.jsx`
            charts `rows.slice(0, 20)` with `dataKey="tool_name"` and
            `interval={0}`, so every tick renders and the rendered label list
            must equal the response's first 20 tool names, in order. A chart
            frozen on the previous range's series fails that; a presence-only
            check would not.
            """
            body = response.json()
            rows = body.get("rows") or []
            charted = rows[:CHART_MAX_SERIES]
            assert analytics_page.tools_chart_container.count() == (1 if charted else 0), (
                f"{label}: the Most Popular Tools chart must render iff the response has "
                f"rows (rows={len(rows)})"
            )
            if not charted:
                return
            subtitle = analytics_page.tools_chart_subtitle.inner_text().strip()
            assert subtitle == f"Top {len(charted)} by usage", (
                f"{label}: bar-chart subtitle {subtitle!r} disagrees with the response's "
                f"{len(charted)} charted series"
            )
            expected_names = [row["tool_name"] for row in charted]
            ticks = analytics_page.get_tools_chart_x_axis_labels()
            logger.info(
                "%s — Most Popular Tools: %d charted rows, rendered ticks %s",
                label, len(charted), ticks,
            )
            assert_category_chart_matches(
                ticks, expected_names, f"{label}: Most Popular Tools chart"
            )

        try:
            with allure.step(
                'Step 1 — Navigate to Settings -> Analytics, select "Last 24h", open the '
                '"Agents & Pipelines" tab (case says "Agents tab under Last 24d" — stale)'
            ):
                analytics_page.navigate()
                # "Last 24h" is the product's DEFAULT preset, and clicking an
                # already-active preset is a deliberate no-op (MUI's exclusive
                # ToggleButtonGroup emits null, `handleDatePresetChange`
                # returns early) — so assert the state instead of clicking it.
                assert analytics_page.get_pressed_preset_labels() == ["Last 24h"], (
                    "Expected the page to open on its default 'Last 24h' preset, got "
                    f"{analytics_page.get_pressed_preset_labels()!r}"
                )
                agents_24h = analytics_page.open_tab_awaiting(
                    analytics_page.tab_agents_pipelines, "agents"
                )
                analytics_page.agents_table_header.wait_for(state="visible")
                analytics_page.wait_for_tab_settled("agents")
                assert analytics_page.is_tab_selected(analytics_page.tab_agents_pipelines)

            with allure.step(
                "Step 2 — Note the Chat Messages chart, the Most Active bar chart and the "
                "Agent & Pipeline Activity table under Last 24h"
            ):
                assert_agents_charts_match(agents_24h, "Agents / Last 24h")
                assert_table_matches(
                    agents_24h,
                    analytics_page.agents_rows,
                    analytics_page.agents_count,
                    "agents & pipelines",
                    "Agents / Last 24h",
                )

            with allure.step('Step 3 — Click "Last 30d": the Agents query re-fires'):
                agents_30d = analytics_page.click_preset(analytics_page.preset_last_30d, "agents")
                analytics_page.agents_table_header.wait_for(state="visible")
                analytics_page.wait_for_tab_settled("agents")
                assert agents_30d.status == 200

            with allure.step("Step 4 — Both Agents charts update their data"):
                assert_agents_charts_match(agents_30d, "Agents / Last 30d")

            with allure.step("Step 5 — The Agent & Pipeline Activity table updates"):
                assert_table_matches(
                    agents_30d,
                    analytics_page.agents_rows,
                    analytics_page.agents_count,
                    "agents & pipelines",
                    "Agents / Last 30d",
                )

            with allure.step(
                "Step 6a — Repeat for the Users tab: it loads under Last 30d and re-fetches "
                "when the preset switches back to Last 24h"
            ):
                users_30d = analytics_page.open_tab_awaiting(analytics_page.tab_users, "users")
                analytics_page.users_table_header.wait_for(state="visible")
                analytics_page.wait_for_tab_settled("users")
                assert_table_matches(
                    users_30d,
                    analytics_page.users_rows,
                    analytics_page.users_count,
                    "users",
                    "Users / Last 30d",
                )

                users_24h = analytics_page.click_preset(analytics_page.preset_last_24h, "users")
                analytics_page.users_table_header.wait_for(state="visible")
                analytics_page.wait_for_tab_settled("users")
                assert_table_matches(
                    users_24h,
                    analytics_page.users_rows,
                    analytics_page.users_count,
                    "users",
                    "Users / Last 24h",
                )

            with allure.step(
                "Step 6b — Repeat for the Tools tab: it loads under Last 24h and re-fetches "
                "when the preset switches to Last 30d"
            ):
                tools_24h = analytics_page.open_tab_awaiting(analytics_page.tab_tools, "tools")
                analytics_page.tools_table_header.wait_for(state="visible")
                analytics_page.wait_for_tab_settled("tools")
                assert analytics_page.tools_details_title.inner_text().strip() == "Tool Details"
                assert_table_matches(
                    tools_24h,
                    analytics_page.tools_rows,
                    analytics_page.tools_count,
                    "tools",
                    "Tools / Last 24h",
                )
                assert_tools_chart_matches(tools_24h, "Tools / Last 24h")

                tools_30d = analytics_page.click_preset(analytics_page.preset_last_30d, "tools")
                analytics_page.tools_table_header.wait_for(state="visible")
                analytics_page.wait_for_tab_settled("tools")
                assert_table_matches(
                    tools_30d,
                    analytics_page.tools_rows,
                    analytics_page.tools_count,
                    "tools",
                    "Tools / Last 30d",
                )
                assert_tools_chart_matches(tools_30d, "Tools / Last 30d")

            with allure.step("Step 7 — No unexpected console errors"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()


class TestAnalyticsDateFilterRetention:
    """ELITEA-2319 — the date filter survives every tab switch."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-analytics/ELITEA-2319_date-filter-retained-across-tabs.md",
        "onetest-ai Test Case link",
    )
    def test_date_filter_retained_when_switching_tabs(self, page):
        """After selecting Last 30d, the preset highlight and both picker values
        are byte-identical on every one of the six tabs the case walks."""
        analytics_page = AnalyticsPage(page)
        console_errors = analytics_page.capture_console_errors()

        try:
            with allure.step('Step 1 — Navigate to Settings -> Analytics and click "Last 30d"'):
                analytics_page.navigate()
                analytics_page.click_preset(analytics_page.preset_last_30d)
                analytics_page.wait_for_overview_settled()

                pressed = analytics_page.get_pressed_preset_labels()
                assert pressed == ["Last 30d"], f"Expected only Last 30d pressed, got {pressed!r}"
                expected_from = analytics_page.get_date_from_text()
                expected_to = analytics_page.get_date_to_text()
                date_from, date_to = analytics_page.get_date_range()
                assert abs((date_to - date_from) - timedelta(days=30)) <= SPAN_TOLERANCE, (
                    f"Expected a 30-day range, got {date_to - date_from}"
                )

            tabs = (
                ("Agents & Pipelines", analytics_page.tab_agents_pipelines),
                ("Tools", analytics_page.tab_tools),
                ("Users", analytics_page.tab_users),
                ("Health", analytics_page.tab_health),
                ("Guide", analytics_page.tab_guide),
                ("Overview", analytics_page.tab_overview),
            )
            for tab_label, tab_locator in tabs:
                with allure.step(
                    f"Steps 2-4 — Switch to the {tab_label} tab: it becomes selected, "
                    '"Last 30d" stays the only highlighted preset, and From/To are unchanged'
                ):
                    tab_locator.click()
                    tab_locator.wait_for(state="visible")
                    assert analytics_page.is_tab_selected(tab_locator), (
                        f"{tab_label} tab should be selected after clicking it"
                    )

                    pressed = analytics_page.get_pressed_preset_labels()
                    assert pressed == ["Last 30d"], (
                        f"On the {tab_label} tab, expected only 'Last 30d' highlighted, got "
                        f"{pressed!r}"
                    )
                    assert analytics_page.get_date_from_text() == expected_from, (
                        f"On the {tab_label} tab, From changed from {expected_from!r} to "
                        f"{analytics_page.get_date_from_text()!r}"
                    )
                    assert analytics_page.get_date_to_text() == expected_to, (
                        f"On the {tab_label} tab, To changed from {expected_to!r} to "
                        f"{analytics_page.get_date_to_text()!r}"
                    )

            with allure.step("Step 5 — No unexpected console errors"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
