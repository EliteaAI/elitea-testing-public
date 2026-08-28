"""Unit tests pinning the blank-composer settle window of ELITEA-2390.

Regression coverage for the review finding on PR #1962:
``_open_blank_composer()`` in
``tests/ui/settings/test_context_settings_new_conversations_only.py`` cited
``_open_genuinely_blank_conversation()`` as its ancestor and then dropped the
one piece of machinery that ancestor exists for — it settled the SPA's delayed
last-viewed-conversation restore with a fixed ``page.wait_for_timeout(1500)``
followed by a single recheck.

Two defects rode on that one line:

1. **It is a hard-don't.** ``.agents/conventions.md`` § Hard don'ts:
   *"No sleep/waitForTimeout — framework waits only"* (Hard Rule 5).
2. **It samples the window exactly once, at the end.** The blank state is
   required to *hold* for the whole settle window. A single late sample only
   ever observes the window's final state, so a restore that lands inside the
   window and is then superseded is accepted as a blank composer — the exact
   race ``_poll_blank_state_holds()`` was written to close, and the reason the
   ancestor polls instead of sleeping.

The fix duplicates the ancestor's :func:`_poll_blank_state_holds` faithfully.
These tests drive the real helper against a fake ChatPage on a virtual clock,
with a timeline whose blank state does NOT hold across the window. The
pre-fix shape returns success on that timeline (verified by reverting the
source); the fixed shape refuses it.
"""

import re
from types import SimpleNamespace

import pytest

from tests.ui.settings import test_context_settings_new_conversations_only as spec

_open_blank_composer = spec.TestContextSettingsApplyToNewConversationsOnly._open_blank_composer

BLANK_URL = "http://localhost:5173/chat"
RESTORED_URL = "http://localhost:5173/chat/566"


class _VirtualClock:
    """Deterministic stand-in for ``time`` — no real waiting, no flake."""

    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


class _FakeChatPage:
    """ChatPage stand-in whose blank/restored state is a function of the time
    elapsed since the last ``+Chat`` click.

    *timeline* is a list of ``(elapsed_seconds_from, url, message_count)``
    ordered by ``elapsed_seconds_from``; the last entry whose threshold has
    passed wins. Modelling it relative to the click is what makes every attempt
    behave identically — each ``+Chat`` restarts the SPA's restore race.
    """

    def __init__(self, clock: _VirtualClock, timeline: list[tuple[float, str, int]]):
        self._clock = clock
        self._timeline = timeline
        self._t0 = 0.0
        self.clicks = 0
        self.slept_ms: list[int] = []
        self.page = SimpleNamespace(
            url=BLANK_URL,
            wait_for_timeout=self._wait_for_timeout,
        )
        self.new_conversation_greeting = SimpleNamespace(wait_for=lambda **kwargs: None)

    # --- the bits the helper drives -----------------------------------
    def click_create_conversation(self, timeout: int = 0) -> None:
        self.clicks += 1
        self._t0 = self._clock.now

    def get_message_count(self) -> int:
        return self._state()[1]

    # --- only the PRE-FIX shape calls this; kept so the red-green revert runs
    def _wait_for_timeout(self, ms: int) -> None:
        self.slept_ms.append(ms)
        self._clock.sleep(ms / 1000.0)

    # --- internals ----------------------------------------------------
    def _state(self) -> tuple[str, int]:
        elapsed = self._clock.now - self._t0
        url, count = self._timeline[0][1], self._timeline[0][2]
        for start, entry_url, entry_count in self._timeline:
            if elapsed >= start:
                url, count = entry_url, entry_count
        self.page.url = url
        return url, count


@pytest.fixture
def clock(monkeypatch):
    """Run the helper's ``time`` on a virtual clock."""
    virtual = _VirtualClock()
    monkeypatch.setattr(
        spec, "time", SimpleNamespace(monotonic=virtual.monotonic, sleep=virtual.sleep)
    )
    return virtual


# Blank, then a restore lands at 0.2s and is superseded again by 0.9s — i.e. the
# blank state does NOT hold across the settle window, but IS blank at its end.
# This is the timeline a single end-of-window sample cannot see.
TRANSIENT_RESTORE = [(0.0, BLANK_URL, 0), (0.2, RESTORED_URL, 5), (0.9, BLANK_URL, 0)]

# The plain one-way restore: it lands and stays.
PERSISTENT_RESTORE = [(0.0, BLANK_URL, 0), (0.2, RESTORED_URL, 5)]

# Nothing ever restores.
STABLE_BLANK = [(0.0, BLANK_URL, 0)]


def test_transient_restore_inside_the_window_is_refused(clock):
    """THE regression test: blank at the window's end, restored in its middle.

    The pre-fix ``wait_for_timeout(1500)`` + one recheck returns success here
    (both signals read blank at t=1.5s). Polling sees the flip at t=0.25s.
    """
    chat = _FakeChatPage(clock, TRANSIENT_RESTORE)

    with pytest.raises(AssertionError, match="Could not reach a blank composer"):
        _open_blank_composer(chat)

    assert chat.clicks == 3, "every attempt should retry rather than accept the restore"


def test_persistent_restore_is_refused(clock):
    """The primary documented mechanism — a restore that lands and stays."""
    chat = _FakeChatPage(clock, PERSISTENT_RESTORE)

    with pytest.raises(AssertionError, match="blank state reverted mid-settle"):
        _open_blank_composer(chat)


def test_stable_blank_composer_is_accepted_on_the_first_attempt(clock):
    """The happy path still costs exactly one ``+Chat`` click."""
    chat = _FakeChatPage(clock, STABLE_BLANK)

    _open_blank_composer(chat)

    assert chat.clicks == 1


def test_helper_never_uses_a_fixed_wait_for_timeout(clock):
    """`.agents/conventions.md` § Hard don'ts — framework waits only.

    Behavioural, not a source grep: if a fixed settle ever comes back, the fake
    page records the call.
    """
    chat = _FakeChatPage(clock, STABLE_BLANK)

    _open_blank_composer(chat)

    assert chat.slept_ms == [], f"fixed wait_for_timeout settle reintroduced: {chat.slept_ms}"


def test_poll_exits_the_instant_a_signal_flips(clock):
    """Fail fast — a definitive failure must not burn the whole window."""
    chat = _FakeChatPage(clock, PERSISTENT_RESTORE)
    chat.click_create_conversation()
    started = clock.now

    settled, reason = spec._poll_blank_state_holds(chat)

    assert settled is False
    assert "reverted mid-settle" in reason
    assert (clock.now - started) < spec.BLANK_SETTLE_MS / 1000.0


def test_poll_reports_settled_when_blank_holds_for_the_whole_window(clock):
    chat = _FakeChatPage(clock, STABLE_BLANK)
    chat.click_create_conversation()

    settled, reason = spec._poll_blank_state_holds(chat)

    assert settled is True
    assert reason == ""


def test_blank_url_pattern_accepts_only_id_less_chat_routes():
    assert spec.BLANK_URL_PATTERN.search(BLANK_URL)
    assert spec.BLANK_URL_PATTERN.search(f"{BLANK_URL}/?foo=bar")
    assert not spec.BLANK_URL_PATTERN.search(RESTORED_URL)
    assert isinstance(spec.BLANK_URL_PATTERN, re.Pattern)
