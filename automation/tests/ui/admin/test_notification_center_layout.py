"""UI test — Notifications Center page loads with correct layout and header.

Read-only verification of the Notifications Center page chrome: header text,
search field, the two toolbar action buttons, the four table columns, and the
absence of a permanent loading state. Nothing is selected, marked, deleted or
created — the logged-in user's real DEV notification history is only read
(`.agents/testing.md` § Test data strategy, read-only-by-default).

Test case: ELITEA-2255
AFS: test-specs/settings-notifications/l1_notifications-center-page-layout-and-header_ELITEA-2255.md

ZERO substitution — no route mock, no injected state, no API seeding. Every
asserted value (header text, column labels, button states, page-range totals) is
produced by the live product against the live DEV backend.

Case-text drift — this test asserts the LIVE contract
-----------------------------------------------------
The case's step 5 names the first toolbar button "Mark as read". Live, there is
ONE physical toggle whose accessible name flips between "Mark selected as read"
and "Mark selected as unread" depending on the current selection's read state
(`NotificationTableToolbar.jsx`); with nothing selected it reads "Mark selected
as unread". Already tracked as clarification EliteaAI/elitea-testing-public#1166
(filed for ELITEA-2259, same button) — not re-filed. The test asserts the name is
one of that known pair, per the reverse-masking guard.

Why "no permanent loading state" needs no loading testid
--------------------------------------------------------
`GridTableContainer.jsx` renders loading / empty / table as three MUTUALLY
EXCLUSIVE branches (`isLoading ? … : isEmpty ? … : children`), and
`GridTablePagination` returns `null` when `totalRows === 0`. So a visible table
body plus a real "{start} - {end} of {total}" range with total > 0 is positive
proof that `isFetching` resolved false and the data branch rendered. Adding a
testid to the SHARED `GridTableContainer` loading node would be a blanket add,
barred by `.agents/testing.md` § Locator policy.

Markers:
    - ui: requires browser
    - admin: notification-centre suite (matches its two sibling specs)
    - p1: priority (AFS metadata l1 — case priority `high`)
    - regression
"""

import logging
import re

import allure
import pytest
from pages.notification_center_page import NotificationCenterPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p1, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000

EXPECTED_HEADER_TEXT = "Notifications Center"
EXPECTED_SEARCH_PLACEHOLDER = "Search"

#: The three data columns, in the DOM order `NOTIFICATION_COLUMNS` declares them,
#: mapped to the exact label each renders. The case's fourth column ("checkbox")
#: is the select-all checkbox, which has no text.
EXPECTED_COLUMNS = [
    ("event_type", "Type"),
    ("notification_text", "Notification"),
    ("created_at", "Date & Time"),
]

#: The mark-toggle button is ONE control whose accessible name flips with the
#: current selection's read state (clarification #1166).
MARK_TOGGLE_LABELS = {"Mark selected as read", "Mark selected as unread"}

#: `GridTablePagination.jsx`: `${startRow} - ${endRow} of ${totalRows}`.
PAGE_INFO_PATTERN = re.compile(r"^(\d+) - (\d+) of (\d+)$")


class TestNotificationCenterLayout:
    """ELITEA-2255 — Notifications Center page loads with correct layout and header."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-notifications/ELITEA-2255_notifications-center-page-loads-with-correct-layout-and-header.md",
        "onetest-ai Test Case link",
    )
    def test_notification_center_page_layout_and_header(self, page):
        """Header, search field, both toolbar actions, the four table columns and a
        settled (non-loading) data state all render on Settings -> Notifications."""
        notif_page = NotificationCenterPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Step 1 — Navigate to Settings -> Notifications: the page loads and the "
            "notification table body is visible"
        ):
            notif_page.navigate()
            assert page.title().startswith("Settings: Notifications"), (
                f"Expected page title to start with 'Settings: Notifications', got {page.title()!r}"
            )
            expect(notif_page.table_body).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step('Step 2 — The page header reads "Notifications Center"'):
            expect(notif_page.page_header).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(notif_page.page_header).to_have_text(EXPECTED_HEADER_TEXT)

        with allure.step(
            'Step 3 — A search input is present in the top-right area (placeholder "Search")'
        ):
            expect(notif_page.search_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(notif_page.search_input).to_be_editable()
            expect(notif_page.search_input).to_have_attribute(
                "placeholder", EXPECTED_SEARCH_PLACEHOLDER
            )

        with allure.step(
            "Step 4 — Both top-right action buttons are present: the mark read/unread "
            "toggle and the delete button (case steps 4-6). Neither is clicked — the "
            "case only asks for presence, and clicking delete would destroy real "
            "notification history."
        ):
            expect(notif_page.mark_toggle_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            mark_label = notif_page.get_mark_toggle_label()
            assert mark_label in MARK_TOGGLE_LABELS, (
                f"Expected the mark-toggle button's accessible name to be one of "
                f"{sorted(MARK_TOGGLE_LABELS)} (clarification #1166 — one toggle, two "
                f"labels), got {mark_label!r}"
            )
            expect(notif_page.delete_selected_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            # Observed initial state: with nothing selected the product's own
            # `isSelectionEmpty` gate disables BOTH bulk actions. Asserted so a
            # regression that makes a destructive bulk action clickable with an
            # empty selection fails loudly.
            assert not notif_page.is_mark_toggle_enabled(), (
                "Expected the mark read/unread toggle to be disabled with no rows selected"
            )
            assert not notif_page.is_delete_selected_enabled(), (
                "Expected the delete-selected button to be disabled with no rows selected"
            )

        with allure.step(
            "Step 5 — The table renders its four columns: select-all checkbox, "
            "Type, Notification, Date & Time"
        ):
            expect(notif_page.select_all_checkbox).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            for field, label in EXPECTED_COLUMNS:
                expect(notif_page.column_header(field)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            rendered_labels = notif_page.column_header_texts([f for f, _ in EXPECTED_COLUMNS])
            assert rendered_labels == [label for _, label in EXPECTED_COLUMNS], (
                f"Expected column headers {[label for _, label in EXPECTED_COLUMNS]} in DOM "
                f"order, got {rendered_labels}"
            )

            row_count = notif_page.notification_row.count()
            assert row_count > 0, (
                "PRECONDITION: the notification table rendered no rows — this read-only "
                "test needs the test account's existing DEV notification history "
                "(see AFS section Test Data). Got 0 rows."
            )
            expect(notif_page.notification_message_text.first).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            logger.info("Table rendered %d notification row(s)", row_count)

        with allure.step(
            "Step 6 — The page is not stuck in a loading state: a real page-range "
            "label is rendered with a non-zero total"
        ):
            page_info = notif_page.get_page_info()
            match = PAGE_INFO_PATTERN.match(page_info)
            assert match, (
                f"Expected the pagination range label to match '{{start}} - {{end}} of "
                f"{{total}}', got {page_info!r} — a missing/blank label would mean the "
                f"page never left the loading (or empty) branch"
            )
            start, end, total = (int(g) for g in match.groups())
            assert total > 0, f"Expected a non-zero notification total, got {total}"
            assert 1 <= start <= end <= total, (
                f"Expected a coherent page range 1 <= start <= end <= total, got {page_info!r}"
            )

        with allure.step("Step 7 — No unexpected console errors were logged"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
