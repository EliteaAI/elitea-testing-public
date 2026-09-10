"""Unit tests pinning the Catalog's response-await diagnostics (FIX card #2169).

Two defects sat one method apart in ``pages/agent_hub_page.py``:

1. **The ``agent_categories`` await never received FIX #2078's diagnostic
   wrapper.** It used a raw ``page.expect_response``, so a fetch that never
   landed produced Playwright's bare ``Timeout Nms exceeded while waiting for
   event "response"`` — a message that names only the predicate's source
   location. This repo has two ledger entries (#2074, #2076) where exactly that
   shape named the WRONG subsystem and cost a full session.
2. **Its predicate filtered on ``response.status == 200``.** A FAILED categories
   fetch therefore never matched, so the wait burned its full 45s budget and
   then reported a blind timeout about a request that had already come back.
   Measured on ``dev.elitea.ai`` with the fetch forced to 404: **45.05s and
   "Timeout 45000ms exceeded" before**, **7.37s and "HTTP 404 Not Found for
   <url>" after**.

The repair generalised the #2078 helper to take the endpoint family as a
parameter. These tests drive the real helper and the real method against a fake
Page, and pin five things a future refactor could silently undo:

* the four existing ``/public_applications/`` call sites keep a byte-identical
  message (:func:`test_applications_diagnostic_message_is_unchanged`) — the pin
  covers ``reload_and_capture_my_liked``, whose only spec fails on DEV for an
  unrelated, pre-existing reason (a duplicate ``catalog-agent-like-button-127``
  card) and so could not be certified live;
* the categories await reports its OWN endpoint family, not the applications one
  (:func:`test_categories_timeout_names_its_own_endpoint_family`) — a listener
  keyed on a family the caller is not waiting on would print ``['none']`` on
  every timeout and actively mislead;
* a non-200 (or contract-breaking) categories response fails fast, quoting the
  real status and URL, instead of degrading into an empty category set — which
  would re-report a backend fault as a filter-rail chip-set delta;
* a **redirect hop does not win the wait** — a 30x fires a ``response`` event
  carrying the REQUESTED url, so without the exclusion it would be reported as a
  backend fault (reviewer round 1; the live path is the forward-auth re-fetch in
  ``EliteaUI/src/api/eliteaApi.js``);
* an exception from the **wrapped body** propagates untouched — the
  ``body_completed`` flag, which is what stops the helper re-labelling a
  navigation/click failure as a response timeout.

⚠️ **What ``_FakePage`` does NOT model — do not read a green run here as coverage
of these.** It runs the body to completion and *then* replays its traffic,
taking the first predicate match. Real ``expect_response`` resolves on the first
match **as it arrives, concurrently with the body**. So this fake cannot
represent: true traffic ordering or timing; a redirect hop racing the retried
200 *during* the body (the Critical above is only pinned here at the level of
"a 3xx never satisfies the predicate" — the concurrent shape was verified live
against ``dev.elitea.ai`` with a throwaway probe, not here); or the body raising
while the wait is still pending. The listener registration/removal window IS
exercised as written, because the fake dispatches from inside
``expect_response``.
"""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from pages.agent_hub_page import AgentHubPage
from pages.base_page import BasePage
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

APPLICATIONS_URL = "https://dev.elitea.ai/api/v2/elitea_core/public_applications/prompt_lib/1?limit=1000"
CATEGORIES_URL = "https://dev.elitea.ai/api/v2/elitea_core/agent_categories/prompt_lib/1"


class _FakeResponse:
    """Stand-in for a Playwright ``Response`` — only what the code under test reads."""

    def __init__(self, url, status=200, status_text="OK", method="GET", body=None):
        self.url = url
        self.status = status
        self.status_text = status_text
        self.request = SimpleNamespace(method=method)
        self._body = body

    @property
    def ok(self):
        return 200 <= self.status < 300

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body

    def text(self):
        return str(self._body)


class _FakePage:
    """Minimal ``Page`` stand-in.

    Dispatches its recorded traffic to every ``on("response")`` listener from
    INSIDE ``expect_response`` — where the real Page does — so the helper's
    listener registration/removal window is exercised as written.
    """

    def __init__(self, traffic):
        self.traffic = traffic
        self.listeners = []

    def on(self, event, handler):
        assert event == "response"
        self.listeners.append(handler)

    def remove_listener(self, event, handler):
        self.listeners.remove(handler)

    def screenshot(self, **_kwargs):  # the @action decorator's failure path
        return b""

    @contextmanager
    def expect_response(self, predicate, timeout):
        info = SimpleNamespace(value=None)
        yield info
        matched = None
        for response in self.traffic:
            for handler in list(self.listeners):
                handler(response)
            if matched is None and predicate(response):
                matched = response
        if matched is None:
            raise PlaywrightTimeoutError(f'Timeout {timeout}ms exceeded while waiting for event "response"')
        info.value = matched


@pytest.fixture
def no_navigation(monkeypatch):
    """Neutralise ``BasePage.navigate`` — these tests exercise the response
    await around it, not the navigation itself."""
    monkeypatch.setattr(BasePage, "navigate", lambda self, path: None)


def test_applications_diagnostic_message_is_unchanged():
    """The four ``/public_applications/`` call sites must be untouched by #2169's
    generalisation — same recorded family, byte-identical re-raised message."""
    page = _FakePage([_FakeResponse(APPLICATIONS_URL), _FakeResponse(CATEGORIES_URL)])
    hub = AgentHubPage(page)

    with pytest.raises(PlaywrightTimeoutError) as excinfo:
        with hub._expect_applications_response(lambda _r: False, 45000, "bulk all-applications"):
            pass

    expected_seen = [f"200 {APPLICATIONS_URL}"]
    assert str(excinfo.value) == (
        "Timed out after 45000ms waiting for the Catalog bulk all-applications response. "
        f"/public_applications/ responses observed meanwhile: {expected_seen}"
    )
    # Family scoping: the categories response in the same traffic is NOT recorded.
    assert "agent_categories" not in str(excinfo.value)
    assert page.listeners == [], "the response listener must be removed in the finally block"


def test_categories_timeout_names_its_own_endpoint_family(no_navigation):
    """A categories fetch that never lands names the ``agent_categories`` family —
    not ``/public_applications/`` and not Playwright's bare timeout text."""
    page = _FakePage([_FakeResponse(APPLICATIONS_URL)])  # sibling traffic only
    hub = AgentHubPage(page)

    with pytest.raises(PlaywrightTimeoutError) as excinfo:
        hub.navigate_and_capture_category_names(response_timeout=45000)

    message = str(excinfo.value)
    assert "waiting for the Catalog agent-categories response" in message
    assert f"{AgentHubPage.AGENT_CATEGORIES_URL_FRAGMENT} responses observed meanwhile: ['none']" in message
    # Pre-#2169 the recorder was hardcoded to the applications family; keying it on
    # the family the caller is NOT waiting on is the failure mode being pinned out.
    assert "/public_applications/" not in message


def test_categories_non_200_is_matched_and_named_with_status_and_url(no_navigation):
    """A non-200 categories response SATISFIES the predicate (which must not filter
    on status) and is reported as a verdict quoting status and URL.

    Named for what is actually pinned: that the response was *matched* rather than
    left to the timeout path. The latency win this buys (45.05s -> 7.37s, measured
    on DEV) is not observable in a fake — only the route taken is.
    """
    page = _FakePage([_FakeResponse(CATEGORIES_URL, status=404, status_text="Not Found", body={"error": "nope"})])
    hub = AgentHubPage(page)

    with pytest.raises(AssertionError) as excinfo:
        hub.navigate_and_capture_category_names(response_timeout=45000)

    message = str(excinfo.value)
    assert "HTTP 404 Not Found" in message
    assert CATEGORIES_URL in message
    # Route check, not a timing check: the verdict came from the predicate matching,
    # not from the wait expiring (which is what a status-filtered predicate produces).
    assert "Timed out after" not in message


def test_categories_200_without_categories_list_is_named_not_degraded(no_navigation):
    """A 200 whose body carries no ``categories`` list must fail explicitly.

    ``.get("categories", [])`` would have returned an empty set, silently
    shrinking the filter rail's expected chips and reporting a contract break as
    a chip-set delta in the caller's assertion.
    """
    page = _FakePage([_FakeResponse(CATEGORIES_URL, body={"rows": []})])
    hub = AgentHubPage(page)

    with pytest.raises(AssertionError) as excinfo:
        hub.navigate_and_capture_category_names(response_timeout=45000)

    assert "carries no 'categories' list" in str(excinfo.value)


def test_redirect_hop_does_not_satisfy_the_categories_predicate(no_navigation):
    """A 30x on the categories URL must NOT be taken as the answer.

    ``page.on("response")`` and ``expect_response`` both fire for redirect hops, and
    a 30x carries the REQUESTED url — so without the exclusion this would be reported
    as ``HTTP 302 Found ... backend/app fault``. The live path is real: EliteaUI's
    ``fetchBaseQuery.fetchFn`` handles ``response.redirected`` and, on a forward-auth
    session-expiry redirect, opens an auth popup and re-fetches the original request.
    The retried 200 is the answer; the 302 is transport.

    Pinned here only as "a 3xx never satisfies the predicate" — with no 200 in the
    traffic the wait must expire rather than return a verdict. The concurrent
    redirect-then-200 shape is not representable in ``_FakePage`` (see module
    docstring) and was verified live instead.
    """
    page = _FakePage([_FakeResponse(CATEGORIES_URL, status=302, status_text="Found")])
    hub = AgentHubPage(page)

    with pytest.raises(PlaywrightTimeoutError) as excinfo:
        hub.navigate_and_capture_category_names(response_timeout=45000)

    message = str(excinfo.value)
    assert "302" not in message.split("observed meanwhile")[0], "the 3xx must not become the verdict"
    # Nothing diagnostic is lost: the recorder has no status filter, so the hop is
    # still visible in the observed-traffic list.
    assert f"302 {CATEGORIES_URL}" in message


def test_body_exception_propagates_untouched():
    """An exception from the WRAPPED BODY must never be re-labelled as a response
    timeout — that is what the helper's ``body_completed`` flag exists for, and it is
    the one contract whose loss would make every navigation failure lie.

    The load-bearing half is the SECOND case. A ``ValueError`` could never be
    re-labelled anyway (the handler only catches ``PlaywrightTimeoutError``), so on
    its own it pins nothing. The case that actually exercises the flag is a
    ``PlaywrightTimeoutError`` raised BY the body — a navigation timeout — which
    without the flag would be rewritten as "Timed out ... waiting for the Catalog
    ... response", naming the wrong subsystem. Verified red-green: deleting the
    ``if not body_completed: raise`` guard fails this test.
    """
    page = _FakePage([])  # no traffic: the wait itself would time out if reached
    hub = AgentHubPage(page)

    with pytest.raises(ValueError, match="navigation blew up"):
        with hub._expect_applications_response(lambda _r: True, 45000, "bulk all-applications"):
            raise ValueError("navigation blew up")
    assert page.listeners == [], "the response listener must be removed in the finally block"

    with pytest.raises(PlaywrightTimeoutError) as excinfo:
        with hub._expect_applications_response(lambda _r: True, 45000, "bulk all-applications"):
            raise PlaywrightTimeoutError("Page.goto: Timeout 15000ms exceeded")
    assert str(excinfo.value) == "Page.goto: Timeout 15000ms exceeded"
    assert "observed meanwhile" not in str(excinfo.value), "a body failure must not be re-labelled"
    assert page.listeners == []
