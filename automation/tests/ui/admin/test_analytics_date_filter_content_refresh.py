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

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression]

SPAN_TOLERANCE = timedelta(minutes=2)

# The Overview KPI cards, in DOM order, with the response field each renders
# (`AnalyticsOverview.jsx`). COST is formatted by `fmtCost`, whose seven
# magnitude branches are deliberately NOT mirrored here — see `_fmt_num`.
KPI_FIELDS = (
    ("TEAM", "unique_users"),
    ("AI ACTIVE", "ai_active_users"),
    ("LLM CALLS", "llm_calls"),
    ("TOOL RUNS", "tool_runs"),
    ("CHAT MSG", "chat_msgs"),
    ("AGENT & PIPELINE RUNS", "agent_runs"),
    ("TOKENS", "total_tokens"),
)


def _fmt_num(value) -> str:
    """Mirror of `AnalyticCommonHelpers.fmtNum` (analyticsCommon.helpers.js).

    Four lines of display contract — `>=1e6 -> "{x}M"`, `>=1e3 -> "{x}K"`,
    `None -> "-"` — applied to the value the SYSTEM returned, so the expected
    string is derived from the real response rather than hand-written.
    """
    if value is None:
        return "-"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def _assert_overview_matches(analytics_page: AnalyticsPage, response, label: str) -> None:
    """Every Overview surface renders what *response* carried for its range."""
    body = response.json()
    kpis = body.get("kpis") or {}

    rendered = analytics_page.get_overview_kpi_values()
    assert len(rendered) == 8, (
        f"{label}: expected 8 Overview KPI cards (case text says 6 — stale), got {len(rendered)}"
    )
    for index, (kpi_label, field) in enumerate(KPI_FIELDS):
        expected = _fmt_num(kpis.get(field))
        assert rendered[index] == expected, (
            f"{label}: KPI {kpi_label!r} rendered {rendered[index]!r}, but the response's "
            f"kpis.{field} = {kpis.get(field)!r} formats to {expected!r}"
        )

    cost_rendered = rendered[7]
    assert cost_rendered.startswith("$"), (
        f"{label}: COST card should render a currency string, got {cost_rendered!r}"
    )
    if not kpis.get("total_llm_cost"):
        assert cost_rendered == "$0.00", (
            f"{label}: response reported no cost, expected '$0.00', got {cost_rendered!r}"
        )
    else:
        assert cost_rendered != "$0.00", (
            f"{label}: response reported cost {kpis.get('total_llm_cost')!r}, but the card "
            f"renders {cost_rendered!r}"
        )

    leaderboard_expected = len(body.get("top_ai_users") or [])
    assert analytics_page.get_leaderboard_row_count() == leaderboard_expected, (
        f"{label}: leaderboard rendered {analytics_page.get_leaderboard_row_count()} rows, the "
        f"response carried {leaderboard_expected}"
    )
    assert analytics_page.overview_leaderboard.count() == (1 if leaderboard_expected else 0), (
        f"{label}: the leaderboard container must be present iff the response has adopters"
    )
    if leaderboard_expected:
        top = (body["top_ai_users"])[0]
        first_row = analytics_page.get_leaderboard_row_text(0)
        assert str(top.get("user_email")) in first_row, (
            f"{label}: first leaderboard row {first_row!r} does not carry the response's top "
            f"adopter {top.get('user_email')!r}"
        )
        assert _fmt_num(top.get("ai_events")) in first_row, (
            f"{label}: first leaderboard row {first_row!r} does not carry the response's top "
            f"score {top.get('ai_events')!r}"
        )

    models_expected = len(body.get("models") or [])
    assert analytics_page.get_model_usage_row_count() == models_expected, (
        f"{label}: Model Usage Breakdown rendered "
        f"{analytics_page.get_model_usage_row_count()} rows, the response carried {models_expected}"
    )
    assert analytics_page.overview_model_usage_table.count() == (1 if models_expected else 0), (
        f"{label}: the Model Usage Breakdown card must be present iff the response has models "
        "(the component returns null for an empty list)"
    )


def _chart_tick_span_days(ticks: list[str]) -> int:
    """Days between the first and last rendered "MM-DD" X-axis tick."""
    assert ticks, "Daily Activity chart rendered no X-axis ticks"
    first_month, first_day = (int(part) for part in ticks[0].split("-"))
    last_month, last_day = (int(part) for part in ticks[-1].split("-"))
    # Month-crossing ranges are handled with a 30-day-per-month approximation —
    # the assertion is about the ORDER OF MAGNITUDE of the span (7 vs 30 days),
    # not a calendar-exact difference.
    return (last_month - first_month) * 30 + (last_day - first_day)


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
                _assert_overview_matches(analytics_page, response_7d, "Last 7d")
                ticks_7d = analytics_page.get_daily_chart_tick_labels()
                span_7d = _chart_tick_span_days(ticks_7d)
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
                _assert_overview_matches(analytics_page, response_30d, "Last 30d")

            with allure.step(
                "Step 5 — The Daily Activity chart's time axis extends to cover 30 days"
            ):
                body_30d = response_30d.json()
                daily_30d = [d["date"][5:] for d in (body_30d.get("daily_activity") or [])]
                ticks_30d = analytics_page.get_daily_chart_tick_labels()
                assert set(ticks_30d) <= set(daily_30d), (
                    f"Chart X ticks {ticks_30d} are not a subset of the response's "
                    f"daily_activity dates {daily_30d}"
                )
                assert ticks_30d[-1] == daily_30d[-1], (
                    f"Chart's last tick {ticks_30d[-1]!r} should be the response's last "
                    f"daily_activity date {daily_30d[-1]!r}"
                )
                span_30d = _chart_tick_span_days(ticks_30d)
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
                body_30d = response_30d.json()
                assert analytics_page.get_leaderboard_row_count() == len(
                    body_30d.get("top_ai_users") or []
                )
                assert analytics_page.get_model_usage_row_count() == len(
                    body_30d.get("models") or []
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
            if has_rows:
                subtitle = analytics_page.agents_chart_subtitle.inner_text().strip()
                expected_series = min(len(body["rows"]), 20)
                assert subtitle == f"Top {expected_series} by runs", (
                    f"{label}: bar-chart subtitle {subtitle!r} disagrees with the response's "
                    f"{expected_series} charted series"
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
                tools_24h = analytics_page.open_tools_tab()
                assert analytics_page.tools_details_title.inner_text().strip() == "Tool Details"
                assert_table_matches(
                    tools_24h,
                    analytics_page.tools_rows,
                    analytics_page.tools_count,
                    "tools",
                    "Tools / Last 24h",
                )

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
