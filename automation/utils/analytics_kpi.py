"""Shared oracle for the Analytics Overview KPI cards (ELITEA-2314..2319).

The Overview tab's eight KPI cards are asserted by two specs — the date-preset
/ custom-range controls (`test_analytics_date_filter_controls.py`) and the
content-refresh walk (`test_analytics_date_filter_content_refresh.py`). Both
compare the RENDERED card text against the values the product's own analytics
response carried for the range under test (`.agents/testing.md` § Fidelity
policy → "How to test a NONDETERMINISTIC producer without substituting it"),
so the display-format mirror below lives here once instead of in each spec.
"""

#: The Overview KPI cards in DOM order, paired with the response field each one
#: renders (`AnalyticsOverview.jsx`). COST is the ninth-but-eighth card and is
#: handled separately — it is formatted by `fmtCost`, whose seven magnitude
#: branches are deliberately NOT mirrored here (see `assert_overview_kpi_cards_match`).
OVERVIEW_KPI_FIELDS = (
    ("TEAM", "unique_users"),
    ("AI ACTIVE", "ai_active_users"),
    ("LLM CALLS", "llm_calls"),
    ("TOOL RUNS", "tool_runs"),
    ("CHAT MSG", "chat_msgs"),
    ("AGENT & PIPELINE RUNS", "agent_runs"),
    ("TOKENS", "total_tokens"),
)

#: Total cards the live Overview renders (the TMS case texts say six — stale).
OVERVIEW_KPI_CARD_COUNT = 8


def fmt_num(value) -> str:
    """Mirror of `AnalyticCommonHelpers.fmtNum` (`analyticsCommon.helpers.js`).

    Four lines of display contract — ``>=1e6 -> "{x}M"``, ``>=1e3 -> "{x}K"``,
    ``None -> "-"`` — applied to the value the SYSTEM returned, so the expected
    string is derived from the real response rather than hand-written.
    """
    if value is None:
        return "-"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def assert_overview_kpi_cards_match(rendered: list[str], kpis: dict, label: str) -> None:
    """Assert the 8 rendered KPI values equal what *kpis* carried.

    *rendered* is `AnalyticsPage.get_overview_kpi_values()` (DOM order);
    *kpis* is the captured response body's ``kpis`` object; *label* names the
    range under test so a failure says which one drifted.

    The COST card is asserted on its currency shape and its zero/non-zero
    branch rather than an exact string: `fmtCost` has seven magnitude branches
    whose mirror would be test-authored precision, not product evidence.
    """
    assert len(rendered) == OVERVIEW_KPI_CARD_COUNT, (
        f"{label}: expected {OVERVIEW_KPI_CARD_COUNT} Overview KPI cards "
        f"(case text says 6 — stale), got {len(rendered)}"
    )
    for index, (kpi_label, field) in enumerate(OVERVIEW_KPI_FIELDS):
        expected = fmt_num(kpis.get(field))
        assert rendered[index] == expected, (
            f"{label}: KPI {kpi_label!r} rendered {rendered[index]!r}, but the response's "
            f"kpis.{field} = {kpis.get(field)!r} formats to {expected!r}"
        )

    cost_rendered = rendered[OVERVIEW_KPI_CARD_COUNT - 1]
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
