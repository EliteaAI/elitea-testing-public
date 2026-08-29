"""Unit tests pinning request-log-backed "the control issued nothing" claims.

Regression coverage for the fix-round-1 finding on PR #1976
(``tests/ui/admin/test_user_delete_via_row_icon.py``, ELITEA-2298): the AFS's
step-3 verify clause and its Coverage-Map cell for case step 2 both read
"click + no DELETE yet", but the spec shipped only::

    expect(users_page.get_row_by_text(email)).to_have_count(1)

A row survives a ``DELETE`` that is still in flight, so that read is satisfied
by a destructive icon just as happily as by a non-destructive one — the test was
green, the AFS claimed a request assertion, and nothing in the suite objected.
The sibling spec (ELITEA-2300) already did it right with a hand-rolled listener,
which is exactly how a shape drifts: correct in one file, silently absent in the
next. Fix round 2 closed the other half of that drift: the batch spec
(ELITEA-2299) made the same "this control issued no DELETE" claim off a
hand-rolled listener with no positive control, and was missing from the list
below — a guard that does not enumerate every claimant is a guard with a hole.
The list is the contract: a delete-flow spec asserting an absence belongs in it.

These tests pin both ends of the fix:

1. :func:`utils.request_capture.collect_requests` records the requests it claims
   to and ignores the rest, returning a live list.
2. The delete-flow specs whose AFS claims "no DELETE was issued" actually assert
   it against that log — and pair it with a positive control, because
   ``assert not urls`` on a listener that was never wired passes vacuously.
"""

import inspect
import re

import pytest
from utils.request_capture import collect_requests

from tests.ui.admin import (
    test_user_delete_cancel_keeps_user,
    test_user_delete_via_row_icon,
    test_users_batch_delete,
)


class _FakeRequest:
    def __init__(self, method: str, url: str):
        self.method = method
        self.url = url


class _FakePage:
    """Records ``page.on`` registrations and can replay requests."""

    def __init__(self):
        self.handlers: dict[str, list] = {}

    def on(self, event: str, handler):
        self.handlers.setdefault(event, []).append(handler)

    def emit(self, request):
        for handler in self.handlers.get("request", []):
            handler(request)


def test_collector_registers_on_the_request_event():
    page = _FakePage()
    collect_requests(page)
    assert "request" in page.handlers


def test_collector_records_only_the_wanted_method():
    page = _FakePage()
    deletes = collect_requests(page)

    page.emit(_FakeRequest("GET", "http://x/api/v2/admin/users/default/400"))
    page.emit(_FakeRequest("POST", "http://x/api/v2/admin/users/default/400"))
    page.emit(_FakeRequest("PUT", "http://x/api/v2/admin/users/default/400"))
    page.emit(_FakeRequest("DELETE", "http://x/api/v2/admin/users/default/400?id[]=7"))

    assert deletes == ["http://x/api/v2/admin/users/default/400?id[]=7"]


def test_collector_does_not_filter_by_url():
    """A control that must issue no delete at all should surface a delete of
    ANY resource — narrowing by URL is how one slips past."""
    page = _FakePage()
    deletes = collect_requests(page)

    page.emit(_FakeRequest("DELETE", "http://x/api/v2/something/else/1"))

    assert deletes == ["http://x/api/v2/something/else/1"]


def test_collector_matches_the_method_case_insensitively():
    page = _FakePage()
    deletes = collect_requests(page, "delete")

    page.emit(_FakeRequest("DELETE", "http://x/api/v2/admin/users/default/400?id[]=7"))

    assert len(deletes) == 1


def test_collector_returns_a_live_list():
    """The caller registers before the action and reads after it — the list it
    was handed has to be the one the recorder keeps appending to."""
    page = _FakePage()
    deletes = collect_requests(page)
    assert deletes == []

    page.emit(_FakeRequest("DELETE", "http://x/a"))
    page.emit(_FakeRequest("DELETE", "http://x/b"))

    assert deletes == ["http://x/a", "http://x/b"]


#: Specs whose AFS claims a control issues no DELETE. A table read cannot make
#: that claim (a row outlives an in-flight DELETE), so each must assert it
#: against the request log.
_SPECS_CLAIMING_NO_DELETE_WAS_ISSUED = [
    test_user_delete_via_row_icon,
    test_user_delete_cancel_keeps_user,
    test_users_batch_delete,
]


@pytest.mark.parametrize(
    "module",
    _SPECS_CLAIMING_NO_DELETE_WAS_ISSUED,
    ids=lambda m: m.__name__.rsplit(".", 1)[-1],
)
def test_no_delete_claims_are_asserted_against_the_request_log(module):
    """This is the check that would have caught the original finding.

    ELITEA-2298 shipped its "the icon deletes nothing on its own" step as a row
    read and ran green for a full review round.
    """
    source = inspect.getsource(module)
    assert "collect_requests(page)" in source, (
        f"{module.__name__} claims a control issues no DELETE; it must capture the "
        "request log via utils.request_capture.collect_requests, because a table "
        "read is satisfied by an in-flight DELETE too."
    )
    assert "assert not delete_requests" in source, (
        f"{module.__name__} captures the request log but never asserts its emptiness "
        "— the 'no DELETE was issued' claim is unbacked."
    )
    # Whitespace-insensitive on purpose: the batch spec's hand-rolled listener
    # was wrapped across lines, which a literal-substring check misses.
    assert not re.search(r"""page\.on\(\s*["']request["']""", source), (
        f"{module.__name__} hand-rolls a page.on('request', ...) listener; use "
        "utils.request_capture.collect_requests so the shape stays one shape."
    )


@pytest.mark.parametrize(
    "module",
    _SPECS_CLAIMING_NO_DELETE_WAS_ISSUED,
    ids=lambda m: m.__name__.rsplit(".", 1)[-1],
)
def test_absence_assertions_carry_a_positive_control(module):
    """``assert not delete_requests`` passes vacuously if the listener was never
    wired, so each spec must also assert the log NON-empty at the point its flow
    genuinely issues a DELETE (ELITEA-2298 and ELITEA-2299: confirming;
    ELITEA-2300: cleanup)."""
    source = inspect.getsource(module)
    assert "len(delete_requests) == 1" in source or "assert delete_requests" in source, (
        f"{module.__name__} asserts a DELETE was NOT issued but never asserts one WAS "
        "— nothing proves the observer is wired, so the absence claim is unfalsifiable."
    )
