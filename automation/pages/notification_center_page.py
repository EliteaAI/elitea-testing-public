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

Locator provenance (ELITEA-2259, adds bulk mark-read/unread coverage):
``notification-checkbox-{id}`` wires ``GridTableRow``'s existing
``checkboxTestId`` prop (already accepted, same shape as
``ArtifactTable.jsx``'s ``artifacts-file-checkbox-${row.id}``) — new
``checkboxTestId={`notification-checkbox-${row.id}`}`` call-site prop on
``NotificationTable.jsx``'s ``<GridTableRow>``. ``notification-mark-toggle-button``
is a new static ``data-testid`` on the toolbar's single read/unread toggle
button (``NotificationTableToolbar.jsx``'s ``BaseBtn``) — the testid stays
constant while the button's ``aria-label`` flips between "Mark selected as
read"/"Mark selected as unread" depending on the current selection's read
state (state lives in the accessible name, not the testid, per
``.agents/testing.md`` § "Testid = stable identity"). ``toast-message`` is the
pre-existing app-wide toast testid (see ``ArtifactsPage.success_toast_message``).

Locator provenance (ELITEA-2255 / ELITEA-2256, adds page-layout and pagination
coverage — ``EliteaAI/EliteaUI@7f772acc`` on ``automation/testids``, not yet on
``main``): every handle below is CALL-SITE wiring of a prop the shared component
already accepted, except two plain attribute adds in ``NotificationTableToolbar.jsx``.
``notifications-center-header`` is a new ``data-testid`` on the toolbar's header
``<Typography>``; ``notifications-search-input`` uses ``SimpleSearchBar``'s existing
``data-testid`` prop (threaded onto its ``InputBase`` ``inputProps``);
``notifications-delete-selected-button`` uses a NEW additive ``buttonTestId`` prop on
``DeleteEntityButton``'s inner ``IconButton`` (``EliteaAI/EliteaUI@30a15ac6``) — its
pre-existing ``testId`` prop lands on the Tooltip's wrapper ``<Box component="span">``,
where ``is_disabled()`` is always ``False``; the call site passes ``buttonTestId``
INSTEAD of ``testId`` so exactly one testid exists, on the button; ``notifications-select-all-checkbox`` and
``notifications-column-header-{field}`` use ``GridTableHeader``'s existing
``selectAllCheckboxTestId`` / ``columnTestIdPrefix`` props;
``notifications-pagination-{prev-button,page-info,page-size-select}`` use
``GridTablePagination``'s existing ``prevButtonTestId`` / ``pageInfoTestId`` /
``pageSizeSelectTestId`` props. ``notifications-pagination-page-size-select-combobox``
is derived automatically by ``SingleSelect.jsx``
(``SelectDisplayProps={{'data-testid': `${dataTestId}-combobox`}}``) — it is the
CLICKABLE display node, whereas the bare ``…-page-size-select`` testid lands on the
MUI ``Select`` root. ``notifications-page-size-option-{n}`` is a per-option ``testId``
supplied at the ``NotificationTable.jsx`` call site and consumed by the pre-existing
``SingleSelectMenuItem.jsx`` line ``data-testid={option.testId ?? …}`` — caller-supplied,
so no other ``SingleSelect`` in the app gains a testid.
"""

import logging

from playwright.sync_api import Locator, Page

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
    mark_toggle_button = LocatorDescriptor(
        testid="notification-mark-toggle-button",
        description="Table toolbar's single mark-selected read/unread toggle button "
        "(ELITEA-2259). One physical button — its accessible name flips between "
        "'Mark selected as read' / 'Mark selected as unread' depending on whether "
        "the currently-selected rows include any unread notification; the testid "
        "itself never changes.",
    )
    success_toast_message = LocatorDescriptor(
        testid="toast-message",
        description="Generic app-wide success toast (reused — see "
        "ArtifactsPage.success_toast_message / SkillsListPage.import_success_toast_message).",
    )

    # Dynamic testid template — per-row checkbox, keyed by notification id
    # (ELITEA-2259). Same shape as ArtifactsPage.ARTIFACT_FILE_CHECKBOX.
    NOTIFICATION_ROW_CHECKBOX = '[data-testid="notification-checkbox-{}"]'

    # ---- ELITEA-2255: page layout / header ----
    page_header = LocatorDescriptor(
        testid="notifications-center-header",
        description='Toolbar page header — renders the literal text "Notifications Center"',
    )
    search_input = LocatorDescriptor(
        testid="notifications-search-input",
        description='Toolbar search field (SimpleSearchBar\'s inner <input>, placeholder "Search")',
    )
    delete_selected_button = LocatorDescriptor(
        testid="notifications-delete-selected-button",
        description="Toolbar delete-selected (trash) button — disabled until a row is selected",
    )
    select_all_checkbox = LocatorDescriptor(
        testid="notifications-select-all-checkbox",
        description="Table header's select-all checkbox — the case's 'checkbox' column",
    )

    # ---- ELITEA-2256: pagination footer ----
    page_info_label = LocatorDescriptor(
        testid="notifications-pagination-page-info",
        description='Pagination range label, format "{start} - {end} of {total}"',
    )
    prev_page_button = LocatorDescriptor(
        testid="notifications-pagination-prev-button",
        description='Pagination "Previous page" button — disabled on the first page',
    )
    page_size_select = LocatorDescriptor(
        testid="notifications-pagination-page-size-select",
        description="Rows-per-page select ROOT (MUI Select). Read its text here; "
        "CLICK page_size_select_combobox instead — the root is not the clickable node.",
    )
    page_size_select_combobox = LocatorDescriptor(
        testid="notifications-pagination-page-size-select-combobox",
        description="Rows-per-page select's clickable display node (SingleSelect derives "
        "this testid from the root's via SelectDisplayProps)",
    )

    # Dynamic testid template — one per grid-table data column, keyed by the
    # column's `field` (event_type / notification_text / created_at). Class-level
    # per `.agents/testing.md` § Locator policy (inline get_by_test_id(f"...") is
    # not the compliant shape).
    NOTIFICATION_COLUMN_HEADER = '[data-testid="notifications-column-header-{}"]'

    # Dynamic testid template — one per rows-per-page option (5/10/50/100).
    PAGE_SIZE_OPTION = '[data-testid="notifications-page-size-option-{}"]'

    # Scoped compound selector — every rendered row checkbox, scoped inside the
    # table body's own testid. Used to read the rendered row-id set without
    # touching a raw (non-testid) handle.
    ROW_CHECKBOXES_IN_BODY = (
        '[data-testid="notification-table-body"] [data-testid^="notification-checkbox-"]'
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

    def _is_notifications_bulk_mark_response(self, response) -> bool:
        """True for the bulk mark-seen/unseen PUT (same URL prefix as the list
        GET/the unread-count probe GET, differs only by HTTP method)."""
        return (
            NOTIFICATIONS_LIST_URL_SUBSTRING in response.url
            and response.request.method == "PUT"
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

    def navigate_and_get_rows(self) -> list[dict]:
        """Navigate to /settings/notifications and return the initial list
        fetch's parsed ``rows[]`` (each row carries ``id`` and ``is_seen``).

        Used to dynamically discover unread notifications (ELITEA-2259 step 2)
        instead of hardcoding notification ids.
        """
        with self.page.expect_response(
            self._is_notifications_list_response, timeout=NAVIGATION_TIMEOUT
        ) as response_info:
            super().navigate("/settings/notifications")
        self.table_body.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        return response_info.value.json()["rows"]

    def reload_and_get_rows(self) -> list[dict]:
        """Reload the page (full navigation) and return the resulting list
        fetch's parsed ``rows[]``.

        Used for the "state persists after reload" checks (ELITEA-2259 steps
        6, 10) — a full reload, not an SPA re-fetch, to confirm server-side
        persistence.
        """
        with self.page.expect_response(
            self._is_notifications_list_response, timeout=NAVIGATION_TIMEOUT
        ) as response_info:
            self.page.reload(wait_until="domcontentloaded")
        self.table_body.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        return response_info.value.json()["rows"]

    def check_notification_checkbox(self, notification_id, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Check the per-row checkbox for the notification with *notification_id*."""
        checkbox = self.page.locator(self.NOTIFICATION_ROW_CHECKBOX.format(notification_id))
        checkbox.wait_for(state="visible", timeout=timeout)
        checkbox.click()
        logger.info("Checked checkbox for notification id %s", notification_id)

    def is_notification_checkbox_checked(self, notification_id, timeout: int = UI_ELEMENT_TIMEOUT) -> bool:
        """Return whether the notification's checkbox is currently checked.

        Same shape as ``ArtifactsPage.is_file_checkbox_checked`` (ELITEA-1840):
        the ``data-testid`` lands on the MUI ``Checkbox`` root, not the nested
        ``<input>``, so Playwright's ``is_checked()`` raises "Not a checkbox or
        radio button" on it — read the ``Mui-checked`` class instead.
        """
        checkbox = self.page.locator(self.NOTIFICATION_ROW_CHECKBOX.format(notification_id))
        checkbox.wait_for(state="visible", timeout=timeout)
        class_attr = checkbox.get_attribute("class") or ""
        return "Mui-checked" in class_attr

    def get_mark_toggle_label(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Return the mark-toggle button's current accessible name
        ('Mark selected as read' / 'Mark selected as unread')."""
        self.mark_toggle_button.wait_for(state="visible", timeout=timeout)
        return self.mark_toggle_button.get_attribute("aria-label") or ""

    def is_mark_toggle_enabled(self, timeout: int = UI_ELEMENT_TIMEOUT) -> bool:
        """Return whether the mark-toggle button is currently enabled."""
        self.mark_toggle_button.wait_for(state="visible", timeout=timeout)
        return not self.mark_toggle_button.is_disabled()

    def click_mark_toggle(self, timeout: int = NAVIGATION_TIMEOUT) -> list[dict]:
        """Click the mark-toggle button; wait for the bulk mark-seen/unseen
        PUT to resolve 200, then for the automatically-triggered list
        refetch (cache-invalidation refetch — no explicit trigger needed),
        and return the refetch's parsed ``rows[]``.

        Returns:
            The post-mutation list fetch's ``rows[]`` (id -> is_seen for
            every row on the current page).
        """
        with self.page.expect_response(
            self._is_notifications_list_response, timeout=timeout
        ) as refetch_info, self.page.expect_response(
            self._is_notifications_bulk_mark_response, timeout=timeout
        ) as put_info:
            self.mark_toggle_button.click()

        put_response = put_info.value
        assert put_response.status == 200, (
            f"Expected the bulk mark-seen/unseen PUT to return 200, got {put_response.status}"
        )
        refetch_response = refetch_info.value
        assert refetch_response.status == 200, (
            f"Expected the post-mutation list refetch to return 200, got {refetch_response.status}"
        )
        logger.info(
            "Clicked mark-toggle button: PUT=%d refetch=%d", put_response.status, refetch_response.status
        )
        return refetch_response.json()["rows"]

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

    # ------------------------------------------------------------------
    # ELITEA-2255 — layout reads
    # ------------------------------------------------------------------

    def column_header(self, field: str) -> Locator:
        """Table column header for *field* (``event_type``/``notification_text``/``created_at``)."""
        return self.page.locator(self.NOTIFICATION_COLUMN_HEADER.format(field))

    def column_header_texts(self, fields: list[str]) -> list[str]:
        """Rendered label of each column header in *fields*, in the order given."""
        return [self.column_header(field).inner_text().strip() for field in fields]

    def is_delete_selected_enabled(self, timeout: int = UI_ELEMENT_TIMEOUT) -> bool:
        """Return whether the toolbar's delete-selected button is currently enabled."""
        self.delete_selected_button.wait_for(state="visible", timeout=timeout)
        return not self.delete_selected_button.is_disabled()

    # ------------------------------------------------------------------
    # ELITEA-2256 — pagination
    # ------------------------------------------------------------------

    def get_page_info(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Return the pagination range label's rendered text, e.g. ``"1 - 50 of 89"``."""
        self.page_info_label.wait_for(state="visible", timeout=timeout)
        return self.page_info_label.inner_text().strip()

    def get_page_size_value(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Return the rows-per-page select's currently displayed value, e.g. ``"50"``."""
        self.page_size_select.wait_for(state="visible", timeout=timeout)
        return self.page_size_select.inner_text().strip()

    def select_page_size(self, page_size: int, timeout: int = NAVIGATION_TIMEOUT):
        """Open the rows-per-page select, choose *page_size*, and wait for the
        resulting notification-list GET.

        Returns the matched Playwright ``Response`` so callers can assert the
        request's own ``limit``/``offset`` and use the response body as the oracle
        for the rendered row count (`.agents/testing.md` § How to test a
        NONDETERMINISTIC producer without substituting it).
        """
        self.page_size_select_combobox.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        self.page_size_select_combobox.click()
        option = self.page.locator(self.PAGE_SIZE_OPTION.format(page_size))
        option.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        with self.page.expect_response(
            self._is_notifications_list_response, timeout=timeout
        ) as response_info:
            option.click()
        logger.info("Selected rows-per-page = %s", page_size)
        return response_info.value

    def get_rendered_row_ids(self) -> list[int]:
        """Return the notification ids of every row currently rendered, in display order.

        Read off each row's ``notification-checkbox-{id}`` testid (scoped inside the
        table body's testid) — the ids the product actually rendered, not a
        test-authored list.
        """
        prefix = "notification-checkbox-"
        testids: list[str] = self.page.locator(self.ROW_CHECKBOXES_IN_BODY).evaluate_all(
            "els => els.map(el => el.getAttribute('data-testid'))"
        )
        return [int(t[len(prefix) :]) for t in testids if t and t.startswith(prefix)]

