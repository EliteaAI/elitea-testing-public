"""Sidebar header page object — ELITEA logo + socket status dot + notification bell.

Surface: ``src/[fsd]/widgets/sidebar-root/ui/SidebarBody.jsx`` (header row) plus
``ui/button/NotificationButton.jsx`` and ``ui/NotificationList.jsx``. This is the
persistent app-shell sidebar, rendered on every authenticated route — NOT the
``/onboarding`` page, even though the two TMS cases that introduced this object
are filed under the onboarding module (ELITEA-2233, ELITEA-2234).

Locator provenance (all added 2026-08-24 on ``automation/testids``, attribute-only
additions on elements that already existed — no new DOM node, no hook, no
render-prop change):

- ``sidebar-socket-status-indicator`` + ``data-socket-status`` —
  EliteaAI/EliteaUI@2c0ac201 (``SidebarBody.jsx``). The dot is ONE element whose
  colour flips with socket state, so the state lives on a ``data-*`` attribute and
  never in the testid value (``.agents/testing.md`` § Locator policy, PR #581).
- ``sidebar-notifications-button``, ``sidebar-notifications-bell-icon`` +
  ``data-has-messages``, ``sidebar-notifications-popover``,
  ``sidebar-notifications-popover-title``, ``sidebar-notifications-close-button``,
  ``sidebar-notifications-mark-all-read-button`` — EliteaAI/EliteaUI@1d512ae2.
  The red badge is an SVG ``<circle>`` rendered INSIDE the bell ``<svg>`` when
  ``hasMessages`` is true, so it cannot carry its own testid (its presence flips
  with state); the badge is located through ``data-has-messages`` on the stable
  bell element instead.
  ``sidebar-notifications-popover`` sits on the Popover's **paper** (via
  ``slotProps.paper``), not on ``<Popover>`` itself: MUI spreads a testid passed to
  the Popover onto the Modal root, which is ``position: fixed; inset: 0`` for every
  popover and would make any geometry/visibility reading meaningless.

``sidebar-toggle`` is pre-existing app-shell chrome (**on main**); it is also
declared in ``chat_page.py`` and ``onboarding_page.py`` for their own flows — this
object declares it as the header anchor the socket dot and the bell are positioned
against.
"""

import logging

from playwright.sync_api import Locator, Page, Response
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.sidebar_header")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# The unread-count probe the bell's badge is driven by:
# GET /api/v2/notifications/notifications/prompt_lib/{personal_project_id}
#     ?only_new=true&only_total=true&limit=1&offset=0
# Distinguished from the notification-center LIST fetch (same URL prefix) by
# `only_total=true`; NotificationCenterPage keys off `sort_by=created_at` for the
# opposite reason.
NOTIFICATIONS_URL_SUBSTRING = "/notifications/notifications/prompt_lib/"
NOTIFICATIONS_UNREAD_COUNT_MARKER = "only_total=true"


class SidebarHeaderPage(BasePage):
    """The sidebar header row: ELITEA logo (+ socket dot) and the notification bell."""

    logo_button = LocatorDescriptor(
        testid="sidebar-toggle",
        description="Sidebar header logo IconButton carrying the ELITEA wordmark "
        "(EliteAIcon). The socket-status dot renders inside it, absolutely "
        "positioned at its top-right corner.",
    )
    socket_status_indicator = LocatorDescriptor(
        testid="sidebar-socket-status-indicator",
        description="8x8 round socket-connection dot inside the logo button. ONE "
        "element for both states: green (#2BD48D) when connected, red (#D71616) "
        "when disconnected; the semantic state is on data-socket-status. MUI's "
        "Tooltip clones its title onto this element as aria-label "
        "('Elitea is connected'), readable without hovering.",
    )
    notifications_button = LocatorDescriptor(
        testid="sidebar-notifications-button",
        description="Clickable bell container, right of the logo in the sidebar "
        "header. Rendered ONLY while the sidebar is expanded "
        "(`{!sideBarCollapsed && <Buttons.NotificationButton />}`).",
    )
    notifications_bell_icon = LocatorDescriptor(
        testid="sidebar-notifications-bell-icon",
        description="The bell SVG itself. Carries data-has-messages='true|false' — "
        "the badge state, since the red dot is a <circle> inside this SVG and "
        "cannot be located on its own.",
    )
    notifications_popover = LocatorDescriptor(
        testid="sidebar-notifications-popover",
        description="Notifications Popover PAPER (NotificationList.jsx). A MUI "
        "Popover, not a modal: no backdrop, and an outside click or Escape closes "
        "it too. MUI unmounts it on close (no keepMounted), so 'closed' is "
        "to_have_count(0).",
    )
    notifications_popover_title = LocatorDescriptor(
        testid="sidebar-notifications-popover-title",
        description="Popover header title — the literal text 'Notifications'.",
    )
    notifications_close_button = LocatorDescriptor(
        testid="sidebar-notifications-close-button",
        description="Popover header 'X' button (aria-label='Close notifications').",
    )
    notifications_mark_all_read_button = LocatorDescriptor(
        testid="sidebar-notifications-mark-all-read-button",
        description="'Mark all as read' footer button. Rendered ONLY when "
        "notifications.length > 0 (NotificationList.jsx), which makes its presence "
        "the product's own 'the list is non-empty' observable.",
    )

    # Class-level scoped / state-filtered selectors (per .claude/rules/page-objects.md
    # — never built inside a method body).
    SOCKET_INDICATOR_IN_LOGO = (
        '[data-testid="sidebar-toggle"] [data-testid="sidebar-socket-status-indicator"]'
    )
    SOCKET_INDICATOR_CONNECTED = (
        '[data-testid="sidebar-socket-status-indicator"][data-socket-status="connected"]'
    )
    SOCKET_INDICATOR_DISCONNECTED = (
        '[data-testid="sidebar-socket-status-indicator"][data-socket-status="disconnected"]'
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Scoped locators
    # ------------------------------------------------------------------

    def socket_indicator_in_logo(self) -> Locator:
        """The socket dot resolved as a DESCENDANT of the logo button.

        'Displayed above the ELITEA logo' is a relationship, not a coordinate —
        a regression that moved the indicator elsewhere in the header would still
        satisfy a bare ``to_be_visible()`` on the unscoped locator.
        """
        return self.page.locator(self.SOCKET_INDICATOR_IN_LOGO)

    def socket_indicator_connected(self) -> Locator:
        """Socket dot filtered on ``data-socket-status="connected"``."""
        return self.page.locator(self.SOCKET_INDICATOR_CONNECTED)

    def socket_indicator_disconnected(self) -> Locator:
        """Socket dot filtered on ``data-socket-status="disconnected"`` — used as an
        absence assertion for the case's 'no red dot is shown' step."""
        return self.page.locator(self.SOCKET_INDICATOR_DISCONNECTED)

    # ------------------------------------------------------------------
    # Navigation / product-produced state
    # ------------------------------------------------------------------

    def _is_unread_count_response(self, response: Response) -> bool:
        """True for the bell's own unread-count probe, false for the notification
        centre's paginated list fetch (same URL prefix, no ``only_total``)."""
        return (
            NOTIFICATIONS_URL_SUBSTRING in response.url
            and NOTIFICATIONS_UNREAD_COUNT_MARKER in response.url
            and response.request.method == "GET"
        )

    def navigate_and_get_unread_total(self, path: str = "/chat") -> int:
        """Navigate to *path* and return the unread-notification ``total`` the
        PRODUCT itself computed for the badge.

        The badge is a pure function of this number
        (``setHasMessages(!!data?.total)``, ``NotificationButton.jsx:63``), so
        capturing the product's own response gives the assertion a real oracle
        instead of a hand-written payload — ``.agents/testing.md`` § *How to test a
        NONDETERMINISTIC producer without substituting it*. Nothing is mocked,
        injected or seeded.

        Returns:
            The ``total`` field of the unread-count response body.
        """
        with self.page.expect_response(
            self._is_unread_count_response, timeout=NAVIGATION_TIMEOUT
        ) as response_info:
            super().navigate(path)
        response = response_info.value
        assert response.status == 200, (
            f"Expected the unread-notification count probe to return 200, "
            f"got {response.status} for {response.url}"
        )
        total = response.json()["total"]
        logger.info("Unread notification total reported by the product: %s", total)
        return total

    # ------------------------------------------------------------------
    # Notifications popover
    # ------------------------------------------------------------------

    @staticmethod
    def _is_notification_list_response(response: Response) -> bool:
        """True for the POPOVER's own paginated notification-list fetch.

        Same URL prefix as the badge's unread-count probe; the probe is the request
        carrying ``only_total=true``, so its ABSENCE is what identifies the list
        fetch (verified live):
        ``GET /api/v2/notifications/notifications/prompt_lib/<pid>?only_new=true&limit=5&offset=0``
        """
        return (
            NOTIFICATIONS_URL_SUBSTRING in response.url
            and NOTIFICATIONS_UNREAD_COUNT_MARKER not in response.url
            and response.request.method == "GET"
        )

    @action("Open the notifications popover")
    def open_notifications(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the bell, wait for the popover's OWN list response, then its paper.

        The paper mounts immediately, but its body has three MUTUALLY EXCLUSIVE
        states driven by that request (``NotificationList.jsx``): five ``Skeleton``
        bars while ``isFetching && !notifications.length``, the "No new notifications
        right now" empty state when ``!notifications.length && !isFetching``, and the
        item list plus "Mark all as read" only once ``notifications.length > 0``.
        Returning on the paper alone therefore hands the caller a SKELETON, and every
        content assertion after it races a live DEV round-trip.

        Waiting on the response is deterministic, not a sleep: ``NotificationList``
        mounts only on a bell click (``{notificationListAnchorEl && <NotificationList/>}``,
        ``NotificationButton.jsx``) and its ``useEffect(() => { refetch(); }, [refetch])``
        forces the round-trip on EVERY open, cache or no cache — so the request is
        guaranteed to fire each time this method runs.
        """
        with self.page.expect_response(
            self._is_notification_list_response, timeout=NAVIGATION_TIMEOUT
        ):
            self.notifications_button.click()
        self.notifications_popover.wait_for(state="visible", timeout=timeout)

    @action("Close the notifications popover via its X button")
    def close_notifications(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the popover header's X and wait for MUI to unmount the popover."""
        self.notifications_close_button.click()
        self.notifications_popover.wait_for(state="detached", timeout=timeout)
