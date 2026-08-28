"""UI test — Users tab loads User Activity table with correct columns and pagination.

Read-only verification against the currently-selected project's own analytics
data (`.agents/testing.md` § Test data strategy — prefer read-only assertions
on existing data when the observable doesn't require fresh state). This case
never creates, modifies, or deletes anything — it only checks the Users-tab
panel's structure (header, search input, table columns, pagination) against
whatever users the selected project already has analytics rows for.

Test case: ELITEA-2312
AFS: test-specs/settings-analytics/l2_users-tab-activity-table_ELITEA-2312.md

Case-text drift (see AFS § Known Defects): the case's step 4 lists 8 columns
including a non-existent "EVENTS" column; the live table has 9 columns
(no "Events" column, plus "Total Tokens"/"Total Cost" the case omits). The
case's step 5 says the Errors value is red "when greater or equal 0" —
literally read, every value including 0 would be red; live observation (all
`errors: 0` rows render default/white) plus source
(`AnalyticsUsers.jsx:144-151`) confirm the real threshold is `> 0`. Filed as
clarification elitea-testing-public#1188. This test asserts the live
contract for both.

Column-set repair (2026-08-28, settings-w06 batch): this spec was RED on
`automation/base` before this change — the UI team added eight token/cost
breakdown columns, so the live header is 17 columns, not the 9 recorded when
ELITEA-2312 was automated. The expected tuple below is updated to the live
contract (never weakened — the assertion is still an exact ordered tuple); the
new occurrence is recorded on the existing case-text-drift issue #1188 rather
than filed as a second one.

**ELITEA-2323 (extension)** — Step 8 appends the two assertions the ELITEA-2312
smoke check does not make (AFS
`test-specs/settings-analytics/lextend_users-tab-search-filters-activity-table_ELITEA-2323.md`):
the filtered set is EXCLUSIVE (every rendered row matches the term, the set
equals the search response's own rows, and it is a strict subset of the
unfiltered set — `>= 1` alone passes even if nothing was filtered), and clearing
the input RESTORES the complete original row list, in order, with its count
label (the covering test clears in `finally` with no assertion at all). Step 7
is unchanged apart from two additive captures it now feeds into Step 8.

Positive-branch note (AFS § Blocked Steps originally deferred this — "if a
future project/environment naturally accumulates a user with errors > 0, the
implementer should extend the test to assert the positive branch against
that real row"): the project this suite's `auth_state` fixture authenticates
into ("Private") DOES have such rows live (discovered 2026-08-05 while
debugging the search-filter step) — both branches are asserted here.
"""

import logging
import re

import allure
import pytest
from pages.analytics_page import AnalyticsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

# The header cells' JSX text is title-case, but `tableCell`'s sx applies
# `text-transform: uppercase` — Playwright's `inner_text()` reflects the
# CSS-rendered (uppercase) text, not the JSX source string, so the expected
# tuple matches what actually renders.
EXPECTED_COLUMN_LABELS = (
    "USER",
    "ACTIVE DAYS",
    "LLM CALLS",
    "TOOL CALLS",
    "AGENT/PIPELINE RUNS",
    "CHAT MSG",
    "ERRORS",
    "TOTAL TOKENS",
    "INPUT TOKENS",
    "OUTPUT TOKENS",
    "TOTAL COST",
    "INPUT TOKEN COST",
    "OUTPUT TOKEN COST",
    "CACHE READ TOKENS",
    "CACHE WRITE TOKENS",
    "CACHE READ COST",
    "CACHE WRITE COST",
)

USER_COUNT_PATTERN = re.compile(r"^(\d+) users$")
PAGE_RANGE_PATTERN = re.compile(r"^\d+–\d+ of \d+$")

# Errors-cell text colors (rgb), confirmed live via getComputedStyle against
# the currently-active theme (AFS § Automation Hints — do not hardcode an
# assumed value without confirming per-theme).
ERRORS_DEFAULT_COLOR = "rgb(255, 255, 255)"  # errors === 0
ERRORS_REJECTED_COLOR = "rgb(215, 22, 22)"  # errors > 0 (palette.status.rejected)


class TestAnalyticsUsersActivityTable:
    """ELITEA-2312 — Users tab's User Activity table: header/count, search
    input, 9-column table, and pagination controls."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/analytics/ELITEA-2312_users-tab-loads-user-activity-table-with-correct-columns-and.md",
        "onetest-ai Test Case link (ELITEA-2312)",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/analytics/ELITEA-2323_users-tab-search-by-email-filters-the-user-activity-table.md",
        "onetest-ai Test Case link (ELITEA-2323)",
    )
    def test_users_tab_activity_table_columns_and_pagination(self, page):
        """Users tab renders its "User Activity" panel with a matching user
        count, a working search-by-email input, the correct 9-column table
        (order + Errors-color contract), and single-page pagination controls."""
        analytics_page = AnalyticsPage(page)
        console_errors = analytics_page.capture_console_errors()

        try:
            with allure.step("Step 1 — Navigate to Settings -> Analytics, click the Users tab"):
                analytics_page.navigate()
                analytics_page.open_users_tab()
                assert analytics_page.is_tab_selected(analytics_page.tab_users), (
                    "Expected the 'Users' tab to be aria-selected=true after clicking it"
                )
                assert analytics_page.users_table_header.is_visible(), (
                    "Expected the Users-tab table header to render without error"
                )

            with allure.step(
                'Step 2 — Verify the section header shows "User Activity" and a user-count '
                "line matching the actual row total"
            ):
                assert analytics_page.users_activity_title.text_content() == "User Activity", (
                    f"Expected title 'User Activity', got "
                    f"{analytics_page.users_activity_title.text_content()!r}"
                )
                count_text = analytics_page.users_count.text_content()
                match = USER_COUNT_PATTERN.match(count_text or "")
                assert match, f"Expected count text matching '{{N}} users', got {count_text!r}"
                row_count = analytics_page.get_users_row_count()
                assert int(match.group(1)) == row_count, (
                    f"Expected count {match.group(1)!r} to match the actual rendered row "
                    f"total {row_count}"
                )

            with allure.step(
                'Step 3 — Verify a "Search by email" input is present, positioned top-right '
                'of the User Activity card (same row as the title/count, justify-content: '
                "space-between)"
            ):
                assert analytics_page.users_search_input.is_visible(), (
                    "Expected the 'Search by email' input to be visible"
                )
                assert (
                    analytics_page.users_search_input.get_attribute("placeholder")
                    == "Search by email"
                ), "Expected placeholder text 'Search by email'"
                title_box = analytics_page.users_activity_title.bounding_box()
                search_box = analytics_page.users_search_input.bounding_box()
                assert title_box and search_box, "Expected both title and search input to have a layout box"
                assert search_box["x"] > title_box["x"] + title_box["width"], (
                    f"Expected the search input to sit to the right of the title "
                    f"(title x={title_box['x']}, w={title_box['width']}; search x={search_box['x']})"
                )
                title_mid_y = title_box["y"] + title_box["height"] / 2
                assert search_box["y"] <= title_mid_y <= search_box["y"] + search_box["height"], (
                    "Expected the search input to be vertically aligned with the title/count "
                    "(same row, justify-content: space-between)"
                )

            with allure.step(
                "Step 4 — Verify the table header row shows exactly the 9 live columns, "
                "in order: User, Active Days, LLM Calls, Tool Calls, Agent/Pipeline Runs, "
                "Chat Msg, Errors, Total Tokens, Total Cost"
            ):
                actual_labels = analytics_page.get_users_table_column_labels()
                assert tuple(actual_labels) == EXPECTED_COLUMN_LABELS, (
                    f"Expected column labels {EXPECTED_COLUMN_LABELS}, got {tuple(actual_labels)}"
                )

            with allure.step(
                "Step 5 — Verify the Errors column's value color: errors === 0 renders in "
                "the table's default text color, errors > 0 renders in the red/rejected "
                "status color"
            ):
                row_count = analytics_page.get_users_row_count()
                assert row_count > 0, (
                    "Expected at least one user row to exercise the Errors-color assertion "
                    "against (AFS precondition: project has usage-analytics data)"
                )
                zero_error_rows_checked = 0
                positive_error_rows_checked = 0
                for i in range(row_count):
                    errors_value = analytics_page.get_user_row_errors_value(i)
                    cell = analytics_page.users_row_errors.nth(i)
                    if errors_value == 0:
                        expect(cell).to_have_css("color", ERRORS_DEFAULT_COLOR)
                        zero_error_rows_checked += 1
                    else:
                        expect(cell).to_have_css("color", ERRORS_REJECTED_COLOR)
                        positive_error_rows_checked += 1
                assert zero_error_rows_checked > 0, (
                    "Expected at least one errors===0 row to assert the default-color branch "
                    "against (AFS precondition: project has usage-analytics data)"
                )
                # The errors>0/red branch was originally marked blocked (AFS § Blocked
                # Steps) for lacking live data — asserted above when present (this
                # project currently has such rows), but not required, since it's live
                # data that may legitimately shift to all-zero over time.
                logger.info(
                    "Errors-color check: %d default-color row(s), %d rejected-color row(s)",
                    zero_error_rows_checked,
                    positive_error_rows_checked,
                )

            with allure.step(
                "Step 6 — Verify pagination controls: rows-per-page selector (default 20), "
                "a page-range label matching '{from}–{to} of {count}', and previous/next "
                "buttons (both disabled on a single page)"
            ):
                assert analytics_page.users_pagination_rows_select.text_content() == "20", (
                    f"Expected default rows-per-page value '20', got "
                    f"{analytics_page.users_pagination_rows_select.text_content()!r}"
                )
                range_text = analytics_page.users_pagination_range.text_content()
                assert range_text and PAGE_RANGE_PATTERN.match(range_text), (
                    f"Expected page-range label matching '{{from}}–{{to}} of {{count}}', "
                    f"got {range_text!r}"
                )
                assert analytics_page.users_pagination_prev.is_disabled(), (
                    "Expected the previous-page button to be disabled on a single page"
                )
                assert analytics_page.users_pagination_next.is_disabled(), (
                    "Expected the next-page button to be disabled on a single page "
                    "(count <= rowsPerPage)"
                )

            with allure.step(
                "Step 7 — Search-filter smoke check: typing an existing user's email "
                "substring narrows the table and updates the count/pagination label"
            ):
                # Captured for ELITEA-2323's Step 8 (additive — the existing
                # assertions below are unchanged): the unfiltered row list and
                # count label, read immediately before the search narrows them.
                pre_row_identifiers = [
                    analytics_page.get_user_row_identifier(i) for i in range(row_count)
                ]
                pre_count_text = analytics_page.users_count.text_content()
                # Search matches the email field server-side — a row lacking an email
                # (rendered as "User {id}") won't match its own display text, so scan
                # for the first row that actually has one rather than assuming row 0.
                email_identifier = next(
                    (
                        identifier
                        for identifier in (
                            analytics_page.get_user_row_identifier(i) for i in range(row_count)
                        )
                        if "@" in identifier
                    ),
                    None,
                )
                assert email_identifier, (
                    "Expected at least one user row with an email identifier to search for "
                    "(AFS precondition: project has usage-analytics data with an emailed user)"
                )
                search_term = email_identifier.split("@")[0]
                search_response = analytics_page.search_users(search_term)
                filtered_row_count = analytics_page.get_users_row_count()
                assert filtered_row_count >= 1, (
                    f"Expected at least one row to remain after searching {search_term!r}"
                )
                filtered_count_text = analytics_page.users_count.text_content()
                filtered_match = USER_COUNT_PATTERN.match(filtered_count_text or "")
                assert filtered_match and int(filtered_match.group(1)) == filtered_row_count, (
                    f"Expected the count label to update to match the filtered row total "
                    f"{filtered_row_count}, got {filtered_count_text!r}"
                )
                filtered_range_text = analytics_page.users_pagination_range.text_content()
                assert filtered_range_text and PAGE_RANGE_PATTERN.match(filtered_range_text), (
                    f"Expected the pagination range label to still match the pattern after "
                    f"filtering, got {filtered_range_text!r}"
                )

            with allure.step(
                "Step 8 — ELITEA-2323: the search result is EXCLUSIVE (only matching rows, "
                "matching the search response, strictly fewer than before) and clearing the "
                "input restores the complete original table"
            ):
                assert analytics_page.users_search_input.input_value() == search_term, (
                    f"Expected the search input to hold the typed term {search_term!r}, got "
                    f"{analytics_page.users_search_input.input_value()!r}"
                )
                filtered_identifiers = [
                    analytics_page.get_user_row_identifier(i)
                    for i in range(analytics_page.get_users_row_count())
                ]
                assert filtered_identifiers, (
                    f"Expected at least one row to match {search_term!r} (it was derived from a "
                    f"row the table itself rendered)"
                )
                non_matching = [
                    identifier
                    for identifier in filtered_identifiers
                    if search_term.lower() not in identifier.lower()
                ]
                assert not non_matching, (
                    f"Expected every remaining row to match {search_term!r}, but these do not: "
                    f"{non_matching}"
                )
                expected_identifiers = [
                    row.get("user_email") or f"User {row.get('user_id')}"
                    for row in search_response.get("rows", [])
                ]
                assert filtered_identifiers == expected_identifiers, (
                    f"Expected the rendered rows to be exactly the search response's rows "
                    f"{expected_identifiers}, got {filtered_identifiers}"
                )
                assert len(filtered_identifiers) < len(pre_row_identifiers), (
                    f"Expected the search to narrow the table (strictly fewer than the "
                    f"{len(pre_row_identifiers)} unfiltered rows), got "
                    f"{len(filtered_identifiers)} — a filter that returns everything would "
                    f"still satisfy a 'at least one row remains' check"
                )
                assert set(filtered_identifiers).issubset(set(pre_row_identifiers)), (
                    f"Expected the filtered rows to be a subset of the unfiltered set, got "
                    f"{sorted(set(filtered_identifiers) - set(pre_row_identifiers))} not present "
                    f"before filtering"
                )
                assert (
                    analytics_page.users_count.text_content()
                    == f"{len(filtered_identifiers)} users"
                ), (
                    f"Expected the count label to read "
                    f"'{len(filtered_identifiers)} users' while filtered, got "
                    f"{analytics_page.users_count.text_content()!r}"
                )
                assert search_response.get("total") == len(filtered_identifiers), (
                    f"Expected the search response's total "
                    f"{search_response.get('total')!r} to match the rendered row count "
                    f"{len(filtered_identifiers)}"
                )

                analytics_page.clear_users_search()
                assert analytics_page.users_search_input.input_value() == "", (
                    "Expected the search input to be empty after clearing it"
                )
                restored_identifiers = [
                    analytics_page.get_user_row_identifier(i)
                    for i in range(analytics_page.get_users_row_count())
                ]
                assert restored_identifiers == pre_row_identifiers, (
                    f"Expected clearing the search to restore the complete original row list, in "
                    f"order: expected {pre_row_identifiers}, got {restored_identifiers}"
                )
                assert analytics_page.users_count.text_content() == pre_count_text, (
                    f"Expected the count label to return to {pre_count_text!r} after clearing "
                    f"the search, got {analytics_page.users_count.text_content()!r}"
                )

            assert not console_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}"
            )
        finally:
            analytics_page.clear_users_search()
            console_errors.stop()
