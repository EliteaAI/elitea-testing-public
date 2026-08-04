"""Notification Center page object (Settings → Notifications).

URL: /settings/notifications

Covers the notification history table (``NotificationTable.jsx``, built on the
shared ``grid-table`` components) — table body, rows, per-row message text, and
"Next page" pagination.

Locator provenance (ELITEA-2257, testid needed for the whole surface — zero
pre-existing testids in the notification-rendering component tree):
``notification-table-body``/``notification-row`` wire the ``data-testid`` prop
``GridTableBody``/``GridTableRow`` (``src/[fsd]/entities/grid-table/ui/``)
already accepted but ``NotificationTable.jsx`` left unwired.
``notification-message-text`` is a new testid on the message cell wrapper.
``notifications-pagination-next-button`` required a new ``nextButtonTestId``
prop on the shared ``GridTablePagination`` component (it had no ``data-testid``
threading at all) — scoped to the "Next" button only, per
``.agents/role-overrides.md`` § locator scope (the "Prev" button is untouched
by this test).
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.notification_center")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Substring shared by both the paginated list fetch and the "next page" fetch —
# distinguishes the full list request (has `sort_by=created_at`) from the
# separate unread-count probe (`only_new=true&only_total=true`), which also
# hits `/notifications/notifications/prompt_lib/{id}` but must NOT be mistaken
# for the list response the table renders from.
NOTIFICATIONS_LIST_URL_SUBSTRING = "/notifications/notifications/prompt_lib/"
NOTIFICATIONS_LIST_URL_MARKER = "sort_by=created_at"


class NotificationCenterPage(BasePage):
    """Settings → Notifications page (notification history table)."""

    table_body = LocatorDescriptor(
        testid="notification-table-body",
        description="Notification table body — scope for row-count/visibility waits",
    )
    notification_row = LocatorDescriptor(
        testid="notification-row",
        description="Notification row (repeatable, one per visible row)",
    )
    notification_message_text = LocatorDescriptor(
        testid="notification-message-text",
        description="Notification message cell text (excludes type icon + date columns)",
    )
    next_page_button = LocatorDescriptor(
        testid="notifications-pagination-next-button",
        description='Pagination "Next page" button — disabled on the last page',
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def _is_notifications_list_response(self, response) -> bool:
        """True for the paginated notification-list GET, false for the
        unread-count probe (same URL prefix, no ``sort_by`` param)."""
        return (
            NOTIFICATIONS_LIST_URL_SUBSTRING in response.url
            and NOTIFICATIONS_LIST_URL_MARKER in response.url
            and response.request.method == "GET"
        )

    def navigate(self) -> None:
        """Navigate to /settings/notifications and wait for the notification
        list fetch to resolve before the table body is considered ready.

        Waiting on the network response (not just DOM visibility) matters here:
        the table renders its empty state briefly before data arrives, so a
        pure `wait_for(state="visible")` on the table body can race the fetch.
        """
        with self.page.expect_response(
            self._is_notifications_list_response, timeout=NAVIGATION_TIMEOUT
        ):
            super().navigate("/settings/notifications")
        self.table_body.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def click_next_page(self):
        """Click "Next page" and wait for the next page's list fetch to resolve.

        Returns the matched Playwright ``Response``.
        """
        with self.page.expect_response(
            self._is_notifications_list_response, timeout=NAVIGATION_TIMEOUT
        ) as response_info:
            self.next_page_button.click()
        self.notification_message_text.first.wait_for(
            state="visible", timeout=UI_ELEMENT_TIMEOUT
        )
        return response_info.value

    def collect_all_notification_texts(self, max_pages: int = 20) -> list[str]:
        """Collect every notification row's rendered message text across ALL
        pages, clicking "Next page" until it becomes disabled.

        Args:
            max_pages: Safety cap on pagination trips (headroom for data growth,
                not an expected trip count — the loop is expected to terminate
                via the disabled "Next" button well before this).

        Returns:
            List of each row's `inner_text()`, in display order, across every
            page visited.

        Raises:
            AssertionError: if the "Next page" button is still enabled after
                `max_pages` trips (loop did not terminate as expected).
        """
        texts: list[str] = []
        for page_num in range(max_pages):
            self.notification_message_text.first.wait_for(
                state="visible", timeout=UI_ELEMENT_TIMEOUT
            )
            texts.extend(self.notification_message_text.all_inner_texts())
            if self.next_page_button.is_disabled():
                logger.info(
                    "Pagination loop terminated after %d page(s), %d row(s) collected",
                    page_num + 1,
                    len(texts),
                )
                return texts
            self.click_next_page()
        raise AssertionError(
            f"Pagination did not terminate (Next page still enabled) within the "
            f"safety cap of {max_pages} pages — {len(texts)} row(s) collected so far"
        )
