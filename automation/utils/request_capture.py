"""Passive capture of the requests a page issues — for absence and count assertions.

Why this exists
---------------
"The control did not do the destructive thing" cannot be proved by reading the
table. A row survives a ``DELETE`` that is still in flight, so
``expect(row).to_have_count(1)`` right after a click is satisfied both by a
non-destructive control and by a destructive one whose request has not landed
yet. The only observable that distinguishes them is the **request log**: a
request is observable the moment the browser *issues* it, long before it
resolves.

This module is deliberately **capture-only and passive**. It registers a
``page.on("request")`` listener and records URLs. Nothing is intercepted,
fabricated, delayed or fulfilled — the page talks to the real backend exactly as
it otherwise would, so every value an assertion reads is still produced by the
system under test (``.agents/testing.md`` § *Fidelity policy*).

Using it correctly
------------------
Three rules, all of which the caller owns:

1. **Register before the action.** The listener only sees requests issued after
   ``page.on`` runs, so collect at the top of the test — never between the click
   and the assertion.
2. **Read after an anchor.** An absence assertion is only meaningful once the
   product has demonstrably finished reacting: assert *after* the state the
   action produces is observable (the confirmation dialog rendered, the refetch
   resolved), not immediately after the click returns.
3. **Give an absence assertion a positive control.** A listener that was never
   wired records nothing, so ``assert not urls`` passes vacuously. Where the
   flow later performs the request for real, assert the count then — that turns
   the earlier "none yet" from an unfalsifiable claim into a checked one.

Usage::

    from utils.request_capture import collect_requests

    delete_requests = collect_requests(page)          # before the first click
    ...
    page_object.open_delete_dialog_for_row(row)       # anchors on dialog-rendered
    assert not delete_requests, f"the icon issued: {delete_requests}"
    ...
    page_object.confirm_delete()
    assert len(delete_requests) == 1                  # positive control
"""

from typing import Any

#: The method this module is reached for most often — the destructive one whose
#: absence a confirmation-dialog flow has to prove.
DELETE = "DELETE"


def collect_requests(page: Any, method: str = DELETE) -> list[str]:
    """Start recording the URL of every *method* request *page* issues from now on.

    Returns the **live** list the recorder appends to — hold onto it and read it
    at assertion time; it keeps growing for the lifetime of the page.

    *method* is matched case-insensitively against the HTTP verb, and no URL
    filtering is applied: a delete of *any* resource is worth surfacing when a
    control is supposed to issue none at all.
    """
    urls: list[str] = []
    wanted = method.upper()

    def _record(request: Any) -> None:
        if request.method.upper() == wanted:
            urls.append(request.url)

    page.on("request", _record)
    return urls
