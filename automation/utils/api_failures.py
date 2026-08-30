"""Transport-level failure capture for UI specs.

Why this exists
---------------
A case that says "the section loads without an Access Denied or 403 error"
cannot be settled by reading the DOM alone. On this product a permission
failure can surface as a ``403`` with **no** access-denied UI at all — that is
exactly the shape of the open bug ``#1773`` on the Secrets route — so a
text-only denial check passes straight over a real denial.

This module is the transport-level half of that check: it records every
``/api/v2/`` response the page received with a ``4xx``/``5xx`` status, so a
spec can assert the *absence* of a permission (or any other) failure as a fact
about what the backend actually returned, not about what the UI chose to
render.

Deliberately shaped like :mod:`utils.console_errors`, its console-level
sibling: a live list you bind once and assert on later, **capture-only** — it
never drops a response, so a spec that wants to tolerate a known defect must
say so explicitly, in the spec, with a ``# Known defect: #N`` comment.

Usage::

    from utils.api_failures import collect_api_failures

    api_failures = collect_api_failures(page)
    ...
    assert not api_failures, f"unexpected API failures: {api_failures}"
"""

from typing import Any

#: Only the app's own API traffic is interesting — static assets, the
#: Socket.IO polling transport (`#1847`) and third-party calls are not what a
#: "no permission error" assertion is about.
API_PATH_FRAGMENT = "/api/v2/"


def format_api_failure(response: Any) -> str:
    """Render a failing ``Response`` as a diagnosable one-liner.

    ``"<method> <status> <url>"`` — the method matters because the same path
    can be readable and un-writable, which is precisely the distinction a
    permission assertion cares about.
    """
    return f"{response.request.method} {response.status} {response.url}"


def collect_api_failures(page: Any, path_fragment: str = API_PATH_FRAGMENT) -> list[str]:
    """Attach a response listener to *page* and return the list it appends to.

    The returned list is live — it fills as the page runs. Bind it once, then
    either assert on the whole list, or slice it per navigation step
    (``failures[mark:]``) to attribute a failure to the section that caused it.

    Args:
        page: The Playwright ``Page`` to observe.
        path_fragment: Only responses whose URL contains this fragment are
            recorded. Defaults to the app's own API prefix.
    """
    failures: list[str] = []

    def _on_response(response: Any) -> None:
        if path_fragment in response.url and response.status >= 400:
            failures.append(format_api_failure(response))

    page.on("response", _on_response)
    return failures
