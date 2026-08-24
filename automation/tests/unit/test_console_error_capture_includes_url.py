"""Unit tests pinning URL-annotated console-error capture.

Regression coverage for the batch-stabilize finding on
``tests/ui/onboarding/test_sidebar_notification_badge.py`` (ELITEA-2234): the
spec's hand-rolled listener recorded ``f"{msg.type}: {msg.text}"`` and dropped
``msg.location``, so when it tripped on two unrelated ``400 (Bad Request)``
resource failures the report read::

    ['error: Failed to load resource: the server responded with a status of 400 (Bad Request)', ...]

— anonymous. There is no way to tell from that whether the flow under test
regressed or an unrelated background resource blipped, and ``--reruns=2`` then
hid the occurrence entirely from the junit trail. It is the same class
``.agents/testing.md`` § *Unconfirmed* has been tracking across 500/404 flavors,
where the standing ask is literally "**capture the failing resource URL** ... so
a shared filter can be written".

The fix is a shared, capture-only helper (``utils.console_errors``). These tests
pin both ends of it:

1. The formatter must surface ``msg.location['url']`` — the browser reports the
   failing resource there, never in the message text.
2. The diagnosed spec must use the shared helper rather than re-growing a
   hand-rolled, URL-less listener (the copy-paste shape this class comes from).
"""

import inspect

import pytest
from utils.console_errors import NO_URL, collect_console_errors, format_console_message

from tests.ui.onboarding import test_sidebar_notification_badge

#: The exact text a "Failed to load resource" console error carries — note it holds
#: the status code and nothing that identifies WHICH resource failed.
_RESOURCE_400 = "Failed to load resource: the server responded with a status of 400 (Bad Request)"


class _FakeConsoleMessage:
    """Minimal stand-in for Playwright's ``ConsoleMessage``."""

    def __init__(self, text: str, url: str | None = None, msg_type: str = "error", location=...):
        self.text = text
        self.type = msg_type
        if location is not ...:
            self.location = location
        else:
            self.location = {"url": url, "lineNumber": 0, "columnNumber": 0} if url else None


class _FakePage:
    """Records ``page.on`` registrations and can replay console messages."""

    def __init__(self):
        self.handlers: dict[str, list] = {}

    def on(self, event: str, handler):
        self.handlers.setdefault(event, []).append(handler)

    def emit(self, msg):
        for handler in self.handlers.get("console", []):
            handler(msg)


def test_formatter_surfaces_the_failing_resource_url():
    """The whole point: a 400/404/500 resource failure must be attributable."""
    formatted = format_console_message(
        _FakeConsoleMessage(_RESOURCE_400, url="http://localhost:5173/api/v1/notifications/")
    )
    assert "http://localhost:5173/api/v1/notifications/" in formatted, (
        "A console error must carry the failing resource URL — without it the "
        "recurring background-resource noise class is indistinguishable from a "
        "genuine regression of the flow under test."
    )
    assert _RESOURCE_400 in formatted and formatted.startswith("error: ")


def test_two_failures_on_different_resources_are_distinguishable():
    """The diagnosed occurrence was two identical-looking 400s; URLs separate them."""
    first = format_console_message(_FakeConsoleMessage(_RESOURCE_400, url="http://x/api/a"))
    second = format_console_message(_FakeConsoleMessage(_RESOURCE_400, url="http://x/api/b"))
    assert first != second


@pytest.mark.parametrize(
    "message",
    [
        _FakeConsoleMessage(_RESOURCE_400),
        _FakeConsoleMessage(_RESOURCE_400, location=None),
        _FakeConsoleMessage(_RESOURCE_400, location={}),
        _FakeConsoleMessage(_RESOURCE_400, location="not-a-dict"),
    ],
    ids=["no-location", "none-location", "empty-location", "odd-location"],
)
def test_formatter_degrades_instead_of_raising_when_no_url_is_reported(message):
    """An exception inside a console callback is swallowed by the event loop and
    would silently disable capture — degrade, never raise."""
    formatted = format_console_message(message)
    assert formatted.endswith(f"@ {NO_URL}")
    assert _RESOURCE_400 in formatted


def test_collector_captures_only_errors_and_annotates_them():
    page = _FakePage()
    errors = collect_console_errors(page)

    page.emit(_FakeConsoleMessage("a warning", url="http://x/w", msg_type="warning"))
    page.emit(_FakeConsoleMessage("some info", url="http://x/i", msg_type="info"))
    page.emit(_FakeConsoleMessage(_RESOURCE_400, url="http://x/api/notifications"))

    assert errors == [f"error: {_RESOURCE_400} @ http://x/api/notifications"]


def test_collector_registers_on_the_console_event():
    page = _FakePage()
    collect_console_errors(page)
    assert "console" in page.handlers


def test_diagnosed_spec_uses_the_shared_url_annotated_collector():
    """The spec must not re-grow a hand-rolled, URL-less console listener.

    This is the check that would have caught the original finding: the listener
    existed, worked, and produced anonymous errors — no assertion anywhere
    objected to the missing URL.
    """
    source = inspect.getsource(test_sidebar_notification_badge)
    assert "collect_console_errors(page)" in source, (
        "test_sidebar_notification_badge must capture console errors via "
        "utils.console_errors.collect_console_errors so every error carries the "
        "failing resource URL."
    )
    assert 'page.on(\n            "console"' not in source and 'page.on("console"' not in source, (
        "A hand-rolled page.on('console', ...) listener re-introduces the URL-less "
        "capture shape; use utils.console_errors.collect_console_errors instead."
    )
