"""Unit tests for ``SidebarHeaderPage._is_notification_list_response()``
(``pages/sidebar_header_page.py``) — ELITEA-2234.

Regression coverage for the onboarding-w4 gate RED: Step 5 failed after 5066 ms on
``sidebar-notifications-mark-all-read-button``, with the failure screenshot showing
the popover open on FIVE grey ``Skeleton`` bars. ``open_notifications()`` waited only
for the Popover PAPER, which mounts instantly — the list itself was still in flight,
so every content assertion raced a live DEV round-trip on Playwright's silent 5 s
``expect`` default.

The fix makes ``open_notifications()`` wait for the popover's OWN list response. That
wait is only as good as the predicate that recognises the response: the popover's list
fetch and the bell badge's unread-count probe share a URL prefix and both are GETs, and
the probe fires on page load — long before the bell is ever clicked. A predicate that
matched the probe would resolve immediately and silently restore the exact defect (a
skeleton handed back to the caller), with no error anywhere. These tests pin the one
discriminator: ``only_total=true`` is present on the probe and absent from the list.

Samples are the real URLs observed live on ``localhost:5173`` against the DEV backend
(``src/api/notifications.js`` builds both from the same ``notificationList`` endpoint;
``NotificationButton.jsx`` passes ``only_total: true``, ``NotificationList.jsx`` does not).
"""

from dataclasses import dataclass

import pytest
from pages.sidebar_header_page import SidebarHeaderPage

_BASE = "http://localhost:5173/api/v2/notifications/notifications/prompt_lib/471"

# NotificationList.jsx — the POPOVER's paginated list (POPOVER_PAGE_SIZE = 5).
_LIST_URL = f"{_BASE}?only_new=true&limit=5&offset=0"
# NotificationButton.jsx — the badge's unread-count probe, fired on page load.
_UNREAD_COUNT_URL = f"{_BASE}?only_new=true&only_total=true&limit=1&offset=0"
# NotificationCenterPage — the Settings > Notifications full list.
_CENTER_LIST_URL = f"{_BASE}?limit=20&offset=0&sort_by=created_at&sort_order=desc"


@dataclass
class _FakeRequest:
    method: str


@dataclass
class _FakeResponse:
    """Minimal stand-in for ``playwright.sync_api.Response`` — the predicate reads
    exactly two things off it."""

    url: str
    request: _FakeRequest


def _get(url: str) -> _FakeResponse:
    return _FakeResponse(url=url, request=_FakeRequest(method="GET"))


def test_matches_the_popover_list_fetch():
    """The request ``open_notifications()`` must wait for."""
    assert SidebarHeaderPage._is_notification_list_response(_get(_LIST_URL)) is True


def test_rejects_the_unread_count_probe():
    """The defect's shape: the probe shares the prefix, is a GET, and fires on load.

    Matching it would make the wait resolve on a request that says nothing about the
    popover's list — i.e. return a skeleton to the caller, exactly as before the fix.
    """
    assert SidebarHeaderPage._is_notification_list_response(_get(_UNREAD_COUNT_URL)) is False
    # Guard the precondition: the sample really is indistinguishable by prefix + method.
    assert "/notifications/notifications/prompt_lib/" in _UNREAD_COUNT_URL


def test_rejects_unrelated_endpoints():
    """A same-origin GET on another endpoint must not satisfy the wait."""
    assert (
        SidebarHeaderPage._is_notification_list_response(
            _get("http://localhost:5173/api/v2/applications/applications/prompt_lib/471")
        )
        is False
    )


@pytest.mark.parametrize("method", ["PUT", "DELETE", "POST"])
def test_rejects_non_get_methods_on_the_same_url(method):
    """``notificationBulkMarkSeen`` (PUT) and ``notificationBulkDelete`` (DELETE) hit the
    IDENTICAL URL (``src/api/notifications.js``). Only the GET is the list read."""
    response = _FakeResponse(url=_LIST_URL, request=_FakeRequest(method=method))
    assert SidebarHeaderPage._is_notification_list_response(response) is False


def test_matches_the_notification_center_list_too():
    """Documents the predicate's deliberate breadth: any non-``only_total`` GET on the
    endpoint counts, including Settings > Notifications.

    That is safe because the predicate is used ONLY inside ``open_notifications()``'s
    ``expect_response`` window, which opens immediately before the bell click — the
    notification-centre page is a different route and is never being loaded there. If a
    future caller uses this predicate outside that window, THIS test is the reminder
    that it needs narrowing (e.g. also excluding ``sort_by=``)."""
    assert SidebarHeaderPage._is_notification_list_response(_get(_CENTER_LIST_URL)) is True
