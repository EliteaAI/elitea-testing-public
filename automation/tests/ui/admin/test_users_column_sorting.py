"""UI test — Users table columns are sortable.

Read-only verification against the active project's existing user rows
(`.agents/testing.md` § Test data strategy). This case never creates, edits
or deletes a user, and sorting is client-side, so nothing is mutated.

The assertions are RELATIONAL, not literal — the expected order is computed
from the *observed* rows rather than a hardcoded name/email/datetime list.
The user set is shared, mutable, real data (project 400 currently carries two
real users plus two orphaned invite rows from an earlier ELITEA-2304 run), so
a literal expectation would break the day anyone invites or removes someone —
and, worse, would still pass if the product stopped sorting but the API
happened to return that order. Both sides of every comparison are read off the
live rendered table, so nothing about the system under test is substituted.

Null placement is part of the asserted contract, not an edge case dodged:
`useTableSort` sorts null/blank values LAST ascending and FIRST descending,
and this project exercises both branches (two rows have no name and no last
login). Note the two columns render their null differently — the Name cell
renders an empty string, the Last-login cell renders the literal "-".

⚠️ Case-text divergence (filed as #1970, `question`; siblings #1880 for the
Personal Tokens table and #1901 for Secrets): case steps 2-4 claim the FIRST
Name-header click sorts ascending and the second descending. The table's
default sort is ALREADY name-ascending
(`useTableSort({defaultField: 'name', defaultDirection: 'asc'})`), so the
first click flips to DESCENDING and the second returns to ascending. The
product is correct and internally consistent; the case text is stale, so this
test asserts the live contract (reverse-masking guard). The ascending state is
still fully covered — at the second click rather than the first.

Test case: ELITEA-2293
AFS: test-specs/settings-users-and-roles/l2_users-table-columns-are-sortable_ELITEA-2293.md
"""

import logging

import allure
import pytest
from pages.admin_users_page import AdminUsersPage
from playwright.sync_api import expect
from utils.console_errors import (
    TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL,
    collect_console_errors,
    exclude_known_defect_urls,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

MIN_USER_ROWS = 2
SORTABLE_FIELDS = ("name", "email", "last_login")
NON_SORTABLE_FIELDS = ("roles", "actions")
# Two columns, two null renderings: GridTableRowNameCell leaves the cell empty
# for a user who has never logged in, while GridTableRowDataCell substitutes
# "-" via its `value || '-'` fallback.
NAME_NULL = ""
LAST_LOGIN_NULL = "-"


def _expected_order(values: list[str], null_marker: str, descending: bool) -> list[str]:
    """Return *values* in the order `useTableSort` renders them.

    Mirrors the product's documented rule rather than re-deriving it: real
    values compare case-insensitively, and null/blank values sort LAST
    ascending / FIRST descending (`useTableSort`'s explicit `aValue == null`
    branch). ISO-8601 datetimes sort correctly as plain strings, so the same
    helper serves the Name, Email and Last-login columns.
    """
    real = sorted((v for v in values if v != null_marker), key=str.lower, reverse=descending)
    nulls = [v for v in values if v == null_marker]
    return nulls + real if descending else real + nulls


class TestUsersColumnSorting:
    """ELITEA-2293 — Users table columns are sortable."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2293_users-table-columns-are-sortable.md",
        "onetest-ai Test Case link",
    )
    def test_users_table_columns_are_sortable(self, page):
        """Exactly the Name, Email and Last-login columns expose a sort
        control; clicking each toggles the rendered row order between its two
        directions — nulls last ascending, first descending — without ever
        adding or dropping a row."""
        users_page = AdminUsersPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Step 1 — Navigate to Settings -> Users with at least two rows: the "
            "populated table renders, exactly the three sortable columns expose a "
            "sort control, and the table arrives already sorted name-ascending"
        ):
            users_page.navigate()

            row_count = users_page.user_row.count()
            assert row_count >= MIN_USER_ROWS, (
                f"Case precondition — expected at least {MIN_USER_ROWS} user rows so the "
                f"ordering assertions are meaningful, got {row_count}"
            )

            for field in SORTABLE_FIELDS:
                expect(users_page.get_sort_icon(field)).to_have_count(1)
            # The case title asserts WHICH columns are sortable — without the
            # negative side the claim would still pass if every column became
            # sortable.
            for field in NON_SORTABLE_FIELDS:
                expect(users_page.get_sort_icon(field)).to_have_count(0)

            names_ascending = users_page.get_row_names()
            assert names_ascending == _expected_order(names_ascending, NAME_NULL, descending=False), (
                "Expected the table to arrive already sorted name-ascending with no "
                "interaction (useTableSort defaultField='name'/'asc', nulls last), got "
                f"{names_ascending}"
            )

        with allure.step(
            "Step 2 — Click the Name column header: the table re-sorts by name "
            "DESCENDING (the default is already ascending, so the first click flips "
            "it — see the case-text divergence filed as #1970)"
        ):
            users_page.click_column_header("name")
            expect(users_page.row_name_cell).to_have_text(
                _expected_order(names_ascending, NAME_NULL, descending=True)
            )

        with allure.step(
            "Step 3 — Click the Name column header again: the table returns to name "
            "ASCENDING, matching the load-time order exactly"
        ):
            users_page.click_column_header("name")
            expect(users_page.row_name_cell).to_have_text(names_ascending)

        with allure.step(
            "Step 4 — Click the Email column header: the table sorts by email "
            "ascending (switching to a new field always starts at 'asc'), and the "
            "row count is unchanged — sorting reorders, it never filters"
        ):
            emails_before = users_page.get_row_emails()
            users_page.click_column_header("email")

            expect(users_page.row_email_cell).to_have_text(
                _expected_order(emails_before, NAME_NULL, descending=False)
            )
            expect(users_page.user_row).to_have_count(row_count)

        with allure.step(
            "Step 5 — Click the Last login column header: dated rows sort in "
            "ascending datetime order and every never-logged-in row ('-') sorts "
            "after them; the row count is still unchanged"
        ):
            last_logins_before = users_page.get_row_last_logins()
            assert any(value != LAST_LOGIN_NULL for value in last_logins_before), (
                "Last-login-sort precondition — expected at least one row with a real "
                f"last-login datetime so the ordering assertion is not vacuous, got "
                f"{last_logins_before}"
            )

            users_page.click_column_header("last_login")

            expect(users_page.row_last_login_cell).to_have_text(
                _expected_order(last_logins_before, LAST_LOGIN_NULL, descending=False)
            )
            expect(users_page.user_row).to_have_count(row_count)

        with allure.step(
            "Step 6 — Click the Last login column header again: the relation "
            "inverts — never-logged-in rows first, then the dated rows in "
            "descending order — and the row count is still unchanged"
        ):
            users_page.click_column_header("last_login")

            expect(users_page.row_last_login_cell).to_have_text(
                _expected_order(last_logins_before, LAST_LOGIN_NULL, descending=True)
            )
            expect(users_page.user_row).to_have_count(row_count)

        with allure.step("Step 7 — Verify no unexpected console errors across the flow"):
            # Known defect: #1971 (regression of the closed #554) — during the
            # project switch this page object performs, EliteaUI's `toolkitTypes`
            # query can fire before `useSelectedProjectId()` resolves and request
            # a project-id-less `.../toolkits/prompt_lib/`, which 404s. Cosmetic
            # in the product, unrelated to anything this case drives. Excluded by
            # that EXACT URL only — never by status code, which would swallow the
            # next genuine 404. Delete this argument when #1971 is fixed.
            unexpected = exclude_known_defect_urls(
                console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL
            )
            assert not unexpected, f"Unexpected console errors: {unexpected}"
