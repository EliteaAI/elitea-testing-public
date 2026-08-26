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

Locator provenance (ELITEA-2258, adds read/unread visual-distinction
coverage — ``EliteaAI/EliteaUI@e0d98f4a`` on ``automation/testids``, not yet
on ``main``): the pre-existing ``notification-message-text`` testid sits on
the message cell's wrapper ``<Box>``, whose computed ``color`` is the
inherited default and does NOT change with ``is_seen`` — the read/unread
colour lives on the inner ``<Typography>`` nodes. Two testids were added for
those: ``notification-message-typography`` is caller-supplied, additive prop
plumbing only (``NotificationTable.jsx``'s ``renderCell`` passes
``messageTestId`` → ``NotificationListItem`` forwards it as ``testId`` →
``NotificationListItemMessage`` renders it as ``data-testid`` on the EXISTING
``<Typography sx={{ color: textColor }}>``); caller-supplied because both
components are shared with the sidebar bell popover (``context='list'``),
which must not gain a testid it never uses (`.agents/testing.md` § shared
components / blanket-add ban). ``notification-date-text`` is a plain
``data-testid`` attribute on the ``created_at`` ``<Typography>`` rendered by
``NotificationTable.jsx``'s own ``renderCell`` — a page-owned file, no shared
component touched.

ELITEA-2264 (search filtering) needed NO new testid — ``notifications-search-input``
and ``notifications-pagination-page-info`` already exist (``EliteaAI/EliteaUI@7f772acc``).
"""

import logging
import re

from playwright.sync_api import Locator, Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

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

# Query param the list GET gains once the debounced search term reaches
# ``MIN_SEARCH_LENGTH`` (2) — ELITEA-2264. Its PRESENCE distinguishes a
# filtered list fetch from the unfiltered one, and its ABSENCE is what proves
# the search was cleared.
NOTIFICATIONS_SEARCH_URL_MARKER = "search="

# Page-info label format rendered by ``GridTablePagination``: "1 - 50 of 89"
# (ASCII hyphen, spaces around it).
PAGE_INFO_PATTERN = re.compile(r"^(\d+)\s*-\s*(\d+)\s+of\s+(\d+)$")

# Bounded window used to prove a request did NOT fire. Comfortably longer than
# the product's 600 ms search debounce, so "nothing fired" is a real verdict
# and not an impatient one. This is a framework wait (``expect_request``
# timing out), never a sleep.
NO_REQUEST_SETTLE_TIMEOUT = 4_000


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

    # ---- ELITEA-2258: per-row colour sources + click target ----
    # Each of these repeats once per rendered row, so they are scoped to ONE row
    # through that row's own ``notification-checkbox-{id}`` testid. Every hop of
    # the selector is a ``[data-testid=`` term (`.agents/testing.md` § Locator
    # policy — no raw handles, no inline ``get_by_test_id(f"...")``).
    ROW_MESSAGE_TYPOGRAPHY = (
        '[data-testid="notification-row"]:has([data-testid="notification-checkbox-{}"]) '
        '[data-testid="notification-message-typography"]'
    )
    ROW_DATE_TEXT = (
        '[data-testid="notification-row"]:has([data-testid="notification-checkbox-{}"]) '
        '[data-testid="notification-date-text"]'
    )

    #: ``getComputedStyle`` read used by the colour getters below. This is a
    #: READ of a value the product itself computed, not a substitution: nothing
    #: is fabricated, injected or replaced (`.agents/testing.md` § Fidelity
    #: policy). Precedent in-repo: ``agent_form_page.py`` reads a computed colour
    #: the same way. There is no other way to observe a computed colour.
    COMPUTED_COLOR_JS = "el => window.getComputedStyle(el).color"

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

    def column_header_texts(self, fields: list[str], timeout: int = UI_ELEMENT_TIMEOUT) -> list[str]:
        """Rendered labels of the *fields* column headers, **in the order the DOM
        renders them** — deliberately NOT in the order of *fields*.

        ELITEA-2255 step 5 asserts the three data columns read "Type",
        "Notification", "Date & Time" *in that order*. Resolving each header by
        its own testid and returning them in the caller's order (the shape this
        method had before fix-round 1) proves each label exists but is blind to
        column ORDER: it returns the argument order no matter how the DOM is
        laid out, so a swapped-column regression passes.

        A comma-joined CSS union is matched with ``querySelectorAll``
        semantics, so its matches come back in **document order** and the
        argument order cannot influence the result — which is what makes the
        caller's ``== [expected labels]`` comparison an order assertion.
        Pinned by ``tests/unit/test_notification_column_header_dom_order.py``.
        """
        union = ", ".join(self.NOTIFICATION_COLUMN_HEADER.format(field) for field in fields)
        headers = self.page.locator(union)
        headers.first.wait_for(state="visible", timeout=timeout)
        return [text.strip() for text in headers.all_inner_texts()]

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


    # ------------------------------------------------------------------
    # ELITEA-2258 — read/unread visual distinction
    # ------------------------------------------------------------------

    def _row_message_typography(self, notification_id) -> Locator:
        return self.page.locator(self.ROW_MESSAGE_TYPOGRAPHY.format(notification_id))

    def _row_date_text(self, notification_id) -> Locator:
        return self.page.locator(self.ROW_DATE_TEXT.format(notification_id))

    def get_row_message_color(self, notification_id, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Return the computed ``color`` of the row's message ``<Typography>``.

        The colour the PRODUCT computed from its own theme tokens
        (``text.primary``/``text.secondary``, driven by ``is_seen``) — the test
        only reads it. Callers must compare colours to each other, never to a
        hardcoded rgb string: these are theme tokens and a palette or light/dark
        change would break a literal while the read-vs-unread contract still holds.
        """
        element = self._row_message_typography(notification_id)
        element.wait_for(state="visible", timeout=timeout)
        return element.evaluate(self.COMPUTED_COLOR_JS)

    def get_row_date_color(self, notification_id, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Return the computed ``color`` of the row's ``created_at`` ``<Typography>``.

        Same read-only, product-computed semantics as ``get_row_message_color``.
        """
        element = self._row_date_text(notification_id)
        element.wait_for(state="visible", timeout=timeout)
        return element.evaluate(self.COMPUTED_COLOR_JS)

    def wait_for_row_colors_to_change(
        self,
        notification_id,
        previous_message_color: str,
        previous_date_color: str,
        timeout: int = UI_ELEMENT_TIMEOUT,
    ) -> None:
        """Block until the row's message AND date colours differ from the given
        baselines.

        Re-rendering after the mark-read refetch is asynchronous, so reading the
        colours straight after the PUT resolves can race the repaint. These are
        auto-retrying web-first assertions on the same computed-style oracle the
        getters read — a framework wait, never a sleep.
        """
        expect(self._row_message_typography(notification_id)).not_to_have_css(
            "color", previous_message_color, timeout=timeout
        )
        expect(self._row_date_text(notification_id)).not_to_have_css(
            "color", previous_date_color, timeout=timeout
        )

    def click_row_expecting_no_mark_mutation(
        self, notification_id, settle_timeout: int = NO_REQUEST_SETTLE_TIMEOUT
    ) -> bool:
        """Click the row (its date cell) and report whether NO bulk-mark request fired.

        Returns:
            ``True`` when no ``PUT`` to the notifications endpoint was observed
            within *settle_timeout* — i.e. the click did not change the row's
            read state.

        The DATE cell is the click target rather than the message cell because
        the message cell's ``<Typography>`` embeds an inline ``<Link
        target="_blank">``: clicking it can land on the anchor and open a tab,
        which is a different case element ("open the linked entity"). The date
        cell is link-free, so this is an unambiguous row click.

        Absence is proven with a bounded ``expect_request`` that is EXPECTED to
        time out — a framework wait, not a sleep.
        """
        fired = True
        try:
            with self.page.expect_request(
                lambda request: (
                    NOTIFICATIONS_LIST_URL_SUBSTRING in request.url and request.method == "PUT"
                ),
                timeout=settle_timeout,
            ):
                cell = self._row_date_text(notification_id)
                cell.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                cell.click()
        except PlaywrightTimeoutError:
            fired = False
        logger.info(
            "Clicked row %s; bulk-mark PUT observed within %dms: %s",
            notification_id,
            settle_timeout,
            fired,
        )
        return not fired

    def restore_notification_unread(self, notification_id) -> None:
        """Cleanup helper — put *notification_id* back into the unread state.

        Idempotent: reloads to read the server's current truth first and does
        nothing when the notification is already unread, so it is safe to call
        from a ``finally`` block whatever the test's outcome was.
        """
        if notification_id is None:
            return
        rows = self.reload_and_get_rows()
        current = {row["id"]: row["is_seen"] for row in rows}
        if current.get(notification_id) is not True:
            logger.info("Notification %s already unread — nothing to restore", notification_id)
            return
        self.check_notification_checkbox(notification_id)
        restored_rows = self.click_mark_toggle()
        restored = {row["id"]: row["is_seen"] for row in restored_rows}
        assert restored.get(notification_id) is False, (
            f"Cleanup failed to restore notification {notification_id} to unread: "
            f"is_seen={restored.get(notification_id)!r}"
        )
        logger.info("Restored notification %s to unread", notification_id)

    # ------------------------------------------------------------------
    # ELITEA-2264 — search filtering
    # ------------------------------------------------------------------

    def _is_notifications_search_response(self, response) -> bool:
        """True for a notification-list GET that carries a ``search=`` parameter."""
        return (
            self._is_notifications_list_response(response)
            and NOTIFICATIONS_SEARCH_URL_MARKER in response.url
        )

    def _sync_rendered_rows_with(self, response, timeout: int = UI_ELEMENT_TIMEOUT) -> list[dict]:
        """Wait until the table renders exactly as many rows as *response* returned.

        The response resolving does not mean React has committed the new rows;
        this pins the DOM to the product's own payload before any caller reads
        rendered text or ids.
        """
        rows = response.json()["rows"]
        expect(self.notification_row).to_have_count(len(rows), timeout=timeout)
        return rows

    def search_notifications(self, term: str, timeout: int = NAVIGATION_TIMEOUT):
        """Type *term* into the search field and wait for the debounced filtered GET.

        Waits on the RESPONSE (the product's 600 ms ``useDebounceValue`` window),
        never on a sleep, then syncs the rendered row count with that response.

        Returns:
            The matched Playwright ``Response`` — callers assert its URL params
            and use its body as the oracle for what should be rendered.
        """
        self.search_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        with self.page.expect_response(
            self._is_notifications_search_response, timeout=timeout
        ) as response_info:
            self.search_input.fill(term)
        response = response_info.value
        self._sync_rendered_rows_with(response)
        logger.info("Searched notifications for %r -> %s", term, response.url)
        return response

    def clear_search(
        self,
        expected_row_count: int,
        settle_timeout: int = NO_REQUEST_SETTLE_TIMEOUT,
        timeout: int = UI_ELEMENT_TIMEOUT,
    ) -> bool:
        """Clear the search field and wait for the unfiltered list to render again.

        Deliberately does NOT wait on a network response. Confirmed live
        2026-08-26: clearing the field issues **no request at all** — RTK-Query
        still holds the unfiltered query it fetched on page load (well inside
        ``keepUnusedDataFor``), so the full list is served from cache. The
        observable that survives either way is the rendered list itself.

        What IS asserted about the network is the absence of a stale FILTERED
        request, proven with a bounded ``expect_request`` that is expected to
        time out — a framework wait, not a sleep.

        Returns:
            ``True`` when no ``search=``-carrying request fired while clearing.
        """
        no_filtered_request = self.fill_search_expecting_no_request(
            "", settle_timeout=settle_timeout
        )
        expect(self.notification_row).to_have_count(expected_row_count, timeout=timeout)
        logger.info(
            "Cleared notification search; %d row(s) rendered again, no filtered request: %s",
            expected_row_count,
            no_filtered_request,
        )
        return no_filtered_request

    def fill_search_expecting_no_request(
        self, term: str, settle_timeout: int = NO_REQUEST_SETTLE_TIMEOUT
    ) -> bool:
        """Type *term* into the search field and report whether NO list request fired.

        Used for the ``MIN_SEARCH_LENGTH`` boundary: a query shorter than 2
        characters is deliberately ignored by the product, so nothing should be
        requested. Absence is proven with a bounded ``expect_request`` that is
        EXPECTED to time out — a framework wait, not a sleep.

        Returns:
            ``True`` when no notification-list request was observed within
            *settle_timeout*.
        """
        self.search_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        fired = True
        try:
            with self.page.expect_request(
                lambda request: (
                    NOTIFICATIONS_LIST_URL_SUBSTRING in request.url
                    and NOTIFICATIONS_SEARCH_URL_MARKER in request.url
                ),
                timeout=settle_timeout,
            ):
                self.search_input.fill(term)
        except PlaywrightTimeoutError:
            fired = False
        logger.info(
            "Typed %r into search; search-carrying request observed within %dms: %s",
            term,
            settle_timeout,
            fired,
        )
        return not fired

    def get_search_value(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Return the search field's currently displayed value."""
        self.search_input.wait_for(state="visible", timeout=timeout)
        return self.search_input.input_value()

    def get_page_total(self, timeout: int = UI_ELEMENT_TIMEOUT) -> int:
        """Return the total row count parsed out of the pagination range label.

        The label is the product's own rendering of the server's ``total``; this
        parses ``"{start} - {end} of {total}"`` and fails loudly on any other shape.
        """
        info = self.get_page_info(timeout=timeout)
        match = PAGE_INFO_PATTERN.match(info)
        assert match, (
            f"Pagination range label did not match the expected "
            f"'{{start}} - {{end}} of {{total}}' format, got {info!r}"
        )
        return int(match.group(3))

    def get_rendered_message_texts(self, timeout: int = UI_ELEMENT_TIMEOUT) -> list[str]:
        """Return every rendered row's message text, in display order."""
        self.notification_message_text.first.wait_for(state="visible", timeout=timeout)
        return self.notification_message_text.all_inner_texts()
