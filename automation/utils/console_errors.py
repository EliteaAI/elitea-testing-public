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

This module is deliberately **capture-only**: :func:`collect_console_errors` never
drops a message. Filtering a known defect stays each spec's explicit, reviewable
decision (with a ``# Known defect: #N`` comment), exactly as before — see
``.agents/testing.md`` § *Merge gate* and the no-masking rule.

:func:`exclude_known_defect_urls` exists to make that decision cheap to express
without duplicating it across specs — but it is **opt-in and URL-keyed**: it drops
nothing unless a spec passes the exact URL it is excluding, and it deliberately
offers no way to filter by status code.

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

#: The one URL a spec may currently choose to exclude, and only by naming it.
#:
#: `EliteaUI/src/api/toolkits.js`'s `toolkitTypes` RTK-Query endpoint builds
#: ``.../toolkits/prompt_lib/${projectId}``; when it fires before
#: `useSelectedProjectId()` resolves, the URL collapses to a project-id-less
#: ``.../toolkits/prompt_lib/`` and 404s. Cosmetic in the product, but it lands
#: in any spec's console assertion. Filed as **#1971** (regression of the
#: closed #554).
#:
#: Declared here so the string is written once and stays greppable — but it is
#: NEVER applied automatically. A spec that wants it out must pass it to
#: :func:`exclude_known_defect_urls` itself, with a ``# Known defect: #1971``
#: comment. Delete both when #1971 is fixed.
TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL = "/api/v2/elitea_core/toolkits/prompt_lib/"


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


def exclude_known_defect_urls(errors: list[str], *url_fragments: str) -> list[str]:
    """Return *errors* minus the entries whose captured URL ends with one of
    *url_fragments*.

    Opt-in and explicit by design — this module stays capture-only (see the
    module docstring), so nothing is dropped unless a spec names the exact URL
    it is excluding, alongside a ``# Known defect: #N`` comment. That keeps the
    decision reviewable in the spec that made it, and keeps it narrow:

    * matching is on the **URL**, never on the status code — a filter keyed to
      "404" would swallow the next genuine one, which is masking
      (``.agents/testing.md`` § Unconfirmed states this explicitly);
    * ``str.endswith`` rather than ``in``, so a fragment cannot accidentally
      match a longer, well-formed URL that merely starts the same way — the
      whole point of #1971's signature is the *missing* trailing segment.
    """
    return [
        error
        for error in errors
        if not any(error.endswith(fragment) for fragment in url_fragments)
    ]
