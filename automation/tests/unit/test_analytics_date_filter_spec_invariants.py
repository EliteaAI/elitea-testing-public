"""Regression guards for the ELITEA-2314..2319 analytics date-filter specs
(review round 1, fix round 1).

Four blocking findings from the fresh-session review, each pinned here so the
same class of defect fails in milliseconds instead of surviving to a live gate:

1. ``AnalyticsPage.wait_for_tab_settled()`` was called five times by
   ``test_analytics_date_filter_content_refresh.py`` and defined nowhere — a
   pure ``AttributeError`` at run time that no static reading of the spec
   catches, and proof that the fix round which introduced the call sites was
   never executed. ``test_specs_only_call_page_object_members_that_exist``
   walks both specs' ASTs and checks every ``analytics_page.<attr>`` against
   ``AnalyticsPage``'s real MRO members.
2. ``chart_tick_span_days()`` differenced YEAR-LESS ``"MM-DD"`` tick labels,
   which goes large-negative across a year boundary (a Last-30d window on
   2027-01-10 scored -331 days), so ELITEA-2317's ``span_30d >= 20`` assertion
   would have failed deterministically for the ~30 days after every New Year.
3. ELITEA-2315's AFS (Coverage Map row 7 + step 7) promises the 8 KPI values
   are matched against the captured response; the shipped spec asserted only
   row counts and chart ticks.
4. ELITEA-2318's case steps 2 and 4 ("note the Chat Messages chart data",
   "verify both charts update their data") were satisfied by a PRESENCE check
   only, which a chart frozen on the previous range's series passes unchanged.

Round 2 added a fifth, the same class as 4:

5. ELITEA-2318's case step 6 ("repeat the steps for the Users and Tools tabs")
   repeats steps 2/4/5, which include chart data — and the Tools tab has a
   "Most Popular Tools" ``BarChart`` of its own. It was neither asserted nor
   declared out of scope, while the AFS disposed the row as a bare
   ``asserted``. ``test_2318_spec_asserts_the_tools_chart_data`` pins the
   assertion and its AFS row together.

Round 3 swept the whole unit for the SAME weakness rather than the one
instance reported, and added four more:

6. ELITEA-2318's "Most Active Agents & Pipelines" BarChart was asserted on
   presence + its ``Top {N} by runs`` subtitle only — neither of which moves
   when the chart is frozen on the previous range (two ranges routinely chart
   the same NUMBER of agents). It has ``interval={0}``, so exact ordered tick
   equality is available, exactly as for the Tools chart in guard 5.
7. ELITEA-2317 asserted its Daily Activity chart on DATA under ``Last 30d`` but
   computed-and-discarded the same span under ``Last 7d`` — one preset covered,
   its sibling not.
8. ELITEA-2314's docstring and all four step titles claim "content re-renders",
   while the spec asserted only the request. A refetch whose result never
   reached the DOM passed.
9. ELITEA-2315's COST card was asserted on currency shape + zero/non-zero
   branch, so any wrong non-zero cost passed. ``fmtCost`` is as mirrorable as
   ``fmtNum``, which the other seven cards already use.

Guards 3, 4 and 5 are the same doc-sync-vs-code shape as
``test_project_context_2272_afs_route_matches_page_object.py``.
"""

import ast
from datetime import date, timedelta
from pathlib import Path

import pytest
from pages.analytics_page import AnalyticsPage
from utils.analytics_format import fmt_cost, fmt_num
from utils.analytics_oracles import chart_tick_span_days, data_span_days

TESTS_UNIT_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = TESTS_UNIT_DIR.parent.parent  # .../automation
REPO_ROOT = AUTOMATION_DIR.parent  # .../elitea-testing-public

ADMIN_TESTS_DIR = AUTOMATION_DIR / "tests" / "ui" / "admin"
CONTROLS_SPEC = ADMIN_TESTS_DIR / "test_analytics_date_filter_controls.py"
CONTENT_SPEC = ADMIN_TESTS_DIR / "test_analytics_date_filter_content_refresh.py"

AFS_DIR = REPO_ROOT / "test-specs" / "settings-analytics"
AFS_2315 = AFS_DIR / "l2_custom-date-range-filters-data_ELITEA-2315.md"
AFS_2318 = AFS_DIR / "l2_preset-switch-updates-tab-content_ELITEA-2318.md"
AFS_2314 = AFS_DIR / "l2_date-presets-update-pickers-and-content_ELITEA-2314.md"


def _declared_members(cls) -> set[str]:
    """Every name declared anywhere in *cls*'s MRO.

    Read from each class's ``__dict__`` rather than via ``hasattr``: the page
    object's locators are ``LocatorDescriptor`` instances, and touching them on
    the CLASS would run descriptor code instead of answering "is this name
    defined?".
    """
    names: set[str] = set()
    for klass in cls.__mro__:
        names |= set(vars(klass))
    return names


def _page_object_attributes(spec_path: Path, variable: str = "analytics_page") -> set[str]:
    """Names the spec reads off its ``analytics_page`` instance."""
    tree = ast.parse(spec_path.read_text(encoding="utf-8"))
    return {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == variable
    }


@pytest.mark.parametrize("spec_path", [CONTROLS_SPEC, CONTENT_SPEC], ids=lambda p: p.name)
def test_specs_only_call_page_object_members_that_exist(spec_path):
    """Every ``analytics_page.<attr>`` the specs use must be defined."""
    declared = _declared_members(AnalyticsPage)
    used = _page_object_attributes(spec_path)
    missing = sorted(used - declared)
    assert not missing, (
        f"{spec_path.name} calls AnalyticsPage members that do not exist: {missing}. "
        "This is an AttributeError at run time — a spec in this state cannot have been "
        "run green, whatever the Run Report says."
    )


def test_specs_actually_exercise_the_page_object():
    """Guard the guard: an empty attribute set would make it vacuously pass."""
    assert len(_page_object_attributes(CONTENT_SPEC)) > 10
    assert len(_page_object_attributes(CONTROLS_SPEC)) > 10


def test_chart_tick_span_is_correct_across_a_year_boundary():
    """A 30-day window straddling New Year must score ~30 days, not negative."""
    first = date(2026, 12, 11)
    response_dates = [(first + timedelta(days=n)).isoformat() for n in range(31)]
    assert response_dates[-1] == "2027-01-10"

    # What recharts renders after thinning: the first and last labels, year-less.
    ticks = ["12-11", "12-21", "01-01", "01-10"]
    span = chart_tick_span_days(ticks, response_dates, "year-boundary chart")

    assert span == 30, (
        f"Expected a 30-day span across the year boundary, got {span}. The pre-fix "
        "month arithmetic scored (1-12)*30 + (10-11) = -331 here, which failed "
        "ELITEA-2317's `span_30d >= 20` assertion deterministically every January."
    )
    assert data_span_days(response_dates) == 30


def test_chart_tick_span_within_one_year_is_unchanged():
    """The ordinary (same-year) case still measures calendar days."""
    response_dates = [(date(2026, 7, 31) + timedelta(days=n)).isoformat() for n in range(29)]
    assert chart_tick_span_days(["07-31", "08-28"], response_dates, "chart") == 28


def test_chart_tick_span_rejects_a_tick_the_response_never_carried():
    """A tick outside the response's own series is a failure, not a guess.

    This is what makes the helper a fidelity oracle: the span is derived from
    the system's payload, so a chart drawing dates the response never returned
    fails loudly instead of being silently date-mathed.
    """
    with pytest.raises(AssertionError, match="no matching date in the response"):
        chart_tick_span_days(["01-01", "01-05"], ["2026-08-01", "2026-08-02"], "chart")


def test_2315_spec_asserts_the_kpi_values_its_afs_promises():
    """ELITEA-2315's AFS step 7 claims the 8 KPI values are matched — so assert them."""
    afs = AFS_2315.read_text(encoding="utf-8")
    assert "KPI values" in afs, (
        "ELITEA-2315's AFS no longer promises a KPI-value assertion. If the coverage "
        "claim was dropped, the Coverage Map row must change with it (doc-sync)."
    )
    spec = CONTROLS_SPEC.read_text(encoding="utf-8")
    assert "assert_overview_content_matches" in spec, (
        "ELITEA-2315's AFS Coverage Map row 7 states the 8 KPI values are matched "
        "against the captured response body, but the spec asserts no KPI value. Paper "
        "that over-claims its code is the review finding this pins. (The KPI oracle is "
        "reached through `assert_overview_content_matches`, which calls "
        "`assert_overview_kpi_cards_match` — pinned by "
        "`test_cost_card_is_asserted_on_value_not_only_on_shape`.)"
    )


def test_2318_spec_asserts_chat_chart_data_not_only_presence():
    """ELITEA-2318's case steps 2/4 are about the chart's DATA, not its existence."""
    spec = CONTENT_SPEC.read_text(encoding="utf-8")
    assert "get_agents_chat_chart_tick_labels" in spec, (
        "The Chat Messages chart is asserted by presence only — a chart frozen with the "
        "previous range's series renders exactly one container and would pass case "
        "step 4 unchanged. Assert its rendered axis against the response's chat_daily."
    )
    afs = AFS_2318.read_text(encoding="utf-8")
    assert "chat_daily" in afs and "tick" in afs.lower(), (
        "ELITEA-2318's AFS must describe the chat-chart data assertion the spec now "
        "makes (doc-sync: the paper states the shipped truth)."
    )


def test_2318_spec_asserts_the_tools_chart_data():
    """Case step 6 repeats steps 2/4/5 — and the Tools tab has a chart too.

    The round-2 finding: the "Most Popular Tools" BarChart
    (``AnalyticsTools.jsx``, rendered on ``toolChartData.length > 0``) was
    neither asserted nor declared out of scope, while the AFS disposed case
    step 6 as a bare ``asserted``. Presence alone would not be enough either —
    same reasoning as guard 4 — so the tick reader is what this pins.
    """
    spec = CONTENT_SPEC.read_text(encoding="utf-8")
    assert "get_tools_chart_x_axis_labels" in spec, (
        "The Tools tab's 'Most Popular Tools' chart is not asserted on its data. Case "
        "step 6 repeats steps 2/4/5, which include chart data, so the tab's own chart "
        "must be compared to that tab's own response — not skipped, and not checked by "
        "presence alone (a chart frozen on the previous range renders identically)."
    )
    assert "assert_tools_chart_matches" in spec, (
        "The Tools-chart oracle is gone; step 6b must call it under BOTH presets."
    )

    afs = AFS_2318.read_text(encoding="utf-8")
    assert "Most Popular Tools" in afs and "tool_name" in afs, (
        "ELITEA-2318's AFS must describe the Tools-chart data assertion the spec now "
        "makes (doc-sync: the paper states the shipped truth)."
    )
    assert "no chart" in afs, (
        "The AFS must say explicitly that the Users tab renders no chart — an "
        "un-asserted surface has to be DECLARED out of scope, not left implicit."
    )


def test_tools_chart_locators_exist_on_the_page_object():
    """The round-2 fix needed two new testids — pin them like any other member."""
    declared = _declared_members(AnalyticsPage)
    for name in ("tools_chart_container", "tools_chart_subtitle", "get_tools_chart_x_axis_labels"):
        assert name in declared, f"AnalyticsPage is missing {name!r}"


def test_2318_spec_asserts_the_agents_bar_chart_data():
    """Round-3 finding: the Agents tab has TWO charts, only one was on data.

    Case steps 2 and 4 name "the Chat Messages chart and Most Active Agents bar
    chart" and "both charts update their data". The bar chart was covered by
    presence + subtitle, and neither detects a stale render — a frozen chart is
    still one container, and two ranges very often chart the same NUMBER of
    agents while charting different ones.
    """
    spec = CONTENT_SPEC.read_text(encoding="utf-8")
    assert "get_agents_chart_x_axis_labels" in spec, (
        "The 'Most Active Agents & Pipelines' chart is not asserted on its data. Its "
        "XAxis has interval={0}, so the rendered tick list equals the response's charted "
        "names in order — presence and a series COUNT are both invariant under staleness."
    )
    assert "entity_name" in spec, (
        "The expected tick list must be derived from the response's own rows "
        "(`entity_name or f'Agent #{entity_id}'`, mirroring AnalyticsAgents.jsx)."
    )
    afs = AFS_2318.read_text(encoding="utf-8")
    assert "Most Active Agents" in afs and "entity_name" in afs, (
        "ELITEA-2318's AFS must describe the bar-chart data assertion the spec now makes."
    )


def test_2317_asserts_both_presets_charts_not_just_the_wider_one():
    """Round-3 finding: the 7d branch computed a span and asserted nothing."""
    spec = CONTENT_SPEC.read_text(encoding="utf-8")
    assert spec.count("assert_date_chart_matches") >= 2, (
        "ELITEA-2317 must run the same chart-data oracle under BOTH presets. Asserting "
        "the 30-day chart on data while the 7-day chart gets presence only is the same "
        "asymmetry class as the two-chart finding above."
    )


def test_2314_asserts_the_content_it_claims_to_refresh():
    """Round-3 finding: 'content re-renders' was narration, not assertion."""
    spec = CONTROLS_SPEC.read_text(encoding="utf-8")
    assert "assert_overview_content_matches" in spec, (
        "ELITEA-2314's docstring and every step title say the content re-renders, but "
        "only the REQUEST was asserted — a refetch whose result never reached the DOM "
        "passed all four presets."
    )
    afs = AFS_2314.read_text(encoding="utf-8")
    assert "Overview content" in afs, (
        "ELITEA-2314's AFS must record the content assertions the spec now makes."
    )


def test_cost_card_is_asserted_on_value_not_only_on_shape():
    """Round-3 finding: COST was the one KPI card without a value assertion."""
    from utils.analytics_oracles import OVERVIEW_KPI_FIELDS

    fields = {field: formatter for _, field, formatter in OVERVIEW_KPI_FIELDS}
    assert len(OVERVIEW_KPI_FIELDS) == 8, (
        f"All 8 Overview KPI cards must have an oracle row, got {len(OVERVIEW_KPI_FIELDS)}"
    )
    assert fields.get("total_llm_cost") is fmt_cost, (
        "The COST card must be asserted against fmt_cost(response value), not on its "
        "currency shape and zero/non-zero branch alone — that weaker form passes any "
        "wrong non-zero cost."
    )


def test_fmt_cost_mirrors_the_products_own_branches():
    """Every `fmtCost` branch, including the JS tie-rounding Python gets wrong."""
    assert fmt_cost(None) == "-"
    assert fmt_cost("nope") == "-"
    assert fmt_cost(0) == "$0.00"
    assert fmt_cost(0.00000012) == "$0.00000012"
    assert fmt_cost(0.005) == "$0.005000"
    assert fmt_cost(0.5) == "$0.5000"
    assert fmt_cost(12.5) == "$12.50"
    assert fmt_cost(2_500_000.0) == "$2.5M"
    assert fmt_cost(-45.678) == "-$45.68"
    # JS `toFixed` rounds a tie away from zero; Python's `:.1f` rounds half to
    # even and would render "$1.2K" here, disagreeing with the product.
    assert fmt_cost(1250.0) == "$1.3K", (
        "fmt_cost must reproduce JS toFixed's half-away-from-zero rounding"
    )
    assert fmt_num(1000) == "1.0K"


def test_chart_tick_pairing_rejects_an_ambiguous_over_a_year_series():
    """A year-less "MM-DD" label cannot address a series longer than a year.

    Today's widest preset is Last 90d so this is unreachable, but the pairing
    would silently pick one of two candidate dates rather than fail — a wrong
    answer, which is worse than a red.
    """
    dates = ["2026-08-28", "2027-08-28"]
    with pytest.raises(AssertionError, match="more than a year"):
        chart_tick_span_days(["08-28", "08-28"], dates, "over-long series")


def test_category_chart_oracle_rejects_a_stale_chart():
    """The bar-chart oracle must FAIL on the exact scenario it exists for.

    Live 2026-08-28 (project 399), the Agents bar chart charted 1 series under
    `Last 24h` and 20 wholly different ones under `Last 30d` — while
    `container.count() == 1` was identical under both. This pins that the
    replacement assertion is not a no-op.
    """
    from utils.analytics_oracles import assert_category_chart_matches

    stale = ["zzinv01431787912318"]
    fresh = ["Reflexion", "User Story Creator", "API Testing Buddy"]
    assert_category_chart_matches(fresh, fresh, "fresh chart")
    with pytest.raises(AssertionError, match="not drawing THIS range's data"):
        assert_category_chart_matches(stale, fresh, "stale chart")
    # Order is part of the contract — recharts renders the series in response
    # order, so a reordered axis is a real defect, not an equivalent rendering.
    with pytest.raises(AssertionError, match="not drawing THIS range's data"):
        assert_category_chart_matches(list(reversed(fresh)), fresh, "reordered chart")
    # Duplicate names are real in this data (six 'elitea-1735-skills-agent' rows
    # under Last 30d), so the oracle must compare LISTS, never sets.
    dupes = ["a", "a", "b"]
    with pytest.raises(AssertionError, match="not drawing THIS range's data"):
        assert_category_chart_matches(["a", "b"], dupes, "collapsed duplicates")


def test_date_chart_oracle_rejects_a_stale_narrower_range():
    """The date-axis oracle must FAIL on a chart frozen on an older range.

    A subset check ALONE passes here — the stale ticks really are a subset of
    the wider new series — which is why the last-tick and span checks exist.
    """
    from utils.analytics_oracles import assert_date_chart_matches

    thirty_days = [(date(2026, 7, 31) + timedelta(days=n)).isoformat() for n in range(30)]
    fresh_ticks = ["07-31", "08-10", "08-20", "08-29"]
    assert assert_date_chart_matches(fresh_ticks, thirty_days, "fresh chart") == 29

    stale_ticks = ["08-01", "08-02"]  # a subset of the new series, but the old range
    assert set(stale_ticks) <= {d[5:] for d in thirty_days}, "precondition: subset check passes"
    with pytest.raises(AssertionError, match="last rendered tick"):
        assert_date_chart_matches(stale_ticks, thirty_days, "stale chart")
