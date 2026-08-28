"""UI test — Overview tab displays all KPI cards with correct labels and non-empty values.

Read-only verification against the currently-selected project's own analytics
data (`.agents/testing.md` § Test data strategy). Nothing is created, modified
or deleted; the test only reads the Overview tab's KPI row.

Test case: ELITEA-2311
AFS: test-specs/settings-analytics/l2_overview-tab-kpi-cards_ELITEA-2311.md

Fidelity (`.agents/testing.md` § Fidelity policy): NO substitution. The
analytics GET's own live response body is captured (`expect_response`) and used
as the ORACLE for every rendered value — the product produces every number, the
test only checks the UI carried it through faithfully. Nothing is stubbed,
intercepted, rewritten or injected.

Case-text drift (see AFS § Metadata, filed elitea-testing-public#1948, same
stale-case-text family as #1185/#1188): the case says "six KPI cards" (live:
eight — TOKENS and COST were added), calls card 6 "AGENT RUNS" (live:
"AGENT & PIPELINE RUNS"), describes the TEAM card as one string "X of Y active
members" (live: three separate elements — value, value-suffix, subtitle), and
describes the AI ACTIVE adoption badge as unconditional (live: rendered only
when `kpis.adoption_rate > 0`). This test asserts the live contract, and covers
the badge's zero branch with an absence assertion so the conditional-render
contract is test-enforced in both directions.
"""

import logging
import re

import allure
import pytest
from pages.analytics_page import AnalyticsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

EXPECTED_KPI_LABELS = (
    "TEAM",
    "AI ACTIVE",
    "LLM CALLS",
    "TOOL RUNS",
    "CHAT MSG",
    "AGENT & PIPELINE RUNS",
    "TOKENS",
    "COST",
)

# Values that would mean the card rendered nothing meaningful (case step 9 /
# Expected Final State). "-" is `fmtNum`/`fmtCost`'s own "missing data" render,
# so a card showing it means the backend sent null for that KPI.
DEGENERATE_VALUE_PATTERN = re.compile(r"^(undefined|nan|null|-)$", re.IGNORECASE)

# AI ACTIVE adoption badge color — `palette.status.published`, confirmed live
# via getComputedStyle against the active theme (same discipline as the Users
# tab's Errors-cell colors: never hardcode an assumed value).
ADOPTION_BADGE_COLOR = "rgb(43, 212, 141)"


def fmt_num(value) -> str:
    """Python port of `AnalyticCommonHelpers.fmtNum` (EliteaUI
    `settings/lib/helpers/analyticsCommon.helpers.js`) — the formatter the KPI
    cards render their numbers through. Kept suite-local (Hard Rule 7: extract
    to `utils/` on the third consumer, not the first)."""
    if value is None:
        return "-"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def fmt_cost(usd) -> str:
    """Python port of `AnalyticCommonHelpers.fmtCost` — the formatter the COST
    card renders through."""
    if usd is None:
        return "-"
    if usd == 0:
        return "$0.00"
    abs_usd = abs(usd)
    sign = "-" if usd < 0 else ""
    if abs_usd < 0.0001:
        return f"{sign}${abs_usd:.8f}"
    if abs_usd < 0.01:
        return f"{sign}${abs_usd:.6f}"
    if abs_usd < 1:
        return f"{sign}${abs_usd:.4f}"
    if abs_usd < 1000:
        return f"{sign}${abs_usd:.2f}"
    if abs_usd < 1_000_000:
        return f"{sign}${abs_usd / 1000:.1f}K"
    return f"{sign}${abs_usd / 1_000_000:.1f}M"


class TestAnalyticsOverviewKpiCards:
    """ELITEA-2311 — Overview tab's eight KPI cards: labels, subtitles, the
    TEAM card's "X of Y" shape, the conditional AI ACTIVE adoption badge, and
    every value checked against the live analytics response."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/analytics/ELITEA-2311_overview-tab-displays-all-six-kpi-cards-with-correct-labels.md",
        "onetest-ai Test Case link",
    )
    def test_overview_tab_kpi_cards(self, page):
        """Overview tab renders eight KPI cards whose labels, subtitles and
        values match the live analytics response, with no blank, "undefined"
        or "NaN" value anywhere."""
        analytics_page = AnalyticsPage(page)
        console_errors = analytics_page.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Analytics; the Overview tab is selected by default"
            ):
                # The page-load GET's 200 is asserted inside the page object.
                analytics_page.navigate_capturing_analytics()
                assert analytics_page.is_tab_selected(analytics_page.tab_overview), (
                    "Expected the 'Overview' tab to be aria-selected=true on page load"
                )
                assert analytics_page.overview_kpi_row.is_visible(), (
                    "Expected the Overview KPI card row to render"
                )

            with allure.step(
                "Step 2 — Click the 'Last 30d' preset, capturing the resulting analytics "
                "response body as the oracle for every value assertion below"
            ):
                body = analytics_page.select_date_preset_capturing_analytics(
                    analytics_page.preset_last_30d
                )
                assert "kpis" in body, (
                    f"Expected the analytics response to carry a 'kpis' object, got keys "
                    f"{sorted(body.keys())}"
                )
                kpis = body["kpis"]

            with allure.step(
                "Step 3 — Verify the KPI card set: exactly eight cards, with the expected "
                "labels and subtitles in rendered order"
            ):
                assert analytics_page.overview_kpi_cards.count() == len(EXPECTED_KPI_LABELS), (
                    f"Expected {len(EXPECTED_KPI_LABELS)} KPI cards, got "
                    f"{analytics_page.overview_kpi_cards.count()}"
                )
                actual_labels = tuple(analytics_page.get_overview_kpi_labels())
                assert actual_labels == EXPECTED_KPI_LABELS, (
                    f"Expected KPI labels {EXPECTED_KPI_LABELS}, got {actual_labels}"
                )
                expected_subtitles = (
                    "active members",
                    f"{kpis['adoption_rate']}% adoption",
                    "event_type = llm",
                    "event_type = tool",
                    "user messages sent",
                    "agents and pipelines interactions",
                    "total LLM tokens consumed",
                    "estimated USD cost",
                )
                actual_subtitles = tuple(analytics_page.get_overview_kpi_subtitles())
                assert actual_subtitles == expected_subtitles, (
                    f"Expected KPI subtitles {expected_subtitles}, got {actual_subtitles}"
                )

            with allure.step(
                'Step 4 — Verify the TEAM card\'s "X of Y" shape against the response '
                "(unique_users / total_project_users)"
            ):
                team_value = (analytics_page.overview_kpi_values.nth(0).text_content() or "").strip()
                assert team_value == fmt_num(kpis["unique_users"]), (
                    f"Expected the TEAM card value to render kpis.unique_users "
                    f"({kpis['unique_users']!r} -> {fmt_num(kpis['unique_users'])!r}), got {team_value!r}"
                )
                expect(analytics_page.overview_kpi_value_suffix).to_have_count(1)
                suffix = (analytics_page.overview_kpi_value_suffix.text_content() or "").strip()
                assert suffix == f"of {fmt_num(kpis['total_project_users'])}", (
                    f"Expected the TEAM card suffix 'of {fmt_num(kpis['total_project_users'])}', "
                    f"got {suffix!r}"
                )

            with allure.step(
                "Step 5 — Verify the AI ACTIVE adoption badge, conditional on the captured "
                "response: present + green when adoption_rate > 0, absent when it is 0"
            ):
                adoption_rate = kpis["adoption_rate"]
                if adoption_rate > 0:
                    expect(analytics_page.overview_kpi_badge).to_have_count(1)
                    badge_text = (analytics_page.overview_kpi_badge.text_content() or "").strip()
                    assert badge_text == f"↑{adoption_rate}%", (
                        f"Expected the adoption badge to read '↑{adoption_rate}%', got {badge_text!r}"
                    )
                    expect(analytics_page.overview_kpi_badge).to_have_css("color", ADOPTION_BADGE_COLOR)
                else:
                    # The product's own documented zero branch — the badge prop is
                    # `undefined`, so nothing renders. Absence assertions are
                    # first-class references (`.agents/testing.md` § Locator policy).
                    expect(analytics_page.overview_kpi_badge).to_have_count(0)
                logger.info("AI ACTIVE adoption_rate=%s (badge branch exercised)", adoption_rate)

            with allure.step(
                "Step 6 — Verify no card renders a degenerate value, and that every value "
                "is the formatted rendering of its own field of the captured response"
            ):
                values = analytics_page.get_overview_kpi_values()
                subtitles = analytics_page.get_overview_kpi_subtitles()
                for label, value in zip(EXPECTED_KPI_LABELS, values):
                    assert value, f"Expected the {label} card to render a non-empty value"
                    assert not DEGENERATE_VALUE_PATTERN.match(value), (
                        f"Expected the {label} card's value to be real data, got {value!r}"
                    )
                for label, subtitle in zip(EXPECTED_KPI_LABELS, subtitles):
                    assert subtitle, f"Expected the {label} card to render a non-empty subtitle"
                    assert not DEGENERATE_VALUE_PATTERN.match(subtitle), (
                        f"Expected the {label} card's subtitle to be real text, got {subtitle!r}"
                    )
                expected_values = (
                    fmt_num(kpis["unique_users"]),
                    fmt_num(kpis["ai_active_users"]),
                    fmt_num(kpis["llm_calls"]),
                    fmt_num(kpis["tool_runs"]),
                    fmt_num(kpis["chat_msgs"]),
                    fmt_num(kpis["agent_runs"]),
                    fmt_num(kpis["total_tokens"]),
                    fmt_cost(kpis["total_llm_cost"]),
                )
                assert tuple(values) == expected_values, (
                    f"Expected the KPI values to render the analytics response faithfully "
                    f"{expected_values}, got {tuple(values)}"
                )

            with allure.step("Step 7 — Verify no console errors were logged throughout"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
