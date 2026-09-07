"""Pins the #2023 navigation-race contract of ``BasePage.dismiss_banner_if_present``.

**Why this is a unit test and not a UI test.** The bug is a *race*: on deployed
envs the SPA redirects right after ``domcontentloaded``, destroying the JS
execution context while the helper's ``page.evaluate`` is in flight. GHA run
``34092431538`` hit it 49 times in one job — and a local run essentially never
does, because ``auth_state`` bypasses login on localhost so no redirect fires.
A timing-dependent failure cannot be a gate, so the contract is pinned
deterministically instead: feed the helper the exact exceptions Playwright
raises and assert what it does with each.

**Fidelity note** (``.agents/testing.md`` § Fidelity policy): the stub below
replaces the *framework helper's own* Playwright call in order to pin an
error-handling contract of the framework. There is no product observable here
and no system under test being substituted — this is a framework unit test, the
established convention for ``tests/unit/`` (cf. ``test_actions.py``, which stubs
the same seam for the ``@action`` decorator).

The error strings are **verbatim from the installed Playwright 1.61.0 driver
bundle** (``playwright/driver/package/lib/coreBundle.js``), not invented:
``"Execution context was destroyed, most likely because of a navigation"``
(lines 23618/23626/35107/…) and ``"Frame was detached"`` (23573/23576). The
canonical traceback on issue #2023 shows the first one reaching pytest verbatim.
"""

import pytest
from pages.base_page import (
    NAVIGATION_RACE_ERROR_FRAGMENTS,
    BasePage,
    is_navigation_race_error,
)
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# ---------------------------------------------------------------------------
# The exact messages Playwright 1.61.0 emits for this race.
# ---------------------------------------------------------------------------
CONTEXT_DESTROYED = "Page.evaluate: Execution context was destroyed, most likely because of a navigation"
CONTEXT_DESTROYED_WORKER = "Page.evaluate: Execution context was destroyed"
FRAME_DETACHED = "Page.evaluate: Frame was detached"
NAVIGATING_FRAME_DETACHED = "Page.evaluate: Navigating frame was detached!"

RACE_MESSAGES = [
    CONTEXT_DESTROYED,
    CONTEXT_DESTROYED_WORKER,
    FRAME_DETACHED,
    NAVIGATING_FRAME_DETACHED,
]

# A real Playwright error that is NOT this race — a broken evaluate argument.
# Must propagate: swallowing it would hide a genuinely broken helper.
EVAL_SYNTAX_ERROR = (
    "Page.evaluate: SyntaxError: Unexpected token ')'\n"
    "    at eval (eval at evaluate (:234:30), <anonymous>:1:1)"
)


class _StubPage:
    """Minimal stand-in for Playwright's ``Page``, seeded with scripted outcomes.

    ``evaluate`` pops the next entry from *outcomes*: an exception instance is
    raised, anything else is returned. Everything the helper touches is
    recorded so the test can assert on the retry shape, not just the verdict.
    """

    def __init__(self, *outcomes):
        self._outcomes = list(outcomes)
        self.evaluate_calls = 0
        self.load_state_waits: list[tuple[str, int | None]] = []
        self.timeouts_waited: list[int] = []

    def evaluate(self, script, *args, **kwargs):
        self.evaluate_calls += 1
        assert self._outcomes, "helper called evaluate() more times than the test scripted"
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    def wait_for_load_state(self, state, timeout=None):
        self.load_state_waits.append((state, timeout))

    def wait_for_timeout(self, milliseconds):
        self.timeouts_waited.append(milliseconds)


# ---------------------------------------------------------------------------
# The classifier itself
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("message", RACE_MESSAGES)
def test_race_messages_are_classified_as_navigation_races(message):
    assert is_navigation_race_error(PlaywrightError(message)) is True


def test_other_playwright_errors_are_not_navigation_races():
    assert is_navigation_race_error(PlaywrightError(EVAL_SYNTAX_ERROR)) is False


def test_timeout_error_is_not_a_navigation_race():
    """``TimeoutError`` subclasses ``Error`` — the classifier must still say no."""
    assert is_navigation_race_error(PlaywrightTimeoutError("Timeout 30000ms exceeded")) is False


def test_non_playwright_exception_is_not_a_navigation_race():
    """A message match alone must not be enough — the type gate comes first."""
    assert is_navigation_race_error(RuntimeError(CONTEXT_DESTROYED)) is False


def test_fragment_list_stays_narrow():
    """Guards against the fix degenerating into a blanket catch by fragment creep.

    Only the two fragments that exist in Playwright 1.61.0's bundle are
    tolerated; widening this set is a deliberate decision that has to change
    this test too.
    """
    assert NAVIGATION_RACE_ERROR_FRAGMENTS == (
        "execution context was destroyed",
        "frame was detached",
    )


# ---------------------------------------------------------------------------
# The helper's behaviour — the contract that actually stops #2023
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("message", RACE_MESSAGES)
def test_navigation_race_is_tolerated_and_retried_once(message):
    """A race, then a clean run: the helper recovers and dismisses the banner."""
    page = _StubPage(PlaywrightError(message), True)

    BasePage(page).dismiss_banner_if_present()  # must not raise

    assert page.evaluate_calls == 2, "the raced evaluate should be retried exactly once"
    assert page.load_state_waits == [("domcontentloaded", BasePage.BANNER_RACE_SETTLE_TIMEOUT)], (
        "the retry must let the navigation settle on a bounded load-state wait, not a sleep"
    )
    assert page.timeouts_waited == [500], "the post-dismiss settle should still run on the retry path"


@pytest.mark.parametrize("message", RACE_MESSAGES)
def test_racing_twice_gives_up_quietly(message):
    """Racing on the retry too: give up, do not raise, do not retry a third time."""
    page = _StubPage(PlaywrightError(message), PlaywrightError(message))

    BasePage(page).dismiss_banner_if_present()  # must not raise

    assert page.evaluate_calls == 2, "retry budget is exactly one"
    assert page.timeouts_waited == [], "nothing was dismissed, so nothing to settle after"


def test_non_race_playwright_error_propagates():
    """A broken script is a real defect and must NOT be swallowed."""
    page = _StubPage(PlaywrightError(EVAL_SYNTAX_ERROR))

    with pytest.raises(PlaywrightError) as excinfo:
        BasePage(page).dismiss_banner_if_present()

    assert "SyntaxError" in str(excinfo.value)
    assert page.evaluate_calls == 1, "a non-race error must not be retried"


def test_timeout_error_propagates():
    page = _StubPage(PlaywrightTimeoutError("Page.evaluate: Timeout 30000ms exceeded"))

    with pytest.raises(PlaywrightTimeoutError):
        BasePage(page).dismiss_banner_if_present()

    assert page.evaluate_calls == 1


def test_non_race_error_on_the_retry_also_propagates():
    """Tolerance covers the race only — a real error surfacing on the retry raises."""
    page = _StubPage(PlaywrightError(CONTEXT_DESTROYED), PlaywrightError(EVAL_SYNTAX_ERROR))

    with pytest.raises(PlaywrightError) as excinfo:
        BasePage(page).dismiss_banner_if_present()

    assert "SyntaxError" in str(excinfo.value)
    assert page.evaluate_calls == 2


def test_settle_wait_timeout_does_not_abort_the_retry():
    """The settle wait is a courtesy; exceeding it must not become a failure."""
    page = _StubPage(PlaywrightError(CONTEXT_DESTROYED), True)
    page.wait_for_load_state = _raise_settle_timeout(page)

    BasePage(page).dismiss_banner_if_present()  # must not raise

    assert page.evaluate_calls == 2, "a slow settle must still be followed by the retry"
    assert page.timeouts_waited == [500]


def _raise_settle_timeout(page):
    def _wait_for_load_state(state, timeout=None):
        page.load_state_waits.append((state, timeout))
        raise PlaywrightTimeoutError(f"Timeout {timeout}ms exceeded")

    return _wait_for_load_state


# ---------------------------------------------------------------------------
# Happy path — unchanged by the fix
# ---------------------------------------------------------------------------


def test_happy_path_dismisses_and_settles():
    page = _StubPage(True)

    BasePage(page).dismiss_banner_if_present()

    assert page.evaluate_calls == 1
    assert page.load_state_waits == [], "no race, so no settle wait"
    assert page.timeouts_waited == [500]


def test_happy_path_without_a_banner_does_nothing():
    page = _StubPage(False)

    BasePage(page).dismiss_banner_if_present()

    assert page.evaluate_calls == 1
    assert page.load_state_waits == []
    assert page.timeouts_waited == [], "nothing dismissed — no post-dismiss settle"
