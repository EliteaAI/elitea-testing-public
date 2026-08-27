"""UI test — Secrets listing: pagination navigates between pages correctly.

Read-only verification against the logged-in user's existing project secrets.
Pagination is pure client-side React state (`usePagination`) over the
already-fetched list — no network request fires on a page change or a page-size
change, so every wait is on the rendered range label / row set, never on a
response and never on a sleep.

Every expectation is computed from the product's OWN total, parsed out of the
range label it rendered — so the spec stays correct as the project's secret
count changes, and still fails loudly if the pagination arithmetic breaks.

No substitution of the system under test: every asserted value is read off the
live rendered table.

Test case: ELITEA-2332
AFS: test-specs/settings-secrets/l3_secrets-pagination-navigates-between-pages_ELITEA-2332.md

Known defect (EliteaAI/elitea-testing-public#1203): see the isolated soft
failure at the end of the flow.
"""

import logging

import allure
import pytest
from pages.secrets_page import SecretsPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

DEFAULT_PAGE_SIZE = 10
SMALLER_PAGE_SIZE = 5


def _is_known_defect_1203(text: str) -> bool:
    """True for the known, filed, isolated console error EliteaAI/
    elitea-testing-public#1203 ("Maximum update depth exceeded" on mount)."""
    return "Maximum update depth exceeded" in text


class TestSecretsPagination:
    """ELITEA-2332 — the next-page arrow advances both the range label and the
    rendered data, and changing the rows-per-page selector re-renders the table
    at the chosen size from the first page."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2332_secrets-listing-pagination-navigates-between-pages-correctly.md",
        "onetest-ai Test Case link",
    )
    def test_secrets_pagination_navigates_between_pages(self, page):
        secrets_page = SecretsPage(page)
        console_errors = collect_console_errors(page)
        soft_failures: list[str] = []

        with allure.step(
            "Step 1 — Navigate to Settings -> Secrets with more than 10 secrets"
        ):
            secrets_page.navigate()
            total = secrets_page.get_pagination_total()
            assert total > DEFAULT_PAGE_SIZE, (
                f"Case precondition — expected more than {DEFAULT_PAGE_SIZE} secrets so "
                f"the table actually paginates, got a total of {total}. This case cannot "
                "be run on a single-page dataset."
            )
            page1_names = secrets_page.get_row_names()

        with allure.step('Step 2 — Verify the page range shows "1 - 10 of N"'):
            assert secrets_page.get_pagination_text() == f"1 - {DEFAULT_PAGE_SIZE} of {total}", (
                f"Expected the first-page range '1 - {DEFAULT_PAGE_SIZE} of {total}', "
                f"got {secrets_page.get_pagination_text()!r}"
            )
            expect(secrets_page.secret_row).to_have_count(DEFAULT_PAGE_SIZE)
            expect(secrets_page.prev_page_button).to_be_disabled()
            expect(secrets_page.next_page_button).to_be_enabled()

        with allure.step("Step 3 — Click the next page arrow"):
            secrets_page.click_next_page()

        with allure.step(
            "Step 4 — Verify the next set of secrets is shown and the page range updates"
        ):
            expected_end = min(2 * DEFAULT_PAGE_SIZE, total)
            assert (
                secrets_page.get_pagination_text()
                == f"{DEFAULT_PAGE_SIZE + 1} - {expected_end} of {total}"
            ), (
                f"Expected the second-page range '{DEFAULT_PAGE_SIZE + 1} - {expected_end} "
                f"of {total}', got {secrets_page.get_pagination_text()!r}"
            )

            page2_names = secrets_page.get_row_names()
            # A range label that advanced while the rows stayed put is exactly
            # the regression this assertion exists to catch.
            assert set(page2_names).isdisjoint(set(page1_names)), (
                "Expected page 2 to render a different set of secrets than page 1; "
                f"overlap: {sorted(set(page2_names) & set(page1_names))}"
            )
            expect(secrets_page.prev_page_button).to_be_enabled()

        with allure.step(
            f'Step 5 — Change "Rows per page" to {SMALLER_PAGE_SIZE}'
        ):
            secrets_page.select_page_size(SMALLER_PAGE_SIZE)

        with allure.step(
            "Step 6 — Verify the table updates to show the selected number of rows "
            "per page (and returns to the first page)"
        ):
            expect(secrets_page.secret_row).to_have_count(SMALLER_PAGE_SIZE)
            expect(secrets_page.page_size_select).to_have_text(str(SMALLER_PAGE_SIZE))
            assert (
                secrets_page.get_pagination_text() == f"1 - {SMALLER_PAGE_SIZE} of {total}"
            ), (
                f"Expected the range to reset to '1 - {SMALLER_PAGE_SIZE} of {total}' after "
                f"the page-size change, got {secrets_page.get_pagination_text()!r}"
            )
            # handlePageSizeChange resets the page index — staying on a now
            # out-of-range page is a classic pagination bug.
            expect(secrets_page.prev_page_button).to_be_disabled()
            assert secrets_page.get_pagination_total() == total, (
                f"Expected the dataset total to be untouched by paging and resizing "
                f"({total}), got {secrets_page.get_pagination_total()}"
            )

        with allure.step("Step 7 — Verify no unexpected console errors across the flow"):
            unexpected_errors = [e for e in console_errors if not _is_known_defect_1203(e)]
            assert not unexpected_errors, f"Unexpected console errors: {unexpected_errors}"

            known_defect_errors = [e for e in console_errors if _is_known_defect_1203(e)]
            if known_defect_errors:
                # Known defect: EliteaAI/elitea-testing-public#1203
                soft_failures.append(
                    "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1203: "
                    f"React 'Maximum update depth exceeded' console error(s) on "
                    f"/settings/secrets mount: {len(known_defect_errors)} occurrence(s)"
                )

        if soft_failures:
            pytest.fail(
                "Test flow completed and all functional assertions passed, but "
                "known-defect soft failures were recorded:\n" + "\n".join(soft_failures)
            )
