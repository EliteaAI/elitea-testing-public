"""URL-annotated console-error capture for UI specs.

Why this exists
---------------
Specs across this suite hand-roll the same listener::

    page.on("console", lambda msg: errors.append(f"{msg.type}: {msg.text}") ...)

which throws away ``msg.location`` — so the recurring background-resource noise
class logged in ``.agents/testing.md`` § *Unconfirmed* ("Failed to load resource:
the server responded with a status of 500/400/404") arrives **anonymous**: no URL,
therefore no way to tell a genuine regression of the flow under test from a blip on
an unrelated resource, and no way to write the shared filter that note explicitly
asks for ("**capture the failing resource URL** ... so a shared filter can be
written").

Playwright *does* carry the failing resource's URL — for "Failed to load resource"
messages the browser reports it in ``ConsoleMessage.location['url']``, not in the
message text. Capturing it costs nothing and makes the next occurrence diagnosable
instead of anonymous.

This module is deliberately **capture-only**: it never drops a message. Filtering a
known defect stays each spec's explicit, reviewable decision (with a
``# Known defect: #N`` comment), exactly as before — see
``.agents/testing.md`` § *Merge gate* and the no-masking rule.

Usage::

    from utils.console_errors import collect_console_errors

    console_errors = collect_console_errors(page)
    ...
    assert not console_errors, f"unexpected console errors: {console_errors}"
"""

from typing import Any

#: Rendered in place of the URL when the browser reported none (most
#: JS-thrown errors carry a location; some synthetic messages do not).
NO_URL = "<no-url>"


def format_console_message(msg: Any) -> str:
    """Render a Playwright ``ConsoleMessage`` as a diagnosable one-liner.

    ``"<type>: <text> @ <url>"`` — the URL comes from ``msg.location``, which is
    where the browser puts the *failing resource* for "Failed to load resource"
    messages (the message text itself only carries the status code).

    Defensive by design: a missing/None/oddly-shaped ``location`` degrades to
    ``NO_URL`` rather than raising inside a console callback, where an exception
    would be swallowed by the event loop and silently disable capture.
    """
    location = getattr(msg, "location", None)
    url = location.get("url") if isinstance(location, dict) else None
    return f"{msg.type}: {msg.text} @ {url or NO_URL}"


def collect_console_errors(page: Any) -> list[str]:
    """Attach a console listener to ``page`` and return the list it appends to.

    The returned list is live — it fills as the page runs, so bind it once at the
    start of a test and assert on it at the end. Only ``error``-type messages are
    captured; warnings/info are ignored, matching the assertion every spec makes.
    """
    errors: list[str] = []

    def _on_console(msg: Any) -> None:
        if msg.type == "error":
            errors.append(format_console_message(msg))

    page.on("console", _on_console)
    return errors
