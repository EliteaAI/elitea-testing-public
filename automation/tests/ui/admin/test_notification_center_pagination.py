"""UI test — Notifications Center pagination controls are present and functional.

Read-only: pagination changes only client-side page state plus GET requests —
nothing is created, marked or deleted, so there is no cleanup and no shared-state
leak (`.agents/testing.md` § Test data strategy).

Test case: ELITEA-2256
AFS: test-specs/settings-notifications/l2_notifications-center-pagination-controls_ELITEA-2256.md

ZERO substitution — no route mock, no injected state, no API seeding. The page
size, the row set and the totals all come from the product's own list responses,
which are used as the ORACLE for the DOM assertions (`.agents/testing.md`
§ How to test a NONDETERMINISTIC producer without substituting it): the rendered
row count is asserted against ``len(response["rows"])`` and the range label
against the product's own total, never against a number this test chose.

Case-text note (no clarification needed)
----------------------------------------
The case illustrates the range label as "1–50 of 195" (en dash, 195 rows). Live it
is an ASCII hyphen with spaces and the account's real total — e.g. "1 - 50 of 89"
(`GridTablePagination.jsx`: ``${startRow} - ${endRow} of ${totalRows}``). The case
says "e.g.", so this is an illustration rather than a contract; the test asserts
the FORMAT by regex and the numbers against the product's own total.

Markers:
    - ui: requires browser
    - admin: notification-centre suite (matches its sibling specs)
    - p2: priority (AFS metadata l2 — case priority `medium`)
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

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000

#: `NotificationCenter.jsx` initialises `paginationModel.pageSize` to 50.
DEFAULT_PAGE_SIZE = 50
#: The case's own example ("e.g. 10"); one of `PAGE_SIZE_OPTIONS` [5, 10, 50, 100].
TARGET_PAGE_SIZE = 10

#: `GridTablePagination.jsx`: `${startRow} - ${endRow} of ${totalRows}`.
PAGE_INFO_PATTERN = re.compile(r"^(\d+) - (\d+) of (\d+)$")


def _parse_page_info(page_info: str) -> tuple[int, int, int]:
    """Parse the pagination range label into ``(start, end, total)``."""
    match = PAGE_INFO_PATTERN.match(page_info)
    assert match, (
        f"Expected the pagination range label to match '{{start}} - {{end}} of "
        f"{{total}}', got {page_info!r}"
    )
    return tuple(int(group) for group in match.groups())  # type: ignore[return-value]


class TestNotificationCenterPagination:
    """ELITEA-2256 — Notifications Center pagination controls are present and functional."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-notifications/ELITEA-2256_notifications-center-pagination-controls-are-present-and-functional.md",
        "onetest-ai Test Case link",
    )
    def test_notification_center_pagination_controls(self, page):
        """Rows-per-page, range label and prev/next arrows are present, and changing
        the page size and paging forward both re-query the backend and re-render the
        table with the corresponding, disjoint slice of notifications."""
        notif_page = NotificationCenterPage(page)
        console_errors = collect_console_errors(page)

        with allure.step("Step 1 — Navigate to Settings -> Notifications"):
            notif_page.navigate()
            expect(notif_page.table_body).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            'Step 2 — The pagination footer shows the "Rows per page" selector, the '
            "page-range label, and prev/next arrows"
        ):
            expect(notif_page.page_size_select).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert notif_page.get_page_size_value() == str(DEFAULT_PAGE_SIZE), (
                f"Expected the default rows-per-page value {DEFAULT_PAGE_SIZE}, got "
                f"{notif_page.get_page_size_value()!r}"
            )

            expect(notif_page.prev_page_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(notif_page.next_page_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(notif_page.prev_page_button).to_be_disabled()

            initial_start, initial_end, total = _parse_page_info(notif_page.get_page_info())
            assert initial_start == 1, f"Expected the first page to start at row 1, got {initial_start}"
            assert initial_end <= total
            assert total > TARGET_PAGE_SIZE, (
                f"PRECONDITION: this case needs more than {TARGET_PAGE_SIZE} notifications on "
                f"the test account so that selecting {TARGET_PAGE_SIZE} rows/page yields more "
                f"than one page; the account currently holds {total}"
            )
            logger.info("Initial page info: %d - %d of %d", initial_start, initial_end, total)

        with allure.step(
            f'Step 3 — Change "Rows per page" to {TARGET_PAGE_SIZE}: the product re-queries '
            f"with limit={TARGET_PAGE_SIZE}&offset=0"
        ):
            response = notif_page.select_page_size(TARGET_PAGE_SIZE)
            assert response.status == 200, (
                f"Expected the re-query after the page-size change to return 200, got {response.status}"
            )
            assert f"limit={TARGET_PAGE_SIZE}" in response.url, (
                f"Expected the re-query URL to carry limit={TARGET_PAGE_SIZE}, got {response.url}"
            )
            assert "offset=0" in response.url, (
                f"Expected the page-size change to reset to offset=0, got {response.url}"
            )
            first_page_rows = response.json()["rows"]

        with allure.step(
            f"Step 4 — The table now shows {TARGET_PAGE_SIZE} rows and the range label "
            f"reads '1 - {TARGET_PAGE_SIZE} of {{total}}'"
        ):
            expect(notif_page.notification_row).to_have_count(
                TARGET_PAGE_SIZE, timeout=UI_ELEMENT_TIMEOUT
            )
            # The response is the oracle: the UI rendered exactly what the product returned.
            assert notif_page.notification_row.count() == len(first_page_rows), (
                f"Expected the rendered row count to equal the product's own response row "
                f"count ({len(first_page_rows)}), got {notif_page.notification_row.count()}"
            )
            assert notif_page.get_page_size_value() == str(TARGET_PAGE_SIZE), (
                f"Expected the rows-per-page selector to read {TARGET_PAGE_SIZE}, got "
                f"{notif_page.get_page_size_value()!r}"
            )
            start, end, total_after = _parse_page_info(notif_page.get_page_info())
            assert (start, end) == (1, TARGET_PAGE_SIZE), (
                f"Expected the range label to read '1 - {TARGET_PAGE_SIZE} of …', got "
                f"'{start} - {end} of {total_after}'"
            )
            assert total_after == total, (
                f"Expected the total to be unchanged by a page-size change ({total}), got {total_after}"
            )
            first_page_ids = notif_page.get_rendered_row_ids()
            assert first_page_ids == [row["id"] for row in first_page_rows], (
                "Expected the rendered row ids to match the product's own response ids, in order"
            )

        with allure.step("Step 5 — Click the next-page arrow"):
            expect(notif_page.next_page_button).to_be_enabled()
            next_response = notif_page.click_next_page()
            assert next_response.status == 200, (
                f"Expected the next-page fetch to return 200, got {next_response.status}"
            )
            assert f"offset={TARGET_PAGE_SIZE}" in next_response.url, (
                f"Expected the next-page fetch to carry offset={TARGET_PAGE_SIZE}, got "
                f"{next_response.url}"
            )
            assert f"limit={TARGET_PAGE_SIZE}" in next_response.url, (
                f"Expected the next-page fetch to keep limit={TARGET_PAGE_SIZE}, got "
                f"{next_response.url}"
            )
            second_page_rows = next_response.json()["rows"]

        with allure.step(
            "Step 6 — The range label updates and a genuinely new set of notifications is shown"
        ):
            start, end, total_page_two = _parse_page_info(notif_page.get_page_info())
            assert (start, end) == (TARGET_PAGE_SIZE + 1, TARGET_PAGE_SIZE * 2), (
                f"Expected the range label to read "
                f"'{TARGET_PAGE_SIZE + 1} - {TARGET_PAGE_SIZE * 2} of …', got "
                f"'{start} - {end} of {total_page_two}'"
            )
            assert total_page_two == total, (
                f"Expected the total to be unchanged by paging ({total}), got {total_page_two}"
            )

            second_page_ids = notif_page.get_rendered_row_ids()
            assert second_page_ids == [row["id"] for row in second_page_rows], (
                "Expected page 2's rendered row ids to match the product's own response ids, in order"
            )
            assert set(second_page_ids).isdisjoint(set(first_page_ids)), (
                f"Expected page 2 to show a NEW set of notifications; ids overlapping page 1: "
                f"{sorted(set(second_page_ids) & set(first_page_ids))}"
            )
            expect(notif_page.prev_page_button).to_be_enabled()

        with allure.step("Step 7 — No unexpected console errors were logged"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
