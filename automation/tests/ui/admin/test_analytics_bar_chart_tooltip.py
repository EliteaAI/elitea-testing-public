"""UI test (family) — hovering a bar in an Analytics bar chart shows that
entity's name and its metric value, updates when a different bar is hovered,
and unmounts on mouse-out.

One parameterized spec, one row per TMS case — the two cases differ only in
data (which tab, which testids, which series name, which response fields);
every action is the same, in the same order, against the same oracle shape:

- **ELITEA-2327** — Agents & Pipelines tab, "Most Active Agents & Pipelines"
- **ELITEA-2328** — Tools tab, "Most Popular Tools"

Read-only verification against the currently-selected project's own analytics
data (`.agents/testing.md` § Test data strategy). This case never creates,
modifies, or deletes anything.

AFS: test-specs/settings-analytics/l2_bar-chart-hover-tooltip_ELITEA-2327-2328.md

Fidelity (`.agents/testing.md` § Fidelity policy) — **no substitutions**. Every
hover is a real `page.mouse.move()` CDP input event (never a `page.evaluate`
dispatched synthetic event), and every asserted label and number is compared
against the live `analytics_agents/` / `analytics_tools/` response body
captured off the wire.

Case-text drift for ELITEA-2327 only (filed elitea-testing-public#1955, sibling
of #1195): the case calls the tab "Agents" and the chart "Most Active Agents"
and asks for the agent's "event count"; live the tab is "Agents & Pipelines",
the chart "Most Active Agents & Pipelines", and the tooltip labels the metric
`Runs` (the underlying response field IS `events`, so the number the case means
is asserted — under the label the product actually renders). ELITEA-2328's text
matches the live product exactly. This test asserts the live contract
(reverse-masking guard).
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


def _agent_label(row: dict) -> str:
    """The Agents bar chart's x-axis category for *row* — `AnalyticsAgents.jsx:57-64`
    maps `entity_name || "Agent #" + entity_id` onto the `name` dataKey."""
    return row.get("entity_name") or f"Agent #{row['entity_id']}"


def _tool_label(row: dict) -> str:
    """The Tools bar chart's x-axis category for *row* (`AnalyticsTools.jsx:37-45`,
    `XAxis dataKey="tool_name"`)."""
    return row["tool_name"]


# One row per TMS case. `open_tab` is the AnalyticsPage method that opens the
# tab AND returns its response body (the oracle); the locator entries are
# AnalyticsPage `LocatorDescriptor` attribute names, resolved via getattr so the
# parameter table stays declarative.
BAR_CHART_CASES = (
    pytest.param(
        {
            "case_id": "ELITEA-2327",
            "tab_locator": "tab_agents_pipelines",
            "open_tab": "open_agents_pipelines_tab_capturing_analytics",
            "chart_title_locator": "agents_chart_title",
            "chart_container_locator": "agents_chart_container",
            "tooltip_locator": "agents_chart_tooltip",
            "expected_chart_title": "Most Active Agents & Pipelines",
            "series_name": "Runs",
            "value_field": "events",
            "label_of": _agent_label,
        },
        id="ELITEA-2327-agents-pipelines",
    ),
    pytest.param(
        {
            "case_id": "ELITEA-2328",
            "tab_locator": "tab_tools",
            "open_tab": "open_tools_tab",
            "chart_title_locator": "tools_chart_title",
            "chart_container_locator": "tools_chart_container",
            "tooltip_locator": "tools_chart_tooltip",
            "expected_chart_title": "Most Popular Tools",
            "series_name": "Calls",
            "value_field": "calls",
            "label_of": _tool_label,
        },
        id="ELITEA-2328-tools",
    ),
)


class TestAnalyticsBarChartTooltip:
    """ELITEA-2327 / ELITEA-2328 — hovering a bar raises a tooltip naming that
    bar's entity and its metric value, both matching the captured response row
    at the same index; hovering a different bar re-renders it against that row;
    moving off the chart unmounts it.

    Neither chart renders a legend, so the series NAME (`Runs` / `Calls`)
    exists in the DOM only inside this tooltip — which is what makes these
    assertions load-bearing rather than cosmetic.
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/analytics/ELITEA-2327_hovering-over-a-bar-in-most-active-agents-chart-shows-agent.md",
        "onetest-ai Test Case link (ELITEA-2327)",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/analytics/ELITEA-2328_hovering-over-most-popular-tools-bar-chart-shows-tool-name-a.md",
        "onetest-ai Test Case link (ELITEA-2328)",
    )
    @pytest.mark.parametrize("case", BAR_CHART_CASES)
    def test_bar_chart_hover_tooltip(self, page, case):
        """Hovering a bar shows that response row's label and metric value;
        hovering a different bar re-renders the tooltip against that row;
        moving away removes the tooltip from the DOM."""
        analytics_page = AnalyticsPage(page)
        console_errors = collect_console_errors(page)

        tab = getattr(analytics_page, case["tab_locator"])
        chart_title = getattr(analytics_page, case["chart_title_locator"])
        chart_container = getattr(analytics_page, case["chart_container_locator"])
        tooltip = getattr(analytics_page, case["tooltip_locator"])
        series_name = case["series_name"]

        with allure.step(
            f'Step 1 — [{case["case_id"]}] Navigate to Settings -> Analytics, select "Last 30d", '
            f"open the tab and capture its response as the oracle"
        ):
            analytics_page.navigate()
            analytics_page.select_date_preset_capturing_analytics(analytics_page.preset_last_30d)
            response = getattr(analytics_page, case["open_tab"])()
            assert analytics_page.is_tab_selected(tab), (
                f"Expected the {case['case_id']} tab to be aria-selected=true after clicking it"
            )

            rows = response.get("rows") or []
            # Precondition, asserted against the captured response: both charts
            # are conditionally rendered (`agentChartData.length > 0` /
            # `toolChartData.length > 0`), and step 4 needs a second bar to move
            # to. A project without enough activity must fail loudly here rather
            # than as a confusing locator timeout.
            assert len(rows) >= 2, (
                f"Expected the selected project to have at least 2 {case['case_id']} rows over "
                f"Last 30d (the chart is not rendered at all with none, and the case's 'move to a "
                f"different bar' step needs a second bar), got {len(rows)}"
            )

            expect(chart_container).to_be_visible()
            expect(chart_title).to_have_text(case["expected_chart_title"])

        with allure.step(f'Step 2 — [{case["case_id"]}] Hover the first plotted bar'):
            # Captured in one pass BEFORE any hover: hovering re-renders the
            # `<Bar>` series (Recharts' active index changes) and a box read
            # afterwards can transiently come back None. A zero-valued row
            # renders a zero-height path with no usable box, so the bars to
            # hover are the first two that actually have one — still keyed on
            # the bar INDEX, so bar i <-> rows[i] stays exact.
            bar_boxes = analytics_page.get_chart_bar_boxes(chart_container)
            assert len(bar_boxes) >= 2, (
                f"Expected the bar chart to render at least 2 bars for the case's "
                f"'move to a different bar' step, got {len(bar_boxes)}"
            )
            hover_indices = [i for i, box in enumerate(bar_boxes) if box and box["height"] > 0][:2]
            assert len(hover_indices) >= 2, (
                f"Expected at least 2 bars with a hoverable (non-zero-height) layout box, got "
                f"{len(hover_indices)} out of {len(bar_boxes)} rendered bars"
            )
            first_index, second_index = hover_indices
            analytics_page.hover_chart_bar_box(bar_boxes[first_index])
            expect(tooltip).to_be_visible()

        with allure.step(
            f'Step 3 — [{case["case_id"]}] Verify the tooltip names the hovered row\'s entity and its '
            f"{series_name} value from the captured response"
        ):
            first_lines = analytics_page.read_chart_tooltip_lines(tooltip)
            expected_first = _expected_tooltip_lines(case, rows[first_index])
            assert first_lines == expected_first, (
                f"Expected the bar-{first_index} tooltip to read {expected_first!r} (label and "
                f"value from the captured response row {first_index}), got {first_lines!r}"
            )
            logger.info("[%s] bar %d tooltip: %s", case["case_id"], first_index, first_lines)

        with allure.step(
            f'Step 4 — [{case["case_id"]}] Move to a different bar and verify the tooltip re-renders '
            f"against that response row"
        ):
            analytics_page.hover_chart_bar_box(bar_boxes[second_index])
            # NOTE: deliberately NOT asserting "the two labels differ" — the
            # top-20 x-axis categories are not unique (distinct entities can
            # share a name), so every assertion keys on the bar INDEX against
            # rows[i], and the full-text change is the honest "it updated" check.
            second_lines = analytics_page.wait_for_chart_tooltip_change(tooltip, first_lines)
            expect(tooltip).to_be_visible()
            expected_second = _expected_tooltip_lines(case, rows[second_index])
            assert second_lines == expected_second, (
                f"Expected the bar-{second_index} tooltip to read {expected_second!r} (label and "
                f"value from the captured response row {second_index}), got {second_lines!r}"
            )

        with allure.step(
            f'Step 5 — [{case["case_id"]}] Move the cursor off the chart and verify the tooltip '
            f"is removed from the DOM"
        ):
            analytics_page.move_mouse_off_chart(chart_container)
            # The shared `ChartTooltip` returns null when `!active`, so the node
            # UNMOUNTS rather than merely hiding — count 0, not not_to_be_visible.
            expect(tooltip).to_have_count(0)

        assert not console_errors, f"Unexpected console errors: {console_errors}"


def _expected_tooltip_lines(case: dict, row: dict) -> list[str]:
    """The `ChartTooltip` render this bar chart owes for *row*: the label line
    followed by the single ``"{series}: {value}"`` line, both derived from the
    captured response — the test never authors an expected value."""
    return [
        case["label_of"](row),
        f"{case['series_name']}: {fmt_num(row[case['value_field']])}",
    ]
