"""UI test — Token name and expiration columns are sortable.

Read-only verification against the logged-in user's existing personal-token
data (`.agents/testing.md` § Test data strategy). This case never creates,
renames, or deletes a token: two of the live rows are irrecoverably `Expired`
(the create form only offers future expirations) and ELITEA-2284's merged test
reads its `expired` branch off them.

The assertions are RELATIONAL, not literal — `observed == sorted(observed)`
rather than a hardcoded name list. The token names are shared, mutable, real
leftover data; a literal expectation would break the day anyone adds a token,
and worse, would still pass if the product stopped sorting but the API happened
to return that order. The values still come from the product either way, so
this is the correct assertion, not a weakened one (AFS § Assertion shape).

⚠️ Case-text divergence (filed as #1880, `question` + `case-text-drift`): case
steps 2-5 claim the FIRST Token-name click sorts ascending and the second
descending. The product's default sort is ALREADY name-ascending
(`useTableSort({ defaultField: 'name', defaultDirection: 'asc' })`), so the
first click flips to DESCENDING and the second returns to ascending. The
product is correct and internally consistent; the case text is stale, so this
test asserts the live contract (reverse-masking guard).

No substitution of the system under test: every asserted value is read off the
live rendered table.

Test case: ELITEA-2279
AFS: test-specs/settings-personal-tokens/l3_token-name-and-expiration-columns-are-sortable_ELITEA-2279.md
"""

import logging

import allure
import pytest
from pages.personal_tokens_page import PersonalTokensPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

MIN_TOKEN_ROWS = 2
SORTABLE_FIELDS = ("name", "expires")
NON_SORTABLE_FIELDS = ("token", "actions")
EXPECTED_SORT_ICON_COUNT = len(SORTABLE_FIELDS)
NEVER_STATE = "never"


class TestPersonalTokensColumnSorting:
    """ELITEA-2279 — Token name and expiration columns are sortable."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/personal-tokens/ELITEA-2279_token-name-and-expiration-columns-are-sortable.md",
        "onetest-ai Test Case link",
    )
    def test_token_name_and_expiration_columns_are_sortable(self, page):
        """Only the name and expiration columns expose a sort control; clicking
        each toggles the rendered row order between its two directions without
        adding or dropping rows."""
        tokens_page = PersonalTokensPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Step 1 — Navigate to Settings -> Personal Tokens with at least two "
            "tokens: the populated table renders, exactly the two sortable "
            "columns expose a sort control, and the table arrives already "
            "sorted name-ascending"
        ):
            tokens_page.navigate()

            row_count = tokens_page.token_row.count()
            assert row_count >= MIN_TOKEN_ROWS, (
                f"Case precondition — expected at least {MIN_TOKEN_ROWS} token rows so "
                f"the ordering assertions are meaningful, got {row_count}"
            )

            sort_icon_count = tokens_page.get_sort_icon_count()
            assert sort_icon_count == EXPECTED_SORT_ICON_COUNT, (
                f"Expected exactly {EXPECTED_SORT_ICON_COUNT} sort controls (the "
                f"'name' and 'expires' columns), got {sort_icon_count}"
            )
            for field in SORTABLE_FIELDS:
                assert tokens_page.get_sort_icon(field).is_visible(), (
                    f"Expected the {field!r} column to expose a visible sort control"
                )
            # The case title asserts WHICH columns are sortable — without the
            # negative side the claim would pass even if all four became sortable.
            for field in NON_SORTABLE_FIELDS:
                expect(tokens_page.get_sort_icon(field)).to_have_count(0)

            names_default = tokens_page.get_row_names()
            assert names_default == sorted(names_default, key=str.lower), (
                "Expected the table to arrive already sorted name-ascending with no "
                f"interaction (useTableSort defaultField='name'/'asc'), got {names_default}"
            )

        with allure.step(
            "Step 2 — Click the Token name column header: the table re-sorts by "
            "name DESCENDING (the default is already ascending, so the first "
            "click flips it — see the case-text divergence filed as #1880)"
        ):
            tokens_page.click_column_header("name")
            expect(tokens_page.row_name_cell).to_have_text(
                sorted(names_default, key=str.lower, reverse=True)
            )

        with allure.step(
            "Step 3 — Click the Token name column header again: the table "
            "returns to name ASCENDING, matching the load-time order"
        ):
            tokens_page.click_column_header("name")
            expect(tokens_page.row_name_cell).to_have_text(names_default)

        with allure.step(
            "Step 4 — Click the Expiration column header: dated rows sort before "
            "the never-expiring rows, and the row count is unchanged (sorting "
            "reorders, it never filters)"
        ):
            states_default = tokens_page.get_row_expiration_states()
            assert NEVER_STATE in states_default and any(
                state != NEVER_STATE for state in states_default
            ), (
                "Expiration-sort precondition — expected the live token set to hold "
                "both never-expiring and dated rows so the ordering assertion is not "
                f"vacuous, got states {states_default}"
            )

            tokens_page.click_column_header("expires")
            # The re-render lands when the first row is no longer a "never" row;
            # to_have_count auto-retries, so this is the wait as well as a check.
            expect(tokens_page.get_first_row_expiration_status(NEVER_STATE)).to_have_count(0)

            states_asc = tokens_page.get_row_expiration_states()
            is_never_asc = [state == NEVER_STATE for state in states_asc]
            assert is_never_asc == sorted(is_never_asc), (
                "Expected every dated row to precede every never-expiring row "
                f"(expires ascending puts null last), got states {states_asc}"
            )
            assert tokens_page.token_row.count() == row_count, (
                f"Expected sorting to reorder rows without changing the row count "
                f"({row_count}), got {tokens_page.token_row.count()}"
            )

        with allure.step(
            "Step 5 — Click the Expiration column header again: the relation "
            "inverts — never-expiring rows sort before the dated rows — and the "
            "row count is still unchanged"
        ):
            tokens_page.click_column_header("expires")
            expect(tokens_page.get_first_row_expiration_status(NEVER_STATE)).to_have_count(1)

            states_desc = tokens_page.get_row_expiration_states()
            is_never_desc = [state == NEVER_STATE for state in states_desc]
            assert is_never_desc == sorted(is_never_desc, reverse=True), (
                "Expected every never-expiring row to precede every dated row "
                f"(expires descending puts null first), got states {states_desc}"
            )
            assert tokens_page.token_row.count() == row_count, (
                f"Expected sorting to reorder rows without changing the row count "
                f"({row_count}), got {tokens_page.token_row.count()}"
            )

        with allure.step("Step 6 — Verify no unexpected console errors across the flow"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
