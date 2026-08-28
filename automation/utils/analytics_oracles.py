"""Shared oracles for the Analytics date-filter cases (ELITEA-2314..2319).

Three specs assert the same Analytics surfaces under different ranges — the
preset / custom-range controls (``test_analytics_date_filter_controls.py``) and
the content-refresh walk (``test_analytics_date_filter_content_refresh.py``).
Every oracle here compares the RENDERED DOM against the values the product's
own analytics response carried for the range under test
(`.agents/testing.md` § Fidelity policy -> "How to test a NONDETERMINISTIC
producer without substituting it"): nothing is stubbed, intercepted or
hand-written, the captured body is the oracle.

They live here rather than in one spec so the three specs cannot drift apart in
assertion STRENGTH. That drift is what two review rounds on this unit were
spent on: the Tools chart was asserted on data while the Agents bar chart was
not, and the 30d branch of a chart check was stronger than the 7d branch of the
same check. A shared oracle makes "another chart / preset with the same
weakness" impossible to leave behind.
"""

from datetime import date

from utils.analytics_format import fmt_cost, fmt_num

#: The Overview KPI cards in DOM order, paired with the response field each one
#: renders and the formatter the product applies (`AnalyticsOverview.jsx`).
OVERVIEW_KPI_FIELDS = (
    ("TEAM", "unique_users", fmt_num),
    ("AI ACTIVE", "ai_active_users", fmt_num),
    ("LLM CALLS", "llm_calls", fmt_num),
    ("TOOL RUNS", "tool_runs", fmt_num),
    ("CHAT MSG", "chat_msgs", fmt_num),
    ("AGENT & PIPELINE RUNS", "agent_runs", fmt_num),
    ("TOKENS", "total_tokens", fmt_num),
    ("COST", "total_llm_cost", fmt_cost),
)

#: Total cards the live Overview renders (the TMS case texts say six — stale).
OVERVIEW_KPI_CARD_COUNT = 8

#: How many days of X-axis span recharts may swallow on a thinned DATE axis.
#: Measured 2026-08-28 (project 399): a 29-day `chat_daily` series rendered a
#: 28-day span, so 10 is generous while still catching a chart frozen on a
#: 24h range (1-day span).
CHART_TICK_EDGE_SLACK_DAYS = 10

#: Both bar charts (`AnalyticsAgents.jsx`, `AnalyticsTools.jsx`) chart
#: `rows.slice(0, 20)`.
CHART_MAX_SERIES = 20


def response_dates(body: dict, field: str) -> list[str]:
    """The full ``"YYYY-MM-DD"`` dates *body* carried under *field*."""
    return [entry["date"][:10] for entry in (body.get(field) or [])]


def _label_index(dates: list[str], what: str) -> dict[str, str]:
    """Map each rendered ``"MM-DD"`` label back to its full ISO date.

    Recharts renders ``date.slice(5)``, so the label alone is year-less. The
    pairing is only well-defined while the series stays under a year: a longer
    range would put two ISO dates behind one label and silently pick a winner.
    That is a wrong ANSWER rather than a failure, so it is rejected outright.
    """
    index: dict[str, str] = {}
    for full in dates:
        label = full[5:]
        if label in index and index[label] != full:
            raise AssertionError(
                f"{what}: the response's series covers more than a year "
                f"({index[label]} and {full} both render as {label!r}), so a rendered "
                "tick cannot be paired to one date — this oracle needs a sub-year range"
            )
        index[label] = full
    return index


def chart_tick_span_days(ticks: list[str], dates: list[str], what: str) -> int:
    """Calendar days between the first and last rendered X-axis tick.

    Recharts renders the labels YEAR-LESS (``"MM-DD"``), so each one is resolved
    back to the full ``"YYYY-MM-DD"`` date the RESPONSE carried before the two
    are differenced. Differencing the bare ``"MM-DD"`` parts is wrong across a
    year boundary: a Last-30d window run on e.g. 2027-01-10 renders 12-11…01-10,
    which month-arithmetic scores as ``(1-12)*30 + (10-11) = -331`` days,
    failing every span assertion deterministically for the ~30 days after New
    Year. Anchoring on the response also keeps the derivation on the system's
    own payload rather than on a calendar the test computed for itself.
    """
    assert ticks, f"{what} rendered no X-axis ticks"
    by_label = _label_index(dates, what)
    unknown = [tick for tick in (ticks[0], ticks[-1]) if tick not in by_label]
    assert not unknown, (
        f"{what}: rendered ticks {unknown} have no matching date in the response's own "
        f"series {dates}"
    )
    first = date.fromisoformat(by_label[ticks[0]])
    last = date.fromisoformat(by_label[ticks[-1]])
    return (last - first).days


def data_span_days(dates: list[str]) -> int:
    """Calendar days the response's own series covers (order-independent)."""
    parsed = [date.fromisoformat(value) for value in dates]
    return (max(parsed) - min(parsed)).days


def assert_date_chart_matches(ticks: list[str], dates: list[str], what: str) -> int:
    """A thinned DATE axis (`AreaChart`) renders THIS range's series.

    Presence is not "the chart updated its data": a chart frozen on the previous
    range's series is still exactly one container. These three checks together
    are what a stale chart fails —

    * every rendered tick is one of the response's own dates (no invented days),
    * the last tick is the series' last date (the axis reaches the new range),
    * the rendered span is within the thinning slack of the data's own span.

    Neither `AnalyticsOverview.jsx`'s Daily Activity chart nor
    `AnalyticsAgents.jsx`'s Chat Messages chart sets ``interval={0}``, so
    recharts THINS the labels and exact list equality is NOT available here —
    unlike the two bar charts (see :func:`assert_category_chart_matches`).

    Returns the rendered span so a caller can compare two ranges.
    """
    labels = [value[5:] for value in dates]
    assert set(ticks) <= set(labels), (
        f"{what} rendered X ticks {ticks} that are not a subset of the response's own "
        f"series {labels}"
    )
    assert ticks and ticks[-1] == labels[-1], (
        f"{what}: last rendered tick {ticks[-1:]!r} should be the response's last "
        f"date {labels[-1]!r} — an axis stopping short is a chart drawing an older range"
    )
    rendered_span = chart_tick_span_days(ticks, dates, what)
    covered = data_span_days(dates)
    assert rendered_span >= covered - CHART_TICK_EDGE_SLACK_DAYS, (
        f"{what}: the axis spans {rendered_span} days while the response's series covers "
        f"{covered} — the chart is not drawing THIS range's series "
        f"(ticks {ticks}, response dates {labels})"
    )
    return rendered_span


def assert_category_chart_matches(ticks: list[str], expected_names: list[str], what: str) -> None:
    """A CATEGORY axis with ``interval={0}`` equals the charted series, in order.

    Both bar charts — `AnalyticsAgents.jsx`'s "Most Active Agents & Pipelines"
    (``dataKey="name"``) and `AnalyticsTools.jsx`'s "Most Popular Tools"
    (``dataKey="tool_name"``) — set ``interval={0}``, so recharts does NOT thin:
    every charted series renders exactly one tick. Exact ordered equality is
    therefore available and is strictly stronger than the date axes' subset +
    span reasoning — a stale chart is caught by length alone, with no slack
    constant to tune.
    """
    assert ticks == expected_names, (
        f"{what}: the chart's X axis renders {ticks} while this response's charted "
        f"series is {expected_names} — the chart is not drawing THIS range's data"
    )


def assert_overview_kpi_cards_match(rendered: list[str], kpis: dict, label: str) -> None:
    """Assert all 8 rendered KPI values equal what *kpis* carried.

    *rendered* is ``AnalyticsPage.get_overview_kpi_values()`` (DOM order);
    *kpis* is the captured response body's ``kpis`` object; *label* names the
    range under test so a failure says which one drifted.

    Every card — COST included — is compared to the response value passed
    through the product's own formatter. An earlier round asserted COST on its
    currency shape and zero/non-zero branch only, on the grounds that mirroring
    ``fmtCost``'s magnitude branches would be "test-authored precision". That
    reasoning does not hold: :func:`fmt_cost` is a mirror of the renderer
    applied to the SYSTEM's value, exactly like :func:`fmt_num` already was for
    the other seven, and the weaker form let a wrong non-zero cost pass.
    """
    assert len(rendered) == OVERVIEW_KPI_CARD_COUNT, (
        f"{label}: expected {OVERVIEW_KPI_CARD_COUNT} Overview KPI cards "
        f"(case text says 6 — stale), got {len(rendered)}"
    )
    for index, (kpi_label, field, formatter) in enumerate(OVERVIEW_KPI_FIELDS):
        expected = formatter(kpis.get(field))
        assert rendered[index] == expected, (
            f"{label}: KPI {kpi_label!r} rendered {rendered[index]!r}, but the response's "
            f"kpis.{field} = {kpis.get(field)!r} formats to {expected!r}"
        )


def assert_overview_content_matches(analytics_page, body: dict, label: str) -> None:
    """Every Overview surface renders what *body* carried for its range.

    KPI cards, the "Top 5 AI Adopters" leaderboard (count, conditional
    container, and the top row's own content) and the Model Usage Breakdown
    (count + the null-for-empty branch). Shared by all three specs so no range
    is checked more weakly than another.
    """
    assert_overview_kpi_cards_match(
        analytics_page.get_overview_kpi_values(), body.get("kpis") or {}, label
    )

    adopters = body.get("top_ai_users") or []
    rendered_rows = analytics_page.get_leaderboard_row_count()
    assert rendered_rows == len(adopters), (
        f"{label}: leaderboard rendered {rendered_rows} rows, the response carried "
        f"{len(adopters)}"
    )
    assert analytics_page.overview_leaderboard.count() == (1 if adopters else 0), (
        f"{label}: the leaderboard container must be present iff the response has adopters"
    )
    if adopters:
        top = adopters[0]
        first_row = analytics_page.get_leaderboard_row_text(0)
        assert str(top.get("user_email")) in first_row, (
            f"{label}: first leaderboard row {first_row!r} does not carry the response's top "
            f"adopter {top.get('user_email')!r}"
        )
        assert fmt_num(top.get("ai_events")) in first_row, (
            f"{label}: first leaderboard row {first_row!r} does not carry the response's top "
            f"score {top.get('ai_events')!r}"
        )

    models = body.get("models") or []
    rendered_models = analytics_page.get_model_usage_row_count()
    assert rendered_models == len(models), (
        f"{label}: Model Usage Breakdown rendered {rendered_models} rows, the response "
        f"carried {len(models)}"
    )
    assert analytics_page.overview_model_usage_table.count() == (1 if models else 0), (
        f"{label}: the Model Usage Breakdown card must be present iff the response has models "
        "(the component returns null for an empty list)"
    )
