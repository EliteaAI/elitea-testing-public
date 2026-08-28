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
2. ``_chart_tick_span_days()`` differenced YEAR-LESS ``"MM-DD"`` tick labels,
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

Guards 3, 4 and 5 are the same doc-sync-vs-code shape as
``test_project_context_2272_afs_route_matches_page_object.py``.
"""

import ast
from datetime import date, timedelta
from pathlib import Path

import pytest
from pages.analytics_page import AnalyticsPage

from tests.ui.admin.test_analytics_date_filter_content_refresh import (
    _chart_tick_span_days,
    _data_span_days,
)

TESTS_UNIT_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = TESTS_UNIT_DIR.parent.parent  # .../automation
REPO_ROOT = AUTOMATION_DIR.parent  # .../elitea-testing-public

ADMIN_TESTS_DIR = AUTOMATION_DIR / "tests" / "ui" / "admin"
CONTROLS_SPEC = ADMIN_TESTS_DIR / "test_analytics_date_filter_controls.py"
CONTENT_SPEC = ADMIN_TESTS_DIR / "test_analytics_date_filter_content_refresh.py"

AFS_DIR = REPO_ROOT / "test-specs" / "settings-analytics"
AFS_2315 = AFS_DIR / "l2_custom-date-range-filters-data_ELITEA-2315.md"
AFS_2318 = AFS_DIR / "l2_preset-switch-updates-tab-content_ELITEA-2318.md"


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
    span = _chart_tick_span_days(ticks, response_dates, "year-boundary chart")

    assert span == 30, (
        f"Expected a 30-day span across the year boundary, got {span}. The pre-fix "
        "month arithmetic scored (1-12)*30 + (10-11) = -331 here, which failed "
        "ELITEA-2317's `span_30d >= 20` assertion deterministically every January."
    )
    assert _data_span_days(response_dates) == 30


def test_chart_tick_span_within_one_year_is_unchanged():
    """The ordinary (same-year) case still measures calendar days."""
    response_dates = [(date(2026, 7, 31) + timedelta(days=n)).isoformat() for n in range(29)]
    assert _chart_tick_span_days(["07-31", "08-28"], response_dates, "chart") == 28


def test_chart_tick_span_rejects_a_tick_the_response_never_carried():
    """A tick outside the response's own series is a failure, not a guess.

    This is what makes the helper a fidelity oracle: the span is derived from
    the system's payload, so a chart drawing dates the response never returned
    fails loudly instead of being silently date-mathed.
    """
    with pytest.raises(AssertionError, match="no matching date in the response"):
        _chart_tick_span_days(["01-01", "01-05"], ["2026-08-01", "2026-08-02"], "chart")


def test_2315_spec_asserts_the_kpi_values_its_afs_promises():
    """ELITEA-2315's AFS step 7 claims the 8 KPI values are matched — so assert them."""
    afs = AFS_2315.read_text(encoding="utf-8")
    assert "KPI values" in afs, (
        "ELITEA-2315's AFS no longer promises a KPI-value assertion. If the coverage "
        "claim was dropped, the Coverage Map row must change with it (doc-sync)."
    )
    spec = CONTROLS_SPEC.read_text(encoding="utf-8")
    assert "assert_overview_kpi_cards_match" in spec, (
        "ELITEA-2315's AFS Coverage Map row 7 states the 8 KPI values are matched "
        "against the captured response body, but the spec asserts no KPI value. Paper "
        "that over-claims its code is the review finding this pins."
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
    assert "get_tools_chart_tick_labels" in spec, (
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
    for name in ("tools_chart_container", "tools_chart_subtitle", "get_tools_chart_tick_labels"):
        assert name in declared, f"AnalyticsPage is missing {name!r}"
