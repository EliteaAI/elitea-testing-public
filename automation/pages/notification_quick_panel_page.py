"""Notification quick panel page object for Elitea platform (GAP-077).

Reachable from ANY page via the sidebar bell button — modeled as a
cross-page overlay object (constructed against whatever ``page`` the test
is currently on), similar in spirit to how other cross-page overlays are
modeled in this suite (e.g. ``components/voice_settings.py``), but using
current-policy testid-only ``LocatorDescriptor`` fields rather than that
file's legacy raw selectors.

Scope is exactly what GAP-077 touches: the bell button, the per-row hover
mark-toggle, and the row's own ``data-seen`` state attribute. The
Notification Center table page (``/settings/notifications``) is out of
scope beyond the one absence check GAP-077's step 8 needs (no per-row
toggle renders in table context) — reused via the same
``mark_toggle_button`` field.

URL: none (overlay reachable from the sidebar on any authenticated page);
Notification Center table lives at /settings/notifications.
"""

import logging

from playwright.sync_api import Page
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.notification_quick_panel")


class NotificationQuickPanelPage(BasePage):
    """Sidebar notification bell + quick panel + per-row mark-read toggle.

    ``NotificationListItem.jsx`` renders the SAME component in both the
    quick panel (``context="list"``) and the Notification Center table
    (``context="table"``) — the mark-toggle only ever renders in the list
    context, so its absence in the table is the compliant testid-based
    proof for GAP-077 step 8 (canon ruling #511 extension: an absence
    check against a real testid is itself a reference).
    """

    bell_button = LocatorDescriptor(
        testid="notification-bell-button",
        description="Sidebar bell button — opens the quick panel popover",
    )

    # One flat testid across all rows (repeated-list-item pattern); state
    # (read/unread) is a `data-*` attribute on the SAME element, per
    # .agents/testing.md "testid = stable identity, state via attribute".
    NOTIFICATION_ITEM_ROW_BY_SEEN = '[data-testid="notification-item-row"][data-seen="{}"]'

    mark_toggle_button = LocatorDescriptor(
        testid="notification-item-mark-toggle-button",
        description="Per-row hover 'Mark as read/unread' toggle (list context only)",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    @action("Open notification quick panel")
    def open_quick_panel(self, timeout: int = 15000) -> None:
        """Click the sidebar bell button to open the quick panel popover.

        Waits for the panel's own list GET
        (``.../notifications/notifications/prompt_lib/{project}?...only_new=true...``,
        excluding the separate bell-count ``only_total`` request) to resolve
        before returning — a short fixed sleep is unreliable here since this
        is a real network round-trip (dev backend), not a local CSS
        animation, and was confirmed to be flaky against a plain sleep.
        """

        def _is_list_response(response) -> bool:
            return (
                "/notifications/notifications/prompt_lib/" in response.url
                and "only_new=true" in response.url
                and "only_total" not in response.url
            )

        with self.page.expect_response(_is_list_response, timeout=timeout):
            self.bell_button.click()
        self.page.wait_for_timeout(200)  # allow React to paint after the response resolves
        logger.info("Notification quick panel opened")

    def unread_rows(self):
        """Return the Locator for all currently-rendered UNREAD rows (``data-seen="false"``)."""
        return self.page.locator(self.NOTIFICATION_ITEM_ROW_BY_SEEN.format("false"))

    def get_unread_row_count(self) -> int:
        """Return how many unread rows are currently rendered in the quick panel."""
        return self.unread_rows().count()

    @action("Hover first unread notification row")
    def hover_first_unread_row(self) -> None:
        """Hover the first unread row — reveals its per-row mark-toggle button."""
        self.unread_rows().first.hover()
        self.page.wait_for_timeout(100)

    def is_mark_toggle_visible(self) -> bool:
        """Return True if a per-row mark-toggle button is currently rendered anywhere on the page.

        The toggle only exists in the DOM while its row is hovered
        (``context === 'list' && isHovered``) — absent both before hover
        and after hover-out, never merely hidden.
        """
        return self.mark_toggle_button.count() > 0 and self.mark_toggle_button.first.is_visible()

    def get_mark_toggle_label(self) -> str:
        """Return the hovered row's mark-toggle ``aria-label`` ('Mark as read' / 'Mark as unread')."""
        return self.mark_toggle_button.first.get_attribute("aria-label") or ""

    @action("Click notification mark-toggle")
    def click_mark_toggle(self) -> None:
        """Click the currently-visible per-row mark-toggle button."""
        self.mark_toggle_button.first.click()
        self.page.wait_for_timeout(300)

    def move_pointer_away(self) -> None:
        """Move the mouse off any row (triggers ``handleMouseLeave`` on the hovered row).

        A plain cursor move, not a locator interaction — used to prove the
        toggle unmounts once its row is no longer hovered (GAP-077 step 7).
        """
        self.page.mouse.move(0, 0)
        self.page.wait_for_timeout(100)
