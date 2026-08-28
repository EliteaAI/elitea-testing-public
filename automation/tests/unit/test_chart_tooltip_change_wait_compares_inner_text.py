"""Regression test for `AnalyticsPage.wait_for_chart_tooltip_change()`'s
comparison basis (PR #1956, review round 1 — ELITEA-2326/2327/2328/2329).

The helper is the settle wait every "move to a second data point" step relies
on: Recharts re-renders the shared `ChartTooltip` a tick after the mousemove
lands, so a caller that reads `inner_text()` straight away can still see the
PREVIOUS point. It waited with::

    expect(tooltip).not_to_have_text(" ".join(previous_lines))

which is a **no-op**. Playwright's text matchers read an element the
`textContent` way by default, and the tooltip's lines are separate child nodes,
so the browser-side text is ``"Aug 12LLM Calls: 3"`` — no separator anywhere —
while `previous_lines` came from `inner_text()` and is re-joined with spaces
(``"Aug 12 LLM Calls: 3"``). Those two strings can never be equal, so the
NEGATIVE assertion was satisfied on its very first poll and the helper returned
before the tooltip had changed at all. Nothing goes red when a wait silently
stops waiting — it degrades into a race — which is exactly why it needs a
static/unit guard rather than a live one.

The fix is `use_inner_text=True`, so both sides of the comparison originate
from `innerText` and Playwright's own whitespace normalisation collapses its
newlines to the single spaces the helper joins with.

These tests drive the real helper against a fake locator + a fake `expect()`
that reproduces the two text views Playwright exposes for one element, and the
retry loop it runs. The behavioural test below FAILS on the pre-fix code
(the helper returns the stale render) and passes on the fixed code.
"""

import pytest
from pages.analytics_page import AnalyticsPage

#: What the tooltip shows before and after the mouse moves to a second point.
STALE_LINES = ["Aug 12", "LLM Calls: 3", "Tool Runs: 1"]
FRESH_LINES = ["Aug 19", "LLM Calls: 42", "Tool Runs: 7"]

#: How many retry polls the fake element keeps rendering the stale point for —
#: i.e. the re-render lag the helper exists to absorb.
POLLS_BEFORE_RERENDER = 2


def _normalize(text: str) -> str:
    """Playwright normalises whitespace when a text matcher is given a string."""
    return " ".join(text.split())


class _FakeTooltip:
    """Stand-in for the tooltip `Locator`, exposing BOTH text views.

    `inner_text()` is the `innerText` view (newline between the tooltip's child
    lines, which is what `read_chart_tooltip_lines` parses). `_playwright_text`
    is what an `expect(...)` text matcher reads: `textContent`-style with **no**
    separator by default, `innerText` when `use_inner_text=True`.
    """

    def __init__(self):
        self.polls = 0
        self.wait_for_calls = 0

    @property
    def _lines(self) -> list[str]:
        return FRESH_LINES if self.polls >= POLLS_BEFORE_RERENDER else STALE_LINES

    def wait_for(self, **_kwargs) -> None:
        self.wait_for_calls += 1

    def inner_text(self) -> str:
        # A real tooltip line can carry incidental padding whitespace.
        return "\n".join(f"  {line}  " for line in self._lines)

    def _playwright_text(self, use_inner_text: bool) -> str:
        """One retry poll of a Playwright text matcher — advances the clock."""
        self.polls += 1
        if use_inner_text:
            return self.inner_text()
        return "".join(self._lines)  # textContent: children concatenated, no separator


class _FakeAssertions:
    """The slice of `LocatorAssertions` this helper uses, with a real retry loop."""

    MAX_POLLS = 20

    def __init__(self, locator: _FakeTooltip, recorder: dict):
        self._locator = locator
        self._recorder = recorder

    def not_to_have_text(self, expected, *, use_inner_text=None, timeout=None, **_kwargs):
        self._recorder["use_inner_text"] = use_inner_text
        self._recorder["timeout"] = timeout
        self._recorder["expected"] = expected
        for _ in range(self.MAX_POLLS):
            actual = self._locator._playwright_text(bool(use_inner_text))
            if _normalize(actual) != _normalize(expected):
                return
        raise AssertionError(
            f"fake not_to_have_text timed out: text stayed {expected!r} for {self.MAX_POLLS} polls"
        )


@pytest.fixture
def tooltip_and_expect(monkeypatch):
    """Install the fake `expect` into the page-object module and hand back the
    fake locator plus the recorder of the arguments the helper passed."""
    locator = _FakeTooltip()
    recorder: dict = {}
    monkeypatch.setattr(
        "pages.analytics_page.expect", lambda target: _FakeAssertions(target, recorder)
    )
    return locator, recorder


@pytest.fixture
def analytics_page() -> AnalyticsPage:
    """The helper under test touches no instance state, so an uninitialised
    instance is enough (and keeps this a unit test — no browser, no network)."""
    return AnalyticsPage.__new__(AnalyticsPage)


def test_textcontent_and_innertext_views_can_never_match(tooltip_and_expect):
    """Documents the mechanism the bug rode on: the joined `previous_lines`
    string matches the element's `innerText` view and CANNOT match its
    `textContent` view, because the tooltip's lines are separate child nodes."""
    locator, _ = tooltip_and_expect
    expected = " ".join(STALE_LINES)

    assert _normalize(locator._playwright_text(use_inner_text=True)) == expected
    assert _normalize(locator._playwright_text(use_inner_text=False)) != expected


def test_wait_returns_only_after_the_tooltip_actually_re_rendered(
    analytics_page, tooltip_and_expect
):
    """The regression: pre-fix the helper returned on the first poll and handed
    back the STALE render (`STALE_LINES`), because the negative assertion was
    trivially satisfied. It must return the point the tooltip changed TO."""
    locator, _ = tooltip_and_expect

    lines = analytics_page.wait_for_chart_tooltip_change(locator, list(STALE_LINES))

    assert lines == FRESH_LINES, (
        "wait_for_chart_tooltip_change returned before the tooltip re-rendered — "
        f"got {lines!r}, which is the render it was told had already been read"
    )
    assert locator.polls >= POLLS_BEFORE_RERENDER, (
        "the wait did not actually retry: it returned after "
        f"{locator.polls} poll(s), before the fake tooltip re-rendered"
    )


def test_wait_compares_against_the_inner_text_view(analytics_page, tooltip_and_expect):
    """Pins the specific argument that makes the comparison real, so a future
    edit that drops it fails here with a message naming the reason."""
    locator, recorder = tooltip_and_expect

    analytics_page.wait_for_chart_tooltip_change(locator, list(STALE_LINES))

    assert recorder["use_inner_text"] is True, (
        "not_to_have_text must be called with use_inner_text=True — without it "
        "Playwright compares against the separator-less textContent view and the "
        "space-joined expectation can never match, making the wait a no-op"
    )
    assert recorder["expected"] == " ".join(STALE_LINES)


def test_read_chart_tooltip_lines_strips_and_drops_blank_lines(analytics_page, tooltip_and_expect):
    """The lines the helper returns are compared verbatim against values derived
    from the captured analytics response, so incidental padding must not leak
    into them — and must not desync them from the joined wait expectation."""
    locator, _ = tooltip_and_expect

    assert analytics_page.read_chart_tooltip_lines(locator) == STALE_LINES
    assert locator.wait_for_calls == 1, "read_chart_tooltip_lines must wait for visibility first"
