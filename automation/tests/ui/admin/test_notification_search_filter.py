"""UI test — Search field filters notifications by text content.

Test case: ELITEA-2264
AFS: test-specs/settings-notifications/l2_search-filters-notifications-by-text_ELITEA-2264.md

Read-only by construction: the search field issues GET requests only, nothing is
created, mutated or deleted, so this spec is safe to run beside the other
notification specs and needs no cleanup beyond leaving the field empty.

The search term is DERIVED FROM THE PRODUCT'S OWN DATA
------------------------------------------------------
The term is not invented by the test: it is a token taken out of the first
rendered notification's text, chosen so that at least one OTHER rendered row
provably does not contain it. Without that excluded row, "the list filtered"
would be unfalsifiable — a search matching everything would pass. The account's
DEV notification history is real and grows (67 rows on 2026-08-04, 89 on
2026-08-26), so no total, id or term is ever hardcoded.

Substitution declaration
------------------------
ZERO substitution — no ``page.route``, no ``route.fulfill``, no ``page.evaluate``,
no monkeypatching, no stubbed client. Every asserted value (row texts, totals,
request URLs) is produced by the live product against the live DEV backend.

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
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression]

#: Minimum token length considered for a search term. Comfortably above the
#: product's own ``MIN_SEARCH_LENGTH`` (2) so the chosen token is selective
#: rather than matching most of the history by accident.
MIN_TERM_LENGTH = 6

#: A single character — below the product's ``MIN_SEARCH_LENGTH``, so typing it
#: must not trigger any filtering (AFS step 7 boundary).
BELOW_MIN_SEARCH_TERM = "8"

TOKEN_PATTERN = re.compile(rf"[A-Za-z0-9]{{{MIN_TERM_LENGTH},}}")


def _pick_discriminating_term(texts: list[str]) -> tuple[str, int]:
    """Pick a search term out of the FIRST rendered row's own text.

    Walks that row's alphanumeric tokens of length >= ``MIN_TERM_LENGTH`` and
    returns the first one that at least one other rendered row does NOT contain,
    together with that other row's index — the row the filter must exclude.

    Returns:
        ``(term, excluded_row_index)``.

    Raises:
        AssertionError: when no such token exists (every visible notification
            shares every long token), which is a missing precondition, not a
            product failure — reported loudly rather than skipped.
    """
    source_text = texts[0]
    for token in TOKEN_PATTERN.findall(source_text):
        needle = token.lower()
        for index, other in enumerate(texts):
            if index == 0:
                continue
            if needle not in other.lower():
                return token, index
    raise AssertionError(
        "No discriminating search term could be derived from the live notification list: "
        f"every one of the {len(texts)} rendered rows contains every >= {MIN_TERM_LENGTH}-character "
        f"token of the first row ({source_text!r}). The precondition 'notification texts are not "
        "all identical' is not met on this account."
    )


class TestNotificationSearchFilter:
    """ELITEA-2264 — Search field filters notifications by text content."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-notifications/ELITEA-2264_search-filters-notifications-by-text.md",
        "onetest-ai Test Case link",
    )
    def test_search_field_filters_notifications_by_text(self, page):
        """Typing a term drawn from the live list filters the table server-side to
        rows containing it (dropping the pagination total and excluding a known
        non-matching row), clearing the field restores the full list, and a
        single-character query is deliberately ignored."""
        notif_page = NotificationCenterPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Step 1 — Navigate to Settings -> Notifications and record the unfiltered baseline"
        ):
            notif_page.navigate_and_get_rows()
            baseline_total = notif_page.get_page_total()
            baseline_texts = notif_page.get_rendered_message_texts()
            baseline_ids = notif_page.get_rendered_row_ids()
            baseline_row_count = len(baseline_ids)
            assert baseline_row_count > 0, (
                "Expected the notification table to render at least one row before searching"
            )
            assert len(baseline_texts) == baseline_row_count, (
                f"Rendered message texts ({len(baseline_texts)}) and rendered row ids "
                f"({baseline_row_count}) disagree — the table is mid-render"
            )
            logger.info("Baseline: %d rendered rows, total %d", baseline_row_count, baseline_total)

        with allure.step(
            "Step 2 — Derive the search term from the product's own data, with a row it "
            "provably excludes"
        ):
            assert baseline_row_count >= 2, (
                f"Need at least 2 notifications to prove filtering excludes something, got "
                f"{baseline_row_count}"
            )
            term, excluded_index = _pick_discriminating_term(baseline_texts)
            source_id = baseline_ids[0]
            excluded_id = baseline_ids[excluded_index]
            logger.info(
                "Search term %r (from row %s); row %s must be filtered out",
                term,
                source_id,
                excluded_id,
            )

        with allure.step(
            "Step 3 — Type the term into the Search input: the field displays it and the "
            "product issues a server-side filtered list request"
        ):
            response = notif_page.search_notifications(term)
            assert notif_page.get_search_value() == term, (
                f"Expected the search field to display {term!r}, got "
                f"{notif_page.get_search_value()!r}"
            )
            assert f"search={term}" in response.url, (
                f"Expected the filtered list request to carry search={term}, got URL {response.url}"
            )
            assert "sort_by=created_at" in response.url, (
                f"Expected the filtered request to be the notification-list GET (sort_by=created_at), "
                f"got URL {response.url}"
            )
            assert response.status == 200, (
                f"Expected the filtered list request to return 200, got {response.status}"
            )

        with allure.step(
            "Step 4 — The list filtered to matching rows only: total dropped, every rendered "
            "row contains the term, the source row is present and the excluded row is gone"
        ):
            filtered_total = notif_page.get_page_total()
            assert filtered_total < baseline_total, (
                f"Searching {term!r} did not reduce the notification total: {filtered_total} vs "
                f"baseline {baseline_total} — the list was not filtered"
            )
            assert filtered_total >= 1, (
                f"Searching {term!r} — a term taken from a live notification — returned no rows"
            )
            filtered_texts = notif_page.get_rendered_message_texts()
            non_matching = [text for text in filtered_texts if term.lower() not in text.lower()]
            assert not non_matching, (
                f"Filtered list rendered {len(non_matching)} row(s) whose text does not contain "
                f"{term!r}: {non_matching}"
            )
            filtered_ids = notif_page.get_rendered_row_ids()
            assert source_id in filtered_ids, (
                f"The notification the term {term!r} was taken from (id {source_id}) is missing "
                f"from the filtered list {filtered_ids}"
            )
            assert excluded_id not in filtered_ids, (
                f"Notification {excluded_id}, whose text does not contain {term!r}, is still "
                f"rendered after filtering"
            )

        with allure.step(
            "Step 5 — Clear the Search input: the field empties, the unfiltered list renders "
            "again and no stale filtered request is issued"
        ):
            no_filtered_request = notif_page.clear_search(baseline_row_count)
            assert no_filtered_request, (
                "Clearing the search field issued another search=-carrying list request; the "
                "cleared field must not keep querying with a filter"
            )
            assert notif_page.get_search_value() == "", (
                f"Expected the search field to be empty after clearing, got "
                f"{notif_page.get_search_value()!r}"
            )

        with allure.step("Step 6 — All notifications are shown again"):
            restored_total = notif_page.get_page_total()
            assert restored_total == baseline_total, (
                f"Expected the total to return to the baseline {baseline_total} after clearing "
                f"the search, got {restored_total}"
            )
            restored_ids = notif_page.get_rendered_row_ids()
            assert len(restored_ids) == baseline_row_count, (
                f"Expected {baseline_row_count} rendered rows after clearing the search, got "
                f"{len(restored_ids)}"
            )
            assert excluded_id in restored_ids, (
                f"Notification {excluded_id}, filtered out by the search, did not come back after "
                "the search was cleared"
            )

        with allure.step(
            "Step 7 — A single-character query is deliberately ignored (MIN_SEARCH_LENGTH = 2): "
            "no filtered request fires and the list stays whole"
        ):
            no_request = notif_page.fill_search_expecting_no_request(BELOW_MIN_SEARCH_TERM)
            assert no_request, (
                f"Typing the single character {BELOW_MIN_SEARCH_TERM!r} issued a filtered list "
                "request; the product's MIN_SEARCH_LENGTH = 2 boundary means queries shorter "
                "than 2 characters must not be applied"
            )
            assert notif_page.get_search_value() == BELOW_MIN_SEARCH_TERM, (
                f"Expected the search field to display {BELOW_MIN_SEARCH_TERM!r}, got "
                f"{notif_page.get_search_value()!r}"
            )
            assert notif_page.get_page_total() == baseline_total, (
                f"A single-character query changed the notification total: "
                f"{notif_page.get_page_total()} vs baseline {baseline_total}"
            )
            notif_page.fill_search_expecting_no_request("")
            assert notif_page.get_search_value() == "", (
                "Expected the search field to be left empty at the end of the test"
            )

        with allure.step("Step 8 — No unexpected console errors across the whole flow"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
